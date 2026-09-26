package com.fingmi.xray.session;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import com.fingmi.xray.config.XrayPreferences;
import com.fingmi.xray.service.XrayOperation;
import com.fingmi.xray.util.XrayErrorSanitizer;

public final class XraySessionController implements XrayServiceClient.Listener, AutoCloseable {

    private static final long NO_OPERATION = Long.MIN_VALUE;
    private static final long CLEANUP_TIMEOUT_MS = 1_500L;
    private static final long STARTUP_TIMEOUT_MS = 30_000L;
    private static final long DISPOSE_UNBIND_DELAY_MS = 500L;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final XrayPreferences preferences;
    private final XrayServiceClient serviceClient;
    private final XraySessionListener listener;

    private long currentOperationId = XrayOperationIds.next();
    private long cleanupOperationId = NO_OPERATION;
    private long startupOperationId = NO_OPERATION;

    private int state = XraySessionListener.IDLE;
    private int socksPort;
    private boolean disposed;

    private final Runnable cleanupTimeout = this::onCleanupTimeout;
    private final Runnable startupTimeout = this::onStartupTimeout;

    public XraySessionController(Context context, XraySessionListener listener) {
        this.preferences = new XrayPreferences(context);
        this.serviceClient = new XrayServiceClient(context, this);
        this.listener = listener;
    }

    public int getState() {
        return state;
    }

    public int getSocksPort() {
        return state == XraySessionListener.RUNNING ? socksPort : 0;
    }

    public boolean isRunning() {
        return state == XraySessionListener.RUNNING;
    }

    public void start() {
        assertMainThread();
        if (disposed || state == XraySessionListener.STARTING || state == XraySessionListener.RUNNING) {
            return;
        }

        try {
            String shareLink = preferences.getShareLink();
            if (shareLink.isEmpty()) {
                fail("Xray is not configured");
                return;
            }

            long operationId = XrayOperationIds.next();
            currentOperationId = operationId;
            startupOperationId = operationId;
            state = XraySessionListener.STARTING;
            socksPort = 0;
            notifyState(XraySessionListener.STARTING, 0, "");
            // A listener may synchronously stop/close/replace this session.
            if (disposed || currentOperationId != operationId
                    || state != XraySessionListener.STARTING) return;

            serviceClient.execute(new XrayServiceClient.Request(
                    operationId,
                    XrayOperation.START,
                    shareLink,
                    preferences.isUdpEnabled(),
                    () -> scheduleStartupTimeout(operationId)));
        } catch (Exception error) {
            startupOperationId = NO_OPERATION;
            main.removeCallbacks(startupTimeout);
            fail(XrayErrorSanitizer.sanitize(error));
        }
    }

    public void stop() {
        assertMainThread();
        if (disposed || state == XraySessionListener.IDLE) return;
        stopSession();
    }

