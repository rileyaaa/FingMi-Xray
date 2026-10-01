package com.fingmi.xray.session;

import android.content.Context;
import android.os.Handler;

import com.fingmi.xray.service.XrayOperation;
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
        Trace.reset();
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

    public static void main(String[] args) throws Exception {
        deleteOrderMatchesReleased();
        phoneAbandonDoesNotRemoteCancel();
        timeoutNotifiesBeforeCancel();
        resultNotifiesBeforeClientReplacement();
        System.out.println("PASS released settings lifecycle");
    }
}
