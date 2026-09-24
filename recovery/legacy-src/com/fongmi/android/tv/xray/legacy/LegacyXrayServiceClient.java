package com.fongmi.android.tv.xray.legacy;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.RemoteException;

import com.fongmi.android.tv.xray.IXrayCallback;
import com.fongmi.android.tv.xray.IXrayService;
import com.fongmi.android.tv.xray.XrayService;

/**
 * Behavior reconstruction of the shipped main-process Binder client (R8 name: hz3/ez3/dz3).
 */
public final class LegacyXrayServiceClient {

    public interface Listener {
        void onOperationResult(LegacyXrayOperationResult result);
        void onConnectionFailure(long operationId, String message);
    }

    public static final class Request {
        public final long operationId;
        public final int operation;
        public final String shareLink;
        public final boolean udp;
        public final Runnable onDispatched;

        public Request(
                long operationId,
                int operation,
                String shareLink,
                boolean udp,
                Runnable onDispatched) {
            this.operationId = operationId;
            this.operation = operation;
            this.shareLink = shareLink == null ? "" : shareLink;
            this.udp = udp;
            this.onDispatched = onDispatched == null ? () -> { } : onDispatched;
        }
    }

    private static final long NO_OPERATION = Long.MIN_VALUE;
    private static final long BIND_TIMEOUT_MS = 5_000L;

