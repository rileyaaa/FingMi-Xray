package com.fingmi.xray.service;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.Process;
import android.os.RemoteException;

import com.fingmi.xray.config.XrayConfigFactory;
import com.fingmi.xray.core.LibXrayBridge;
import com.fingmi.xray.security.XrayCertificatePins;
import com.fingmi.xray.security.XrayShareLinkSecurity;
import com.fingmi.xray.util.XrayErrorSanitizer;

import org.json.JSONObject;

import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.TimeUnit;

public final class XrayService extends Service {

    private static final long NO_SESSION = Long.MIN_VALUE;

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor(new XrayThreadFactory());
    private final XrayGenerationGate sessionGate = new XrayGenerationGate();
    private final XrayGenerationGate operationGate = new XrayGenerationGate();

    private volatile long activeSessionId = NO_SESSION;

    private LibXrayBridge bridge;
    private XrayConfigFactory configFactory;
    private XrayCertificatePins certificatePins;

    private final IXrayService.Stub binder = new IXrayService.Stub() {
        @Override
        public void validate(long operationId, String shareLink, boolean udp, IXrayCallback callback) {
            operationGate.begin(operationId);
            executor.execute(() -> validateInternal(operationId, shareLink, udp, callback));
        }

        @Override
        public void test(long operationId, String shareLink, boolean udp, IXrayCallback callback) {
            operationGate.begin(operationId);
            executor.execute(() -> testInternal(operationId, shareLink, udp, callback));
        }

        @Override
        public void start(long operationId, String shareLink, boolean udp, IXrayCallback callback) {
            sessionGate.begin(operationId);
            operationGate.begin(operationId);
            executor.execute(() -> startInternal(operationId, shareLink, udp, callback));
        }

        @Override
        public void stop(long operationId, IXrayCallback callback) {
            sessionGate.begin(operationId);
            operationGate.begin(operationId);
            executor.execute(() -> stopInternal(operationId, callback));
        }

        @Override
        public void resetSecurity(long operationId, IXrayCallback callback) {
            operationGate.begin(operationId);
            executor.execute(() -> resetSecurityInternal(operationId, callback));
        }

        @Override
        public void cancel(int operation, long operationId) {
            cancelInternal(operation, operationId);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        bridge = new LibXrayBridge();
        certificatePins = new XrayCertificatePins(this);
        XrayShareLinkSecurity shareLinkSecurity =
                new XrayShareLinkSecurity(bridge, certificatePins);
        configFactory = new XrayConfigFactory(bridge, shareLinkSecurity);
    }

    @Override
    public IBinder onBind(Intent intent) {
        return binder;
    }

    private void validateInternal(
            long operationId,
            String shareLink,
            boolean udp,
            IXrayCallback callback) {
        try {
            ensureOperationCurrent(operationId);
            ensureNoLiveSession();

            Exception bindError = null;
            for (int attempt = 0; attempt < 3; attempt++) {
                try {
                    int port = bridge.getFreePort();
                    JSONObject config = configFactory.create(port, shareLink, udp);
                    ensureOperationCurrent(operationId);
                    bridge.validateConfig(config);
                    ensureOperationCurrent(operationId);
                    ensureOperationCurrent(operationId);
                    send(callback, operationId, XrayOperation.VALIDATE, true, 0, -1L, "");
                    return;
                } catch (Exception error) {
                    bindError = error;
                    if (!isBindError(error) || attempt == 2) throw error;
                }
            }
            if (bindError != null) throw bindError;
            throw new IllegalStateException("Unable to allocate Xray port");
        } catch (Exception error) {
            send(callback, operationId, XrayOperation.VALIDATE, false, 0, -1L, errorMessage(error));
        }
    }

    private void testInternal(
            long operationId,
            String shareLink,
            boolean udp,
            IXrayCallback callback) {
        try {
            ensureOperationCurrent(operationId);
            ensureNoLiveSession();

            Exception bindError = null;
            for (int attempt = 0; attempt < 3; attempt++) {
                try {
                    int port = bridge.getFreePort();
                    JSONObject config = configFactory.create(port, shareLink, udp);
                    ensureOperationCurrent(operationId);
                    bridge.validateConfig(config);
                    ensureOperationCurrent(operationId);
                    long latency = bridge.testLatency(config, XrayConfigFactory.PROXY_TAG);
                    ensureOperationCurrent(operationId);
                    send(callback, operationId, XrayOperation.TEST, true, 0, latency, "");
                    return;
                } catch (Exception error) {
                    bindError = error;
                    if (!isBindError(error) || attempt == 2) throw error;
                }
            }
            if (bindError != null) throw bindError;
            throw new IllegalStateException("Unable to allocate Xray port");
        } catch (Exception error) {
            send(callback, operationId, XrayOperation.TEST, false, 0, -1L, errorMessage(error));
        }
    }

    private void startInternal(
            long operationId,
            String shareLink,
            boolean udp,
            IXrayCallback callback) {
        if (!ensureSessionCurrent(operationId, callback)) return;

        try {
            stopCore();
            if (!ensureSessionCurrent(operationId, callback)) return;

            Exception bindError = null;
            for (int attempt = 0; attempt < 3; attempt++) {
                if (!ensureSessionCurrent(operationId, callback)) return;

                int port = bridge.getFreePort();
                JSONObject config = configFactory.create(port, shareLink, udp);

                try {
                    if (!ensureSessionCurrent(operationId, callback)) return;
                    bridge.validateConfig(config);
                    if (!ensureSessionCurrent(operationId, callback)) return;

                    bridge.run(config);
                    activeSessionId = operationId;

                    if (!bridge.isRunning()) {
                        throw new IllegalStateException("Xray core did not enter running state");
                    }

                    if (!sessionGate.isCurrent(operationId)) {
                        stopCoreQuietly();
                        ensureSessionCurrent(operationId, callback);
                        return;
                    }

                    if (send(callback, operationId, XrayOperation.START, true, port, -1L, "")) {
                        return;
                    }

                    if (!stopCoreQuietly()) cancelInternal(XrayOperation.START, operationId);
                    return;
                } catch (Exception error) {
                    bindError = error;
                    boolean cleaned = stopCoreQuietly();
                    if (!ensureSessionCurrent(operationId, callback)) return;
                    if (!cleaned) throw error;
                    if (!isBindError(error) || attempt == 2) throw error;
                }
            }

            if (bindError != null) throw bindError;
        } catch (Exception error) {
            boolean cleaned = stopCoreQuietly();
            if (!ensureSessionCurrent(operationId, callback)) return;

            String message = errorMessage(error);
            if (!cleaned) message = "Xray cleanup required process reset: " + message;

            boolean delivered = send(
                    callback,
                    operationId,
                    XrayOperation.START,
                    false,
                    0,
                    -1L,
                    message);
            if (!cleaned || !delivered) cancelInternal(XrayOperation.START, operationId);
        }
    }

    private void stopInternal(long operationId, IXrayCallback callback) {
        if (!sessionGate.isCurrent(operationId)) {
            send(callback, operationId, XrayOperation.STOP, true, 0, -1L, "");
            return;
        }

        try {
            stopCore();
            send(callback, operationId, XrayOperation.STOP, true, 0, -1L, "");
        } catch (Exception error) {
            if (!sessionGate.isCurrent(operationId)) {
                send(callback, operationId, XrayOperation.STOP, true, 0, -1L, "");
                return;
            }

            boolean delivered = send(
                    callback,
                    operationId,
                    XrayOperation.STOP,
                    false,
                    0,
                    -1L,
                    "Xray cleanup required process reset: " + errorMessage(error));
            if (!delivered) cancelInternal(XrayOperation.STOP, operationId);
        }
    }

    private void resetSecurityInternal(long operationId, IXrayCallback callback) {
        try {
            ensureOperationCurrent(operationId);
            certificatePins.clear();
            ensureOperationCurrent(operationId);
            send(callback, operationId, XrayOperation.RESET_SECURITY, true, 0, -1L, "");
        } catch (Exception error) {
            send(
                    callback,
                    operationId,
                    XrayOperation.RESET_SECURITY,
                    false,
                    0,
                    -1L,
                    errorMessage(error));
        }
    }

    private void cancelInternal(int operation, long operationId) {
        boolean cancelled;
        if (operation == XrayOperation.START || operation == XrayOperation.STOP) {
            cancelled = sessionGate.cancel(operationId);
        } else if (operation == XrayOperation.VALIDATE
                || operation == XrayOperation.TEST
                || operation == XrayOperation.RESET_SECURITY) {
            cancelled = operationGate.cancel(operationId);
        } else {
            return;
        }

        if (cancelled) {
            sessionGate.invalidateAll();
            operationGate.invalidateAll();
            killPrivateProcess();
        }
    }

    private void ensureOperationCurrent(long operationId) {
        if (!operationGate.isCurrent(operationId)) {
            throw new IllegalStateException("Xray operation superseded by newer request");
        }
    }

    private boolean ensureSessionCurrent(long operationId, IXrayCallback callback) {
        if (sessionGate.isCurrent(operationId)) return true;
        send(
                callback,
                operationId,
                XrayOperation.START,
                false,
                0,
                -1L,
                "Xray startup superseded by newer request");
        return false;
    }

    private void ensureNoLiveSession() throws Exception {
        if (activeSessionId != NO_SESSION || bridge.isRunning()) {
            throw new IllegalStateException("Xray live session is running");
        }
    }

    private void stopCore() throws Exception {
        Exception last = null;
        try {
            for (int attempt = 0; attempt < 2; attempt++) {
                try {
                    bridge.stop();
                    activeSessionId = NO_SESSION;
                    return;
                } catch (Exception error) {
                    last = error;
                }
            }
            if (last != null) throw last;
        } finally {
            activeSessionId = NO_SESSION;
        }
    }

    private boolean stopCoreQuietly() {
        try {
            stopCore();
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    private static boolean isBindError(Exception error) {
        String message = error.getMessage();
        if (message == null) return false;
        String value = message.toLowerCase(Locale.ROOT);
        return value.contains("address already in use")
                || value.contains("bind:")
                || value.contains("failed to listen")
                || value.contains("cannot assign requested address");
    }

    private static boolean send(
            IXrayCallback callback,
            long operationId,
            int operation,
            boolean success,
            int socksPort,
            long latencyMs,
            String message) {
        if (callback == null) return false;
        try {
            callback.onResult(
                    operationId,
                    operation,
                    success,
                    socksPort,
                    latencyMs,
                    XrayErrorSanitizer.sanitize(message));
            return true;
        } catch (RemoteException ignored) {
            return false;
        }
    }

    private static String errorMessage(Exception error) {
        String value = XrayErrorSanitizer.sanitize(error);
        return value.isBlank() ? "Xray operation failed" : value;
    }

    private static void killPrivateProcess() {
        Process.killProcess(Process.myPid());
    }

    @Override
    public void onDestroy() {
        sessionGate.invalidateAll();
        operationGate.invalidateAll();

        executor.execute(this::stopCoreQuietly);
        executor.shutdown();
        try {
            if (!executor.awaitTermination(3L, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
            executor.shutdownNow();
        } finally {
            super.onDestroy();
            killPrivateProcess();
        }
    }

    private static final class XrayThreadFactory implements ThreadFactory {
        @Override
        public Thread newThread(Runnable runnable) {
            Thread thread = new Thread(runnable, "fingmi-xray");
            thread.setDaemon(true);
            return thread;
        }
    }
}
