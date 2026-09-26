package com.fingmi.xray.session;
import android.content.Context;
import android.os.Handler;
import com.fingmi.xray.service.XrayOperation;
import java.util.*;

/** Executes the actual production controller with a virtual clock and Binder boundary double. */
public final class SessionRaceTest {
    static XraySessionController controller;
    static void check(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    static XrayServiceClient transport() { return XrayServiceClient.last; }
    static void fresh(XraySessionListener listener) { Handler.reset(); controller=new XraySessionController(new Context(),listener); }
    static void reply(XrayServiceClient.Request request, boolean success) {
        controller.onResult(new XrayResult(request.operationId,request.operation,success,success?12345:0,0,success?"":"synthetic failure"));
    }
    static void running() { controller.start(); reply(transport().latest(),true); }
    static void oldStopFailure() {
        fresh((s,p,m)->{});running();controller.stop();var old=transport().latest();controller.start();var next=transport().latest();
        reply(old,false);
        check(controller.getState()==XraySessionListener.STARTING,"old STOP failure changed new START");
        check(transport().cancellations==0,"old STOP disconnected new START");
        reply(next,true);check(controller.isRunning(),"new START did not survive");
    }
    static void oldStopTimeout() {
        fresh((s,p,m)->{});running();controller.stop();controller.start();var next=transport().latest();
        Handler.advance(1500);
        check(controller.getState()==XraySessionListener.STARTING,"old STOP timeout changed new START");
        check(transport().cancellations==0,"old STOP timeout cancelled new START");
        reply(next,true);check(controller.isRunning(),"new START failed after old timeout");
    }
    static void cancelInsideStartingNotification() {
        fresh((s,p,m)->{if(s==XraySessionListener.STARTING)controller.stop();});controller.start();
        check(transport().requests.size()==1 && transport().latest().operation==XrayOperation.STOP,"cancelled START dispatched after STOP");
    }
    static void restartInsideStoppedNotification() {
        boolean[] restart={false};fresh((s,p,m)->{if(s==XraySessionListener.IDLE && restart[0]){restart[0]=false;controller.start();}});
        running();restart[0]=true;controller.stop();
        var requests=transport().requests;
        check(requests.size()==3 && requests.get(1).operation==XrayOperation.STOP && requests.get(2).operation==XrayOperation.START,"old STOP dispatched after replacement START");
    }
    static void oldStartAfterStopIsIgnored() {
        fresh((s,p,m)->{});controller.start();var old=transport().latest();controller.stop();controller.start();var next=transport().latest();
        reply(old,true);check(controller.getState()==XraySessionListener.STARTING,"late old START became current");
        reply(next,true);check(controller.isRunning(),"current START lost");
        controller.close();reply(next,true);check(!controller.isRunning(),"closed controller revived");
    }
    static void currentTimeoutStillCancels() {
        fresh((s,p,m)->{});controller.start();Handler.advance(30000);
        check(!controller.isRunning() && transport().cancellations==1,"current START timeout did not cancel");
        fresh((s,p,m)->{});running();controller.stop();Handler.advance(1500);
        check(transport().cancellations==1,"current STOP cleanup did not cancel");
    }
    static void failureCleanupPrecedesReentrantRetry() {
        for(int kind=0;kind<3;kind++) {
            List<Integer> states=new ArrayList<>();int[] cleanupAtRetry={-1};
            fresh((state,port,message)->{states.add(state);if(state==XraySessionListener.ERROR){cleanupAtRetry[0]=transport().disconnects;controller.start();}});
            controller.start();var old=transport().latest();
            if(kind==0)reply(old,false);
            else if(kind==1)Handler.advance(30000);
            else controller.onConnectionFailure(old.operationId,"synthetic Binder death");
            check(cleanupAtRetry[0]>0,"failure notified before cleaning old transport");
            check(transport().disconnects==cleanupAtRetry[0],"old failure disconnected reentrant retry");
            check(controller.getState()==XraySessionListener.STARTING && states.get(states.size()-1)==XraySessionListener.STARTING,"stale IDLE notification followed reentrant retry");
        }
    }
    static void stoppedFailureCleanupPrecedesReentrantRetry() {
        boolean[] retry={false};int[] cleanupAtRetry={-1};
        fresh((state,port,message)->{if(state==XraySessionListener.IDLE && retry[0]){retry[0]=false;cleanupAtRetry[0]=transport().disconnects;controller.start();}});
        running();controller.stop();var old=transport().latest();retry[0]=true;reply(old,false);
        check(cleanupAtRetry[0]>0 && transport().disconnects==cleanupAtRetry[0],"old STOP failure cleaned new transport");
        check(controller.getState()==XraySessionListener.STARTING,"retry did not remain STARTING");
    }
    static void closeCannotBeResurrectedByIdleListener() {
        fresh((state,port,message)->{if(state==XraySessionListener.IDLE)controller.start();});
        running();controller.close();
        check(transport().requests.size()==2 && transport().latest().operation==XrayOperation.STOP,"close allowed a replacement START");
        check(!controller.isRunning(),"close retained running state");
    }
    public static void main(String[] args) {
        Map<String,Runnable> tests=new LinkedHashMap<>();
        tests.put("old STOP failure",SessionRaceTest::oldStopFailure);
        tests.put("old STOP timeout",SessionRaceTest::oldStopTimeout);
        tests.put("reentrant START cancellation",SessionRaceTest::cancelInsideStartingNotification);
        tests.put("reentrant replacement START",SessionRaceTest::restartInsideStoppedNotification);
        tests.put("late START/release",SessionRaceTest::oldStartAfterStopIsIgnored);
        tests.put("current timeout",SessionRaceTest::currentTimeoutStillCancels);
        tests.put("failure/reentrant retry",SessionRaceTest::failureCleanupPrecedesReentrantRetry);
        tests.put("STOP failure/reentrant retry",SessionRaceTest::stoppedFailureCleanupPrecedesReentrantRetry);
        tests.put("close reentrancy",SessionRaceTest::closeCannotBeResurrectedByIdleListener);
        int failed=0;for(var entry:tests.entrySet())try{entry.getValue().run();System.out.println("PASS "+entry.getKey());}catch(AssertionError error){failed++;System.out.println("FAIL "+entry.getKey()+": "+error.getMessage());}
        if(failed!=0)throw new AssertionError(failed+" session races failed");
    }
}