    private void stopSession() {
        startupOperationId = NO_OPERATION;
        main.removeCallbacks(startupTimeout);

        long operationId = XrayOperationIds.next();
        currentOperationId = operationId;
        state = XraySessionListener.IDLE;
        socksPort = 0;
        cleanupOperationId = operationId;
        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                XrayOperation.STOP,
                "",
                false,
                () -> scheduleCleanupTimeout(operationId)));
        // Dispatch STOP before notifying listeners that may start a replacement.
        if (!disposed && currentOperationId == operationId)
            notifyState(XraySessionListener.IDLE, 0, "");
    }

    @Override
    public void close() {
        assertMainThread();
        if (disposed) return;

        // Seal the lifecycle before any transport/listener can reenter.
        disposed = true;
        if (state != XraySessionListener.IDLE) stopSession();

        if (cleanupOperationId == NO_OPERATION) {
            main.postDelayed(serviceClient::disconnect, DISPOSE_UNBIND_DELAY_MS);
        }
    }

    @Override
    public void onResult(XrayResult result) {
        assertMainThread();

        if (result.operation == XrayOperation.STOP
                && result.operationId == cleanupOperationId) {
            cleanupOperationId = NO_OPERATION;
            main.removeCallbacks(cleanupTimeout);
            if (result.operationId != currentOperationId) return;

            if (!result.success) {
                serviceClient.cancel(XrayOperation.STOP, result.operationId);
                if (!disposed) {
                    String message = XrayErrorSanitizer.sanitize(result.message);
                    if (state == XraySessionListener.IDLE) {
                        notifyState(XraySessionListener.IDLE, 0, message);
                    } else {
                        fail(message);
                    }
                }
                return;
            }

            if (disposed) {
                serviceClient.disconnect();
                return;
            }

            if (result.operationId != currentOperationId) return;
        }

        if (disposed || result.operationId != currentOperationId) return;

        if (result.operation == XrayOperation.START) {
            startupOperationId = NO_OPERATION;
            main.removeCallbacks(startupTimeout);
            cleanupOperationId = NO_OPERATION;
            main.removeCallbacks(cleanupTimeout);

            if (!result.success) {
                serviceClient.disconnect();
                fail(result.message);
                return;
            }

            state = XraySessionListener.RUNNING;
            socksPort = result.socksPort;
            notifyState(XraySessionListener.RUNNING, socksPort, "");
            return;
        }

        if (result.operation == XrayOperation.STOP) {
            cleanupOperationId = NO_OPERATION;
            main.removeCallbacks(cleanupTimeout);

            if (result.success) {
                serviceClient.disconnect();
                return;
            }

            serviceClient.cancel(XrayOperation.STOP, result.operationId);
            String message = XrayErrorSanitizer.sanitize(result.message);
            if (state == XraySessionListener.IDLE) {
                notifyState(XraySessionListener.IDLE, 0, message);
            } else {
                fail(message);
            }
        }
    }

    @Override
    public void onConnectionFailure(long operationId, String message) {
        assertMainThread();

        if (operationId == startupOperationId) {
            startupOperationId = NO_OPERATION;
            main.removeCallbacks(startupTimeout);
        }
        if (operationId == cleanupOperationId) {
            cleanupOperationId = NO_OPERATION;
            main.removeCallbacks(cleanupTimeout);
        }

        if (operationId != currentOperationId) return;

        cleanupOperationId = NO_OPERATION;
        main.removeCallbacks(cleanupTimeout);

        serviceClient.disconnect();
        if (!disposed
                && (state == XraySessionListener.STARTING
                || state == XraySessionListener.RUNNING)) {
            fail(message);
        }
    }

    private void scheduleCleanupTimeout(long operationId) {
        if (cleanupOperationId != operationId) return;
        main.removeCallbacks(cleanupTimeout);
        main.postDelayed(cleanupTimeout, CLEANUP_TIMEOUT_MS);
    }

    private void scheduleStartupTimeout(long operationId) {
        if (startupOperationId != operationId
                || currentOperationId != operationId
                || state != XraySessionListener.STARTING) {
            return;
        }
        main.removeCallbacks(startupTimeout);
        main.postDelayed(startupTimeout, STARTUP_TIMEOUT_MS);
    }

    private void onCleanupTimeout() {
        long operationId = cleanupOperationId;
        if (operationId == NO_OPERATION) return;

        cleanupOperationId = NO_OPERATION;
        // Cleanup owns only its STOP, never a replacement START or its Binder.
        if (operationId != currentOperationId) return;
        serviceClient.cancel(XrayOperation.STOP, operationId);
    }

    private void onStartupTimeout() {
        long operationId = startupOperationId;
        if (operationId == NO_OPERATION) return;

        startupOperationId = NO_OPERATION;
        main.removeCallbacks(startupTimeout);

        if (!disposed
                && currentOperationId == operationId
                && state == XraySessionListener.STARTING) {
            serviceClient.cancel(XrayOperation.START, operationId);
            fail("Xray startup timed out");
        }
    }

    private void fail(String message) {
        state = XraySessionListener.IDLE;
        socksPort = 0;
        String safe = XrayErrorSanitizer.sanitize(message);
        long failedOperationId = currentOperationId;
        notifyState(XraySessionListener.ERROR, 0, safe);
        if (!disposed && currentOperationId == failedOperationId
                && state == XraySessionListener.IDLE)
            notifyState(XraySessionListener.IDLE, 0, "");
    }

    private void notifyState(int state, int port, String message) {
        if (listener != null) listener.onXrayStateChanged(state, port, message == null ? "" : message);
    }

    private static void assertMainThread() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("XraySessionController must be used from the main thread");
        }
    }
}

