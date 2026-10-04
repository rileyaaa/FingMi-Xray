#!/usr/bin/env python3
"""Compile actual recovery core/app adapters and guard one-way module dependencies."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "tv-recovery/src/main/java/com/fingmi/tvrecovery"
ADAPTER = ROOT / "app/src/main/java/com/fingmi/integration/recovery/FongMiNetworkRecovery.java"

for module in ("xray", "tv-recovery"):
    for source in (ROOT / module / "src/main").rglob("*.java"):
        text = source.read_text()
        for forbidden in ("com.fongmi.", "com.github.catvod.", "com.fingmi.integration."):
            if forbidden in text:
                raise SystemExit(f"{module} core depends on app/upstream: {source}")
    gradle = (ROOT / module / "build.gradle").read_text()
    projects = set(re.findall(r"project\(\s*['\"]([^'\"]+)['\"]\s*\)", gradle))
    allowed = {":libxray"} if module == "xray" else set()
    if projects - allowed:
        raise SystemExit(f"reverse/cross-module dependency in {module}: {projects - allowed}")

home = (ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java").read_text()
for forbidden in ("new NetworkRecoveryCoordinator", "TvNetworkLifecycle.", "hasInternetCapability(", "resetApiNetworkForResume()"):
    if forbidden in home:
        raise SystemExit(f"recovery implementation leaked into Home: {forbidden}")
if "new FongMiNetworkRecovery(" not in home:
    raise SystemExit("Home must connect the app-owned recovery adapter")
for old in ("NetworkRecoveryCoordinator", "TvNetworkLifecycle"):
    if (ROOT / f"app/src/main/java/com/fongmi/android/tv/network/{old}.java").exists():
        raise SystemExit(f"duplicate recovery implementation: {old}")

# Android/App/HTTP are boundary doubles; lifecycle, coordinator and both
# flavor adapters below are the actual production source, not copied models.
STUBS = {
    "androidx/annotation/NonNull.java": "package androidx.annotation; public @interface NonNull {}",
    "androidx/annotation/Nullable.java": "package androidx.annotation; public @interface Nullable {}",
    "android/os/Bundle.java": "package android.os; public class Bundle {}",
    "android/content/Context.java": """package android.content;
        public class Context {
            public static final String CONNECTIVITY_SERVICE = "connectivity";
            public final android.net.ConnectivityManager network = new android.net.ConnectivityManager();
            public Object getSystemService(String name) { return network; }
        }""",
    "android/content/Intent.java": """package android.content;
        public class Intent {
            public static final String ACTION_SCREEN_OFF="off", ACTION_SCREEN_ON="on";
            private final String action;
            public Intent(String action) { this.action=action; }
            public String getAction() { return action; }
        }""",
    "android/content/IntentFilter.java": "package android.content; public class IntentFilter { public void addAction(String value) {} }",
    "android/content/BroadcastReceiver.java": "package android.content; public abstract class BroadcastReceiver { public abstract void onReceive(Context c, Intent i); }",
    "android/app/Activity.java": "package android.app; public class Activity { public boolean changing; public boolean isChangingConfigurations() { return changing; } }",
    "android/app/Application.java": """package android.app;
        import android.content.*; import android.os.Bundle;
        public class Application extends Context {
            public ActivityLifecycleCallbacks lifecycle; public BroadcastReceiver receiver;
            public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks value) { lifecycle=value; }
            public Intent registerReceiver(BroadcastReceiver value, IntentFilter filter) { receiver=value; return null; }
            public interface ActivityLifecycleCallbacks {
                void onActivityCreated(Activity a, Bundle b); void onActivityStarted(Activity a);
                void onActivityResumed(Activity a); void onActivityPaused(Activity a);
                void onActivityStopped(Activity a); void onActivitySaveInstanceState(Activity a, Bundle b);
                void onActivityDestroyed(Activity a);
            }
        }""",
    "android/net/Network.java": "package android.net; public class Network {}",
    "android/net/NetworkCapabilities.java": """package android.net;
        public class NetworkCapabilities { public static final int NET_CAPABILITY_INTERNET=12;
            public boolean ready; public boolean hasCapability(int value) { return ready; } }""",
    "android/net/ConnectivityManager.java": """package android.net;
        public class ConnectivityManager {
            public final NetworkCapabilities capabilities = new NetworkCapabilities();
            public Network getActiveNetwork() { return new Network(); }
            public NetworkCapabilities getNetworkCapabilities(Network n) { return capabilities; }
        }""",
    "com/fongmi/android/tv/App.java": """package com.fongmi.android.tv;
        import java.util.ArrayList;
        public class App {
            public static final ArrayList<String> events = new ArrayList<>();
            public static final ArrayList<Runnable> queue = new ArrayList<>();
            public static void post(Runnable r, long delay) { queue.add(r); }
            public static void removeCallbacks(Runnable r) { queue.removeIf(item -> item==r); }
            public static void tick() { queue.remove(0).run(); }
        }""",
    "com/fongmi/android/tv/api/loader/BaseLoader.java": """package com.fongmi.android.tv.api.loader;
        public class BaseLoader {
            private static final BaseLoader INSTANCE=new BaseLoader(); public Runnable after;
            public static BaseLoader get() { return INSTANCE; }
            public void clear(Runnable value) { com.fongmi.android.tv.App.events.add("spider"); after=value; }
        }""",
    "com/fongmi/android/tv/utils/ImgUtil.java": "package com.fongmi.android.tv.utils; public class ImgUtil { public static void resetNetworkFailures() { com.fongmi.android.tv.App.events.add(\"images\"); } }",
    "com/github/catvod/net/OkHttp.java": "package com.github.catvod.net; public class OkHttp { public static void resetApiNetworkForResume() { com.fongmi.android.tv.App.events.add(\"api-dns\"); } }",
    "com/fongmi/android/tv/service/DLNARendererService.java": """package com.fongmi.android.tv.service;
        public class DLNARendererService {
            public static int starts, stops;
            public static void start(android.content.Context c) { starts++; }
            public static void stop(android.content.Context c) { stops++; }
        }""",
    "RecoveryIntegrationTest.java": """import android.app.*; import android.content.*;
        import com.fingmi.integration.recovery.FongMiNetworkRecovery;
        import com.fingmi.tvrecovery.TvNetworkLifecycle;
        import com.fongmi.android.tv.App;
        import com.fongmi.android.tv.api.loader.BaseLoader;
        import com.fongmi.android.tv.service.DLNARendererService;
        import java.util.List;
        public class RecoveryIntegrationTest {
            static boolean alive=true; static int refreshes;
            static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
            static FongMiNetworkRecovery owner(Application app) {
                return new FongMiNetworkRecovery(app, ()->App.events.add("cancel"),
                    ()->App.events.add("progress"), ()->alive, ()->refreshes++);
            }
            public static void main(String[] args) {
                boolean tv=args[0].equals("leanback");
                Application app=new Application(); Activity activity=new Activity();
                FongMiNetworkRecovery first=owner(app);
                app.lifecycle.onActivityStarted(activity); app.lifecycle.onActivityResumed(activity);
                first.check(); check(App.events.isEmpty(), "cold start must not rebuild");
                activity.changing=true; app.lifecycle.onActivityStopped(activity);
                app.lifecycle.onActivityStarted(activity); activity.changing=false;
                check(TvNetworkLifecycle.generation()==0, "configuration change is not standby");
                app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_OFF));
                app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_ON));
                check(TvNetworkLifecycle.generation()==1, "screen resume generation");
                first.check(); first.check();
                check(App.events.equals(List.of("progress","cancel","api-dns","images","spider")), "one ordered rebuild");
                BaseLoader.get().after.run(); app.network.capabilities.ready=true;
                App.tick(); check(refreshes==0, "wait for two stable checks");
                App.tick(); check(refreshes==1 && TvNetworkLifecycle.recoveredGeneration()==1, "mark after stable refresh");
                first.close(); FongMiNetworkRecovery second=owner(app); second.check();
                check(App.events.size()==5, "recreated home skips completed generation");
                app.lifecycle.onActivityResumed(activity);
                app.lifecycle.onActivityStopped(activity); app.lifecycle.onActivityStarted(activity);
                check(TvNetworkLifecycle.generation()==2, "background resume generation");
                second.check(); Runnable stale=BaseLoader.get().after; second.close(); stale.run();
                check(App.queue.isEmpty() && refreshes==1, "closed owner discards late completion");
                FongMiNetworkRecovery third=owner(app); third.check(); alive=false;
                BaseLoader.get().after.run(); App.tick(); App.tick();
                check(refreshes==1 && TvNetworkLifecycle.recoveredGeneration()==1, "dead owner cannot mark recovered");
                third.close(); alive=true; FongMiNetworkRecovery fourth=owner(app); fourth.check();
                BaseLoader.get().after.run(); App.tick(); App.tick();
                check(refreshes==2 && TvNetworkLifecycle.recoveredGeneration()==2, "new owner recovers incomplete generation");
                fourth.close();
                check(DLNARendererService.starts==(tv?2:0) && DLNARendererService.stops==(tv?2:0), "flavor DLNA ownership");
                System.out.println("PASS "+args[0]+" actual recovery core/adapter lifecycle");
            }
        }""",
}

with tempfile.TemporaryDirectory(prefix="fork-modules-") as directory:
    work = Path(directory)
    stubs = []
    for name, text in STUBS.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        stubs.append(str(path))
    for flavor in ("leanback", "mobile"):
        classes = work / flavor
        subprocess.run([
            "java", "com.sun.tools.javac.Main", "--release", "17", "-d", str(classes),
            *stubs, *(str(p) for p in CORE.glob("*.java")), str(ADAPTER),
            str(ROOT / f"app/src/{flavor}/java/com/fingmi/integration/recovery/TvDlnaLifecycle.java"),
        ], check=True)
        subprocess.run(["java", "-cp", str(classes), "RecoveryIntegrationTest", flavor], check=True)
print("PASS independent module boundaries and FongMi adapter")
