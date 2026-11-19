#!/usr/bin/env python3
"""Compile real Xray playback ownership classes and test synchronous listener reentry.

Only Android, OkHttp and the Binder controller boundary are synthetic; the
production session/identity/listener Java sources are compiled without edits.
The fake controller deliberately dispatches synchronously, as real main-thread
listener callbacks may reenter before an outer callback returns.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "xray/src/main/java/com/fingmi/xray/session"
STUBS = {
    "android/content/Context.java": "package android.content; public class Context {}",
    "android/os/Looper.java": """package android.os;
public class Looper {
    private static final Looper MAIN = new Looper();
    public static Looper myLooper(){return MAIN;}
    public static Looper getMainLooper(){return MAIN;}
}""",
    "okhttp3/OkHttpClient.java": "package okhttp3; public class OkHttpClient {}",
    "com/fingmi/xray/network/XrayHttpClient.java": """package com.fingmi.xray.network;
import okhttp3.OkHttpClient;
public final class XrayHttpClient implements AutoCloseable {
    public boolean closed;
    public final int port;
    public XrayHttpClient(int port, OkHttpClient base){this.port=port;}
    public OkHttpClient client(){return new OkHttpClient();}
    public void close(){closed=true;}
}""",
    "com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java":
        "package com.fingmi.xray.network; public class PublicPlaybackDestinationInterceptor {}",
    "com/fingmi/xray/util/XrayErrorSanitizer.java": """package com.fingmi.xray.util;
public final class XrayErrorSanitizer {
    public static String sanitize(Throwable e){return "synthetic-failure";}
}""",
    "com/fingmi/xray/session/XrayPlaybackAddress.java": """package com.fingmi.xray.session;
public final class XrayPlaybackAddress {
    public static boolean supports(String url){return url!=null && url.startsWith("https://");}
    public static boolean supportsDirectLiveSource(String url){return supports(url);}
}""",
    "com/fingmi/xray/session/XraySessionController.java": """package com.fingmi.xray.session;
import android.content.Context;
public final class XraySessionController {
    private final XraySessionListener listener;
    private int state=XraySessionListener.IDLE;
    private int attempts;
    public XraySessionController(Context context, XraySessionListener listener){this.listener=listener;}
    public boolean isRunning(){return state==XraySessionListener.RUNNING;}
    public int getState(){return state;}
    public void start(){state=XraySessionListener.RUNNING;
        listener.onXrayStateChanged(state, 12346 + attempts++, "running");}
    public void stop(){if(state==XraySessionListener.IDLE)return;
        state=XraySessionListener.IDLE; listener.onXrayStateChanged(state,0,"");}
    // Mirror the real controller's ERROR callback after resetting its state.
    public void failForTest(){state=XraySessionListener.IDLE;
        listener.onXrayStateChanged(XraySessionListener.ERROR,0,"failed");}
    // Exercise stop()'s defensive cleanup when a controller is already IDLE.
    public void silentIdleForTest(){state=XraySessionListener.IDLE;}
    public void close(){stop();}
}""",
}
HARNESS = r"""
import android.content.Context;
import okhttp3.OkHttpClient;
import com.fingmi.xray.network.XrayHttpClient;
import com.fingmi.xray.session.XrayPlaybackSession;
import com.fingmi.xray.session.XraySessionListener;
import com.fingmi.xray.session.XraySessionController;
import java.util.ArrayList;
import java.util.List;

public final class SessionReentryTest {
    private static int passed;
    private static void check(boolean v,String label) {
        if (!v) throw new AssertionError(label);
    }
    private static final class Scenario implements XrayPlaybackSession.Listener {
        final List<Integer> states=new ArrayList<>();
        final List<XrayHttpClient> installations=new ArrayList<>();
        XrayPlaybackSession session;
        boolean retryOnAttach, retryOnDetach, throwAfterRetry;
        boolean throwOnce, retryOnRollback, retryOnError;
        boolean retryThenThrowOnDetach, retryThenThrowOnError;
        boolean throwOnceOnDetach, throwOnceOnError;
        XrayHttpClient attached;
        int rollbacks;

