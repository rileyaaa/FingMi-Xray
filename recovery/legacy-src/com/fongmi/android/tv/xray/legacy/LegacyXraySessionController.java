package com.fongmi.android.tv.xray.legacy;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

/**
 * Behavior reconstruction of the shipped per-playback state machine (R8 name: yz3).
 */
public final class LegacyXraySessionController
        implements LegacyXrayServiceClient.Listener {

    private static final long NONE = Long.MIN_VALUE;
    private static final long PREVIOUS_CLEANUP_TIMEOUT_MS = 1_500L;
    private static final long STARTUP_TIMEOUT_MS = 30_000L;
    private static final long DISPOSE_UNBIND_DELAY_MS = 500L;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final LegacyXrayConfigStore configStore;
    private final LegacyXrayServiceClient serviceClient;
    private final LegacyXraySessionListener listener;

    private long currentOperationId = LegacyXrayOperationIds.next();
    private long cleanupOperationId = NONE;
    private long startupOperationId = NONE;

    private int state = LegacyXraySessionListener.OFF;
    private boolean disposed;

    private final Runnable cleanupTimeout = () -> {
        long operationId = cleanupOperationId;
        if (operationId == NONE) return;

        cleanupOperationId = NONE;

        // Exact shipped behavior: once a newer start has already reached RUNNING,
        // this stale cleanup timeout no longer cancels the old STOP.
        if (state != LegacyXraySessionListener.RUNNING) {
            if (!disposed && state == LegacyXraySessionListener.STARTING) {
                fail("Previous Xray session cleanup timed out");
            }
            serviceClient.cancel(LegacyXrayOperation.STOP, operationId);
        }
    };

    private final Runnable startupTimeout = () -> {
        long operationId = startupOperationId;
        if (operationId == NONE) return;

        startupOperationId = NONE;
        main.removeCallbacks(startupTimeout);

        if (!disposed
                && currentOperationId == operationId
                && state == LegacyXraySessionListener.STARTING) {
            fail("Xray startup timed out");
            serviceClient.cancel(LegacyXrayOperation.START, operationId);
        }
    };

    public LegacyXraySessionController(
            Context context,
            LegacyXraySessionListener listener) {
        configStore = new LegacyXrayConfigStore(context);
        serviceClient = new LegacyXrayServiceClient(context, this);
        this.listener = listener;
    }

    public int state() {
        return state;
    }

    public void start() {
        requireMainThread();

        if (disposed
                || state == LegacyXraySessionListener.STARTING
                || state == LegacyXraySessionListener.RUNNING) {
            return;
        }

        try {
            String shareLink = configStore.getShareLink();
            if (shareLink.isEmpty()) {
                fail("Xray is not configured");
                return;
            }

            long operationId = LegacyXrayOperationIds.next();
            currentOperationId = operationId;
            startupOperationId = operationId;
            state = LegacyXraySessionListener.STARTING;
            listener.onXrayState(LegacyXraySessionListener.STARTING, 0, "");

            boolean udp = configStore.isUdpEnabled();
            serviceClient.execute(
                    new LegacyXrayServiceClient.Request(
                            operationId,
                            LegacyXrayOperation.START,
                            shareLink,
                            udp,
                            () -> scheduleStartupTimeout(operationId)));
        } catch (Exception error) {
            startupOperationId = NONE;
            main.removeCallbacks(startupTimeout);
            fail(LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    public void stop() {
        requireMainThread();

        if (disposed || state == LegacyXraySessionListener.OFF) return;

        startupOperationId = NONE;
        main.removeCallbacks(startupTimeout);

        long operationId = LegacyXrayOperationIds.next();
        currentOperationId = operationId;
        state = LegacyXraySessionListener.OFF;
        listener.onXrayState(LegacyXraySessionListener.OFF, 0, "");

        cleanupOperationId = operationId;
        serviceClient.execute(
                new LegacyXrayServiceClient.Request(
                        operationId,
                        LegacyXrayOperation.STOP,
                        "",
                        false,
                        () -> scheduleCleanupTimeout(operationId)));
    }

    public void dispose() {
        requireMainThread();

        if (disposed) return;
        if (state != LegacyXraySessionListener.OFF) {
            stop();
        }

        disposed = true;
        if (cleanupOperationId == NONE) {
            main.postDelayed(serviceClient::disconnect, DISPOSE_UNBIND_DELAY_MS);
        }
    }

    @Override
    public void onOperationResult(LegacyXrayOperationResult result) {
        requireMainThread();

        if (result.operation == LegacyXrayOperation.STOP
                && result.operationId == cleanupOperationId) {
            cleanupOperationId = NONE;
            main.removeCallbacks(cleanupTimeout);

            if (!result.success) {
                if (!disposed) {
                    String message = LegacyXrayErrorSanitizer.sanitize(result.message);
                    if (state == LegacyXraySessionListener.OFF) {
                        listener.onXrayState(
                                LegacyXraySessionListener.OFF,
                                0,
                                message);
                    } else {
                        fail(message);
                    }
                }

                serviceClient.cancel(
                        LegacyXrayOperation.STOP,
                        result.operationId);
                return;
            }

            if (disposed) {
                serviceClient.disconnect();
                return;
            } else if (result.operationId != currentOperationId) {
                return;
            }
        }

        if (disposed || result.operationId != currentOperationId) return;

        if (result.operation == LegacyXrayOperation.START) {
            cleanupOperationId = NONE;
            main.removeCallbacks(cleanupTimeout);
            startupOperationId = NONE;
            main.removeCallbacks(startupTimeout);

            if (!result.success) {
                fail(result.message);
                serviceClient.disconnect();
                return;
            }

            state = LegacyXraySessionListener.RUNNING;
            listener.onXrayState(
                    LegacyXraySessionListener.RUNNING,
                    result.socksPort,
                    "");
            return;
        }

        if (result.operation == LegacyXrayOperation.STOP) {
            cleanupOperationId = NONE;
            main.removeCallbacks(cleanupTimeout);

            if (result.success) {
                serviceClient.disconnect();
                return;
            }

            String message = LegacyXrayErrorSanitizer.sanitize(result.message);
            if (state == LegacyXraySessionListener.OFF) {
                listener.onXrayState(
                        LegacyXraySessionListener.OFF,
                        0,
                        message);
            } else {
                fail(message);
            }
            serviceClient.cancel(
                    LegacyXrayOperation.STOP,
                    result.operationId);
        }
    }

    @Override
    public void onConnectionFailure(long operationId, String message) {
        requireMainThread();

        if (operationId == startupOperationId) {
            startupOperationId = NONE;
            main.removeCallbacks(startupTimeout);
        }

        if (operationId == cleanupOperationId) {
            cleanupOperationId = NONE;
            main.removeCallbacks(cleanupTimeout);
        }

        if (operationId != currentOperationId) return;

        cleanupOperationId = NONE;
        main.removeCallbacks(cleanupTimeout);

        if (!disposed
                && (state == LegacyXraySessionListener.STARTING
                || state == LegacyXraySessionListener.RUNNING)) {
            fail(message);
        }
        serviceClient.disconnect();
    }

    private void scheduleCleanupTimeout(long operationId) {
        if (cleanupOperationId != operationId) return;
        main.removeCallbacks(cleanupTimeout);
        main.postDelayed(cleanupTimeout, PREVIOUS_CLEANUP_TIMEOUT_MS);
    }

    private void scheduleStartupTimeout(long operationId) {
        if (startupOperationId != operationId
                || currentOperationId != operationId
                || state != LegacyXraySessionListener.STARTING) {
            return;
        }

        main.removeCallbacks(startupTimeout);
        main.postDelayed(startupTimeout, STARTUP_TIMEOUT_MS);
    }

    private void fail(String rawMessage) {
        state = LegacyXraySessionListener.OFF;
        String message = rawMessage == null ? "" : rawMessage;
        listener.onXrayState(
                LegacyXraySessionListener.ERROR,
                0,
                message);
        listener.onXrayState(
                LegacyXraySessionListener.OFF,
                0,
                "");
    }

    private static void requireMainThread() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException(
                    "Legacy Xray session controller must run on the main thread");
        }
    }
}
