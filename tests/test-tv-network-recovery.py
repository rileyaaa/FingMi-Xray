#!/usr/bin/env python3
"""Guard the released Android TV network-recovery generation boundary."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "tests/test-fork-module-boundaries.py")], check=True)
subprocess.run([sys.executable, str(ROOT / "tests/test-tv-recovery-cold-entry.py")], check=True)
LIFECYCLE = ROOT / "tv-recovery/src/main/java/com/fingmi/tvrecovery/TvNetworkLifecycle.java"
COORDINATOR = ROOT / "tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java"
ADAPTER = ROOT / "app/src/main/java/com/fingmi/integration/recovery/FongMiNetworkRecovery.java"
HOME = ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java"
GLIDE = ROOT / "app/src/main/java/com/fongmi/android/tv/utils/OkGlideModule.java"
IMG = ROOT / "app/src/main/java/com/fongmi/android/tv/utils/ImgUtil.java"
JAR_LOADER = ROOT / "app/src/main/java/com/fongmi/android/tv/api/loader/JarLoader.java"
JS_LOADER = ROOT / "app/src/main/java/com/fongmi/android/tv/api/loader/JsLoader.java"
PY_LOADER = ROOT / "app/src/main/java/com/fongmi/android/tv/api/loader/PyLoader.java"
LEANBACK_MANIFEST = ROOT / "app/src/leanback/AndroidManifest.xml"
REFERENCE = ROOT / "docs/apk-reference/shared/sources/p000/gn3.java"
OKHTTP = ROOT / "catvod/src/main/java/com/github/catvod/net/OkHttp.java"
OKDNS = ROOT / "catvod/src/main/java/com/github/catvod/net/OkDns.java"
PROXY_SELECTOR = ROOT / "catvod/src/main/java/com/github/catvod/net/OkProxySelector.java"
PROXY_AUTH = ROOT / "catvod/src/main/java/com/github/catvod/net/OkAuthenticator.java"
PROXY_REDIRECT = ROOT / "catvod/src/main/java/com/github/catvod/net/ProxyRedirectInterceptor.java"
PROXY_TEST = ROOT / "catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java"
SETTING = ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java"

# Ordinary FongMi business/config/UI files must remain byte-for-byte equal
# to their selected, publicly verified upstream release. 5.6.3 and 5.8.7
# have different canonical blobs; neither may be silently rewritten by the
# fork's TV network recovery overlay. Future upstream versions need a review.
UPSTREAM_EXACT_BLOBS = {
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/KeepActivity.java":
        "bcf1a307d3aecc3118023fe0dcb4bfb617ca251f",
    "app/src/main/java/com/fongmi/android/tv/api/SiteApi.java":
        "3ec904af4ae0f65ee4d6dfe12216138eb9da1d41",
    "app/src/main/java/com/fongmi/android/tv/api/config/BaseConfig.java":
        "f3af7bafc7173abbf98ce81bd85f17db4a359120",
    "app/src/main/java/com/fongmi/android/tv/api/config/VodConfig.java":
        "d0948453838b237520be27952d0122410ea50b9d",
    "app/src/main/java/com/fongmi/android/tv/api/config/LiveConfig.java":
        "403c34d6b2ff416545abda204ec3af10ec38d020",
    "app/src/main/java/com/fongmi/android/tv/api/config/WallConfig.java":
        "841de7fa6c4853db1cb32d0bffa59854086704ee",
    "app/src/main/java/com/fongmi/android/tv/api/parser/LiveParser.java":
        "69aa742e7ee0b5778c6de2ef1e38198ee229d3ff",
    "app/src/main/java/com/fongmi/android/tv/event/ConfigEvent.java":
        "688fe40e6e9044fa5e83f75eebfa9072fcf501ca",
    "app/src/main/java/com/fongmi/android/tv/utils/Notify.java":
        "5df37107be415ee8039a71d32b00170c20ac47ea",
}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload).hexdigest()


# The real 5.8.7 upstream intentionally changes seven business files.
# The original 5.6.3 hashes must never block a legitimate upstream upgrade.
UPSTREAM_EXACT_BLOBS_587 = {
    **UPSTREAM_EXACT_BLOBS,
    "app/src/main/java/com/fongmi/android/tv/api/SiteApi.java":
        "54f0d7b2c416d1fac5b9211ad7765e3e08a43809",
    "app/src/main/java/com/fongmi/android/tv/api/config/BaseConfig.java":
        "4b8096248630a0276c0527bd27c0d1511ec33be4",
    "app/src/main/java/com/fongmi/android/tv/api/config/VodConfig.java":
        "e69df3e32c719cf2ac97d4f533b19d19cf567c4a",
    "app/src/main/java/com/fongmi/android/tv/api/config/LiveConfig.java":
        "f087d0f29000b0a69c53dfae9bd8002b85622c59",
    "app/src/main/java/com/fongmi/android/tv/api/config/WallConfig.java":
        "7e255f9565df34bcb116dacf58ab71c8c83d7519",
    "app/src/main/java/com/fongmi/android/tv/api/parser/LiveParser.java":
        "6f4b7ff3ff95e21851a9a82f90be55fee7b695ed",
    "app/src/main/java/com/fongmi/android/tv/utils/Notify.java":
        "da3cda84726535bc7c4bce81b563db1cabb38b24",
}
import re

version_match = re.search(
    r'\bversionName\s+"v(\d+\.\d+\.\d+)-xray\.\d+"',
    (ROOT / "app/build.gradle").read_text(encoding="utf-8"),
)
if not version_match:
    raise SystemExit("Unknown fork version; cannot select canonical upstream source hashes")
upstream_version = version_match.group(1)
if upstream_version == "5.6.3":
    pinned_source_blobs = UPSTREAM_EXACT_BLOBS
elif upstream_version == "5.8.7":
    pinned_source_blobs = UPSTREAM_EXACT_BLOBS_587
else:
    raise SystemExit("TV network recovery has no approved upstream baseline for " + upstream_version)

for relative, expected in pinned_source_blobs.items():
    source = ROOT / relative
    if not source.is_file():
        raise SystemExit(f"missing fixed-upstream source: {relative}")
    actual = git_blob_sha(source)
    if actual != expected:
        raise SystemExit(
            "TV recovery scope drifted into ordinary FongMi source: "
            f"{relative} expected={expected} actual={actual}"
        )

setting_source = SETTING.read_text(encoding="utf-8")
for forbidden in (
    "mDeferredConfigUiAction",
    "runDeferredConfigUi",
    "runConfigUi(",
    "Notify.dismiss(SettingActivity.this)",
):
    if forbidden in setting_source:
        raise SystemExit(
            f"SettingActivity must not carry TV-recovery callback state: {forbidden}"
        )

for path in (LIFECYCLE, COORDINATOR, ADAPTER, HOME, GLIDE, IMG, JAR_LOADER, JS_LOADER, PY_LOADER, LEANBACK_MANIFEST, REFERENCE, OKHTTP, OKDNS, PROXY_SELECTOR, PROXY_AUTH, PROXY_REDIRECT, PROXY_TEST):
    if not path.is_file():
        raise SystemExit(f"missing TV network recovery source: {path.relative_to(ROOT)}")

lifecycle = LIFECYCLE.read_text(encoding="utf-8")
reference = REFERENCE.read_text(encoding="utf-8")
home = HOME.read_text(encoding="utf-8")
adapter = ADAPTER.read_text(encoding="utf-8")
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
    "renderer.start()",
    "renderer.stop()",
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
for needle in (
    "private static final AtomicLong networkFailureEpoch = new AtomicLong();",
    "networkFailureEpoch.incrementAndGet();",
    "long requestEpoch = networkFailureEpoch.get();",
    "if (requestEpoch != networkFailureEpoch.get()) return true;",
):
    if needle not in img:
        raise SystemExit(f"ImgUtil missing stale Glide failure generation guard: {needle}")
if "ImgUtil.resetNetworkFailures();" not in adapter:
    raise SystemExit("FongMi recovery adapter must reset transient image failures")

glide = GLIDE.read_text(encoding="utf-8")
if "new OkHttpUrlLoader.Factory(OkHttp.client())" in glide:
    raise SystemExit("Glide must not pin the API client across TV network generations")
for needle in (
    "new OkHttpUrlLoader.Factory(request -> OkHttp.client().newCall(request))",
):
    if needle not in glide:
        raise SystemExit(f"OkGlideModule missing recovered-client handoff: {needle}")

base_loader = (ROOT / "app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java").read_text(encoding="utf-8")
spider_loader = ROOT / "app/src/main/java/com/fongmi/android/tv/api/loader/SpiderLoader.java"
if "private void clearLoaders(" in base_loader:
    # New public FongMi 5.8+ implementation centralized per-Spider disposal.
    if not spider_loader.exists():
        raise SystemExit("New BaseLoader lacks its SpiderLoader cleanup owner")
    spider = spider_loader.read_text(encoding="utf-8")
    for needle in (
        "for (Spider spider : active) failure = destroySpider(spider, failure);",
        "for (Spider spider : active) failure = closeSpider(spider, failure);",
        "spider.destroy();",
        "} catch (RuntimeException | Error error) {",
    ):
        if needle not in spider:
            raise SystemExit(f"New SpiderLoader lost per-Spider failure isolation: {needle}")
    for needle in (
        "public void clear(Runnable onComplete)",
        "clearLoaders(previous, retired);",
        "if (onComplete != null) App.post(onComplete);",
    ):
        if needle not in base_loader:
            raise SystemExit(f"New BaseLoader lacks finished-cleanup callback: {needle}")
else:
    # Old 5.6.3 upstream has separate Jar/JS/Python implementation.
    for loader_path in (JAR_LOADER, JS_LOADER, PY_LOADER):
        loader = loader_path.read_text(encoding="utf-8")
        if "spiders.values().forEach(Spider::destroy)" in loader:
            raise SystemExit(
                f"{loader_path.name} must isolate each Spider.destroy failure"
            )
        for needle in (
            "for (Spider spider : spiders.values()) {",
            "spider.destroy();",
            "} catch (Throwable ignored) {",
        ):
            if needle not in loader:
                raise SystemExit(
                    f"{loader_path.name} missing per-Spider cleanup tolerance: {needle}"
                )
    js_loader = JS_LOADER.read_text(encoding="utf-8")
    if "try {\\n            Module.get().clear();\\n        } catch (Throwable ignored) {" not in js_loader:
        raise SystemExit("JsLoader must tolerate QuickJS module-cache cleanup failure")

okhttp = OKHTTP.read_text(encoding="utf-8")
okdns = OKDNS.read_text(encoding="utf-8")
selector = PROXY_SELECTOR.read_text(encoding="utf-8")
proxy_auth = PROXY_AUTH.read_text(encoding="utf-8")
proxy_redirect = PROXY_REDIRECT.read_text(encoding="utf-8")
proxy_test = PROXY_TEST.read_text(encoding="utf-8")

for needle in (
    "new ProxyRedirectInterceptor(selector)",
    ".followRedirects(false)",
    "builder.interceptors().removeIf(item -> item instanceof ProxyRedirectInterceptor)",
    "public static void resetApiNetworkForResume()",
    "get().client = null;",
    "cleanupClientAsync(",
    "NETWORK_CLEANUP.execute(() -> {",
):
    if needle not in okhttp:
        raise SystemExit(f"OkHttp missing upstream redirect/current recovery coexistence contract: {needle}")

reset_body = okhttp.split("public static void resetApiNetworkForResume()", 1)[1].split("public static void cleanupClientAsync", 1)[0]
if "get().player = null" in reset_body:
    raise SystemExit("TV network recovery must not destroy the dedicated playback client")
if "selector().clear()" in reset_body:
    raise SystemExit("TV network recovery must not erase configured proxy rules; stale redirect policies die with the retired API client")

for needle in (
    "Dns resolver;",
    "resolver = doh != null ? doh : Dns.SYSTEM;",
    "return resolver.lookup(get(hostname));",
):
    if needle not in okdns:
        raise SystemExit(f"OkDns missing network-generation resolver snapshot contract: {needle}")
if "return (doh != null ? doh : Dns.SYSTEM).lookup(get(hostname));" in okdns:
    raise SystemExit("OkDns lookup must not re-read volatile DoH after leaving the reset lock")

for needle in (
    "generation++;",
    "Policy policy(",
    "previous.generation == generation",
    "sharesProxyCredentials(Policy other)",
):
    if needle not in selector:
        raise SystemExit(f"OkProxySelector missing redirect-policy generation contract: {needle}")

for needle in (
    ".tag(OkProxySelector.Policy.class)",
    "Credentials.basic(username, password, StandardCharsets.UTF_8)",
):
    if needle not in proxy_auth:
        raise SystemExit(f"OkAuthenticator missing redirect-scoped credential contract: {needle}")

for needle in (
    "chain.getProxy() == null && chain.getProxySelector() == selector",
    ".sharesProxyCredentials(",

    'removeHeader("Proxy-Authorization")',
    'removeHeader("Authorization")',
    "followUpCount",

    "chain.getFollowSslRedirects()",
):
    if needle not in proxy_redirect:
        raise SystemExit(f"ProxyRedirectInterceptor missing upstream redirect safety contract: {needle}")

for needle in (
    "redirectChainCarriesProxyAcrossIpTargets",
    "redirectUsesTargetHostRule",
    "redirectToDifferentProxyDoesNotForwardOldCredentials",
    "warmDirectConnectionDoesNotBypassRedirectProxy",
    "noRedirectClientReturnsRedirectResponse",
    "redirect302ChangesPostToGetAndDropsCrossHostAuthorization",
    "redirect307PreservesPostMethod",
):
    if needle not in proxy_test:
        raise SystemExit(f"upstream proxy redirect regression suite missing case: {needle}")

coordinator = COORDINATOR.read_text(encoding="utf-8")
for needle in (
    "if (recovering) return;",
    "hooks.schedule(poll, 0);",
    "recovering = false;\n            check();",
):
    if needle not in coordinator:
        raise SystemExit(f"NetworkRecoveryCoordinator missing serialized recovery contract: {needle}")

for needle in (
    "TvNetworkLifecycle.recoveredGeneration()",
    "OkHttp.resetApiNetworkForResume()",
    "BaseLoader.get().clear(after)",
    "NetworkCapabilities.NET_CAPABILITY_INTERNET",
    "TvNetworkLifecycle.markRecovered(TvNetworkLifecycle.generation())",
):
    if needle not in adapter:
        raise SystemExit(f"FongMi adapter missing TV recovery contract: {needle}")

HARNESS = r"""
package com.fingmi.tvrecovery;

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
    harness = work / "com/fingmi/tvrecovery/NetworkRecoveryParityTest.java"
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
            "com.fingmi.tvrecovery.NetworkRecoveryParityTest",
        ],
        check=True,
    )