        Scenario open() {
            session=new XrayPlaybackSession(new Context(),new OkHttpClient(),this);
            session.begin("vod:synthetic");
            session.mediaUrlChanged("https://media.example/video");
            check(session.enable(),"enable rejected");
            return this;
        }
        void retry() {
            session.stop(false);
            check(session.enable(),"reentrant retry refused");
        }
        @Override public void onProxyChanged(XrayHttpClient client,boolean preserve) {
            if(client==null) {
                attached=null;
                if(retryThenThrowOnDetach){retryThenThrowOnDetach=false;
                    check(session.enable(),"IDLE detach retry rejected");
                    throw new IllegalStateException("old IDLE detach failed after retry");}
                if(throwOnceOnDetach){throwOnceOnDetach=false;
                    throw new IllegalStateException("ordinary detach failure");}
                if(retryOnDetach){retryOnDetach=false;retry();}
                return;
            }
            attached=client;
            installations.add(client);
            if(retryOnAttach){retryOnAttach=false;retry();return;}
            if(throwAfterRetry){throwAfterRetry=false;retry();
                throw new IllegalStateException("old callback failed after retry");}
            if(throwOnce){throwOnce=false;
                throw new IllegalStateException("synthetic first attach failure");}
        }
        @Override public void onProxyError() {
            rollbacks++;
            if(retryThenThrowOnError){retryThenThrowOnError=false;
                attached=null;
                check(session.enable(),"ERROR detach retry rejected");
                throw new IllegalStateException("old ERROR detach failed after retry");}
            if(throwOnceOnError){throwOnceOnError=false;
                attached=null;
                throw new IllegalStateException("ordinary ERROR detach failure");}
            if(retryOnRollback){retryOnRollback=false;retry();return;}
            onProxyChanged(null,false);
        }
        @Override public void onStateChanged(int state,String message) {
            states.add(state);
            if(state==XraySessionListener.ERROR && retryOnError){
                retryOnError=false;retry();
            }
        }
    }
    static void sameStateRetry() {
        Scenario a=new Scenario(); a.retryOnAttach=true; a.open();
        check(a.installations.size()==2,"reentrant retry did not install both endpoints");
        check(a.installations.get(0).closed && !a.installations.get(1).closed,
            "reentrant retry leaked old resource");
        check(a.states.equals(List.of(1,3)),"obsolete RUNNING repeated: "+a.states);
        a.session.close();passed++;
    }
    static void detachRetry() {
        Scenario a=new Scenario().open();
        XrayHttpClient first=a.session.resources();
        a.states.clear();a.retryOnDetach=true;
        a.session.onXrayStateChanged(XraySessionListener.RUNNING,9999,"stale");
        check(first.closed,"previous proxy not closed");
        check(a.installations.size()==2 && a.installations.get(1).port==12347,
            "stale RUNNING installed obsolete endpoint");
        check(a.session.resources()==a.installations.get(1),"new endpoint overwritten");
        check(a.states.equals(List.of(1,3)),"detach retry state changed: "+a.states);
        a.session.close();passed++;
    }
    static void throwAfterRetry() {
        Scenario a=new Scenario();a.throwAfterRetry=true;a.open();
        check(a.session.state()==XraySessionListener.RUNNING,"old exception stopped retry");
        check(a.installations.size()==2 && a.installations.get(0).closed,
            "old exception leaked resources");
        check(a.session.resources()==a.installations.get(1)
                && !a.installations.get(1).closed,"old exception removed new resource");
        check(a.states.equals(List.of(1,3)),"old exception published stale ERROR: "+a.states);
        a.session.close();passed++;
    }
    static void rollbackRetry() {
        Scenario a=new Scenario();a.throwOnce=true;a.retryOnRollback=true;a.open();
        check(a.session.state()==XraySessionListener.RUNNING,"rollback stopped retry");
        check(a.installations.size()==2 && a.installations.get(0).closed,
            "rollback resource cleanup changed");
        check(a.session.resources()==a.installations.get(1)
                && !a.installations.get(1).closed,"rollback destroyed new endpoint");
        check(a.states.equals(List.of(1,3)),"old rollback sent ERROR/IDLE: "+a.states);
        a.session.close();passed++;
    }
    static void errorListenerRetry() {
        Scenario a=new Scenario();a.throwOnce=true;a.retryOnError=true;a.open();
        check(a.session.state()==XraySessionListener.RUNNING,"old STOP stopped ERROR retry");
        check(a.installations.size()==2 && a.installations.get(0).closed,
            "ERROR listener resource cleanup changed");
        check(a.session.resources()==a.installations.get(1)
                && !a.installations.get(1).closed,"ERROR listener new endpoint closed");
        check(a.states.equals(List.of(4,1,3)),"ERROR listener stale trailing IDLE: "+a.states);
        a.session.close();passed++;
    }
    static void normalFailureStillStops() {
        Scenario a=new Scenario();a.throwOnce=true;a.open();
        check(a.session.state()==XraySessionListener.IDLE && a.session.resources()==null,
            "unrecovered attach failure did not stop");
        check(a.installations.size()==1 && a.installations.get(0).closed,
            "ordinary failure leaked failed proxy");
        check(a.states.equals(List.of(4,1)),"ordinary ERROR -> IDLE changed: "+a.states);
        a.session.close();passed++;
    }
    static XraySessionController fakeController(Scenario a) {
        try {
            var field=XrayPlaybackSession.class.getDeclaredField("service");
            field.setAccessible(true);
            return (XraySessionController)field.get(a.session);
        } catch (ReflectiveOperationException error) {
            throw new AssertionError("Cannot access fixture controller",error);
        }
    }
    static void fakeControllerError(Scenario a) {
        fakeController(a).failForTest();
    }
    static void idleDetachErrorAfterRetry() {
        Scenario a=new Scenario().open();
        XrayHttpClient old=a.attached;
        a.states.clear();a.retryThenThrowOnDetach=true;
        a.session.stop(false);
        check(a.session.state()==XraySessionListener.RUNNING,"IDLE detach stopped retry");
        check(old.closed && a.installations.size()==2,"IDLE detach old client leak");
        check(a.attached==a.session.resources() && a.attached==a.installations.get(1),
            "stale IDLE detach rolled back replacement proxy");
        check(a.rollbacks==0 && a.states.equals(List.of(3)),
            "obsolete IDLE rollback was published: "+a.states);
        a.session.close();passed++;
    }
    static void errorDetachErrorAfterRetry() {
        Scenario a=new Scenario().open();
        XrayHttpClient old=a.attached;
        a.states.clear();a.retryThenThrowOnError=true;
        fakeControllerError(a);
        check(a.session.state()==XraySessionListener.RUNNING,"ERROR detach stopped retry");
        check(old.closed && a.installations.size()==2,"ERROR detach old client leak");
        check(a.attached==a.session.resources() && a.attached==a.installations.get(1),
            "stale ERROR detach rolled back replacement proxy");
        check(a.rollbacks==1 && a.states.equals(List.of(3)),
            "obsolete ERROR rollback was published: "+a.states);
        a.session.close();passed++;
    }
    static void idleStopFallbackFailureAfterRetry() {
        Scenario a=new Scenario().open();
        XrayHttpClient old=a.attached;
        a.states.clear();a.retryThenThrowOnDetach=true;
        // stop() can also be asked to clean up an orphaned proxy when the
        // controller is already IDLE. The fallback must be reentry-safe too.
        fakeController(a).silentIdleForTest();
        a.session.stop(false);
        check(a.session.state()==XraySessionListener.RUNNING,"fallback stopped retry");
        check(old.closed && a.installations.size()==2,"fallback old client leak");
        check(a.attached==a.session.resources() && a.attached==a.installations.get(1),
            "stale stop fallback rolled back replacement proxy");
        check(a.rollbacks==0 && a.states.equals(List.of(3)),
            "stale stop fallback rollback was published: "+a.states);
        a.session.close();passed++;
    }
    static void ordinaryIdleDetachFailureRetries() {
        Scenario a=new Scenario().open();
        XrayHttpClient old=a.attached;
        a.states.clear();a.throwOnceOnDetach=true;
        a.session.stop(false);
        check(old.closed && a.session.resources()==null && a.attached==null,
            "ordinary IDLE detach left a proxy active");
        check(a.rollbacks==1 && a.states.equals(List.of(1)),
            "ordinary IDLE rollback was omitted: "+a.states);
        a.session.close();passed++;
    }
    static void ordinaryErrorDetachFailureRetries() {
        Scenario a=new Scenario().open();
        XrayHttpClient old=a.attached;
        a.states.clear();a.throwOnceOnError=true;
        fakeControllerError(a);
        check(old.closed && a.session.resources()==null && a.attached==null,
            "ordinary ERROR detach left a proxy active");
        check(a.rollbacks==2 && a.states.equals(List.of(4)),
            "ordinary ERROR rollback was omitted: "+a.states);
        a.session.close();passed++;
    }
    public static void main(String[] args) {
        sameStateRetry();detachRetry();throwAfterRetry();rollbackRetry();
        errorListenerRetry();normalFailureStillStops();
        idleDetachErrorAfterRetry();errorDetachErrorAfterRetry();
        idleStopFallbackFailureAfterRetry();
        ordinaryIdleDetachFailureRetries();ordinaryErrorDetachFailureRetries();
        System.out.println("PASS real XrayPlaybackSession synchronous reentry: "+passed+" scenarios");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-playback-reentry-") as directory:
    work = Path(directory)
    sources = []
    for name, value in {**STUBS, "SessionReentryTest.java": HARNESS}.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value.strip() + "\n", encoding="utf-8")
        sources.append(path)
    sources.extend(PRODUCTION / name for name in (
        "XrayPlaybackSession.java", "PlaybackIdentityGate.java", "XraySessionListener.java"
    ))
    classes = work / "classes"
    subprocess.run(["java", "com.sun.tools.javac.Main", "--release", "17",
                    "-d", str(classes), *map(str, sources)], check=True, timeout=60)
    subprocess.run(["java", "-cp", str(classes), "SessionReentryTest"],
                   check=True, timeout=60)
