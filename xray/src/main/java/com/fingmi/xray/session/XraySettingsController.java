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

    public boolean isTlsFragmentEnabled() {
        return preferences.isTlsFragmentEnabled();
    }

    public String getLiveAutoGroups() { return preferences.getLiveAutoGroups(); }

    public String getLiveAutoChannels() { return preferences.getLiveAutoChannels(); }

    public void save(String shareLink, boolean udp, boolean tlsFragment,
                     String groups, String channels) throws Exception {
        assertMainThread();
        ensureOpen();
        if (activeOperation == XrayOperation.RESET_SECURITY) return;
        preferences.save(shareLink, udp, tlsFragment, groups, channels);
    }

    public void save(String shareLink, boolean udp) throws Exception {
        save(shareLink, udp, false);
    }

    public void save(String shareLink, boolean udp, boolean tlsFragment) throws Exception {
        assertMainThread();
        ensureOpen();
        // Released UI blocks Save only while RESET_SECURITY owns the settings process.
        if (activeOperation == XrayOperation.RESET_SECURITY) return;
        preferences.save(shareLink, udp, tlsFragment);
    }

    public long test(String shareLink, boolean udp) {
        return test(shareLink, udp, false);
    }

    public long test(String shareLink, boolean udp, boolean tlsFragment) {
        assertMainThread();
        ensureIdle();
        return begin(
                XrayOperation.TEST,
                XrayShareLinkNormalizer.normalize(shareLink),
                udp,
                tlsFragment);
    }

    public long validate(String shareLink, boolean udp) {
        return validate(shareLink, udp, false);
    }

    public long validate(String shareLink, boolean udp, boolean tlsFragment) {
        assertMainThread();
        ensureIdle();
        return begin(
                XrayOperation.VALIDATE,
                XrayShareLinkNormalizer.normalize(shareLink),
                udp,
                tlsFragment);
    }

    public long delete() throws Exception {
        return delete(null);
    }

    public long delete(Runnable onLocalCleared) throws Exception {
        assertMainThread();
        ensureIdle();

        // Released SettingXrayActivity claims the RESET_SECURITY generation
        // before rebuilding its Binder client. It then clears local storage/UI
        // before dispatching the remote security reset.
        long operationId = XrayOperationIds.next();
        activeOperationId = operationId;
        activeOperation = XrayOperation.RESET_SECURITY;

        replaceClient();
        XrayServiceClient ownerClient = serviceClient;
        boolean localClearedCallbackDelivered = false;
        try {
            preferences.clear();
            localClearedCallbackDelivered = notifyLocalCleared(onLocalCleared);

            // Local-clear callbacks are re-entrant. cancel/abandon/close (or a
            // replacement delete after one of them) can retire this operation
            // before its remote RESET_SECURITY has even been dispatched.
            if (closed
                    || activeOperationId != operationId
                    || activeOperation != XrayOperation.RESET_SECURITY
                    || serviceClient != ownerClient) {
                return operationId;
            }

            ownerClient.execute(new XrayServiceClient.Request(
                    operationId,
                    XrayOperation.RESET_SECURITY,
                    "",
                    false,
                    () -> scheduleTimeout(operationId)));
            return operationId;
        } catch (Exception | LinkageError error) {
            // The released store removes SharedPreferences before deleting its
            // AndroidKeyStore key. Key deletion can therefore fail after the
            // saved node is already gone. Keep surfacing the storage failure,
            // but make the UI reflect the state that actually committed.
            if (!localClearedCallbackDelivered && !preferences.isConfigured()) {
                notifyLocalCleared(onLocalCleared);
            }
            // The recovery UI callback is re-entrant too. If it retired this
            // failed delete and created a newer settings operation, do not let
            // the outer partial-delete cleanup destroy that newer owner.
            if (!closed
                    && activeOperationId == operationId
                    && activeOperation == XrayOperation.RESET_SECURITY
                    && serviceClient == ownerClient) {
                clearActive();
                replaceClient();
            }
            throw error;
        }
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

    private long begin(int operation, String shareLink, boolean udp, boolean tlsFragment) {
        ensureOpen();

        long operationId = XrayOperationIds.next();
        activeOperationId = operationId;
        activeOperation = operation;

        serviceClient.execute(new XrayServiceClient.Request(
                operationId,
                operation,
                shareLink,
                udp,
                tlsFragment,
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
        XrayServiceClient ownerClient = serviceClient;
        clearTimeout();

        // Invalidate local state before the synchronous Binder cancel. The
        // released Activity surfaces the timeout before cancelling/unbinding.
        XrayOperationIds.next();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        notifyResult(
                operationId,
                operation,
                false,
                -1L,
                "Xray operation timed out");

        // Listener callbacks are re-entrant. A new operation may already own
        // this client, or abandon/delete/close may have replaced it entirely.
        // Only the unchanged old owner may be cancelled/disconnected here.
        if (!closed
                && activeOperationId == NO_OPERATION
                && serviceClient == ownerClient) {
            ownerClient.cancel(operation, operationId);
            replaceClient();
        }
    }

    @Override
    public void onResult(XrayResult result) {
        assertMainThread();
        if (closed || result.operationId != activeOperationId) return;

        int operation = activeOperation;
        XrayServiceClient ownerClient = serviceClient;
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        notifyResult(
                result.operationId,
                operation,
                result.success,
                result.latencyMs,
                XrayErrorSanitizer.sanitize(result.message));

        if (!closed
                && activeOperationId == NO_OPERATION
                && serviceClient == ownerClient) {
            replaceClient();
        }
    }

    @Override
    public void onConnectionFailure(long operationId, String message) {
        assertMainThread();
        if (closed || operationId != activeOperationId) return;

        int operation = activeOperation;
        XrayServiceClient ownerClient = serviceClient;
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        notifyResult(
                operationId,
                operation,
                false,
                -1L,
                XrayErrorSanitizer.sanitize(message));

        if (!closed
                && activeOperationId == NO_OPERATION
                && serviceClient == ownerClient) {
            replaceClient();
        }
    }

    private static boolean notifyLocalCleared(Runnable action) {
        if (action == null) return false;
        try {
            action.run();
        } catch (RuntimeException | LinkageError ignored) {
            // UI cleanup failure must not prevent remote RESET_SECURITY.
        }
        return true;
    }

    private void notifyResult(
            long operationId,
            int operation,
            boolean success,
            long latencyMs,
            String message) {
        if (listener == null) return;
        try {
            listener.onXraySettingsResult(
                    operationId,
                    operation,
                    success,
                    latencyMs,
                    message == null ? "" : message);
        } catch (RuntimeException | LinkageError ignored) {
            // A UI/listener failure must not strand the remote Binder operation
            // or prevent the old client generation from being cleaned up.
        }
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
