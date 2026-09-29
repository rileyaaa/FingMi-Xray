#!/usr/bin/env python3
"""Guard the released Android TV network-recovery generation boundary."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = ROOT / "app/src/main/java/com/fongmi/android/tv/network/TvNetworkLifecycle.java"
COORDINATOR = ROOT / "app/src/main/java/com/fongmi/android/tv/network/NetworkRecoveryCoordinator.java"
HOME = ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java"
GLIDE = ROOT / "app/src/main/java/com/fongmi/android/tv/utils/OkGlideModule.java"
IMG = ROOT / "app/src/main/java/com/fongmi/android/tv/utils/ImgUtil.java"
LEANBACK_MANIFEST = ROOT / "app/src/leanback/AndroidManifest.xml"
REFERENCE = ROOT / "docs/apk-reference/shared/sources/p000/gn3.java"

for path in (LIFECYCLE, COORDINATOR, HOME, GLIDE, IMG, LEANBACK_MANIFEST, REFERENCE):
    if not path.is_file():
        raise SystemExit(f"missing TV network recovery source: {path.relative_to(ROOT)}")

lifecycle = LIFECYCLE.read_text(encoding="utf-8")
reference = REFERENCE.read_text(encoding="utf-8")
home = HOME.read_text(encoding="utf-8")
manifest = LEANBACK_MANIFEST.read_text(encoding="utf-8")

for forbidden in (
    "android.permission.RECEIVE_BOOT_COMPLETED",
    ".receiver.BootReceiver",
    "android.intent.action.BOOT_COMPLETED",
    "android.intent.action.QUICKBOOT_POWERON",
):
    if forbidden in manifest:
        raise SystemExit(f"Leanback manifest must not bypass network recovery with boot callback: {forbidden}")

for forbidden in (
    "mNetworkListener",
    "addListener(mNetworkListener)",
    "removeListener(mNetworkListener)",
):
    if forbidden in home:
        raise SystemExit(f"HomeActivity must recover only when Home itself resumes/focuses: {forbidden}")

for needle in (
    "protected void onResume()",
    "if (hasFocus) checkNetworkGeneration();",
):
    if needle not in home:
        raise SystemExit(f"HomeActivity missing released foreground recovery check: {needle}")

for needle in (
    "Intent.ACTION_SCREEN_OFF",
    "Intent.ACTION_SCREEN_ON",
    "backgroundPending = true;",
    "generation++;",
    "TvDlnaLifecycle.start(application)",
    "TvDlnaLifecycle.stop(application)",
):
    if needle not in lifecycle:
        raise SystemExit(f"TvNetworkLifecycle missing released generation contract: {needle}")

for forbidden in (
    "ConnectivityManager",
    "NetworkCallback",
    "registerDefaultNetworkCallback",
    "activeNetwork",
    "networkWasLost",
    "onAvailable(Network",
    "onLost(Network",
    "CopyOnWriteArraySet",
    "addListener(",
    "notifyListeners(",
):
    if forbidden in lifecycle:
        raise SystemExit(
            f"TvNetworkLifecycle must not add a default-network generation source absent from released gn3: {forbidden}"
        )

for needle in (
    'intentFilter.addAction("android.intent.action.SCREEN_OFF")',
    'intentFilter.addAction("android.intent.action.SCREEN_ON")',
    "onActivityStarted",
    "onActivityStopped",
):
    if needle not in reference:
        raise SystemExit(f"released gn3 evidence missing expected lifecycle trigger: {needle}")

for forbidden in ("ConnectivityManager", "NetworkCallback", "registerDefaultNetworkCallback"):
    if forbidden in reference:
        raise SystemExit(f"released gn3 unexpectedly contains network callback evidence: {forbidden}")

img = IMG.read_text(encoding="utf-8")
if "public static void resetNetworkFailures()" not in img or "failed.clear();" not in img:
    raise SystemExit("ImgUtil must forget transient image failures on network generation recovery")
if "ImgUtil.resetNetworkFailures();" not in home:
    raise SystemExit("HomeActivity network recovery must reset transient image failures")

glide = GLIDE.read_text(encoding="utf-8")
if "new OkHttpUrlLoader.Factory(OkHttp.client())" in glide:
    raise SystemExit("Glide must not pin the API client across TV network generations")
for needle in (
    "new OkHttpUrlLoader.Factory(request -> OkHttp.client().newCall(request))",
):
    if needle not in glide:
        raise SystemExit(f"OkGlideModule missing recovered-client handoff: {needle}")

coordinator = COORDINATOR.read_text(encoding="utf-8")
for needle in (
    "if (recovering) return;",
    "hooks.schedule(poll, 0);",
    "recovering = false;\n            check();",
):
    if needle not in coordinator:
        raise SystemExit(f"NetworkRecoveryCoordinator missing serialized recovery contract: {needle}")

for needle in (
    "new NetworkRecoveryCoordinator(TvNetworkLifecycle.recoveredGeneration()",
    "OkHttp.resetApiNetworkForResume()",
    "BaseLoader.get().clear(after)",
    "NetworkCapabilities.NET_CAPABILITY_INTERNET",
    "TvNetworkLifecycle.markRecovered(TvNetworkLifecycle.generation())",
    "checkNetworkGeneration();",
):
    if needle not in home:
        raise SystemExit(f"HomeActivity missing TV recovery contract: {needle}")

HARNESS = r"""
package com.fongmi.android.tv.network;

