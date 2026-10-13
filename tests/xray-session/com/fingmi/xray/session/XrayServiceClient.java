package com.fingmi.xray.session;
import android.content.Context;
import com.fingmi.xray.test.Trace;
import java.util.*;
/** Test-only Binder transport. It records commands, never substitutes controller logic. */
final class XrayServiceClient {
    interface Listener { void onResult(XrayResult result); void onConnectionFailure(long id, String message); }
    static final class Request {
        final long operationId; final int operation; final Runnable onDispatched;
        final String shareLink; final boolean udp; final boolean tlsFragment;
        Request(long id, int op, String share, boolean udp, Runnable dispatched) {
            this(id, op, share, udp, false, dispatched);
        }
        Request(long id, int op, String share, boolean udp, boolean tlsFragment, Runnable dispatched) {
            operationId=id; operation=op; onDispatched=dispatched;
            shareLink=share; this.udp=udp; this.tlsFragment=tlsFragment;
        }
    }
    static XrayServiceClient last;
    final List<Request> requests = new ArrayList<>();
    int cancellations, disconnects;
    int lastCancelledOperation = -1;
    long lastCancelledOperationId = Long.MIN_VALUE;
    XrayServiceClient(Context context, Listener listener) {
        last=this;
        Trace.add("client:create");
    }
    void execute(Request request) {
        requests.add(request);
        Trace.add("client:execute:" + request.operation);
        request.onDispatched.run();
    }
    void cancel(int op, long id) {
        cancellations++;
        lastCancelledOperation = op;
        lastCancelledOperationId = id;
        Trace.add("client:cancel:" + op);
        disconnect();
    }
    void disconnect() {
        disconnects++;
        Trace.add("client:disconnect");
    }
    Request latest() { return requests.get(requests.size()-1); }
}
