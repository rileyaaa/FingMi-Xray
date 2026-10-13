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

            // Submit the Binder command before invoking the re-entrant listener.
            // While the Service is still binding, XrayServiceClient intentionally
            // keeps only the latest pending request. Notifying first lets a
            // listener STOP be overwritten by this stale outer START.
            serviceClient.execute(new XrayServiceClient.Request(
                    operationId,
                    XrayOperation.START,
                    shareLink,
                    preferences.isUdpEnabled(),
                    preferences.isTlsFragmentEnabled(),
                    () -> scheduleStartupTimeout(operationId)));
            notifyState(XraySessionListener.STARTING, 0, "");
        } catch (Exception error) {
            startupOperationId = NO_OPERATION;
            main.removeCallbacks(startupTimeout);
            fail(XrayErrorSanitizer.fromException(error));
        } catch (LinkageError error) {
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
        // Submit STOP before the re-entrant IDLE notification. If the listener
        // immediately starts a replacement while binding is still pending, that
        // newer START correctly becomes the client's latest pending request; its
        // Service start path begins by stopping any old Core itself.
        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                XrayOperation.STOP,
                "",
                false,
                () -> scheduleCleanupTimeout(operationId)));
        notifyState(XraySessionListener.IDLE, 0, "");
    }

    @Override
    public void close() {
        assertMainThread();
        if (disposed) return;

        // Seal the controller before the IDLE notification emitted by stopSession().
        // Otherwise a re-entrant listener can start a new session during close and
        // leave a pending START after this owner has been disposed.
        disposed = true;
        if (state != XraySessionListener.IDLE) {
            stopSession();
        }

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
                String message = XrayErrorSanitizer.sanitize(result.message);

                if (!disposed
                        && result.operationId != currentOperationId
                        && state == XraySessionListener.STARTING) {
                    abortReplacementStartAfterCleanupFailure(message);
                    return;
                }

                if (!disposed) {
                    if (state == XraySessionListener.IDLE) {
                        notifyState(XraySessionListener.IDLE, 0, message);
                    } else if (state != XraySessionListener.RUNNING
                            || result.operationId == currentOperationId) {
                        fail(message);
                    }
                }

                // A stale STOP failure cannot clean or cancel a newer START.
                // If that newer START is already RUNNING, its own start path
                // has successfully executed stopCore() first, so the stale
                // cleanup failure no longer owns the live session.
                // Notification callbacks are re-entrant. If they synchronously
                // started a newer session, the old STOP no longer owns this
                // client and must not disconnect/cancel the replacement.
                if (result.operationId == currentOperationId) {
                    serviceClient.cancel(XrayOperation.STOP, result.operationId);
                }
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

        if (result.operation == XrayOperation.START) {
            cleanupOperationId = NO_OPERATION;
            main.removeCallbacks(cleanupTimeout);
            startupOperationId = NO_OPERATION;
            main.removeCallbacks(startupTimeout);

            if (!result.success) {
                fail(result.message);
                if (currentOperationId == result.operationId) {
                    serviceClient.disconnect();
                }
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
            if (currentOperationId == result.operationId) {
                serviceClient.cancel(XrayOperation.STOP, result.operationId);
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

        if (!disposed
                && (state == XraySessionListener.STARTING
                || state == XraySessionListener.RUNNING)) {
            fail(message);
        }
        if (currentOperationId == operationId) {
            serviceClient.disconnect();
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
        if (state == XraySessionListener.RUNNING) return;

        if (!disposed
                && state == XraySessionListener.STARTING
                && currentOperationId != operationId) {
            abortReplacementStartAfterCleanupFailure(
                    "Previous Xray session cleanup timed out");
            return;
        }

        serviceClient.cancel(XrayOperation.STOP, operationId);
    }

    private void abortReplacementStartAfterCleanupFailure(String message) {
        long replacementOperationId = currentOperationId;
        startupOperationId = NO_OPERATION;
        main.removeCallbacks(startupTimeout);

        // The released controller only cancelled the stale STOP here. Once a
        // replacement START has already claimed the Service session generation,
        // cancelling that old STOP is a no-op and can leave the replacement
        // START alive after the UI has emitted ERROR -> IDLE. Invalidate the
        // local owner and cancel the actual replacement START instead.
        currentOperationId = NO_OPERATION;
        fail(message);

        // Listener callbacks are deliberately re-entrant. If ERROR/IDLE caused
        // a newer START to be issued synchronously, that new Service generation
        // supersedes the failed replacement and must keep its Binder client.
        // Only disconnect/cancel when no newer owner appeared during notify.
        if (currentOperationId == NO_OPERATION) {
            serviceClient.cancel(XrayOperation.START, replacementOperationId);
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
            if (currentOperationId == operationId) {
                serviceClient.cancel(XrayOperation.START, operationId);
            }
        }
    }

    private void fail(String message) {
        state = XraySessionListener.IDLE;
        socksPort = 0;
        String safe = XrayErrorSanitizer.sanitize(message);
        notifyState(XraySessionListener.ERROR, 0, safe);
        // ERROR listeners may synchronously start a newer operation. Do not
        // publish a stale trailing IDLE event over that replacement START.
        if (state == XraySessionListener.IDLE) {
            notifyState(XraySessionListener.IDLE, 0, "");
        }
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
