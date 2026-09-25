package com.fongmi.android.tv.xray;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.Process;
import android.os.RemoteException;

import com.fongmi.android.tv.xray.legacy.LegacyLibXrayApi;
import com.fongmi.android.tv.xray.legacy.LegacyXrayCertificateStore;
import com.fongmi.android.tv.xray.legacy.LegacyXrayErrorSanitizer;
import com.fongmi.android.tv.xray.legacy.LegacyXrayGenerationGate;
import com.fongmi.android.tv.xray.legacy.LegacyXrayOperation;
import com.fongmi.android.tv.xray.legacy.LegacyXrayRuntimeConfigFactory;
import com.fongmi.android.tv.xray.legacy.LegacyXrayTransportSecurity;

import org.json.JSONObject;

import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * Behavior reconstruction of the shipped v5.6.0-xray.5 XrayService.
 *
 * <p>This is recovery source, not the final refactored module.</p>
 */
public final class XrayService extends Service {

    private static final long NO_SESSION = Long.MIN_VALUE;

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor(
                    runnable -> {
                        Thread thread =
                                new Thread(
                                        runnable,
                                        "fongmi-xray-core");
                        thread.setDaemon(true);
                        return thread;
                    });

    private final LegacyXrayGenerationGate sessionGate =
            new LegacyXrayGenerationGate();

    private final LegacyXrayGenerationGate operationGate =
            new LegacyXrayGenerationGate();

    private final LegacyLibXrayApi core =
            new LegacyLibXrayApi();

    private volatile long activeSessionId = NO_SESSION;

    private LegacyXrayCertificateStore certificateStore;
    private LegacyXrayRuntimeConfigFactory configFactory;

    private final IXrayService.Stub binder =
            new IXrayService.Stub() {
                @Override
                public void validate(
                        long operationId,
                        String shareLink,
                        boolean udp,
                        IXrayCallback callback) {
                    operationGate.begin(operationId);
                    executor.execute(
                            () -> validateInternal(
                                    operationId,
                                    shareLink,
                                    udp,
                                    callback));
                }

                @Override
                public void test(
                        long operationId,
                        String shareLink,
                        boolean udp,
                        IXrayCallback callback) {
                    operationGate.begin(operationId);
                    executor.execute(
                            () -> testInternal(
                                    operationId,
                                    shareLink,
                                    udp,
                                    callback));
                }

                @Override
                public void start(
                        long operationId,
                        String shareLink,
                        boolean udp,
                        IXrayCallback callback) {
                    sessionGate.begin(operationId);
                    operationGate.begin(operationId);
                    executor.execute(
                            () -> startInternal(
                                    operationId,
                                    shareLink,
                                    udp,
                                    callback));
                }

                @Override
                public void stop(
                        long operationId,
                        IXrayCallback callback) {
                    sessionGate.begin(operationId);
                    operationGate.begin(operationId);
                    executor.execute(
                            () -> stopInternal(operationId, callback));
                }

                @Override
                public void resetSecurity(
                        long operationId,
                        IXrayCallback callback) {
                    operationGate.begin(operationId);
                    executor.execute(
                            () -> resetSecurityInternal(
                                    operationId,
                                    callback));
                }

                @Override
                public void cancel(
                        int operation,
                        long operationId) {
                    cancelInternal(operation, operationId);
                }
            };

    @Override
    public IBinder onBind(Intent intent) {
        ensureSecurityHelpers();
        return binder;
    }

    private synchronized void ensureSecurityHelpers() {
        if (certificateStore != null && configFactory != null) return;

        certificateStore =
                new LegacyXrayCertificateStore(this);
        LegacyXrayTransportSecurity security =
                new LegacyXrayTransportSecurity(
                        core,
                        certificateStore);
        configFactory =
                new LegacyXrayRuntimeConfigFactory(
                        core,
                        security);
    }

