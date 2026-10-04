#!/usr/bin/env python3
"""Execute the real XrayService with deterministic platform/native/storage boundaries.

Barriers test supersession and cancellation before trust persistence. This is a
host JVM check, not Android Binder/ART or native execution; native configuration
compatibility is covered separately by test-current-native-share-chain.py.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "xray/src/main/java/com/fingmi/xray"

STUBS = {
    'android/app/Service.java': r'''
package android.app;
public class Service {
    public void onCreate() {
    }
    public android.os.IBinder onBind(android.content.Intent i) {
        return null;
    }
    public void onDestroy() {
    }
}
''',
    'android/content/Intent.java': r'''
package android.content;
public class Intent {
}
''',
    'android/os/IBinder.java': r'''
package android.os;
public interface IBinder {
}
''',
    'android/os/Process.java': r'''
package android.os;
public class Process {
    public static volatile int killed;
    public static int myPid() {
        return 1;
    }
    public static void killProcess(int p) {
        killed++;
    }
}
''',
    'android/os/RemoteException.java': r'''
package android.os;
public class RemoteException extends Exception {
}
''',
    'com/fingmi/xray/config/XrayConfigFactory.java': r'''
package com.fingmi.xray.config;
import java.util.concurrent.*;
public class XrayConfigFactory {
    public static final String PROXY_TAG="proxy";
    public static volatile CountDownLatch entered, release;
    public XrayConfigFactory(com.fingmi.xray.core.LibXrayBridge b,com.fingmi.xray.security.XrayShareLinkSecurity s) {
    }
    public PreparedConfig prepare(int port,String link,boolean udp)throws Exception {
        if(link.equals("blocked")) {
            entered.countDown();
            if(!release.await(5,TimeUnit.SECONDS))throw new AssertionError("prepare barrier timed out");
        }
        return new PreparedConfig();
    }
    public static class PreparedConfig {
        public org.json.JSONObject config() {
            return new org.json.JSONObject();
        }
        public void commitTrust() {
            com.fingmi.xray.core.LibXrayBridge.trusts++;
        }
    }
}
''',
    'com/fingmi/xray/core/LibXrayBridge.java': r'''
package com.fingmi.xray.core;
public class LibXrayBridge {
    public static volatile boolean running;
    public static volatile int stopsFail, runs, trusts, tests;
    public static void reset() {
        running=false;
        stopsFail=0;
        runs=0;
        trusts=0;
        tests=0;
    }
    public int getFreePort() {
        return 12345;
    }
    public void validateConfig(org.json.JSONObject x) {
    }
    public long testLatency(org.json.JSONObject x,String tag) {
        tests++;
        return 10;
    }
    public void run(org.json.JSONObject x) {
        runs++;
        running=true;
    }
    public boolean isRunning() {
        return running;
    }
    public void stop() throws Exception {
        if(stopsFail>0) {
            stopsFail--;
            throw new Exception("synthetic stop failure");
        }
        running=false;
    }
}
''',
    'com/fingmi/xray/security/XrayCertificatePins.java': r'''
package com.fingmi.xray.security;
public class XrayCertificatePins {
    public XrayCertificatePins(Object context) {
    }
    public static void resetAll(Object context) {
    }
}
''',
    'com/fingmi/xray/security/XrayShareLinkSecurity.java': r'''
package com.fingmi.xray.security;
public class XrayShareLinkSecurity {
    public XrayShareLinkSecurity(com.fingmi.xray.core.LibXrayBridge b,XrayCertificatePins p) {
    }
}
''',
    'com/fingmi/xray/service/IXrayCallback.java': r'''
package com.fingmi.xray.service;
public interface IXrayCallback {
    void onResult(long id,int op,boolean ok,int port,long latency,String message) throws Exception;
}
''',
    'com/fingmi/xray/service/IXrayService.java': r'''
package com.fingmi.xray.service;
public interface IXrayService extends android.os.IBinder {
    void validate(long id,String link,boolean udp,IXrayCallback cb);
    void test(long id,String link,boolean udp,IXrayCallback cb);
    void start(long id,String link,boolean udp,IXrayCallback cb);
    void stop(long id,IXrayCallback cb);
    void resetSecurity(long id,IXrayCallback cb);
    void cancel(int op,long id);
    abstract class Stub implements IXrayService {
    }
}
''',
    'org/json/JSONObject.java': r'''
package org.json;
public class JSONObject {
}
''',
}

HARNESS = r'''
import com.fingmi.xray.service.*;
import com.fingmi.xray.core.LibXrayBridge;
import com.fingmi.xray.config.XrayConfigFactory;
import java.util.concurrent.*;
public class ServiceAudit {
    static int scenarios;
    static class Reply implements IXrayCallback {
        final BlockingQueue<Boolean> values=new LinkedBlockingQueue<>();
        public void onResult(long id,int op,boolean ok,int port,long latency,String message) {
            values.add(ok);
        }
        boolean await()throws Exception {
            Boolean v=values.poll(5,TimeUnit.SECONDS);
            if(v==null)throw new AssertionError("missing callback");
            return v;
        }
    }
    static void check(boolean value,String text) {
        if(!value)throw new AssertionError(text);
    }
    static XrayService fresh() {
        LibXrayBridge.reset();
        XrayService s=new XrayService();
        s.onCreate();
        return s;
    }
    static IXrayService binder(XrayService s) {
        return (IXrayService)s.onBind(new android.content.Intent());
    }
    static void pass(String text) {
        scenarios++;
        System.out.println("PASS actual Service "+text);
    }
    static void block() {
        XrayConfigFactory.entered=new CountDownLatch(1);
        XrayConfigFactory.release=new CountDownLatch(1);
    }
    static void entered()throws Exception {
        check(XrayConfigFactory.entered.await(5,TimeUnit.SECONDS),"prepare not reached");
    }
    public static void main(String[] args)throws Exception {
        XrayService s=fresh();
        IXrayService b=binder(s);
        Reply start=new Reply();
        b.start(1,"normal",false,start);
        check(start.await()&&LibXrayBridge.running&&LibXrayBridge.trusts==1,"start/trust");
        pass("successful start commits trust");
        Reply test=new Reply();
        b.test(2,"normal",false,test);
        check(!test.await()&&LibXrayBridge.tests==0&&LibXrayBridge.running,"test touched live core");
        pass("test rejects live session without disturbing core");
        Reply stop=new Reply();
        b.stop(3,stop);
        check(stop.await()&&!LibXrayBridge.running,"stop left running");
        pass("stop releases core");
        s.onDestroy();

        s=fresh();
        b=binder(s);
        block();
        Reply old=new Reply(), next=new Reply();
        b.start(10,"blocked",false,old);
        entered();
        b.start(11,"normal",false,next);
        XrayConfigFactory.release.countDown();
        check(!old.await()&&next.await()&&LibXrayBridge.runs==1&&LibXrayBridge.trusts==1,"superseded start escaped");
        pass("replacement start rejects stale preparation and trust");
        s.onDestroy();

        s=fresh();
        b=binder(s);
        block();
        old=new Reply();
        stop=new Reply();
        b.start(20,"blocked",false,old);
        entered();
        b.stop(21,stop);
        XrayConfigFactory.release.countDown();
        check(!old.await()&&stop.await()&&!LibXrayBridge.running&&LibXrayBridge.trusts==0,"stop/start supersession");
        pass("stop during preparation prevents core run and trust");
        s.onDestroy();

        s=fresh();
        b=binder(s);
        CountDownLatch callback=new CountDownLatch(1);
        b.start(30,"normal",false,(id,op,ok,port,latency,message)-> {
            callback.countDown();
            throw new Exception("synthetic dead callback");
        });
        check(callback.await(5,TimeUnit.SECONDS),"callback missing");
        Reply after=new Reply();
        b.validate(31,"normal",false,after);
        check(after.await()&&!LibXrayBridge.running,"dead callback left core live");
        pass("undeliverable successful start cleans core");
        s.onDestroy();

        s=fresh();
        b=binder(s);
        start=new Reply();
        b.start(40,"normal",false,start);
        check(start.await(),"setup start");
        LibXrayBridge.stopsFail=2;
        stop=new Reply();
        b.stop(41,stop);
        check(!stop.await()&&LibXrayBridge.running,"stop failure setup");
        after=new Reply();
        b.validate(42,"normal",false,after);
        check(!after.await(),"validation entered still running core");
        pass("failed stop remains protected by native running state");
        int kills=android.os.Process.killed;
        b.cancel(XrayOperation.STOP,41);
        check(android.os.Process.killed==kills+1,"owned cancellation did not reset process");
        pass("owned cancellation requests private process reset");
        s.onDestroy();

        s=fresh();
        b=binder(s);
        block();
        old=new Reply();
        b.validate(50,"blocked",false,old);
        entered();
        kills=android.os.Process.killed;
        b.cancel(XrayOperation.VALIDATE,50);
        XrayConfigFactory.release.countDown();
        check(!old.await()&&LibXrayBridge.trusts==0&&android.os.Process.killed==kills+1,"cancelled validation wrote trust");
        pass("cancelled validation cannot commit trust");
        s.onDestroy();
        System.out.println("PASS "+scenarios+" real Service execution scenarios; platform/native/config/pin boundaries are deterministic substitutes");
    }
}
'''

with tempfile.TemporaryDirectory(prefix="xray-service-execution-") as directory:
    work = Path(directory)
    files = []
    for name, content in STUBS.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        files.append(path)
    harness = work / "ServiceAudit.java"
    harness.write_text(HARNESS, encoding="utf-8")
    files.append(harness)
    files += [PRODUCTION / "service" / name for name in (
        "XrayService.java", "XrayGenerationGate.java", "XrayOperation.java")]
    files.append(PRODUCTION / "util/XrayErrorSanitizer.java")
    classes = work / "classes"
    classes.mkdir()
    subprocess.run([
        "java", "com.sun.tools.javac.Main", "--release", "17",
        "-d", str(classes), *map(str, files),
    ], check=True, timeout=60)
    subprocess.run([
        "java", "-cp", str(classes), "ServiceAudit",
    ], check=True, timeout=60)
