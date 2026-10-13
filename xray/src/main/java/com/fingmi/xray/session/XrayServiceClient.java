package com.fingmi.xray.session;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.RemoteException;

import com.fingmi.xray.service.IXrayCallback;
import com.fingmi.xray.service.IXrayService;
import com.fingmi.xray.service.XrayOperation;
import com.fingmi.xray.service.XrayService;
import com.fingmi.xray.util.XrayErrorSanitizer;

final class XrayServiceClient {

    interface Listener {
        void onResult(XrayResult result);
        void onConnectionFailure(long operationId, String message);
    }

    static final class Request {
        final long operationId;
        final int operation;
        final String shareLink;
        final boolean udp;
        final boolean tlsFragment;
        final Runnable onDispatched;

        Request(
                long operationId,
                int operation,
                String shareLink,
                boolean udp,
                Runnable onDispatched) {
            this(operationId, operation, shareLink, udp, false, onDispatched);
        }

        Request(
                long operationId,
                int operation,
                String shareLink,
                boolean udp,
                boolean tlsFragment,
                Runnable onDispatched) {
            this.operationId = operationId;
            this.operation = operation;
            this.shareLink = shareLink == null ? "" : shareLink;
            this.udp = udp;
            this.tlsFragment = tlsFragment;
            this.onDispatched = onDispatched == null ? () -> { } : onDispatched;
        }
    }

    private static final long BIND_TIMEOUT_MS = 5_000L;
    private static final long NO_OPERATION = Long.MIN_VALUE;

    private final Context context;
    private final Listener listener;
    private final Handler main = new Handler(Looper.getMainLooper());

    private IXrayService service;
    private Request pending;
    private XrayConnection connection;
    private long connectionGeneration;
    private long callbackGeneration;
    private long activeOperationId = NO_OPERATION;
    private boolean binding;

    XrayServiceClient(Context context, Listener listener) {
        this.context = context.getApplicationContext();
        this.listener = listener;
    }

    synchronized void execute(Request request) {
        pending = request;
        if (service != null) {
            dispatchLocked();
            return;
        }
        if (binding) return;

        binding = true;
        long generation = ++connectionGeneration;
        XrayConnection next = new XrayConnection(generation);
        connection = next;
        main.removeCallbacks(next.timeout);
        main.postDelayed(next.timeout, BIND_TIMEOUT_MS);

        Intent intent = new Intent(context, XrayService.class);
        try {
            if (!context.bindService(intent, next, Context.BIND_AUTO_CREATE)) {
                failLocked(next, "Xray service bind failed");
            }
        } catch (Exception error) {
            failLocked(next, XrayErrorSanitizer.fromException(error));
        } catch (LinkageError error) {
            failLocked(next, XrayErrorSanitizer.sanitize(error));
        }
    }

    synchronized void cancel(int operation, long operationId) {
        try {
            if (service != null) {
                try {
                    service.cancel(operation, operationId);
                } catch (Exception | LinkageError ignored) {
                }
            }
        } finally {
            disconnectLocked();
        }
    }

    synchronized void disconnect() {
        disconnectLocked();
    }

    private void dispatchLocked() {
        Request request = pending;
        pending = null;
        if (request == null || service == null) return;

        activeOperationId = request.operationId;
        long generation = callbackGeneration;
        IXrayCallback callback = new IXrayCallback.Stub() {
            @Override
            public void onResult(
                    long operationId,
                    int operation,
                    boolean success,
                    int socksPort,
                    long latencyMs,
                    String message) {
                XrayResult result = new XrayResult(
                        operationId,
                        operation,
                        success,
                        socksPort,
                        latencyMs,
                        XrayErrorSanitizer.sanitize(message));
                main.post(() -> deliverResult(generation, result));
            }
        };

        try {
            switch (request.operation) {
                case XrayOperation.VALIDATE ->
                        service.validate(request.operationId, request.shareLink, request.udp, request.tlsFragment, callback);
                case XrayOperation.TEST ->
                        service.test(request.operationId, request.shareLink, request.udp, request.tlsFragment, callback);
                case XrayOperation.START ->
                        service.start(request.operationId, request.shareLink, request.udp, request.tlsFragment, callback);
                case XrayOperation.STOP ->
                        service.stop(request.operationId, callback);
                case XrayOperation.RESET_SECURITY ->
                        service.resetSecurity(request.operationId, callback);
                default -> throw new IllegalArgumentException("Unknown Xray operation");
            }
            request.onDispatched.run();
        } catch (Exception error) {
            failLocked(connection, XrayErrorSanitizer.fromException(error));
        } catch (LinkageError error) {
            failLocked(connection, XrayErrorSanitizer.sanitize(error));
        }
    }

