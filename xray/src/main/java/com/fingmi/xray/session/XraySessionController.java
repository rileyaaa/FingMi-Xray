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

        startupOperationId = NO_OPERATION;
        main.removeCallbacks(startupTimeout);

        long operationId = XrayOperationIds.next();
        currentOperationId = operationId;
        state = XraySessionListener.IDLE;
        socksPort = 0;
        notifyState(XraySessionListener.IDLE, 0, "");

        cleanupOperationId = operationId;
        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                XrayOperation.STOP,
                "",
                false,
                () -> scheduleCleanupTimeout(operationId)));
    }

    @Override
    public void close() {
        assertMainThread();
        if (disposed) return;

        if (state != XraySessionListener.IDLE) stop();
        disposed = true;

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

            if (!result.success) {
                if (!disposed) {
                    String message = XrayErrorSanitizer.sanitize(result.message);
                    if (state == XraySessionListener.IDLE) {
                        notifyState(XraySessionListener.IDLE, 0, message);
                    } else {
                        fail(message);
                    }
                }
                serviceClient.cancel(XrayOperation.STOP, result.operationId);
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
                fail(result.message);
                serviceClient.disconnect();
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

            String message = XrayErrorSanitizer.sanitize(result.message);
            if (state == XraySessionListener.IDLE) {
                notifyState(XraySessionListener.IDLE, 0, message);
            } else {
                fail(message);
            }
            serviceClient.cancel(XrayOperation.STOP, result.operationId);
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

        if (!disposed
                && (state == XraySessionListener.STARTING
                || state == XraySessionListener.RUNNING)) {
            fail(message);
        }
        serviceClient.disconnect();
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
        // A newer START may already be RUNNING. Its live Binder connection
        // must not be disconnected by the previous STOP timeout.
        if (state != XraySessionListener.RUNNING) {
            if (!disposed && state == XraySessionListener.STARTING) {
                fail("Previous Xray session cleanup timed out");
            }
            serviceClient.cancel(XrayOperation.STOP, operationId);
        }
    }

    private void onStartupTimeout() {
        long operationId = startupOperationId;
        if (operationId == NO_OPERATION) return;

        startupOperationId = NO_OPERATION;
        main.removeCallbacks(startupTimeout);

        if (!disposed
                && currentOperationId == operationId
                && state == XraySessionListener.STARTING) {
            fail("Xray startup timed out");
            serviceClient.cancel(XrayOperation.START, operationId);
        }
    }

    private void fail(String message) {
        state = XraySessionListener.IDLE;
        socksPort = 0;
        String safe = XrayErrorSanitizer.sanitize(message);
        notifyState(XraySessionListener.ERROR, 0, safe);
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
