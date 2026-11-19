#!/usr/bin/env python3
"""Deterministic lifecycle tests for the real XrayServiceClient."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "xray/src/main/java/com/fingmi/xray"

STUBS = {
    "android/content/ComponentName.java": r'''
package android.content;
public final class ComponentName {}
''',
    "android/content/Intent.java": r'''
package android.content;
public final class Intent {
    public Intent(Context context, Class<?> type) {}
}
''',
    "android/content/ServiceConnection.java": r'''
package android.content;
import android.os.IBinder;
public interface ServiceConnection {
    void onServiceConnected(ComponentName name, IBinder binder);
    void onServiceDisconnected(ComponentName name);
    void onBindingDied(ComponentName name);
    void onNullBinding(ComponentName name);
}
''',
    "android/content/Context.java": r'''
package android.content;
public class Context {
    public static final int BIND_AUTO_CREATE = 1;
    public Context getApplicationContext() { return this; }
    public boolean bindService(Intent intent, ServiceConnection connection, int flags) {
        throw new UnsupportedOperationException();
    }
    public void unbindService(ServiceConnection connection) {}
}
''',
    "android/os/RemoteException.java": r'''
package android.os;
public class RemoteException extends Exception {
    public RemoteException() {}
    public RemoteException(String message) { super(message); }
}
''',
    "android/os/IBinder.java": r'''
package android.os;
public interface IBinder {
    interface DeathRecipient { void binderDied(); }
    void linkToDeath(DeathRecipient recipient, int flags) throws RemoteException;
    boolean unlinkToDeath(DeathRecipient recipient, int flags);
}
''',
    "android/os/Looper.java": r'''
package android.os;
public final class Looper {
    private static final Looper MAIN = new Looper();
    private Looper() {}
    public static Looper getMainLooper() { return MAIN; }
    public static Looper myLooper() { return MAIN; }
}
''',
    "android/os/Handler.java": r'''
package android.os;
import java.util.Comparator;
import java.util.PriorityQueue;
public final class Handler {
    private record Task(long time, long sequence, Runnable callback) {}
    private static final PriorityQueue<Task> TASKS =
            new PriorityQueue<>(Comparator.comparingLong(Task::time)
                    .thenComparingLong(Task::sequence));
    private static long now;
    private static long sequence;
    public Handler(Looper looper) {}
    public boolean post(Runnable callback) { return postDelayed(callback, 0L); }
    public boolean postDelayed(Runnable callback, long delay) {
        TASKS.add(new Task(now + delay, ++sequence, callback));
        return true;
    }
    public void removeCallbacks(Runnable callback) {
        TASKS.removeIf(task -> task.callback == callback);
    }
    public static void reset() {
        TASKS.clear();
        now = 0L;
        sequence = 0L;
    }
    public static int pendingCount() { return TASKS.size(); }
    public static void advance(long amount) {
        long target = now + amount;
        while (!TASKS.isEmpty() && TASKS.peek().time <= target) {
            Task task = TASKS.remove();
            now = task.time;
            task.callback.run();
        }
        now = target;
    }
}
''',
    "com/fingmi/xray/service/IXrayCallback.java": r'''
package com.fingmi.xray.service;
public interface IXrayCallback {
    void onResult(long operationId, int operation, boolean success,
            int socksPort, long latencyMs, String message);
    abstract class Stub implements IXrayCallback {}
}
''',
    "com/fingmi/xray/service/IXrayService.java": r'''
package com.fingmi.xray.service;
import android.os.IBinder;
public interface IXrayService {
    void validate(long id, String link, boolean udp, boolean tlsFragment, IXrayCallback callback) throws Exception;
    void test(long id, String link, boolean udp, boolean tlsFragment, IXrayCallback callback) throws Exception;
    void start(long id, String link, boolean udp, boolean tlsFragment, IXrayCallback callback) throws Exception;
    void stop(long id, IXrayCallback callback) throws Exception;
    void resetSecurity(long id, IXrayCallback callback) throws Exception;
    void cancel(int operation, long id) throws Exception;
    abstract class Stub {
        public interface ServiceBinder extends IBinder {
            IXrayService service();
        }
        public static IXrayService asInterface(IBinder binder) {
            return ((ServiceBinder) binder).service();
        }
    }
}
''',
    "com/fingmi/xray/service/XrayService.java": r'''
package com.fingmi.xray.service;
public final class XrayService {}
''',
    "com/fingmi/xray/session/ServiceClientLifecycleTest.java": r'''
package com.fingmi.xray.session;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Handler;
import android.os.IBinder;
import android.os.RemoteException;

import com.fingmi.xray.service.IXrayCallback;
import com.fingmi.xray.service.IXrayService;
import com.fingmi.xray.service.XrayOperation;

import java.util.ArrayList;
import java.util.List;

public final class ServiceClientLifecycleTest {

    private static final ComponentName NAME = new ComponentName();

    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static final class Listener implements XrayServiceClient.Listener {
        final List<XrayResult> results = new ArrayList<>();
        final List<Long> failures = new ArrayList<>();
        final List<String> failureMessages = new ArrayList<>();

        @Override
        public void onResult(XrayResult result) {
            results.add(result);
        }

        @Override
        public void onConnectionFailure(long operationId, String message) {
            failures.add(operationId);
            failureMessages.add(message);
        }
    }

    private static final class FakeContext extends Context {
        ServiceConnection lastConnection;
        final List<ServiceConnection> unbound = new ArrayList<>();
        final List<String> trace = new ArrayList<>();
        boolean bindResult = true;
        boolean throwBindLinkage;
        boolean throwUnbindLinkage;

        @Override
        public Context getApplicationContext() {
            return this;
        }

        @Override
        public boolean bindService(Intent intent, ServiceConnection connection, int flags) {
            lastConnection = connection;
            trace.add("bind");
            if (throwBindLinkage) {
                throw new NoClassDefFoundError("synthetic bind linkage");
            }
            return bindResult;
        }

        @Override
        public void unbindService(ServiceConnection connection) {
            trace.add("unbind");
            if (throwUnbindLinkage) {
                throw new NoClassDefFoundError("synthetic unbind linkage");
            }
            unbound.add(connection);
        }
    }

    private static final class FakeService implements IXrayService {
        final List<String> calls = new ArrayList<>();
        final List<String> trace;
        IXrayCallback callback;
        boolean throwCancelLinkage;
        boolean lastUdp, lastTlsFragment;

        FakeService(List<String> trace) {
            this.trace = trace;
        }

        private void call(String name, long id, IXrayCallback cb) {
            calls.add(name + ":" + id);
            callback = cb;
        }

        @Override
        public void validate(long id, String link, boolean udp, boolean tlsFragment, IXrayCallback cb) {
            lastUdp = udp;
            lastTlsFragment = tlsFragment;
            call("validate", id, cb);
        }

        @Override
        public void test(long id, String link, boolean udp, boolean tlsFragment, IXrayCallback cb) {
            lastUdp = udp;
            lastTlsFragment = tlsFragment;
            call("test", id, cb);
        }

        @Override
        public void start(long id, String link, boolean udp, boolean tlsFragment, IXrayCallback cb) {
            lastUdp = udp;
            lastTlsFragment = tlsFragment;
            call("start", id, cb);
        }

        @Override
        public void stop(long id, IXrayCallback cb) {
            call("stop", id, cb);
        }

        @Override
        public void resetSecurity(long id, IXrayCallback cb) {
            call("reset", id, cb);
        }

        @Override
        public void cancel(int operation, long id) {
            trace.add("remote-cancel:" + operation + ":" + id);
            if (throwCancelLinkage) {
                throw new NoClassDefFoundError("synthetic cancel linkage");
            }
        }
    }

    private static final class FakeBinder implements IXrayService.Stub.ServiceBinder {
        final FakeService service;
        DeathRecipient recipient;
        boolean throwOnLink;
        boolean throwLinkageOnLink;
        boolean throwLinkageOnUnlink;
        boolean throwLinkageOnAsInterface;
        boolean throwRuntimeOnAsInterface;
        int unlinkCount;

        FakeBinder(FakeService service) {
            this.service = service;
        }

        @Override
        public IXrayService service() {
            if (throwLinkageOnAsInterface) {
                throw new NoClassDefFoundError("synthetic asInterface linkage");
            }
            if (throwRuntimeOnAsInterface) {
                throw new IllegalStateException("synthetic asInterface runtime");
            }
            return service;
        }

        @Override
        public void linkToDeath(DeathRecipient recipient, int flags) throws RemoteException {
            if (throwLinkageOnLink) {
                throw new NoClassDefFoundError("synthetic link linkage");
            }
            if (throwOnLink) throw new RemoteException("synthetic link failure");
            this.recipient = recipient;
        }

        @Override
        public boolean unlinkToDeath(DeathRecipient recipient, int flags) {
            if (throwLinkageOnUnlink) {
                throw new NoClassDefFoundError("synthetic unlink linkage");
            }
            if (this.recipient == recipient) this.recipient = null;
            unlinkCount++;
            return true;
        }

        void die() {
            DeathRecipient current = recipient;
            if (current != null) current.binderDied();
        }
    }

    private static XrayServiceClient.Request request(
            long id, int operation, Runnable dispatched) {
        return new XrayServiceClient.Request(
                id,
                operation,
                "trojan://synthetic@example.invalid:443",
                false,
                dispatched);
    }

    private static FakeBinder connect(FakeContext context, FakeService service) {
        FakeBinder binder = new FakeBinder(service);
        context.lastConnection.onServiceConnected(NAME, binder);
        return binder;
    }

    private static void pendingRequestReplacementMatchesReleased() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);
        int[] dispatch = {0, 0};

        client.execute(request(1L, XrayOperation.TEST, () -> dispatch[0]++));
        ServiceConnection original = context.lastConnection;
        client.execute(request(2L, XrayOperation.VALIDATE, () -> dispatch[1]++));

        FakeService service = new FakeService(context.trace);
        FakeBinder binder = new FakeBinder(service);
        original.onServiceConnected(NAME, binder);

        check(service.calls.equals(List.of("validate:2")),
                "binding generation did not keep only the latest pending request: " + service.calls);
        check(dispatch[0] == 0 && dispatch[1] == 1,
                "released pending dispatch ownership changed");
    }

    private static void fragmentOptionReachesEachBinderOperation() {
        for (int operation : new int[] {XrayOperation.VALIDATE, XrayOperation.TEST, XrayOperation.START}) {
            Handler.reset();
            FakeContext context = new FakeContext();
            XrayServiceClient client = new XrayServiceClient(context, new Listener());
            client.execute(new XrayServiceClient.Request(101L, operation,
                    "trojan://synthetic@example.invalid:443", false, true, () -> {}));
            FakeService service = new FakeService(context.trace);
            connect(context, service);
            check(!service.lastUdp && service.lastTlsFragment,
                    "Binder dispatch lost the independent fragment option for " + operation);
            client.execute(new XrayServiceClient.Request(102L, operation,
                    "trojan://synthetic@example.invalid:443", true, false, () -> {}));
            check(service.lastUdp && !service.lastTlsFragment,
                    "Binder dispatch reused a stale fragment option for " + operation);
            client.execute(request(103L, operation, () -> {}));
            check(!service.lastTlsFragment, "legacy request enabled fragmentation");
            client.disconnect();
        }
    }

    private static void currentCallbackDelivered() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(3L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        connect(context, service);
        service.callback.onResult(3L, XrayOperation.TEST, true, 0, 17L, "");
        Handler.advance(0L);

        check(listener.results.size() == 1 && listener.results.get(0).operationId == 3L,
                "current callback was not delivered");
    }

    private static void disconnectInvalidatesPostedCallback() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(4L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        connect(context, service);
        service.callback.onResult(4L, XrayOperation.TEST, true, 0, 18L, "");
        client.disconnect();
        Handler.advance(0L);

        check(listener.results.isEmpty(), "stale callback survived disconnect generation");
    }

    private static void cancelCallsRemoteBeforeUnbindAndInvalidatesCallback() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(5L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        connect(context, service);
        IXrayCallback oldCallback = service.callback;
        context.trace.clear();

        client.cancel(XrayOperation.TEST, 5L);

        check(context.trace.equals(List.of(
                        "remote-cancel:" + XrayOperation.TEST + ":5",
                        "unbind")),
                "cancel/unbind order changed: " + context.trace);

        oldCallback.onResult(5L, XrayOperation.TEST, true, 0, 19L, "");
        Handler.advance(0L);
        check(listener.results.isEmpty(), "cancelled callback was delivered");
    }

    private static void cancelLinkageStillUnbindsAndInvalidatesCallback() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(51L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        connect(context, service);
        IXrayCallback oldCallback = service.callback;
        service.throwCancelLinkage = true;
        context.trace.clear();

        client.cancel(XrayOperation.TEST, 51L);

        check(context.trace.equals(List.of(
                        "remote-cancel:" + XrayOperation.TEST + ":51",
                        "unbind")),
                "cancel LinkageError did not preserve disconnect cleanup: " + context.trace);

        oldCallback.onResult(51L, XrayOperation.TEST, true, 0, 20L, "");
        Handler.advance(0L);
        check(listener.results.isEmpty(),
                "callback survived cancel LinkageError disconnect");
    }

    private static void bindTimeoutDisconnectsThenReportsFailure() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(6L, XrayOperation.VALIDATE, () -> {}));
        ServiceConnection timedOut = context.lastConnection;
        Handler.advance(5_000L);

        check(context.unbound.contains(timedOut), "bind timeout did not unbind");
        check(listener.failures.equals(List.of(6L)), "bind timeout failure id changed");
        check(listener.failureMessages.get(0).contains("timed out"),
                "bind timeout failure message changed");
    }

    private static void staleServiceConnectionCannotReplaceCurrent() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(7L, XrayOperation.TEST, () -> {}));
        ServiceConnection stale = context.lastConnection;
        client.disconnect();

        client.execute(request(8L, XrayOperation.VALIDATE, () -> {}));
        ServiceConnection current = context.lastConnection;

        FakeService staleService = new FakeService(context.trace);
        stale.onServiceConnected(NAME, new FakeBinder(staleService));
        check(staleService.calls.isEmpty(), "stale ServiceConnection dispatched a request");

        FakeService currentService = new FakeService(context.trace);
        FakeBinder currentBinder = new FakeBinder(currentService);
        current.onServiceConnected(NAME, currentBinder);
        check(currentService.calls.equals(List.of("validate:8")),
                "current ServiceConnection lost request ownership");

        int unbindBefore = context.unbound.size();
        stale.onServiceDisconnected(NAME);
        check(context.unbound.size() == unbindBefore + 1,
                "stale disconnect was not detached independently");

        currentService.callback.onResult(
                8L, XrayOperation.VALIDATE, true, 0, -1L, "");
        Handler.advance(0L);
        check(listener.results.size() == 1 && listener.results.get(0).operationId == 8L,
                "stale connection failure disturbed current generation");
    }

    private static void nullBindingDisconnectsAndReportsFailure() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(86L, XrayOperation.TEST, () -> {}));
        ServiceConnection nullBinding = context.lastConnection;
        nullBinding.onNullBinding(NAME);
        Handler.advance(0L);

        check(context.unbound.contains(nullBinding),
                "null Binder binding was not unbound");
        check(listener.failures.equals(List.of(86L)),
                "null Binder binding lost the pending operation");
        check(listener.failureMessages.get(0).contains("no binder"),
                "null Binder binding failure message changed");
        check(Handler.pendingCount() == 0,
                "null Binder binding did not remove its scheduled bind timeout");
        Handler.advance(5_000L);
        check(listener.failures.equals(List.of(86L)),
                "null Binder binding left a live bind timeout");
    }

    private static void activeServiceDisconnectReportsFailureAndInvalidatesCallback(
            boolean bindingDied) {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(bindingDied ? 88L : 87L, XrayOperation.START, () -> {}));
        FakeService service = new FakeService(context.trace);
        ServiceConnection connection = context.lastConnection;
        connect(context, service);
        IXrayCallback stale = service.callback;

        if (bindingDied) connection.onBindingDied(NAME);
        else connection.onServiceDisconnected(NAME);
        Handler.advance(0L);

        long expected = bindingDied ? 88L : 87L;
        check(context.unbound.contains(connection),
                "terminal service callback did not unbind the active connection");
        check(listener.failures.equals(List.of(expected)),
                "terminal service callback lost the active operation");
        stale.onResult(expected, XrayOperation.START, true, 12345, -1L, "");
        Handler.advance(0L);
        check(listener.results.isEmpty(),
                "terminal service callback allowed a stale START result");
    }

    private static void bindLinkageReportsFailureAndUnbinds() {
        Handler.reset();
        FakeContext context = new FakeContext();
        context.throwBindLinkage = true;
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(81L, XrayOperation.TEST, () -> {}));
        Handler.advance(0L);

        check(context.unbound.contains(context.lastConnection),
                "bind LinkageError did not unbind failed connection");
        check(listener.failures.equals(List.of(81L)),
                "bind LinkageError did not report pending operation");
    }

    private static void asInterfaceLinkageReportsFailureAndUnbinds() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(82L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        FakeBinder binder = new FakeBinder(service);
        binder.throwLinkageOnAsInterface = true;
        context.lastConnection.onServiceConnected(NAME, binder);
        Handler.advance(0L);

        check(context.unbound.contains(context.lastConnection),
                "asInterface LinkageError did not unbind connection");
        check(listener.failures.equals(List.of(82L)),
                "asInterface LinkageError did not report pending operation");
    }

    private static void asInterfaceRuntimeReportsFailureAndUnbinds() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(821L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        FakeBinder binder = new FakeBinder(service);
        binder.throwRuntimeOnAsInterface = true;
        context.lastConnection.onServiceConnected(NAME, binder);
        Handler.advance(0L);

        check(context.unbound.contains(context.lastConnection),
                "asInterface RuntimeException did not unbind connection");
        check(listener.failures.equals(List.of(821L)),
                "asInterface RuntimeException did not report pending operation");
    }

    private static void linkToDeathLinkageReportsFailureAndUnbinds() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(83L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        FakeBinder binder = new FakeBinder(service);
        binder.throwLinkageOnLink = true;
        context.lastConnection.onServiceConnected(NAME, binder);
        Handler.advance(0L);

        check(context.unbound.contains(context.lastConnection),
                "linkToDeath LinkageError did not unbind connection");
        check(listener.failures.equals(List.of(83L)),
                "linkToDeath LinkageError did not report pending operation");
    }

    private static void unlinkLinkageStillCompletesCancelDisconnect() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(84L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        FakeBinder binder = connect(context, service);
        IXrayCallback oldCallback = service.callback;
        binder.throwLinkageOnUnlink = true;
        context.trace.clear();

        client.cancel(XrayOperation.TEST, 84L);

        check(context.trace.equals(List.of(
                        "remote-cancel:" + XrayOperation.TEST + ":84",
                        "unbind")),
                "unlink LinkageError interrupted cancel cleanup: " + context.trace);
        oldCallback.onResult(84L, XrayOperation.TEST, true, 0, 21L, "");
        Handler.advance(0L);
        check(listener.results.isEmpty(),
                "callback survived unlink LinkageError disconnect");
    }

    private static void unbindLinkageStillInvalidatesCallbackGeneration() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(85L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        connect(context, service);
        IXrayCallback oldCallback = service.callback;
        context.throwUnbindLinkage = true;
        context.trace.clear();

        client.disconnect();

        check(context.trace.equals(List.of("unbind")),
                "unbind LinkageError was not attempted: " + context.trace);
        oldCallback.onResult(85L, XrayOperation.TEST, true, 0, 22L, "");
        Handler.advance(0L);
        check(listener.results.isEmpty(),
                "callback survived unbind LinkageError disconnect");
    }

    private static void binderDeathReportsActiveOperation() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(9L, XrayOperation.START, () -> {}));
        FakeService service = new FakeService(context.trace);
        FakeBinder binder = connect(context, service);
        binder.die();
        Handler.advance(0L);

        check(listener.failures.equals(List.of(9L)),
                "Binder death did not report active operation");
        check(listener.failureMessages.get(0).contains("process died"),
                "Binder death message changed");
    }

    private static void linkToDeathFailureReportsConnectionFailure() {
        Handler.reset();
        FakeContext context = new FakeContext();
        Listener listener = new Listener();
        XrayServiceClient client = new XrayServiceClient(context, listener);

        client.execute(request(10L, XrayOperation.TEST, () -> {}));
        FakeService service = new FakeService(context.trace);
        FakeBinder binder = new FakeBinder(service);
        binder.throwOnLink = true;
        context.lastConnection.onServiceConnected(NAME, binder);
        Handler.advance(0L);

        check(listener.failures.equals(List.of(10L)),
                "linkToDeath failure lost active request");
        check(listener.failureMessages.get(0).contains("connection died"),
                "linkToDeath failure message changed");
    }

    public static void main(String[] args) {
        fragmentOptionReachesEachBinderOperation();
        pendingRequestReplacementMatchesReleased();
        currentCallbackDelivered();
        disconnectInvalidatesPostedCallback();
        cancelCallsRemoteBeforeUnbindAndInvalidatesCallback();
        cancelLinkageStillUnbindsAndInvalidatesCallback();
        bindTimeoutDisconnectsThenReportsFailure();
        staleServiceConnectionCannotReplaceCurrent();
        nullBindingDisconnectsAndReportsFailure();
        activeServiceDisconnectReportsFailureAndInvalidatesCallback(false);
        activeServiceDisconnectReportsFailureAndInvalidatesCallback(true);
        bindLinkageReportsFailureAndUnbinds();
        asInterfaceLinkageReportsFailureAndUnbinds();
        asInterfaceRuntimeReportsFailureAndUnbinds();
        linkToDeathLinkageReportsFailureAndUnbinds();
        unlinkLinkageStillCompletesCancelDisconnect();
        unbindLinkageStillInvalidatesCallbackGeneration();
        binderDeathReportsActiveOperation();
        linkToDeathFailureReportsConnectionFailure();
        System.out.println("PASS released XrayServiceClient lifecycle");
    }
}
''',
}

with tempfile.TemporaryDirectory(prefix="xray-service-client-") as directory:
    work = Path(directory)
    generated = []
    for relative, content in STUBS.items():
        path = work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n")
        generated.append(path)

    production = [
        PRODUCTION / "session/XrayServiceClient.java",
        PRODUCTION / "session/XrayResult.java",
        PRODUCTION / "service/XrayOperation.java",
        PRODUCTION / "util/XrayErrorSanitizer.java",
    ]
    subprocess.run(
        [
            "java",
            "com.sun.tools.javac.Main",
            "--release",
            "17",
            "-d",
            str(work / "classes"),
            *map(str, production),
            *map(str, generated),
        ],
        check=True,
    )
    subprocess.run(
        [
            "java",
            "-cp",
            str(work / "classes"),
            "com.fingmi.xray.session.ServiceClientLifecycleTest",
        ],
        check=True,
    )
