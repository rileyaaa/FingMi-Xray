#!/usr/bin/env python3
"""Verify the new host/recovery batch without executing the known media gate."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from prepare_candidate import ROOT, LOCK, blob, guard_fork, overlay, verified_checkout


def method(text, signature):
    # Exact source anchors in the pinned inputs; braces here are plain Java.
    start = text.index(signature)
    brace = text.index("{", start)
    level = 1
    for pos in range(brace + 1, len(text)):
        if text[pos] == "{":
            level += 1
        elif text[pos] == "}":
            level -= 1
            if level == 0:
                return text[start:pos+1]
    raise AssertionError("Unbalanced method: " + signature)


def run(*args, cwd=None):
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-tv", type=Path, required=True)
    parser.add_argument("--tv", type=Path, required=True)
    parser.add_argument("--android", action="store_true")
    a = parser.parse_args()
    old, tv = a.old_tv.resolve(), a.tv.resolve()
    guard_fork()
    verified_checkout(old, "old_tv")
    verified_checkout(tv, "tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-host-batch-") as temp:
        work = Path(temp)
        candidate = work/"candidate"
        conflicts, manual = overlay(old, tv, candidate)
        home = "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java"
        vm = "app/src/main/java/com/fongmi/android/tv/model/SiteViewModel.java"
        runner = "app/src/main/java/com/fongmi/android/tv/model/ViewModelTaskRunner.java"
        http = "catvod/src/main/java/com/github/catvod/net/OkHttp.java"
        dns = "catvod/src/main/java/com/github/catvod/net/OkDns.java"
        img = "app/src/main/java/com/fongmi/android/tv/utils/ImgUtil.java"
        glide = "app/src/main/java/com/fongmi/android/tv/utils/OkGlideModule.java"
        loader = "app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java"
        required = {home,vm,runner,http,dns,img,glide,loader}
        required.update(row["path"] for row in LOCK["fork_scope"] if row["strategy"] in ("reviewed-recovery-host", "reviewed-live-host"))
        if required.intersection(conflicts + manual):
            raise AssertionError("Recovery host still has a scope conflict: " + str(required.intersection(conflicts + manual)))
        for row in LOCK["fork_scope"]:
            if row["strategy"] in ("reviewed-recovery-host", "reviewed-live-host", "recovery-loader-590"):
                assert blob(candidate/row["path"]) == row["resolved"]
        def text(path):
            return (candidate/path).read_text()
        def upstream(path):
            return (tv/path).read_text()
        # No replay of external ACTION_VIEW/SEND; retain service ownership on exit.
        for sig in ("private void consumeAction()", "public static void releaseResources()", "private void checkAction(Intent intent)"):
            assert method(text(home),sig) == method(upstream(home),sig), sig
        init = method(text(home),"protected void initView(Bundle savedInstanceState)")
        assert init.index("setAdapter();") < init.index("new FongMiNetworkRecovery(") < init.index("checkPermission();")
        assert "consumeAction()" not in init
        assert "actionReady && recoveryResumed && !isFinishing() && !isDestroyed()" in method(text(home),"private boolean canRecoverHome()")
        assert "if (canRecoverHome() && mNetworkRecovery != null)" in method(text(home),"private void checkNetworkGeneration()")
        assert "this::canRecoverHome" in init
        assert "recoveryResumed = false;" in method(text(home),"protected void onPause()")
        assert "recoveryResumed = false;" in method(text(home),"protected void onDestroy()")
        assert "tasks.cancel(TaskType.RESULT);" in method(text(vm),"public void cancelResultRequest()")
        assert "loadingHome = false;" in method(text(vm),"public void cancelResultRequest()")
        assert blob(candidate/runner) == blob(tv/runner)
        for sig in ("public static Call.Factory player(Auth.Context auth)", "static Request applyAuth(Request request, Auth.Context auth)", "public static synchronized OkHttpClient player()", "private static OkHttpClient.Builder getBuilder()"):
            assert method(text(http),sig) == method(upstream(http),sig), "upstream auth/player/redirect drift: " + sig
        reset = method(text(http),"public static void resetApiNetworkForResume()")
        assert "get().client = null;" in reset and "dns().resetForNetworkChange();" in reset and "cleanupClientAsync(oldClient);" in reset
        assert "player" not in reset and "selector().clear()" not in reset
        assert blob(candidate/dns) == blob(ROOT/dns)
        assert blob(candidate/glide) == blob(ROOT/glide)
        assert method(text(img),"public static void load(String text, String url, ImageView view, boolean vod)") == method(upstream(img),"public static void load(String text, String url, ImageView view, boolean vod)")
        assert "networkFailureEpoch.incrementAndGet();" in method(text(img),"public static void resetNetworkFailures()")
        assert "requestEpoch != networkFailureEpoch.get()" in text(img)
        print("PASS exact host recovery port; upstream Intent, request runner, auth/redirect, player client and image-load contracts retained", flush=True)
        run(sys.executable,ROOT/"tests/test-upstream-host-recovery.py","--candidate",candidate)
        run(sys.executable,ROOT/"tests/test-upstream-live-host.py","--candidate",candidate)
        run(sys.executable,ROOT/"tests/test-upstream-recovery-loader.py","--base-loader",tv/loader)
        # Exercise the actual transferred Xray core/session/normalizer sources.
        # Use only these module-level tests; old Live/PlayerManager host tests
        # must not be represented as passing on the unresolved 5.9.0 hosts.
        for rel in ("tests","recovery/legacy-src"):
            shutil.copytree(ROOT/rel,candidate/rel,dirs_exist_ok=True)
        for name in ("test-xray-normalizer-parity.py","test-xray-session-races.py","test-xray-playback-session-reentry.py"):
            run(sys.executable,candidate/"tests"/name)
        print("PASS transferred Xray Java module regressions; native/runtime/player host remain separate",flush=True)
        if a.android:
            lib = work/"android-library"
            lib.mkdir()
            for name in ("gradle","tv-recovery"):
                shutil.copytree((tv if name=="gradle" else candidate)/name,lib/name)
            for name in ("gradlew","gradle.properties","build.gradle"):
                shutil.copyfile(tv/name,lib/name)
            settings = re.sub(r"(?m)^include .*$","",(tv/"settings.gradle").read_text())
            (lib/"settings.gradle").write_text(settings+"\ninclude ':tv-recovery'\n")
            assert not (lib/"app").exists()
            run("bash",lib/"gradlew","--no-daemon","-Porg.gradle.java.installations.auto-download=false",":tv-recovery:assembleDebug",":tv-recovery:testDebugUnitTest",cwd=lib)
            print("PASS actual adapted Android recovery library compile and unit tests; no APK",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review; complete host/app/native gate not passed",flush=True)


if __name__ == "__main__":
    main()
