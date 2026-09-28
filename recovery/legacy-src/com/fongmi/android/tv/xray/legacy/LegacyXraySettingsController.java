package com.fongmi.android.tv.xray.legacy;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

/**
 * Readable reconstruction of the shipped settings-side Xray operation owner.
 *
 * The final APK kept this separate from playback-session state: settings
 * validate/test/reset operations have their own generation and a 45 second
 * UI timeout.
 */
public final class LegacyXraySettingsController
        implements LegacyXrayServiceClient.Listener, AutoCloseable {

    public interface Listener {
        void onResult(
                long operationId,
                int operation,
                boolean success,
                long latencyMs,
                String message);
    }

    private static final long NO_OPERATION = Long.MIN_VALUE;
    private static final long TIMEOUT_MS = 45_000L;

    private final Context context;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final LegacyXrayConfigStore store;
    private final Listener listener;

    private LegacyXrayServiceClient client;
    private long activeOperationId = NO_OPERATION;
    private int activeOperation = -1;
    private long timeoutOperationId = NO_OPERATION;
    private boolean closed;

    private final Runnable timeout = this::onTimeout;

    public LegacyXraySettingsController(
            Context context,
            Listener listener) {
        this.context = context.getApplicationContext();
        this.store = new LegacyXrayConfigStore(context);
        this.listener = listener;
        this.client = new LegacyXrayServiceClient(context, this);
    }

    public boolean isConfigured() {
        return store.isConfigured();
    }

    public String getShareLink() throws Exception {
        return store.getShareLink();
    }

    public boolean isUdpEnabled() {
        return store.isUdpEnabled();
    }

    public void save(String link, boolean udp) throws Exception {
        if (closed) throw new IllegalStateException("Xray settings controller is closed");
        // The shipped UI only blocks Save while RESET_SECURITY is in flight.
        if (activeOperation == LegacyXrayOperation.RESET_SECURITY) return;
        store.save(link, udp);
    }

    public long test(String link, boolean udp) {
        ensureIdle();
        String normalized = LegacyXrayShareLinkNormalizer.normalize(link);
        return begin(
                LegacyXrayOperation.TEST,
                normalized,
                udp);
    }

    public long validate(String link, boolean udp) {
        ensureIdle();
        String normalized = LegacyXrayShareLinkNormalizer.normalize(link);
        return begin(
                LegacyXrayOperation.VALIDATE,
                normalized,
                udp);
    }

    public long delete() throws Exception {
        ensureIdle();

        // DEX/JADX-verified SettingXrayActivity order:
        // own RESET_SECURITY -> replace Binder client -> clear local store ->
        // clear visible fields -> dispatch RESET_SECURITY.
        long operationId = LegacyXrayOperationIds.next();
        activeOperationId = operationId;
        activeOperation = LegacyXrayOperation.RESET_SECURITY;

        replaceClient();
        try {
            store.clear();
            client.execute(
                    new LegacyXrayServiceClient.Request(
                            operationId,
                            LegacyXrayOperation.RESET_SECURITY,
                            "",
                            false,
                            () -> scheduleTimeout(operationId)));
            return operationId;
        } catch (Exception error) {
            clearTimeout();
            activeOperationId = NO_OPERATION;
            activeOperation = -1;
            replaceClient();
            throw error;
        }
    }

    /**
     * Used when a phone import arrives while test/validate is running.
     *
     * The shipped settings Activity invalidates the local generation and
     * disconnects the Binder without sending an explicit remote cancel.
     */
    public void abandon() {
        if (closed) return;
        clearTimeout();

        // Shipped SettingXrayActivity invalidates the local operation identity
        // on phone import before abandoning the old Binder generation.
        LegacyXrayOperationIds.next();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;
        replaceClient();
    }

    public boolean hasActiveOperation() {
        return activeOperationId != NO_OPERATION;
    }

    public int activeOperation() {
        return activeOperation;
    }

    private long begin(
            int operation,
            String link,
            boolean udp) {
        if (closed) throw new IllegalStateException("Xray settings controller is closed");

        long operationId = LegacyXrayOperationIds.next();
        activeOperationId = operationId;
        activeOperation = operation;

        client.execute(
                new LegacyXrayServiceClient.Request(
                        operationId,
                        operation,
                        link,
                        udp,
                        () -> scheduleTimeout(operationId)));
        return operationId;
    }

    private void ensureIdle() {
        if (closed) throw new IllegalStateException("Xray settings controller is closed");
        if (hasActiveOperation()) {
            throw new IllegalStateException("Xray settings operation is already running");
        }
    }

    private void scheduleTimeout(long operationId) {
        if (activeOperationId != operationId) return;
        timeoutOperationId = operationId;
        main.removeCallbacks(timeout);
        main.postDelayed(timeout, TIMEOUT_MS);
    }

    private void clearTimeout() {
        timeoutOperationId = NO_OPERATION;
        main.removeCallbacks(timeout);
    }

    private void onTimeout() {
        long operationId = timeoutOperationId;
        if (operationId == NO_OPERATION
                || operationId != activeOperationId) {
            return;
        }

        int operation = activeOperation;
        clearTimeout();

        // Mirrors SettingXrayActivity/rc2 case 15: first invalidate local
        // generation, then cancel the exact remote operation and rebuild the
        // Binder client for the next request.
        LegacyXrayOperationIds.next();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        // DEX/JADX-verified in SettingXrayActivity's rc2 case 15:
        // surface the timeout to the UI before making the synchronous Binder
        // cancel call, then replace the client after that exact operation is
        // cancelled/unbound.
        if (listener != null) {
            listener.onResult(
                    operationId,
                    operation,
                    false,
                    -1L,
                    "Xray operation timed out");
        }

        client.cancel(operation, operationId);
        replaceClient();
    }

    @Override
    public void onOperationResult(
            LegacyXrayOperationResult result) {
        if (closed || result.operationId != activeOperationId) return;

        int operation = activeOperation;
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        if (listener != null) {
            listener.onResult(
                    result.operationId,
                    operation,
                    result.success,
                    result.latencyMs,
                    LegacyXrayErrorSanitizer.sanitize(result.message));
        }

        replaceClient();
    }

    @Override
    public void onConnectionFailure(
            long operationId,
            String message) {
        if (closed || operationId != activeOperationId) return;

        int operation = activeOperation;
        clearTimeout();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        if (listener != null) {
            listener.onResult(
                    operationId,
                    operation,
                    false,
                    -1L,
                    LegacyXrayErrorSanitizer.sanitize(message));
        }

        replaceClient();
    }

    private void replaceClient() {
        LegacyXrayServiceClient old = client;
        if (old != null) old.disconnect();
        if (!closed) client = new LegacyXrayServiceClient(context, this);
    }

    @Override
    public void close() {
        if (closed) return;
        closed = true;
        clearTimeout();

        // Final Activity destroy invalidates the local generation and unbinds;
        // it does not issue a remote cancel for an in-flight settings op.
        LegacyXrayOperationIds.next();
        activeOperationId = NO_OPERATION;
        activeOperation = -1;

        if (client != null) client.disconnect();
        client = null;
    }
}
