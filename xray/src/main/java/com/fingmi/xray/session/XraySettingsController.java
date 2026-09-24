package com.fingmi.xray.session;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import com.fingmi.xray.config.XrayPreferences;
import com.fingmi.xray.config.XrayShareLinkNormalizer;
import com.fingmi.xray.service.XrayOperation;
import com.fingmi.xray.util.XrayErrorSanitizer;

public final class XraySettingsController implements XrayServiceClient.Listener, AutoCloseable {

    public interface Listener {
        void onXraySettingsResult(
                long operationId,
                int operation,
                boolean success,
                long latencyMs,
                String message);
    }

    private static final long OPERATION_TIMEOUT_MS = 45_000L;
    private static final long NO_OPERATION = Long.MIN_VALUE;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final XrayPreferences preferences;
    private final XrayServiceClient serviceClient;
    private final Listener listener;

    private long activeOperationId = NO_OPERATION;
    private int activeOperation = -1;
    private boolean closed;

    private final Runnable timeout = this::onTimeout;

    public XraySettingsController(Context context, Listener listener) {
        preferences = new XrayPreferences(context);
        serviceClient = new XrayServiceClient(context, this);
        this.listener = listener;
    }

    public boolean isConfigured() {
        return preferences.isConfigured();
    }

    public String getShareLink() throws Exception {
        return preferences.getShareLink();
    }

    public boolean isUdpEnabled() {
        return preferences.isUdpEnabled();
    }

    public void save(String shareLink, boolean udp) throws Exception {
        assertMainThread();
        ensureOpen();
        if (activeOperation != XrayOperation.RESET_SECURITY) {
            preferences.save(XrayShareLinkNormalizer.normalize(shareLink), udp);
        }
    }

    public long test(String shareLink, boolean udp) {
        assertMainThread();
        ensureOpen();
        ensureIdle();

        String normalized = XrayShareLinkNormalizer.normalize(shareLink);
        long operationId = XrayOperationIds.next();
        begin(operationId, XrayOperation.TEST);

        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                XrayOperation.TEST,
                normalized,
                udp,
                () -> scheduleTimeout(operationId)));
        return operationId;
    }

    public long delete() throws Exception {
        assertMainThread();
        ensureOpen();
        ensureIdle();

        preferences.clear();

        long operationId = XrayOperationIds.next();
        begin(operationId, XrayOperation.RESET_SECURITY);

        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                XrayOperation.RESET_SECURITY,
                "",
                false,
                () -> scheduleTimeout(operationId)));
        return operationId;
    }

    public void cancel() {
        assertMainThread();
        if (activeOperationId == NO_OPERATION) return;

        long operationId = activeOperationId;
        int operation = activeOperation;
        clearActive();
        serviceClient.cancel(operation, operationId);
    }

    @Override
    public void onResult(XrayResult result) {
        assertMainThread();
        if (closed || result.operationId != activeOperationId) return;

        int operation = activeOperation;
        clearActive();
        serviceClient.disconnect();

        if (listener != null) {
            listener.onXraySettingsResult(
                    result.operationId,
                    operation,
                    result.success,
                    result.latencyMs,
                    result.message);
        }
    }

    @Override
    public void onConnectionFailure(long operationId, String message) {
        assertMainThread();
        if (closed || operationId != activeOperationId) return;

        int operation = activeOperation;
        clearActive();
        serviceClient.disconnect();

        if (listener != null) {
            listener.onXraySettingsResult(
                    operationId,
                    operation,
                    false,
                    -1L,
                    XrayErrorSanitizer.sanitize(message));
        }
    }

    @Override
    public void close() {
        assertMainThread();
        if (closed) return;
        closed = true;
        cancel();
        main.removeCallbacks(timeout);
        serviceClient.disconnect();
    }

    private void begin(long operationId, int operation) {
        activeOperationId = operationId;
        activeOperation = operation;
    }

    private void scheduleTimeout(long operationId) {
        if (operationId != activeOperationId) return;
        main.removeCallbacks(timeout);
        main.postDelayed(timeout, OPERATION_TIMEOUT_MS);
    }

    private void onTimeout() {
        if (activeOperationId == NO_OPERATION) return;

        long operationId = activeOperationId;
        int operation = activeOperation;
        clearActive();
        serviceClient.cancel(operation, operationId);

        if (listener != null) {
            listener.onXraySettingsResult(
                    operationId,
                    operation,
                    false,
                    -1L,
                    "Xray operation timed out");
        }
    }

    private void clearActive() {
        main.removeCallbacks(timeout);
        activeOperationId = NO_OPERATION;
        activeOperation = -1;
    }

    private void ensureIdle() {
        if (activeOperationId != NO_OPERATION) {
            throw new IllegalStateException("Another Xray operation is already running");
        }
    }

    private void ensureOpen() {
        if (closed) throw new IllegalStateException("Xray settings controller is closed");
    }

    private static void assertMainThread() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("XraySettingsController must be used from the main thread");
        }
    }
}
