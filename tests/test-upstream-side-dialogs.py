#!/usr/bin/env python3
"""Test only the pinned 5.9 dialog request-owner methods, not full Android UI."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/upstream-adaptation"))
from prepare_candidate import LOCK, blob, guard_fork, overlay, verified_checkout
from verify_recovery_batch import method

FIXTURE = r'''
import java.util.function.BiFunction;
class OkHttpClient {}
class OkHttp {
    static final OkHttpClient api = new OkHttpClient(), player = new OkHttpClient();
    static OkHttpClient client() { return api; }
    static OkHttpClient player() { return player; }
}
class PlayerManager {
    OkHttpClient proxy;
    boolean suspended;
    OkHttpClient getPlaybackHttpClient(OkHttpClient fallback) {
        return proxy == null ? fallback : proxy;
    }
    boolean isXrayPlaybackSuspended() { return suspended; }
}
class PlaybackDialog {
    static PlayerManager current;
    static boolean isCurrentPlayer(Object view, PlayerManager owner) { return owner == current; }
}
class SubtitleApi {
    static int current = -1;
    static void cancel(int id) { if (id == current) current = -1; }
}
class DanmakuApi {
    static int current = -1;
    static void cancel(int id) { if (id == current) current = -1; }
}
class Adapter { int getItemCount() { return 0; } }
class Scroller { void endLoading(boolean more) {} }
public class DialogHarness {
    static int assertions;
    static void check(boolean value, String message) {
        assertions++;
        if (!value) throw new AssertionError(message);
    }
    // Both test classes embed exact methods from the generated candidate.
    __CLASSES__
    public static void main(String[] args) {
        __TESTS__
        System.out.println("PASS actual 5.9 dialog request-owner methods: " + assertions + " assertions");
    }
}
'''
BASE = "app/src/main/java/com/fongmi/android/tv/ui/dialog/"
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-tv", type=Path, required=True)
    parser.add_argument("--tv", type=Path, required=True)
    a = parser.parse_args()
    guard_fork()
    old, tv = a.old_tv.resolve(), a.tv.resolve()
    verified_checkout(old, "old_tv")
    verified_checkout(tv, "tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-dialog-") as tmp:
        root = Path(tmp)
        candidate = root/"candidate"
        conflicts, manual = overlay(old, tv, candidate)
        classes, tests = [], []
        for name, api, fallback in (("SubtitleSearchDialog", "SubtitleApi", "api"),
                                    ("DanmakuSearchDialog", "DanmakuApi", "player")):
            path = BASE+name+".java"
            row = next(x for x in LOCK["fork_scope"] if x["path"] == path)
            assert path not in conflicts+manual and blob(candidate/path) == row["resolved"], path
            src = (candidate/path).read_text()
            assert api+".cancel()" not in src, path
            assert "cancelRequest();" in method(src, "public void onDestroyView()"), path
            assert "this.player != null && this.player != player" in method(src, "private void bindPlayer(PlayerManager player)"), path
            methods = "\n".join(method(src, sig) for sig in (
                "private void cancelRequest()", "private void onXrayTransitionCancelled(long generation)",
                "private void requestWithPlaybackClient(BiFunction<OkHttpClient, Runnable, Integer> request)"))
            classes.append("""
            static class %s {
                PlayerManager player;
                Object binding = new Object();
                int requestId = -1, results, started;
                long requestGeneration;
                final Adapter adapter = new Adapter();
                final Scroller scroller = new Scroller();
                Runnable completion;
                OkHttpClient chosen;
                void showResults(boolean empty) { results++; }
                void start(int id) { requestWithPlaybackClient((client, done) -> {
                    chosen = client; completion = done; started++; %s.current = id; return id;
                }); }
                %s
            }
            """ % (name, api, methods))
            tests.append("""
            {
                PlayerManager owner = new PlayerManager();
                PlaybackDialog.current = owner;
                %s d = new %s();
                d.player = owner;
                d.start(1);
                check(d.chosen == OkHttp.%s, "normal route");
                Runnable old = d.completion;
                owner.proxy = new OkHttpClient();
                d.start(2);
                check(d.chosen == owner.proxy && d.requestId == 2, "proxy route");
                old.run();
                check(d.results == 0 && d.requestId == 2 && %s.current == 2, "stale completion");
                d.completion.run();
                check(d.results == 1 && d.requestId == -1 && %s.current == -1, "current completion");
                owner.suspended = true;
                d.start(3);
                check(d.started == 2 && d.results == 2, "suspended does not fall back");
                owner.suspended = false;
                d.start(4);
                %s other = new %s();
                other.player = owner;
                other.start(5);
                d.cancelRequest();
                check(%s.current == 5 && other.requestId == 5, "old view cannot cancel new request");
                PlaybackDialog.current = new PlayerManager();
                d.start(6);
                check(d.started == 3 && %s.current == 5, "retired owner cannot issue");
                other.binding = null;
                other.completion.run();
                check(other.results == 0, "destroyed view ignored");
            }
            """ % (name, name, fallback, api, api, name, name, api, api))
        java = FIXTURE.replace("__CLASSES__", "\n".join(classes)).replace("__TESTS__", "\n".join(tests))
        src = root/"DialogHarness.java"
        src.write_text(java)
        subprocess.run(["javac", "--release", "17", str(src)], check=True)
        subprocess.run(["java", "-cp", str(root), "DialogHarness"], check=True)
        # One mutation proves the stale UI completion assertion is sensitive.
        bad = java.replace("generation != requestGeneration || binding == null", "binding == null")
        assert bad != java
        src.write_text(bad)
        subprocess.run(["javac", "--release", "17", str(src)], check=True)
        r = subprocess.run(["java", "-cp", str(root), "DialogHarness"], text=True, capture_output=True)
        assert r.returncode != 0 and "stale completion" in r.stderr, r.stderr
        print("PASS dialog generation negative control; deterministic UI/API boundaries, not Android linkage", flush=True)
        print("REMAINING_SCOPE", len(conflicts), "unresolved", len(manual), "old-media-review", flush=True)

if __name__ == "__main__":
    main()
