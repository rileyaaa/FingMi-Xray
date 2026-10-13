package com.fingmi.xray.session;

import android.content.Context;
import android.os.Handler;

import com.fingmi.xray.service.XrayOperation;
import com.fingmi.xray.config.XrayPreferences;
import com.fingmi.xray.test.Trace;

/** Released settings-side Binder generation and callback ordering contract. */
public final class SettingsLifecycleTest {

    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static void before(String earlier, String later) {
        int a = Trace.indexOf(earlier);
        int b = Trace.indexOf(later);
        check(a >= 0, "missing trace: " + earlier + " in " + Trace.events());
        check(b >= 0, "missing trace: " + later + " in " + Trace.events());
        check(a < b, earlier + " did not happen before " + later + ": " + Trace.events());
    }

    private static XraySettingsController fresh(XraySettingsController.Listener listener) {
        Handler.reset();
        XrayPreferences.udpEnabled = false;
        XrayPreferences.tlsFragmentEnabled = false;
        Trace.reset();
        com.fingmi.xray.config.XrayPreferences.configured = true;
        com.fingmi.xray.config.XrayPreferences.throwClearAfterRemoval = false;
        com.fingmi.xray.config.XrayPreferences.throwShareLinkLinkage = false;
        XraySettingsController controller =
                new XraySettingsController(new Context(), listener);
        Trace.reset();
        return controller;
    }

    private static void deleteOrderMatchesReleased() throws Exception {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {});
        long operationId = controller.delete(() -> Trace.add("ui:clear"));
        XrayServiceClient.Request request = XrayServiceClient.last.latest();

        check(request.operationId == operationId, "RESET operation id changed");
        check(request.operation == XrayOperation.RESET_SECURITY, "RESET operation missing");
        before("client:disconnect", "client:create");
        before("client:create", "preferences:clear");
        before("preferences:clear", "ui:clear");
        before("ui:clear", "client:execute:" + XrayOperation.RESET_SECURITY);

