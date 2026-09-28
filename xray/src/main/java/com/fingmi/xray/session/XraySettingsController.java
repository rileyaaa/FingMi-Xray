package com.fingmi.xray.session;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import com.fingmi.xray.config.XrayPreferences;
import com.fingmi.xray.config.XrayShareLinkNormalizer;
import com.fingmi.xray.service.XrayOperation;
import com.fingmi.xray.util.XrayErrorSanitizer;

/**
 * Settings-side Xray operation owner. This deliberately mirrors the released
 * APK's one-operation-per-Binder-generation lifecycle.
 */
public final class XraySettingsController implements XrayServiceClient.Listener, AutoCloseable {

    public interface Listener {
        void onXraySettingsResult(
                long operationId,
                int operation,
                boolean success,
                long latencyMs,
                String message);
    }

    private static final long NO_OPERATION = Long.MIN_VALUE;
    private static final long OPERATION_TIMEOUT_MS = 45_000L;

    private final Context context;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final XrayPreferences preferences;
    private final Listener listener;

    private XrayServiceClient serviceClient;
    private long activeOperationId = NO_OPERATION;
    private int activeOperation = -1;
    private long timeoutOperationId = NO_OPERATION;
    private boolean closed;

    private final Runnable timeout = this::onTimeout;

    public XraySettingsController(Context context, Listener listener) {
        this.context = context.getApplicationContext();
        this.preferences = new XrayPreferences(context);
        this.listener = listener;
        this.serviceClient = new XrayServiceClient(context, this);
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
        // Released UI blocks Save only while RESET_SECURITY owns the settings process.
        if (activeOperation == XrayOperation.RESET_SECURITY) return;
        preferences.save(shareLink, udp);
    }

    public long test(String shareLink, boolean udp) {
        assertMainThread();
        ensureIdle();
        return begin(
                XrayOperation.TEST,
                XrayShareLinkNormalizer.normalize(shareLink),
                udp);
    }

    public long validate(String shareLink, boolean udp) {
        assertMainThread();
        ensureIdle();
        return begin(
                XrayOperation.VALIDATE,
                XrayShareLinkNormalizer.normalize(shareLink),
                udp);
    }

    public long delete() throws Exception {
        assertMainThread();
        ensureIdle();

        // Clear the visible/saved node first, then clear transport-security state
        // inside the private process.
        preferences.clear();
        return begin(XrayOperation.RESET_SECURITY, "", false);
    }

    public void cancel() {
        assertMainThread();
        if (closed || activeOperationId == NO_OPERATION) return;

        long operationId = activeOperationId;
        int operation = activeOperation;
        clearActive();
        serviceClient.cancel(operation, operationId);
        replaceClient();
    }

    /**
     * Phone import invalidates the local generation and abandons the old Binder
     * without issuing a native remote cancel, matching the released APK.
     */
    public void abandon() {
        assertMainThread();
        if (closed) return;
        clearActive();
        XrayOperationIds.next();
        replaceClient();
    }

    public boolean hasActiveOperation() {
        return activeOperationId != NO_OPERATION;
    }

    public int activeOperation() {
        return activeOperation;
    }

    private long begin(int operation, String shareLink, boolean udp) {
        ensureOpen();

        long operationId = XrayOperationIds.next();
        activeOperationId = operationId;
        activeOperation = operation;

        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                operation,
                shareLink,
                udp,
                () -> scheduleTimeout(operationId)));
        return operationId;
    }

    private void scheduleTimeout(long operationId) {
        if (activeOperationId != operationId) return;
        timeoutOperationId = operationId;
        main.removeCallbacks(timeout);
        main.postDelayed(timeout, OPERATION_TIMEOUT_MS);
    }

    private void clearTimeout() {
        timeoutOperationId = NO_OPERATION;
        main.removeCallbacks(timeout);
    }

    private void onTimeout() {
        long operationId = timeoutOperationId;
        if (operationId == NO_OPERATION || operationId != activeOperationId) return;

        int operation = activeOperation;
        clearTimeout();

        // Invalidate local state before the synchronous Binder cancel. The
        // released Activity surfaces the timeout before cancelling/unbinding.
        XrayOperationIds.next();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        if (listener != null) {
            listener.onXraySettingsResult(
                    operationId,
                    operation,
                    false,
                    -1L,
                    "Xray operation timed out");
        }

        serviceClient.cancel(operation, operationId);
        replaceClient();
    }

    @Override
    public void onResult(XrayResult result) {
        assertMainThread();
        if (closed || result.operationId != activeOperationId) return;

        int operation = activeOperation;
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        if (listener != null) {
            listener.onXraySettingsResult(
                    result.operationId,
                    operation,
                    result.success,
                    result.latencyMs,
                    XrayErrorSanitizer.sanitize(result.message));
        }

        replaceClient();
    }

    @Override
    public void onConnectionFailure(long operationId, String message) {
        assertMainThread();
        if (closed || operationId != activeOperationId) return;

        int operation = activeOperation;
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        if (listener != null) {
            listener.onXraySettingsResult(
                    operationId,
                    operation,
                    false,
                    -1L,
                    XrayErrorSanitizer.sanitize(message));
        }

        replaceClient();
    }

    private void replaceClient() {
        XrayServiceClient old = serviceClient;
        if (old != null) old.disconnect();
        if (!closed) serviceClient = new XrayServiceClient(context, this);
    }

    private void clearActive() {
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;
    }

    private void ensureIdle() {
        ensureOpen();
        if (hasActiveOperation()) {
            throw new IllegalStateException("Xray settings operation is already running");
        }
    }

    private void ensureOpen() {
        if (closed) throw new IllegalStateException("Xray settings controller is closed");
    }

    @Override
    public void close() {
        assertMainThread();
        if (closed) return;

        closed = true;
        clearActive();
        XrayOperationIds.next();

        if (serviceClient != null) serviceClient.disconnect();
        serviceClient = null;
    }

    private static void assertMainThread() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            throw new IllegalStateException("XraySettingsController must be used from the main thread");
        }
    }
}
