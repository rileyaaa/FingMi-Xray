package com.fingmi.xray.session;
import android.content.Context;
import android.os.Handler;
import com.fingmi.xray.service.XrayOperation;
import java.util.*;

/** Executes the production controller against the released yz3 lifecycle contract. */
public final class SessionRaceTest {
    static XraySessionController controller;
    static void check(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    static XrayServiceClient transport() { return XrayServiceClient.last; }
    static void fresh(XraySessionListener listener) { Handler.reset(); controller=new XraySessionController(new Context(),listener); }
    static void reply(XrayServiceClient.Request request, boolean success) {
        controller.onResult(new XrayResult(request.operationId,request.operation,success,success?12345:0,0,success?"":"synthetic failure"));
    }
    static void running() { controller.start(); reply(transport().latest(),true); }

    static void oldStopFailureMatchesReleased() {
        List<Integer> states=new ArrayList<>();
        fresh((s,p,m)->states.add(s));running();controller.stop();var old=transport().latest();controller.start();var next=transport().latest();
        reply(old,false);
        check(controller.getState()==XraySessionListener.IDLE,"old STOP failure did not fail replacement START");
        check(transport().cancellations==1,"old STOP failure was not cancelled");
        check(states.get(states.size()-2)==XraySessionListener.ERROR && states.get(states.size()-1)==XraySessionListener.IDLE,"released ERROR -> IDLE sequence missing");
        reply(next,true);
        check(controller.isRunning(),"current START callback was no longer owned after old STOP failure");
    }

    static void oldStopTimeoutMatchesReleased() {
        List<Integer> states=new ArrayList<>();
        fresh((s,p,m)->states.add(s));running();controller.stop();controller.start();var next=transport().latest();
        Handler.advance(1500);
        check(controller.getState()==XraySessionListener.IDLE,"old STOP timeout did not fail replacement START");
        check(transport().cancellations==1,"old STOP timeout did not cancel old STOP");
        check(states.get(states.size()-2)==XraySessionListener.ERROR && states.get(states.size()-1)==XraySessionListener.IDLE,"cleanup timeout did not emit ERROR -> IDLE");
        reply(next,true);
        check(controller.isRunning(),"current START callback was no longer owned after cleanup timeout");
    }

    static void runningReplacementClearsOldCleanupTimeout() {
        fresh((s,p,m)->{});running();controller.stop();controller.start();var next=transport().latest();
        reply(next,true);
        Handler.advance(1500);
        check(controller.isRunning(),"running replacement was changed by stale cleanup timeout");
        check(transport().cancellations==0,"stale cleanup timeout cancelled after replacement reached RUNNING");
    }

    static void stopInsideStartingNotificationMatchesReleasedOrder() {
        fresh((s,p,m)->{if(s==XraySessionListener.STARTING)controller.stop();});
        controller.start();
        var requests=transport().requests;
        check(requests.size()==2,"released START callback ordering changed request count");
        check(requests.get(0).operation==XrayOperation.STOP && requests.get(1).operation==XrayOperation.START,"released STARTING reentry order is not STOP -> START");
        check(controller.getState()==XraySessionListener.IDLE,"released STARTING reentry state changed");
    }

    static void restartInsideStoppedNotificationMatchesReleasedOrder() {
        boolean[] restart={false};
        fresh((s,p,m)->{if(s==XraySessionListener.IDLE && restart[0]){restart[0]=false;controller.start();}});
        running();restart[0]=true;controller.stop();
        var requests=transport().requests;
        check(requests.size()==3,"released STOP callback ordering changed request count");
        check(requests.get(1).operation==XrayOperation.START && requests.get(2).operation==XrayOperation.STOP,"released IDLE reentry order is not START -> old STOP");
        check(controller.getState()==XraySessionListener.STARTING,"replacement START state was not preserved");
    }

    static void oldStartAfterStopIsIgnored() {
        fresh((s,p,m)->{});controller.start();var old=transport().latest();controller.stop();controller.start();var next=transport().latest();
        reply(old,true);
        check(controller.getState()==XraySessionListener.STARTING,"late old START became current");
        reply(next,true);
        check(controller.isRunning(),"current START lost");
    }

    static void currentTimeoutsStillCancel() {
        fresh((s,p,m)->{});controller.start();Handler.advance(30000);
        check(controller.getState()==XraySessionListener.IDLE && transport().cancellations==1,"current START timeout did not fail then cancel");
        fresh((s,p,m)->{});running();controller.stop();Handler.advance(1500);
        check(transport().cancellations==1,"current STOP cleanup did not cancel");
    }

    static void startupTimeoutNotifiesBeforeCancel() {
        int[] cancellationsAtError={-1};
        fresh((s,p,m)->{if(s==XraySessionListener.ERROR)cancellationsAtError[0]=transport().cancellations;});
        controller.start();Handler.advance(30000);
        check(cancellationsAtError[0]==0,"startup timeout cancelled before released ERROR callback");
        check(transport().cancellations==1,"startup timeout did not cancel after notification");
    }

    static void startFailureNotifiesBeforeDisconnect() {
        int[] disconnectsAtError={-1};
        fresh((s,p,m)->{if(s==XraySessionListener.ERROR)disconnectsAtError[0]=transport().disconnects;});
        controller.start();reply(transport().latest(),false);
        check(disconnectsAtError[0]==0,"START failure disconnected before released ERROR callback");
        check(transport().disconnects==1,"START failure did not disconnect after notification");
    }

    static void connectionFailureNotifiesBeforeDisconnect() {
        int[] disconnectsAtError={-1};
        fresh((s,p,m)->{if(s==XraySessionListener.ERROR)disconnectsAtError[0]=transport().disconnects;});
        controller.start();var request=transport().latest();
        controller.onConnectionFailure(request.operationId,"synthetic Binder death");
        check(disconnectsAtError[0]==0,"Binder failure disconnected before released ERROR callback");
        check(transport().disconnects==1,"Binder failure did not disconnect after notification");
    }

    static void closeMatchesReleasedOrdering() {
        boolean[] restart={false};
        fresh((s,p,m)->{if(s==XraySessionListener.IDLE && restart[0]){restart[0]=false;controller.start();}});
        running();restart[0]=true;controller.close();
        var requests=transport().requests;
        check(requests.size()==3,"released close ordering changed request count");
        check(requests.get(1).operation==XrayOperation.START && requests.get(2).operation==XrayOperation.STOP,"close did not stop before sealing disposed state");
        check(controller.getState()==XraySessionListener.STARTING,"close no longer follows released callback ordering");
    }

    public static void main(String[] args) {
        Map<String,Runnable> tests=new LinkedHashMap<>();
        tests.put("old STOP failure",SessionRaceTest::oldStopFailureMatchesReleased);
        tests.put("old STOP timeout",SessionRaceTest::oldStopTimeoutMatchesReleased);
        tests.put("running replacement cleanup",SessionRaceTest::runningReplacementClearsOldCleanupTimeout);
        tests.put("STARTING callback order",SessionRaceTest::stopInsideStartingNotificationMatchesReleasedOrder);
        tests.put("IDLE callback order",SessionRaceTest::restartInsideStoppedNotificationMatchesReleasedOrder);
        tests.put("late START",SessionRaceTest::oldStartAfterStopIsIgnored);
        tests.put("current timeouts",SessionRaceTest::currentTimeoutsStillCancel);
        tests.put("startup timeout order",SessionRaceTest::startupTimeoutNotifiesBeforeCancel);
        tests.put("START failure order",SessionRaceTest::startFailureNotifiesBeforeDisconnect);
        tests.put("Binder failure order",SessionRaceTest::connectionFailureNotifiesBeforeDisconnect);
        tests.put("close order",SessionRaceTest::closeMatchesReleasedOrdering);
        int failed=0;
        for(var entry:tests.entrySet())try{
            entry.getValue().run();
            System.out.println("PASS "+entry.getKey());
        }catch(AssertionError error){
            failed++;
            System.out.println("FAIL "+entry.getKey()+": "+error.getMessage());
        }
        if(failed!=0)throw new AssertionError(failed+" released session lifecycle tests failed");
    }
}