    private void deliverResult(long generation, XrayResult result) {
        synchronized (this) {
            if (generation != callbackGeneration) return;
        }
        listener.onResult(result);
    }

    private synchronized void failLocked(XrayConnection expected, String message) {
        if (expected != null && expected != connection) {
            expected.detach();
            try {
                context.unbindService(expected);
            } catch (RuntimeException | LinkageError ignored) {
            }
            return;
        }

        long failedOperationId =
                pending != null ? pending.operationId : activeOperationId;
        disconnectLocked();

        if (failedOperationId != NO_OPERATION) {
            long generation = callbackGeneration;
            main.post(() -> {
                synchronized (XrayServiceClient.this) {
                    if (generation != callbackGeneration) return;
                }
                listener.onConnectionFailure(
                        failedOperationId,
                        XrayErrorSanitizer.sanitize(message));
            });
        }
    }

    private void disconnectLocked() {
        connectionGeneration++;
        callbackGeneration++;
        pending = null;
        activeOperationId = NO_OPERATION;

        XrayConnection old = connection;
        connection = null;
        service = null;
        binding = false;

        if (old != null) {
            main.removeCallbacks(old.timeout);
            old.detach();
            try {
                context.unbindService(old);
            } catch (RuntimeException | LinkageError ignored) {
            }
        }
    }

    private final class XrayConnection implements ServiceConnection, IBinder.DeathRecipient {

        final long generation;
        final Runnable timeout = () -> onBindTimeout(this);
        IBinder binder;

        XrayConnection(long generation) {
            this.generation = generation;
        }

        @Override
        public void onServiceConnected(ComponentName name, IBinder binder) {
            synchronized (XrayServiceClient.this) {
                if (this != connection || generation != connectionGeneration) {
                    try {
                        context.unbindService(this);
                    } catch (RuntimeException | LinkageError ignored) {
                    }
                    return;
                }

                main.removeCallbacks(timeout);
                binding = false;
                this.binder = binder;
                try {
                    service = IXrayService.Stub.asInterface(binder);
                    binder.linkToDeath(this, 0);
                    dispatchLocked();
                } catch (RemoteException error) {
                    failLocked(this, "Xray service connection died");
                } catch (RuntimeException error) {
                    failLocked(this, XrayErrorSanitizer.fromException(error));
                } catch (LinkageError error) {
                    failLocked(this, XrayErrorSanitizer.sanitize(error));
                }
            }
        }

        @Override
        public void onServiceDisconnected(ComponentName name) {
            synchronized (XrayServiceClient.this) {
                failLocked(this, "Xray service disconnected");
            }
        }

        @Override
        public void onBindingDied(ComponentName name) {
            synchronized (XrayServiceClient.this) {
                failLocked(this, "Xray service binding died");
            }
        }

        @Override
        public void onNullBinding(ComponentName name) {
            synchronized (XrayServiceClient.this) {
                failLocked(this, "Xray service returned no binder");
            }
        }

        @Override
        public void binderDied() {
            synchronized (XrayServiceClient.this) {
                failLocked(this, "Xray service process died");
            }
        }

        void detach() {
            main.removeCallbacks(timeout);
            if (binder != null) {
                try {
                    binder.unlinkToDeath(this, 0);
                } catch (Exception | LinkageError ignored) {
                }
                binder = null;
            }
        }
    }

    private void onBindTimeout(XrayConnection expected) {
        synchronized (this) {
            if (expected != connection || !binding || service != null) return;
            failLocked(expected, "Xray service connection timed out");
        }
    }
}
