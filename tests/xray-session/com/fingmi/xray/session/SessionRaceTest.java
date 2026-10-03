package com.fingmi.xray.session;
import android.content.Context;
import android.os.Handler;
import com.fingmi.xray.config.XrayPreferences;
import com.fingmi.xray.service.XrayOperation;
import java.util.*;

/** Executes the production controller against the released yz3 contract plus documented current race fixes. */
public final class SessionRaceTest {
    static XraySessionController controller;
    static void check(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    static XrayServiceClient transport() { return XrayServiceClient.last; }
    static void fresh(XraySessionListener listener) { Handler.reset(); controller=new XraySessionController(new Context(),listener); }
    static void reply(XrayServiceClient.Request request, boolean success) {
        controller.onResult(new XrayResult(request.operationId,request.operation,success,success?12345:0,0,success?"":"synthetic failure"));
    }
    static void running() { controller.start(); reply(transport().latest(),true); }

    static void oldStopFailureTerminatesReplacementStart() {
        List<Integer> states=new ArrayList<>();
        fresh((s,p,m)->states.add(s));running();controller.stop();var old=transport().latest();controller.start();var next=transport().latest();
        reply(old,false);
        check(controller.getState()==XraySessionListener.IDLE,"old STOP failure did not fail replacement START");
        check(transport().cancellations==1,"replacement START was not cancelled after old STOP failure");
        check(transport().lastCancelledOperation==XrayOperation.START,"old STOP failure cancelled the stale STOP instead of replacement START");
        check(transport().lastCancelledOperationId==next.operationId,"old STOP failure cancelled the wrong replacement START");
        check(states.get(states.size()-2)==XraySessionListener.ERROR && states.get(states.size()-1)==XraySessionListener.IDLE,"ERROR -> IDLE sequence missing");
        reply(next,true);
        check(!controller.isRunning() && controller.getState()==XraySessionListener.IDLE,"late replacement START revived Xray after cleanup failure");
    }

    static void oldStopTimeoutTerminatesReplacementStart() {
        List<Integer> states=new ArrayList<>();
        fresh((s,p,m)->states.add(s));running();controller.stop();controller.start();var next=transport().latest();
        Handler.advance(1500);
        check(controller.getState()==XraySessionListener.IDLE,"old STOP timeout did not fail replacement START");
        check(transport().cancellations==1,"replacement START was not cancelled after old STOP timeout");
        check(transport().lastCancelledOperation==XrayOperation.START,"old STOP timeout cancelled the stale STOP instead of replacement START");
        check(transport().lastCancelledOperationId==next.operationId,"old STOP timeout cancelled the wrong replacement START");
        check(states.get(states.size()-2)==XraySessionListener.ERROR && states.get(states.size()-1)==XraySessionListener.IDLE,"cleanup timeout did not emit ERROR -> IDLE");
        reply(next,true);
        check(!controller.isRunning() && controller.getState()==XraySessionListener.IDLE,"late replacement START revived Xray after cleanup timeout");
    }

    static void runningReplacementClearsOldCleanupTimeout() {
        fresh((s,p,m)->{});running();controller.stop();controller.start();var next=transport().latest();
        reply(next,true);
        Handler.advance(1500);
        check(controller.isRunning(),"running replacement was changed by stale cleanup timeout");
        check(transport().cancellations==0,"stale cleanup timeout cancelled after replacement reached RUNNING");
    }

    static void cleanupFailureAllowsNewerReentrantRetry() {
        boolean[] retry={false};
        fresh((s,p,m)->{
            if(s==XraySessionListener.IDLE && retry[0]){
                retry[0]=false;
                controller.start();
            }
        });
        running();
        controller.stop();
        controller.start();
        var failedReplacement=transport().latest();
        retry[0]=true;
        Handler.advance(1500);
        var newest=transport().latest();
        check(newest.operationId!=failedReplacement.operationId,"cleanup failure did not create a newer reentrant START");
        check(controller.getState()==XraySessionListener.STARTING,"newer reentrant START was not preserved");
        check(transport().cancellations==0,"cleanup failure disconnected the newer reentrant START");
        reply(failedReplacement,true);
        check(controller.getState()==XraySessionListener.STARTING,"late failed replacement START displaced newer retry");
        reply(newest,true);
        check(controller.isRunning(),"newer reentrant retry could not reach RUNNING");
    }

    static void stopInsideStartingNotificationKeepsLatestIntent() {
        fresh((s,p,m)->{if(s==XraySessionListener.STARTING)controller.stop();});
        controller.start();
        var requests=transport().requests;
        check(requests.size()==2,"STARTING reentry changed request count");
        check(requests.get(0).operation==XrayOperation.START && requests.get(1).operation==XrayOperation.STOP,
                "STARTING reentry must submit START before listener STOP");
        check(controller.getState()==XraySessionListener.IDLE,"STARTING reentry state changed");
    }

    static void restartInsideStoppedNotificationKeepsLatestIntent() {
        boolean[] restart={false};
        fresh((s,p,m)->{if(s==XraySessionListener.IDLE && restart[0]){restart[0]=false;controller.start();}});
        running();restart[0]=true;controller.stop();
        var requests=transport().requests;
        check(requests.size()==3,"IDLE reentry changed request count");
        check(requests.get(1).operation==XrayOperation.STOP && requests.get(2).operation==XrayOperation.START,
                "IDLE reentry must submit old STOP before replacement START");
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

    static void startFailureAllowsReentrantRetry() {
        boolean[] retry={true};
        List<Integer> states=new ArrayList<>();
        fresh((s,p,m)->{
            states.add(s);
            if(s==XraySessionListener.ERROR && retry[0]){
                retry[0]=false;
                controller.start();
            }
        });
        controller.start();
        var failed=transport().latest();
        reply(failed,false);
        var newest=transport().latest();
        check(newest.operationId!=failed.operationId,"START failure did not create a newer reentrant retry");
        check(controller.getState()==XraySessionListener.STARTING,"START failure disconnected the newer retry");
        check(transport().disconnects==0,"START failure disconnected after a newer owner appeared");
        check(states.get(states.size()-1)==XraySessionListener.STARTING,
                "START failure published stale IDLE after reentrant START");
        reply(newest,true);
        check(controller.isRunning(),"reentrant retry after START failure could not reach RUNNING");
    }

    static void startupTimeoutAllowsReentrantRetry() {
        boolean[] retry={true};
        fresh((s,p,m)->{
            if(s==XraySessionListener.ERROR && retry[0]){
                retry[0]=false;
                controller.start();
            }
        });
        controller.start();
        var timedOut=transport().latest();
        Handler.advance(30000);
        var newest=transport().latest();
        check(newest.operationId!=timedOut.operationId,"startup timeout did not create a newer retry");
        check(controller.getState()==XraySessionListener.STARTING,"startup timeout displaced the newer retry");
        check(transport().cancellations==0,"startup timeout cancelled/disconnected a newer owner");
        reply(newest,true);
        check(controller.isRunning(),"reentrant retry after startup timeout could not reach RUNNING");
    }

    static void connectionFailureAllowsReentrantRetry() {
        boolean[] retry={true};
        fresh((s,p,m)->{
            if(s==XraySessionListener.ERROR && retry[0]){
                retry[0]=false;
                controller.start();
            }
        });
        controller.start();
        var failed=transport().latest();
        controller.onConnectionFailure(failed.operationId,"synthetic Binder death");
        var newest=transport().latest();
        check(newest.operationId!=failed.operationId,"Binder failure did not create a newer retry");
        check(controller.getState()==XraySessionListener.STARTING,"Binder failure displaced the newer retry");
        check(transport().disconnects==0,"Binder failure disconnected a newer owner");
        reply(newest,true);
        check(controller.isRunning(),"reentrant retry after Binder failure could not reach RUNNING");
    }

    static void stopFailureAllowsReentrantRetry() {
        boolean[] retry={false};
        fresh((s,p,m)->{
            if(s==XraySessionListener.IDLE && retry[0]){
                retry[0]=false;
                controller.start();
            }
        });
        running();
        controller.stop();
        var failed=transport().latest();
        retry[0]=true;
        reply(failed,false);
        var newest=transport().latest();
        check(newest.operationId!=failed.operationId,"STOP failure did not create a newer retry");
        check(controller.getState()==XraySessionListener.STARTING,"STOP failure displaced the newer retry");
        check(transport().cancellations==0,"STOP failure cancelled/disconnected a newer owner");
        reply(newest,true);
        check(controller.isRunning(),"reentrant retry after STOP failure could not reach RUNNING");
    }

    static void preferenceLinkageFailsWithoutDispatch() {
        List<Integer> states=new ArrayList<>();
        fresh((s,p,m)->states.add(s));
        XrayPreferences.throwShareLinkLinkage=true;
        try {
            controller.start();
        } finally {
            XrayPreferences.throwShareLinkLinkage=false;
        }
        check(controller.getState()==XraySessionListener.IDLE,
                "preference LinkageError did not return controller to IDLE");
        check(states.equals(List.of(XraySessionListener.ERROR, XraySessionListener.IDLE)),
                "preference LinkageError did not emit ERROR -> IDLE");
        check(transport().requests.isEmpty(),
                "preference LinkageError dispatched a Binder START");
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
        check(requests.size()==2,"close allowed a reentrant START after disposal");
        check(requests.get(1).operation==XrayOperation.STOP,"close did not submit STOP");
        check(controller.getState()==XraySessionListener.IDLE,"close did not finish in IDLE");
    }

    public static void main(String[] args) {
        Map<String,Runnable> tests=new LinkedHashMap<>();
        tests.put("old STOP failure",SessionRaceTest::oldStopFailureTerminatesReplacementStart);
        tests.put("old STOP timeout",SessionRaceTest::oldStopTimeoutTerminatesReplacementStart);
        tests.put("running replacement cleanup",SessionRaceTest::runningReplacementClearsOldCleanupTimeout);
        tests.put("cleanup failure reentrant retry",SessionRaceTest::cleanupFailureAllowsNewerReentrantRetry);
        tests.put("STARTING callback order",SessionRaceTest::stopInsideStartingNotificationKeepsLatestIntent);
        tests.put("IDLE callback order",SessionRaceTest::restartInsideStoppedNotificationKeepsLatestIntent);
        tests.put("late START",SessionRaceTest::oldStartAfterStopIsIgnored);
        tests.put("current timeouts",SessionRaceTest::currentTimeoutsStillCancel);
        tests.put("startup timeout order",SessionRaceTest::startupTimeoutNotifiesBeforeCancel);
        tests.put("START failure reentrant retry",SessionRaceTest::startFailureAllowsReentrantRetry);
        tests.put("startup timeout reentrant retry",SessionRaceTest::startupTimeoutAllowsReentrantRetry);
        tests.put("Binder failure reentrant retry",SessionRaceTest::connectionFailureAllowsReentrantRetry);
        tests.put("STOP failure reentrant retry",SessionRaceTest::stopFailureAllowsReentrantRetry);
        tests.put("preference LinkageError",SessionRaceTest::preferenceLinkageFailsWithoutDispatch);
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
        if(failed!=0)throw new AssertionError(failed+" Xray session lifecycle tests failed");
    }
}