        Trace.reset();
        controller.save("trojan://replacement@example.invalid:443", false);
        check(!Trace.events().contains("preferences:save"),
                "Save was allowed during RESET_SECURITY");
    }

    private static void partialLocalDeleteStillClearsUi() {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {});
        com.fingmi.xray.config.XrayPreferences.throwClearAfterRemoval = true;
        boolean[] cleared = {false};
        try {
            controller.delete(() -> {
                cleared[0] = true;
                Trace.add("ui:clear");
            });
            throw new AssertionError("partial local delete failure was not surfaced");
        } catch (Exception expected) {
        }
        check(cleared[0], "UI was not cleared after local preferences were already removed");
        check(!com.fingmi.xray.config.XrayPreferences.configured,
                "partial local delete test did not remove stored node");
        check(!controller.hasActiveOperation(),
                "partial local delete failure left RESET_SECURITY active");
    }

    private static void localClearCallbackFailureStillDispatchesReset() throws Exception {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {});
        int[] calls = {0};
        long operationId = controller.delete(() -> {
            calls[0]++;
            throw new IllegalStateException("synthetic UI clear failure");
        });
        XrayServiceClient.Request request = XrayServiceClient.last.latest();
        check(calls[0] == 1,
                "local-clear UI callback must be isolated without duplicate delivery");
        check(!com.fingmi.xray.config.XrayPreferences.configured,
                "local-clear callback failure did not keep storage cleared");
        check(controller.hasActiveOperation(),
                "local-clear callback failure aborted RESET_SECURITY");
        check(request.operationId == operationId,
                "local-clear callback failure changed RESET_SECURITY owner");
        check(request.operation == XrayOperation.RESET_SECURITY,
                "local-clear callback failure skipped RESET_SECURITY dispatch");
    }

    private static void localClearCancelDoesNotRedispatchReset() throws Exception {
        XraySettingsController[] holder = new XraySettingsController[1];
        XrayServiceClient[] deleteOwner = new XrayServiceClient[1];
        holder[0] = fresh((id, op, ok, latency, message) -> {});
        holder[0].delete(() -> {
            deleteOwner[0] = XrayServiceClient.last;
            holder[0].cancel();
        });
        check(deleteOwner[0] != null, "delete owner client was not captured");
        check(deleteOwner[0].requests.isEmpty(),
                "cancelled delete redispatched RESET_SECURITY after local-clear callback");
        check(deleteOwner[0].cancellations == 1,
                "local-clear cancel did not cancel the pending RESET owner");
        check(!holder[0].hasActiveOperation(),
                "local-clear cancel left delete active");
    }

    private static void localClearAbandonDoesNotRedispatchReset() throws Exception {
        XraySettingsController[] holder = new XraySettingsController[1];
        XrayServiceClient[] deleteOwner = new XrayServiceClient[1];
        holder[0] = fresh((id, op, ok, latency, message) -> {});
        holder[0].delete(() -> {
            deleteOwner[0] = XrayServiceClient.last;
            holder[0].abandon();
        });
        check(deleteOwner[0] != null, "delete owner client was not captured");
        check(deleteOwner[0].requests.isEmpty(),
                "abandoned delete redispatched RESET_SECURITY after local-clear callback");
        check(deleteOwner[0].cancellations == 0,
                "local-clear abandon unexpectedly sent remote RESET cancel");
        check(!holder[0].hasActiveOperation(),
                "local-clear abandon left delete active");
    }

    private static void localClearCloseDoesNotRedispatchReset() throws Exception {
        XraySettingsController[] holder = new XraySettingsController[1];
        XrayServiceClient[] deleteOwner = new XrayServiceClient[1];
        holder[0] = fresh((id, op, ok, latency, message) -> {});
        holder[0].delete(() -> {
            deleteOwner[0] = XrayServiceClient.last;
            holder[0].close();
        });
        check(deleteOwner[0] != null, "delete owner client was not captured");
        check(deleteOwner[0].requests.isEmpty(),
                "closed delete redispatched RESET_SECURITY after local-clear callback");
        check(!holder[0].hasActiveOperation(),
                "local-clear close left delete active");
    }

    private static void partialDeleteCallbackCanCreateReplacement() {
        XraySettingsController[] holder = new XraySettingsController[1];
        XrayServiceClient[] replacementClient = new XrayServiceClient[1];
        holder[0] = fresh((id, op, ok, latency, message) -> {});
        com.fingmi.xray.config.XrayPreferences.throwClearAfterRemoval = true;
        try {
            holder[0].delete(() -> {
                holder[0].abandon();
                holder[0].test("trojan://replacement@example.invalid:443", false);
                replacementClient[0] = XrayServiceClient.last;
            });
            throw new AssertionError("partial delete failure was not surfaced");
        } catch (Exception expected) {
        }
        check(replacementClient[0] != null,
                "partial-delete recovery callback did not create replacement client");
        check(holder[0].hasActiveOperation(),
                "partial-delete outer cleanup destroyed replacement operation");
        check(XrayServiceClient.last == replacementClient[0],
                "partial-delete outer cleanup replaced the newer settings client");
        check(replacementClient[0].requests.size() == 1,
                "partial-delete replacement TEST request was not preserved");
        check(replacementClient[0].disconnects == 0,
                "partial-delete outer cleanup disconnected replacement client");
    }

    private static void phoneAbandonDoesNotRemoteCancel() {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {});
        controller.test("trojan://synthetic@example.invalid:443", false);
        Trace.reset();
        controller.abandon();
        check(!Trace.events().contains("client:cancel:" + XrayOperation.TEST),
                "phone import sent a remote TEST cancel");
        before("client:disconnect", "client:create");
    }

    private static void timeoutNotifiesBeforeCancel() {
        XraySettingsController controller = fresh((id, op, ok, latency, message) ->
                Trace.add("listener:timeout"));
        controller.test("trojan://synthetic@example.invalid:443", false);
        Trace.reset();
        Handler.advance(45_000L);
        before("listener:timeout", "client:cancel:" + XrayOperation.TEST);
        before("client:cancel:" + XrayOperation.TEST, "client:create");
    }

    private static void resultNotifiesBeforeClientReplacement() {
        XraySettingsController controller = fresh((id, op, ok, latency, message) ->
                Trace.add("listener:result"));
        controller.test("trojan://synthetic@example.invalid:443", false);
        XrayServiceClient.Request request = XrayServiceClient.last.latest();
        Trace.reset();
        controller.onResult(new XrayResult(
                request.operationId,
                request.operation,
                true,
                0,
                12L,
                ""));
        before("listener:result", "client:disconnect");
        before("client:disconnect", "client:create");
    }

    private static void throwingTimeoutListenerStillCleansOldOwner() {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {
            throw new IllegalStateException("synthetic listener failure");
        });
        controller.test("trojan://synthetic@example.invalid:443", false);
        XrayServiceClient client = XrayServiceClient.last;
        Handler.advance(45_000L);
        check(!controller.hasActiveOperation(), "throwing timeout listener left operation active");
        check(client.cancellations == 1, "throwing timeout listener skipped remote cancel");
        check(client.disconnects >= 1, "throwing timeout listener skipped old client disconnect");
        check(XrayServiceClient.last != client, "throwing timeout listener skipped client replacement");
    }

    private static void throwingResultListenerStillReplacesOldClient() {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {
            throw new IllegalStateException("synthetic listener failure");
        });
        controller.test("trojan://synthetic@example.invalid:443", false);
        XrayServiceClient client = XrayServiceClient.last;
        XrayServiceClient.Request request = client.latest();
        controller.onResult(new XrayResult(
                request.operationId,
                request.operation,
                true,
                0,
                12L,
                ""));
        check(!controller.hasActiveOperation(), "throwing result listener left operation active");
        check(client.disconnects == 1, "throwing result listener skipped old client disconnect");
        check(XrayServiceClient.last != client, "throwing result listener skipped client replacement");
    }

    private static void resultCallbackCanStartReplacement() {
        XraySettingsController[] holder = new XraySettingsController[1];
        boolean[] retry = {true};
        holder[0] = fresh((id, op, ok, latency, message) -> {
            if (retry[0]) {
                retry[0] = false;
                holder[0].test("trojan://replacement@example.invalid:443", false);
            }
        });
        XrayServiceClient client = XrayServiceClient.last;
        holder[0].test("trojan://synthetic@example.invalid:443", false);
        XrayServiceClient.Request first = client.latest();
        holder[0].onResult(new XrayResult(first.operationId, first.operation, true, 0, 12L, ""));
        check(holder[0].hasActiveOperation(), "result callback replacement lost active owner");
        check(XrayServiceClient.last == client, "result callback replacement client was discarded");
        check(client.requests.size() == 2, "result callback replacement request was not preserved");
        check(client.disconnects == 0, "old result disconnected replacement operation");
    }

    private static void timeoutCallbackCanStartReplacement() {
        XraySettingsController[] holder = new XraySettingsController[1];
        boolean[] retry = {true};
        holder[0] = fresh((id, op, ok, latency, message) -> {
            if (retry[0]) {
                retry[0] = false;
                holder[0].test("trojan://replacement@example.invalid:443", false);
            }
        });
        XrayServiceClient client = XrayServiceClient.last;
        holder[0].test("trojan://synthetic@example.invalid:443", false);
        Handler.advance(45_000L);
        check(holder[0].hasActiveOperation(), "timeout callback replacement lost active owner");
        check(XrayServiceClient.last == client, "timeout callback replacement client was discarded");
        check(client.requests.size() == 2, "timeout callback replacement request was not preserved");
        check(client.cancellations == 0, "old timeout cancelled replacement operation");
        check(client.disconnects == 0, "old timeout disconnected replacement operation");
    }

    private static void throwingTimeoutListenerCanStillStartReplacement() {
        XraySettingsController[] holder = new XraySettingsController[1];
        boolean[] retry = {true};
        holder[0] = fresh((id, op, ok, latency, message) -> {
            if (retry[0]) {
                retry[0] = false;
                holder[0].test("trojan://replacement@example.invalid:443", false);
            }
            throw new IllegalStateException("synthetic listener failure after replacement");
        });
        XrayServiceClient client = XrayServiceClient.last;
        holder[0].test("trojan://synthetic@example.invalid:443", false);
        Handler.advance(45_000L);
        check(holder[0].hasActiveOperation(),
                "throwing timeout listener displaced its replacement owner");
        check(XrayServiceClient.last == client,
                "throwing timeout listener replaced the replacement client");
        check(client.requests.size() == 2,
                "throwing timeout listener lost replacement request");
        check(client.cancellations == 0,
                "old timeout cancelled replacement after listener threw");
        check(client.disconnects == 0,
                "old timeout disconnected replacement after listener threw");
    }

    private static void connectionFailureCallbackCanStartReplacement() {
        XraySettingsController[] holder = new XraySettingsController[1];
        boolean[] retry = {true};
        holder[0] = fresh((id, op, ok, latency, message) -> {
            if (retry[0]) {
                retry[0] = false;
                holder[0].test("trojan://replacement@example.invalid:443", false);
            }
        });
        XrayServiceClient client = XrayServiceClient.last;
        holder[0].test("trojan://synthetic@example.invalid:443", false);
        XrayServiceClient.Request first = client.latest();
        holder[0].onConnectionFailure(first.operationId, "synthetic Binder death");
        check(holder[0].hasActiveOperation(), "connection failure replacement lost active owner");
        check(XrayServiceClient.last == client, "connection failure replacement client was discarded");
        check(client.requests.size() == 2, "connection failure replacement request was not preserved");
        check(client.disconnects == 0, "old connection failure disconnected replacement operation");
    }

    private static void unsavedFragmentTestUsesExplicitSnapshot() throws Exception {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {});
        controller.test("trojan://synthetic@example.invalid:443", true, true);
        XrayServiceClient.Request test = XrayServiceClient.last.latest();
        check(test.udp && test.tlsFragment, "unsaved TEST options were not captured");
        check(!controller.isUdpEnabled() && !controller.isTlsFragmentEnabled(),
                "TEST unexpectedly persisted unsaved options");
        controller.save("trojan://synthetic@example.invalid:443", false, false);
        check(test.udp && test.tlsFragment, "save mutated an in-flight TEST snapshot");
        controller.abandon();
        controller.save("trojan://synthetic@example.invalid:443", true, true);
        controller.validate("trojan://synthetic@example.invalid:443", false, false);
        XrayServiceClient.Request validate = XrayServiceClient.last.latest();
        check(!validate.udp && !validate.tlsFragment,
                "VALIDATE read saved options instead of explicit unsaved input");
        controller.abandon();
        controller.test("trojan://synthetic@example.invalid:443", false);
        check(!XrayServiceClient.last.latest().tlsFragment,
                "legacy TEST overload unexpectedly enabled fragmentation");
    }

    private static void savedFragmentStateClearsWithNode() throws Exception {
        XraySettingsController controller = fresh((id, op, ok, latency, message) -> {});
        controller.save("trojan://synthetic@example.invalid:443", true, true);
        check(controller.isUdpEnabled() && controller.isTlsFragmentEnabled(),
                "saved node options were lost");
        controller.delete(() -> {
            check(!controller.isUdpEnabled() && !controller.isTlsFragmentEnabled(),
                    "delete callback saw stale saved options");
        });
        check(!XrayServiceClient.last.latest().tlsFragment,
                "RESET_SECURITY carried a stale fragment option");
    }

    public static void main(String[] args) throws Exception {
        unsavedFragmentTestUsesExplicitSnapshot();
        savedFragmentStateClearsWithNode();
        deleteOrderMatchesReleased();
        partialLocalDeleteStillClearsUi();
        localClearCallbackFailureStillDispatchesReset();
        localClearCancelDoesNotRedispatchReset();
        localClearAbandonDoesNotRedispatchReset();
        localClearCloseDoesNotRedispatchReset();
        partialDeleteCallbackCanCreateReplacement();
        phoneAbandonDoesNotRemoteCancel();
        timeoutNotifiesBeforeCancel();
        resultNotifiesBeforeClientReplacement();
        throwingTimeoutListenerStillCleansOldOwner();
        throwingResultListenerStillReplacesOldClient();
        resultCallbackCanStartReplacement();
        timeoutCallbackCanStartReplacement();
        throwingTimeoutListenerCanStillStartReplacement();
        connectionFailureCallbackCanStartReplacement();
        System.out.println("PASS released settings lifecycle");
    }
}