import java.util.ArrayList;
import java.util.List;

public final class NetworkRecoveryParityTest {
    private static final class Fake implements NetworkRecoveryCoordinator.Hooks {
        long generation;
        boolean ready;
        Runnable spiderDone;
        Runnable scheduled;
        int refreshes;
        final List<String> events = new ArrayList<>();

        @Override public long generation() { return generation; }
        @Override public void cancelRequests() { events.add("cancel"); }
        @Override public void resetApiAndDns() { events.add("api-dns"); }
        @Override public void clearSpiders(Runnable after) {
            events.add("spider");
            spiderDone = after;
        }
        @Override public boolean networkReady() { return ready; }
        @Override public void schedule(Runnable action, long delayMillis) { scheduled = action; }
        @Override public void unschedule(Runnable action) {
            if (scheduled == action) scheduled = null;
        }
        @Override public void showProgress() { events.add("progress"); }
        @Override public void refreshHome() { refreshes++; }

        void completeSpider() {
            Runnable done = spiderDone;
            spiderDone = null;
            if (done == null) throw new AssertionError("missing spider completion");
            done.run();
        }

        void tick() {
            Runnable action = scheduled;
            scheduled = null;
            if (action == null) throw new AssertionError("missing scheduled recovery poll");
            action.run();
        }
    }

    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static void same(List<String> actual, String... expected) {
        check(actual.size() == expected.length, "event count " + actual);
        for (int i = 0; i < expected.length; i++) {
            check(expected[i].equals(actual.get(i)), "event order " + actual);
        }
    }

    private static void oneGeneration() {
        Fake fake = new Fake();
        NetworkRecoveryCoordinator recovery = new NetworkRecoveryCoordinator(0, fake);
        recovery.check();
        check(fake.events.isEmpty(), "initial generation must be a no-op");

        fake.generation = 1;
        recovery.check();
        same(fake.events, "progress", "cancel", "api-dns", "spider");
        recovery.check();
        check(fake.events.size() == 4, "same generation must not restart recovery");

        fake.completeSpider();
        fake.ready = true;
        fake.tick();
        check(fake.refreshes == 0, "one stable check must not refresh");
        fake.tick();
        check(fake.refreshes == 1, "two stable checks must refresh exactly once");
        check(recovery.appliedGeneration() == 1, "generation 1 must be applied");
    }

    private static void staleSpiderCompletion() {
        Fake fake = new Fake();
        NetworkRecoveryCoordinator recovery = new NetworkRecoveryCoordinator(0, fake);

        fake.generation = 1;
        recovery.check();
        Runnable stale = fake.spiderDone;

        fake.generation = 2;
        recovery.check();
        check(fake.events.size() == 4, "new generation must wait for in-flight spider clear");
        stale.run();
        check(fake.scheduled != null, "released flow posts stability check after spider clear");
        check(fake.events.size() == 4, "generation restart must wait for the posted poll");
        fake.tick();
        same(
                fake.events,
                "progress", "cancel", "api-dns", "spider",
                "progress", "cancel", "api-dns", "spider");

        fake.completeSpider();
        fake.ready = true;
        fake.tick();
        fake.tick();
        check(fake.refreshes == 1, "newest generation must refresh once");
        check(recovery.appliedGeneration() == 2, "newest generation must win");
    }

    private static void generationChangesWhilePolling() {
        Fake fake = new Fake();
        NetworkRecoveryCoordinator recovery = new NetworkRecoveryCoordinator(0, fake);

        fake.generation = 1;
        recovery.check();
        fake.completeSpider();
        fake.ready = false;

        fake.generation = 2;
        fake.tick();

        same(
                fake.events,
                "progress", "cancel", "api-dns", "spider",
                "progress", "cancel", "api-dns", "spider");
        check(recovery.recovering(), "new generation must remain in recovery");
        check(fake.refreshes == 0, "stale polling must never refresh Home");
    }

    public static void main(String[] args) {
        oneGeneration();
        staleSpiderCompletion();
        generationChangesWhilePolling();
        System.out.println("PASS released TV network recovery generation/race parity");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="tv-network-recovery-") as directory:
    work = Path(directory)
    harness = work / "com/fongmi/android/tv/network/NetworkRecoveryParityTest.java"
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text(HARNESS.strip() + "\n", encoding="utf-8")
    classes = work / "classes"

    subprocess.run(
        [
            "java",
            "com.sun.tools.javac.Main",
            "--release",
            "17",
            "-d",
            str(classes),
            str(COORDINATOR),
            str(harness),
        ],
        check=True,
    )
    subprocess.run(
        [
            "java",
            "-cp",
            str(classes),
            "com.fongmi.android.tv.network.NetworkRecoveryParityTest",
        ],
        check=True,
    )