    private void validateInternal(
            long operationId,
            String shareLink,
            boolean udp,
            IXrayCallback callback) {
        try {
            ensureOperationCurrent(operationId);
            ensureNoLiveSession();

            Exception last = null;
            for (int attempt = 0; attempt < 3; attempt++) {
                try {
                    int port = core.getFreePort();
                    JSONObject config =
                            configFactory.create(
                                    port,
                                    shareLink,
                                    udp);

                    ensureOperationCurrent(operationId);
                    core.validate(config);
                    ensureOperationCurrent(operationId);
                    ensureOperationCurrent(operationId);

                    sendResult(
                            callback,
                            operationId,
                            LegacyXrayOperation.VALIDATE,
                            true,
                            0,
                            -1L,
                            "");
                    return;
                } catch (Exception error) {
                    last = error;
                    if (!isBindFailure(error)) throw error;

                    if (attempt + 1 >= 3) {
                        throw error;
                    }
                }
            }

            if (last != null) throw last;
            throw new IllegalStateException(
                    "Unable to allocate Xray port");
        } catch (Exception error) {
            sendResult(
                    callback,
                    operationId,
                    LegacyXrayOperation.VALIDATE,
                    false,
                    0,
                    -1L,
                    LegacyXrayErrorSanitizer.fromException(error));
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

            Exception last = null;
            for (int attempt = 0; attempt < 3; attempt++) {
                try {
                    int port = core.getFreePort();
                    JSONObject config =
                            configFactory.create(
                                    port,
                                    shareLink,
                                    udp);

                    ensureOperationCurrent(operationId);
                    core.validate(config);
                    ensureOperationCurrent(operationId);

                    long latency =
                            core.testLatency(
                                    config,
                                    LegacyXrayRuntimeConfigFactory.PROXY_TAG);

                    ensureOperationCurrent(operationId);
                    sendResult(
                            callback,
                            operationId,
                            LegacyXrayOperation.TEST,
                            true,
                            0,
                            latency,
                            "");
                    return;
                } catch (Exception error) {
                    last = error;
                    if (!isBindFailure(error)) throw error;

                    if (attempt + 1 >= 3) {
                        throw error;
                    }
                }
            }

            if (last != null) throw last;
            throw new IllegalStateException(
                    "Unable to allocate Xray port");
        } catch (Exception error) {
            sendResult(
                    callback,
                    operationId,
                    LegacyXrayOperation.TEST,
                    false,
                    0,
                    -1L,
                    LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    private void startInternal(
            long operationId,
            String shareLink,
            boolean udp,
            IXrayCallback callback) {
        if (notifyIfStartSuperseded(operationId, callback)) {
            return;
        }

        try {
            stopCore();

            if (notifyIfStartSuperseded(operationId, callback)) {
                return;
            }

            Exception last = null;
            for (int attempt = 0; attempt < 3; attempt++) {
                if (notifyIfStartSuperseded(
                        operationId,
                        callback)) {
                    return;
                }

                int port = core.getFreePort();
                JSONObject config =
                        configFactory.create(
                                port,
                                shareLink,
                                udp);

                if (notifyIfStartSuperseded(
                        operationId,
                        callback)) {
                    return;
                }

                try {
                    core.validate(config);

                    if (notifyIfStartSuperseded(
                            operationId,
                            callback)) {
                        return;
                    }

                    core.run(config);
                    activeSessionId = operationId;

                    if (!core.isRunning()) {
                        throw new IllegalStateException(
                                "Xray core did not enter running state");
                    }

                    if (!sessionGate.isCurrent(operationId)) {
                        try {
                            stopCore();
                        } catch (Exception ignored) {
                        }
                        notifyIfStartSuperseded(
                                operationId,
                                callback);
                        return;
                    }

                    boolean delivered =
                            sendResult(
                                    callback,
                                    operationId,
                                    LegacyXrayOperation.START,
                                    true,
                                    port,
                                    -1L,
                                    "");
                    if (delivered) return;

                    boolean cleaned;
                    try {
                        stopCore();
                        cleaned = true;
                    } catch (Exception ignored) {
                        cleaned = false;
                    }

                    if (cleaned) return;

                    cancelInternal(
                            LegacyXrayOperation.START,
                            operationId);
                    return;
                } catch (Exception error) {
                    last = error;

                    boolean cleaned;
                    try {
                        stopCore();
                        cleaned = true;
                    } catch (Exception ignored) {
                        cleaned = false;
                    }

                    if (notifyIfStartSuperseded(
                            operationId,
                            callback)) {
                        return;
                    }

                    if (!cleaned) throw error;
                    if (!isBindFailure(error)) throw error;

                    if (attempt + 1 >= 3) {
                        throw error;
                    }
                }
            }

            if (last != null) throw last;
            return;
        } catch (Exception error) {
            boolean cleaned;
            try {
                stopCore();
                cleaned = true;
            } catch (Exception ignored) {
                cleaned = false;
            }

            if (notifyIfStartSuperseded(
                    operationId,
                    callback)) {
                return;
            }

            String message =
                    LegacyXrayErrorSanitizer.fromException(error);
            if (!cleaned) {
                message =
                        "Xray cleanup required process reset: "
                                + message;
            }

            boolean delivered =
                    sendResult(
                            callback,
                            operationId,
                            LegacyXrayOperation.START,
                            false,
                            0,
                            -1L,
                            message);

            if (cleaned && delivered) return;

            cancelInternal(
                    LegacyXrayOperation.START,
                    operationId);
        }
    }

    private void stopInternal(
            long operationId,
            IXrayCallback callback) {
        if (!sessionGate.isCurrent(operationId)) {
            sendResult(
                    callback,
                    operationId,
                    LegacyXrayOperation.STOP,
                    true,
                    0,
                    -1L,
                    "");
            return;
        }

        try {
            stopCore();
            sendResult(
                    callback,
                    operationId,
                    LegacyXrayOperation.STOP,
                    true,
                    0,
                    -1L,
                    "");
        } catch (Exception error) {
            if (!sessionGate.isCurrent(operationId)) {
                sendResult(
                        callback,
                        operationId,
                        LegacyXrayOperation.STOP,
                        true,
                        0,
                        -1L,
                        "");
                return;
            }

            boolean delivered =
                    sendResult(
                            callback,
                            operationId,
                            LegacyXrayOperation.STOP,
                            false,
                            0,
                            -1L,
                            "Xray cleanup required process reset: "
                                    + LegacyXrayErrorSanitizer
                                            .fromException(error));

            // Exact shipped behavior: if main process received the STOP
            // failure, it issues cancel(operation=4,id), which kills this
            // process. Only an undeliverable failure is killed here.
            if (delivered) return;

            cancelInternal(
                    LegacyXrayOperation.STOP,
                    operationId);
        }
    }

    private void resetSecurityInternal(
            long operationId,
            IXrayCallback callback) {
        try {
            ensureOperationCurrent(operationId);

            LegacyXrayCertificateStore.resetAll(this);

            synchronized (this) {
                certificateStore = null;
                configFactory = null;
                ensureSecurityHelpers();
            }

            sendResult(
                    callback,
                    operationId,
                    LegacyXrayOperation.RESET_SECURITY,
                    true,
                    0,
                    -1L,
                    "");
        } catch (Exception error) {
            sendResult(
                    callback,
                    operationId,
                    LegacyXrayOperation.RESET_SECURITY,
                    false,
                    0,
                    -1L,
                    LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    private void ensureNoLiveSession() throws Exception {
        if (activeSessionId != NO_SESSION
                || core.isRunning()) {
            throw new IllegalStateException(
                    "Xray live session is running");
        }
    }

    private void ensureOperationCurrent(long operationId) {
        if (!operationGate.isCurrent(operationId)) {
            throw new IllegalStateException(
                    "Xray operation superseded by newer request");
        }
    }

    /**
     * @return true when the requested start is stale and a failure callback
     * was attempted.
     */
    private boolean notifyIfStartSuperseded(
            long operationId,
            IXrayCallback callback) {
        if (sessionGate.isCurrent(operationId)) {
            return false;
        }

        sendResult(
                callback,
                operationId,
                LegacyXrayOperation.START,
                false,
                0,
                -1L,
                "Xray startup superseded by newer request");
        return true;
    }

    private void stopCore() throws Exception {
        Exception last = null;
        try {
            for (int attempt = 0; attempt < 2; attempt++) {
                try {
                    core.stop();
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

    private void cancelInternal(
            int operation,
            long operationId) {
        boolean cancelled;

        if (operation == LegacyXrayOperation.START
                || operation == LegacyXrayOperation.STOP) {
            cancelled =
                    sessionGate.cancelCurrent(operationId);
        } else if (operation == LegacyXrayOperation.VALIDATE
                || operation == LegacyXrayOperation.TEST
                || operation
                        == LegacyXrayOperation.RESET_SECURITY) {
            cancelled =
                    operationGate.cancelCurrent(operationId);
        } else {
            return;
        }

        if (!cancelled) return;

        sessionGate.invalidateAll();
        operationGate.invalidateAll();
        Process.killProcess(Process.myPid());
    }

    private static boolean isBindFailure(Exception error) {
        String message = error.getMessage();
        if (message == null) return false;

        String value = message.toLowerCase(Locale.ROOT);
        return value.contains("address already in use")
                || value.contains("bind:")
                || value.contains("failed to listen")
                || value.contains(
                        "cannot assign requested address");
    }

    private static boolean sendResult(
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
                    LegacyXrayErrorSanitizer.sanitize(message));
            return true;
        } catch (RemoteException ignored) {
            return false;
        }
    }

    @Override
    public void onDestroy() {
        sessionGate.invalidateAll();
        operationGate.invalidateAll();

        executor.execute(
                () -> {
                    try {
                        stopCore();
                    } catch (Exception ignored) {
                    }
                });

        executor.shutdown();
        try {
            if (!executor.awaitTermination(
                    3L,
                    TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
            executor.shutdownNow();
        } finally {
            super.onDestroy();
            Process.killProcess(Process.myPid());
        }
    }
}