    private final Context context;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());

    private IXrayService service;
    private Request pending;
    private BindConnection connection;

    /**
     * Guards callbacks/failures from an old binding generation.
     * Recovered field: hz3.f7574g.
     */
    private long callbackGeneration;

    /**
     * Monotonic id used only to identify each ServiceConnection instance.
     * Recovered field: hz3.f7575h.
     */
    private long bindSequence;

    private long activeOperationId = NO_OPERATION;
    private boolean binding;

    public LegacyXrayServiceClient(Context context, Listener listener) {
        this.context = context.getApplicationContext();
        this.listener = listener;
    }

    public synchronized void execute(Request request) {
        pending = request;

        if (service != null) {
            dispatchPendingLocked();
            return;
        }
        if (binding) return;

        binding = true;
        BindConnection next = new BindConnection(++bindSequence);
        connection = next;

        main.removeCallbacks(next.timeout);
        main.postDelayed(next.timeout, BIND_TIMEOUT_MS);

        Intent intent = new Intent(context, XrayService.class);
        if (!context.bindService(intent, next, Context.BIND_AUTO_CREATE)) {
            failLocked(next, "Xray service bind failed");
        }
    }

    public synchronized void cancel(int operation, long operationId) {
        if (service != null) {
            try {
                service.cancel(operation, operationId);
            } catch (Exception ignored) {
            }
        }
        disconnectLocked();
    }

    public synchronized void disconnect() {
        disconnectLocked();
    }

    private void dispatchPendingLocked() {
        Request request = pending;
        pending = null;
        if (request == null || service == null) return;

        activeOperationId = request.operationId;
        long callbackGenerationAtDispatch = callbackGeneration;

        IXrayCallback callback = new IXrayCallback.Stub() {
            @Override
            public void onResult(
                    long operationId,
                    int operation,
                    boolean success,
                    int socksPort,
                    long latencyMs,
                    String message) {
                LegacyXrayOperationResult result = new LegacyXrayOperationResult(
                        operationId,
                        operation,
                        success,
                        socksPort,
                        latencyMs,
                        message);
                main.post(() -> {
                    synchronized (LegacyXrayServiceClient.this) {
                        if (callbackGenerationAtDispatch != callbackGeneration) return;
                    }
                    listener.onOperationResult(result);
                });
            }
        };

        try {
            switch (request.operation) {
                case LegacyXrayOperation.VALIDATE:
                    service.validate(
                            request.operationId,
                            request.shareLink,
                            request.udp,
                            callback);
                    break;
                case LegacyXrayOperation.TEST:
                    service.test(
                            request.operationId,
                            request.shareLink,
                            request.udp,
                            callback);
                    break;
                case LegacyXrayOperation.START:
                    service.start(
                            request.operationId,
                            request.shareLink,
                            request.udp,
                            callback);
                    break;
                case LegacyXrayOperation.STOP:
                    service.stop(request.operationId, callback);
                    break;
                case LegacyXrayOperation.RESET_SECURITY:
                    service.resetSecurity(request.operationId, callback);
                    break;
                default:
                    throw new IllegalArgumentException("Unknown Xray operation");
            }

            request.onDispatched.run();
        } catch (Exception error) {
            failLocked(connection, LegacyXrayErrorSanitizer.fromException(error));
        }
    }

    private synchronized void failLocked(BindConnection expected, String rawMessage) {
        if (expected != null && expected != connection) {
            expected.detach();
            try {
                context.unbindService(expected);
            } catch (IllegalArgumentException ignored) {
            }
            return;
        }

        BindConnection current = connection;
        if (current != null) {
            main.removeCallbacks(current.timeout);
        }

        long failedOperationId =
                pending != null ? pending.operationId : activeOperationId;

        long failureGeneration = ++callbackGeneration;
        connection = null;
        service = null;
        pending = null;
        activeOperationId = NO_OPERATION;
        binding = false;

        if (current != null) {
            current.detach();
            try {
                context.unbindService(current);
            } catch (IllegalArgumentException ignored) {
            }
        }

        if (failedOperationId == NO_OPERATION) return;

        String message = LegacyXrayErrorSanitizer.sanitize(rawMessage);
        main.post(() -> {
            synchronized (LegacyXrayServiceClient.this) {
                if (failureGeneration != callbackGeneration) return;
            }
            listener.onConnectionFailure(failedOperationId, message);
        });
    }

    private void disconnectLocked() {
        callbackGeneration++;

        BindConnection old = connection;
        if (old != null) {
            main.removeCallbacks(old.timeout);
        }

        pending = null;
        activeOperationId = NO_OPERATION;
        connection = null;
        service = null;
        binding = false;

        if (old != null) {
            old.detach();
            try {
                context.unbindService(old);
            } catch (IllegalArgumentException ignored) {
            }
        }
    }

    private final class BindConnection implements ServiceConnection, IBinder.DeathRecipient {

        final long sequence;
        final Runnable timeout = () -> {
            synchronized (LegacyXrayServiceClient.this) {
                if (this == connection && binding && service == null) {
                    failLocked(this, "Xray service connection timed out");
                }
            }
        };

        IBinder binder;

        BindConnection(long sequence) {
            this.sequence = sequence;
        }

        @Override
        public void onServiceConnected(ComponentName name, IBinder serviceBinder) {
            synchronized (LegacyXrayServiceClient.this) {
                if (this != connection) {
                    try {
                        context.unbindService(this);
                    } catch (IllegalArgumentException ignored) {
                    }
                    return;
                }

                main.removeCallbacks(timeout);
                binding = false;
                binder = serviceBinder;
                service = IXrayService.Stub.asInterface(serviceBinder);

                try {
                    serviceBinder.linkToDeath(this, 0);
                    dispatchPendingLocked();
                } catch (RemoteException error) {
                    failLocked(this, "Xray service connection died");
                }
            }
        }

        @Override
        public void onServiceDisconnected(ComponentName name) {
            failLocked(this, "Xray service disconnected");
        }

        @Override
        public void onBindingDied(ComponentName name) {
            failLocked(this, "Xray service binding died");
        }

        @Override
        public void onNullBinding(ComponentName name) {
            failLocked(this, "Xray service returned no binder");
        }

        @Override
        public void binderDied() {
            failLocked(this, "Xray service process died");
        }

        void detach() {
            main.removeCallbacks(timeout);
            if (binder == null) return;
            try {
                binder.unlinkToDeath(this, 0);
            } catch (Exception ignored) {
            }
            binder = null;
        }

        @Override
        public String toString() {
            return "XrayBindConnection{" + sequence + '}';
        }
    }
}
