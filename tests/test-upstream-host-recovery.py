#!/usr/bin/env python3
"""JDK host-boundary regression for the reviewed 5.9.0 recovery port.

Compile the actual candidate lifecycle/coordinator/adapter and Leanback bridge.
Android, Spider cleanup and HTTP/DNS/Glide resource operations are deterministic
boundary doubles; no Android Activity, real network or player is executed.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

P = "app/src/main/java/com/fingmi/integration/recovery/"
T = "tv-recovery/src/main/java/com/fingmi/tvrecovery/"
D = "app/src/leanback/java/com/fingmi/integration/recovery/"
SOURCES = {
    T + "TvNetworkLifecycle.java": "97a04e5cad533cd5d2b94a4a64c5fdaf500ada1a",
    T + "NetworkRecoveryCoordinator.java": "657dd853d5cb93e317b3ab5d81c988c55dfc09b2",
    P + "FongMiNetworkRecovery.java": "6b4495c6fdc7fab013cc2f38ab37a7937dfc6a72",
    D + "TvDlnaLifecycle.java": "a0bc77a9ef7eed0453f924b98616c78ec6e2b20c",
}
STUBS = {
    "android/Manifest.java": 'package android; public class Manifest { public static class permission { public static final String ACCESS_LOCAL_NETWORK="local"; } }',
    "android/os/Build.java": 'package android.os; public class Build { public static class VERSION { public static int SDK_INT=37; } }',
    "android/content/pm/PackageManager.java": 'package android.content.pm; public class PackageManager { public static final int PERMISSION_GRANTED=0; }',
    "androidx/annotation/NonNull.java": 'package androidx.annotation; public @interface NonNull {}',
    "androidx/annotation/Nullable.java": 'package androidx.annotation; public @interface Nullable {}',
    "android/os/Bundle.java": 'package android.os; public class Bundle {}',
    "android/content/Context.java": '''package android.content;
        public class Context {
            public int permission=-1; public static final String CONNECTIVITY_SERVICE="connectivity";
            public final android.net.ConnectivityManager network=new android.net.ConnectivityManager();
            public int checkSelfPermission(String name){if(!name.equals("local"))throw new AssertionError(name);return permission;}
            public Object getSystemService(String name){return network;}
        }''',
    "android/content/Intent.java": '''package android.content;
        public class Intent {
            public static final String ACTION_SCREEN_OFF="off", ACTION_SCREEN_ON="on";
            private final String action; public Intent(String action){this.action=action;}
            public String getAction(){return action;}
        }''',
    "android/content/IntentFilter.java": 'package android.content; public class IntentFilter { public void addAction(String s){} }',
    "android/content/BroadcastReceiver.java": 'package android.content; public abstract class BroadcastReceiver { public abstract void onReceive(Context c,Intent i); }',
    "android/app/Activity.java": 'package android.app; public class Activity { public boolean changing; public boolean isChangingConfigurations(){return changing;} }',
    "android/app/Application.java": '''package android.app;
        import android.content.*; import android.os.Bundle;
        public class Application extends Context {
            public ActivityLifecycleCallbacks lifecycle; public BroadcastReceiver receiver;
            public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks value){lifecycle=value;}
            public Intent registerReceiver(BroadcastReceiver value,IntentFilter filter){receiver=value;return null;}
            public interface ActivityLifecycleCallbacks {
                void onActivityCreated(Activity a,Bundle b);void onActivityStarted(Activity a);
                void onActivityResumed(Activity a);void onActivityPaused(Activity a);
                void onActivityStopped(Activity a);void onActivitySaveInstanceState(Activity a,Bundle b);
                void onActivityDestroyed(Activity a);
            }
        }''',
    "android/net/Network.java": 'package android.net; public class Network {}',
    "android/net/NetworkCapabilities.java": 'package android.net; public class NetworkCapabilities { public static final int NET_CAPABILITY_INTERNET=12; public boolean ready; public boolean hasCapability(int v){return ready;} }',
    "android/net/ConnectivityManager.java": '''package android.net;
        public class ConnectivityManager {
            public final NetworkCapabilities capabilities=new NetworkCapabilities();
            public Network getActiveNetwork(){return new Network();}
            public NetworkCapabilities getNetworkCapabilities(Network n){return capabilities;}
        }''',
    "com/fongmi/android/tv/App.java": '''package com.fongmi.android.tv;
        import java.util.*;
        public class App {
            public static final List<String> events=new ArrayList<>();
            public static final Queue<Runnable> queue=new ArrayDeque<>();
            public static void post(Runnable r,long d){queue.add(r);}
            public static void removeCallbacks(Runnable r){queue.removeIf(x->x==r);}
            public static void tick(){queue.remove().run();}
        }''',
    "com/fongmi/android/tv/api/loader/BaseLoader.java": '''package com.fongmi.android.tv.api.loader;
        public class BaseLoader {
            private static final BaseLoader INSTANCE=new BaseLoader();public Runnable after;
            public static BaseLoader get(){return INSTANCE;}
            public void clear(Runnable r){com.fongmi.android.tv.App.events.add("spider");after=r;}
        }''',
    "com/fongmi/android/tv/utils/ImgUtil.java": 'package com.fongmi.android.tv.utils; public class ImgUtil { public static void resetNetworkFailures(){com.fongmi.android.tv.App.events.add("images");} }',
    "com/github/catvod/net/OkHttp.java": 'package com.github.catvod.net; public class OkHttp { public static void resetApiNetworkForResume(){com.fongmi.android.tv.App.events.add("api-dns");} }',
    "com/fongmi/android/tv/service/DLNARendererService.java": '''package com.fongmi.android.tv.service;
        public class DLNARendererService {
            public static int starts,stops;
            public static void start(android.content.Context c){starts++;}
            public static void stop(android.content.Context c){stops++;}
        }''',
    "HostRecoveryTest.java": '''import android.app.*;import android.content.*;import android.os.Build;
        import java.util.*;
        import com.fingmi.integration.recovery.FongMiNetworkRecovery;
        import com.fingmi.tvrecovery.TvNetworkLifecycle;
        import com.fongmi.android.tv.App;
        import com.fongmi.android.tv.api.loader.BaseLoader;
        import com.fongmi.android.tv.service.DLNARendererService;
        public class HostRecoveryTest {
            static int checks,refreshes;
            static boolean homeReady=true;
            static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
            static void screen(Application app,String s){app.receiver.onReceive(app,new Intent(s));}
            static FongMiNetworkRecovery owner(Application app){return new FongMiNetworkRecovery(app,()->App.events.add("cancel"),()->App.events.add("progress"),()->homeReady,()->refreshes++);}
            static void complete(Application app){BaseLoader.get().after.run();app.network.capabilities.ready=false;App.tick();
                int count=refreshes;app.network.capabilities.ready=true;App.tick();check(refreshes==count,"one ready sample refreshed");App.tick();}
            public static void main(String[] args){
                Application app=new Application();Activity home=new Activity(), video=new Activity(), cold=new Activity();
                FongMiNetworkRecovery r=owner(app);
                r.onLocalNetworkPermissionGranted();check(DLNARendererService.starts==0,"renderer before foreground");
                app.lifecycle.onActivityStarted(home);app.lifecycle.onActivityResumed(home);r.check();
                check(DLNARendererService.starts==0,"API37 denied permission ignored");check(App.events.isEmpty(),"cold start recovered");
                app.permission=0;r.onLocalNetworkPermissionGranted();r.onLocalNetworkPermissionGranted();r.check();
                check(DLNARendererService.starts==1,"permission grant must start exactly once");
                app.lifecycle.onActivityStopped(cold);app.lifecycle.onActivityDestroyed(cold);
                app.lifecycle.onActivityStarted(video);app.lifecycle.onActivityPaused(home);app.lifecycle.onActivityResumed(video);app.lifecycle.onActivityStopped(home);
                app.lifecycle.onActivityStarted(home);app.lifecycle.onActivityResumed(home);app.lifecycle.onActivityStopped(video);r.check();
                check(TvNetworkLifecycle.generation()==0&&DLNARendererService.stops==0&&App.events.isEmpty(),"ordinary in-app navigation recovered");
                home.changing=true;app.lifecycle.onActivityStopped(home);app.lifecycle.onActivityDestroyed(home);
                home=new Activity();app.lifecycle.onActivityStarted(home);app.lifecycle.onActivityResumed(home);r.check();
                check(TvNetworkLifecycle.generation()==0&&DLNARendererService.starts==1,"configuration recreation restarted renderer");
                screen(app,Intent.ACTION_SCREEN_OFF);screen(app,Intent.ACTION_SCREEN_OFF);r.check();
                check(DLNARendererService.stops==1&&DLNARendererService.starts==1,"duplicate OFF or background check restarted renderer");
                screen(app,Intent.ACTION_SCREEN_ON);screen(app,Intent.ACTION_SCREEN_ON);r.check();r.check();
                check(TvNetworkLifecycle.generation()==1&&DLNARendererService.starts==2,"screen ON/focus restart did not happen exactly once");
                check(App.events.equals(List.of("progress","cancel","api-dns","images","spider")),"resume resource ordering");
                complete(app);check(refreshes==1&&TvNetworkLifecycle.recoveredGeneration()==1,"first wake not recovered");r.check();check(App.events.size()==5,"repeat focus rebuilt network");
                app.lifecycle.onActivityStopped(home);screen(app,Intent.ACTION_SCREEN_ON);r.onLocalNetworkPermissionGranted();
                check(TvNetworkLifecycle.generation()==1&&DLNARendererService.starts==2,"background SCREEN ON consumed generation or started renderer");
                app.permission=-1;app.lifecycle.onActivityStarted(home);app.lifecycle.onActivityResumed(home);r.check();
                check(TvNetworkLifecycle.generation()==2&&DLNARendererService.starts==2,"permission revocation on resume bypassed");
                app.permission=0;r.onLocalNetworkPermissionGranted();check(DLNARendererService.starts==3,"grant after wake lost");
                Runnable stale=BaseLoader.get().after;r.close();stale.run();check(App.queue.isEmpty()&&refreshes==1,"closed Home accepted stale clear");
                FongMiNetworkRecovery next=owner(app);next.check();complete(app);
                check(refreshes==2&&TvNetworkLifecycle.recoveredGeneration()==2,"new Home failed to recover pending generation");
                next.close();app.lifecycle.onActivityStopped(home);app.permission=-1;Build.VERSION.SDK_INT=36;
                app.lifecycle.onActivityStarted(home);app.lifecycle.onActivityResumed(home);
                check(DLNARendererService.starts==4,"pre-37 permission gate changed legacy renderer behavior");
                FongMiNetworkRecovery f1=owner(app);App.events.clear();f1.check();
                long first=TvNetworkLifecycle.generation(),previous=TvNetworkLifecycle.recoveredGeneration();
                check(first==previous+1&&App.events.size()==5,"first wake did not start slow clear");
                Runnable slow=BaseLoader.get().after;
                app.lifecycle.onActivityStarted(video);homeReady=false;app.lifecycle.onActivityPaused(home);
                app.lifecycle.onActivityResumed(video);app.lifecycle.onActivityStopped(home);
                screen(app,Intent.ACTION_SCREEN_OFF);screen(app,Intent.ACTION_SCREEN_ON);
                check(TvNetworkLifecycle.generation()==first+1,"second wake while Live active was lost");
                slow.run();App.tick();
                check(App.events.size()==5&&refreshes==2&&TvNetworkLifecycle.recoveredGeneration()==previous,"background Home reset or consumed the latest generation");
                slow.run();check(App.queue.isEmpty(),"duplicate completion scheduled hidden recovery");
                app.lifecycle.onActivityStarted(home);homeReady=true;app.lifecycle.onActivityResumed(home);app.lifecycle.onActivityStopped(video);
                f1.check();f1.check();check(App.queue.size()==1,"resume/focus did not coalesce deferred poll");
                App.tick();check(App.events.size()==10&&refreshes==2,"return to Home did not start exactly one new clear");
                slow.run();check(App.queue.isEmpty(),"old callback completed the new clear");
                complete(app);f1.check();
                check(refreshes==3&&TvNetworkLifecycle.recoveredGeneration()==first+1&&App.events.size()==10,"latest generation not recovered exactly once");
                f1.close();
                System.out.println("PASS "+checks+" actual candidate recovery/renderer lifecycle assertions");
            }
        }''',
}


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    a = parser.parse_args()
    sources = {Path(name).name: (a.candidate/name).read_bytes() for name in SOURCES}
    for name, expected in SOURCES.items():
        assert git_blob(sources[Path(name).name]) == expected, "reviewed host source drift: " + name
    with tempfile.TemporaryDirectory(prefix="fingmi-590-host-recovery-") as temp:
        root = Path(temp)
        for name, source in STUBS.items():
            path = root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        def run(files, positive):
            for name, data in files.items():
                (root/name).write_bytes(data)
            classes = root/"classes"
            classes.mkdir(exist_ok=True)
            subprocess.run(["javac", "--release", "17", "-d", str(classes), *map(str, sorted(root.rglob("*.java")))], check=True, capture_output=True)
            result = subprocess.run(["java", "-cp", str(classes), "HostRecoveryTest"], capture_output=True, text=True, timeout=20)
            if positive:
                assert result.returncode == 0, result.stdout+result.stderr
                print(result.stdout.strip())
            else:
                assert result.returncode != 0 and "AssertionError" in result.stderr, result.stdout+result.stderr
        run(sources, True)
        mutations = [
            ("FongMiNetworkRecovery.java", b"public boolean canRecoverHome() { return homeRecoverable.getAsBoolean(); }", b"public boolean canRecoverHome() { return true; }"),
            ("TvDlnaLifecycle.java", b"Build.VERSION.SDK_INT >= 37", b"Build.VERSION.SDK_INT >= 99"),
            ("TvNetworkLifecycle.java", b"if (startedActivities.isEmpty() || backgroundPending) return;", b"if (false) return;"),
            ("FongMiNetworkRecovery.java", b"public void onLocalNetworkPermissionGranted() { lifecycle.startRendererIfNeeded(); }", b"public void onLocalNetworkPermissionGranted() {}"),
            ("FongMiNetworkRecovery.java", b"        lifecycle.startRendererIfNeeded();\n        coordinator.check();", b"        coordinator.check();"),
        ]
        for name, old, new in mutations:
            assert sources[name].count(old) == 1
            changed = dict(sources)
            changed[name] = sources[name].replace(old,new)
            run(changed, False)
        print("PASS 5 negative controls rejected; Android and network boundaries are doubles")


if __name__ == "__main__":
    main()
