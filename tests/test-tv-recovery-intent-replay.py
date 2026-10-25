#!/usr/bin/env python3
"""Execute the actual Home recovery callback and methods against a JVM UI boundary.

The coordinator is compiled unchanged. Home's callback, showContent and checkAction
are extracted from the selected source tree; this is not a full Android Activity test.
No network, Gradle, Android SDK, or third-party dependencies are used.
"""
from pathlib import Path
import argparse
import re
import shutil
import subprocess
import tempfile


def block(source: str, marker: str) -> str:
    start = source.index(marker)
    opening = source.index("{", start)
    depth = 0
    # These selected methods contain no braces in literals/comments. Fail loudly
    # if the source shape changes instead of silently testing a hand-written copy.
    for i in range(opening, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if not depth:
                return source[start:i + 1]
    raise ValueError(f"Unterminated source block: {marker}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not shutil.which("javac") or not shutil.which("java"):
        raise SystemExit("A JDK (javac and java) is required")
    root = args.repo.resolve()
    home = (root / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java").read_text()
    init = block(home, "protected void initView(Bundle savedInstanceState)")
    callbacks = re.findall(r"\(\)\s*->\s*\{([^{}]*)\}\);", init)
    if len(callbacks) != 1 or "getVideo();" not in callbacks[0]:
        raise SystemExit("Unexpected Home recovery callback shape; review the test extractor")
    show = block(home, "private void showContent()")
    action = block(home, "private void checkAction(Intent intent)")
    coordinator = root / "tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java"
    java = r'''
import java.util.ArrayDeque;
import java.util.function.Consumer;
import com.fingmi.tvrecovery.NetworkRecoveryCoordinator;

public final class HomeRecoveryIntentHarness {
    private final Binding mBinding = new Binding();
    private Intent intent;
    private int launches, refreshes, focuses;
    private Intent getIntent() { return intent; }
    private void setFocus() { focuses++; }
    private void getVideo() { refreshes++; }
    private void checkType(Intent ignored) { launches++; } // File/playlist UI boundary
    private Runnable recoveryCallback() { return () -> { CALLBACK }; }
    SHOW
    ACTION
    static final class Binding { final Progress progressLayout = new Progress(); }
    static final class Progress { int shown; void showContent() { shown++; } }
    static final class Intent {
        static final String ACTION_SEND="SEND", ACTION_VIEW="VIEW", ACTION_SEARCH="SEARCH";
        static final String EXTRA_TEXT="text";
        final String action, text; final Object data;
        Intent(String action, String text, Object data) { this.action=action; this.text=text; this.data=data; }
        String getAction() { return action; }
        String getStringExtra(String key) { return text; }
        Object getData() { return data; }
    }
    static final class SearchManager { static final String QUERY="query"; }
    static final class TextUtils { static boolean isEmpty(String s) { return s==null || s.isEmpty(); } }
    static final class VideoActivity { static void push(HomeRecoveryIntentHarness h,String s) { h.launches++; } }
    static final class SearchActivity { static void start(HomeRecoveryIntentHarness h,String s) { h.launches++; } }
    static final class PermissionUtil {
        static void requestFile(HomeRecoveryIntentHarness h, Consumer<Boolean> callback) { callback.accept(true); }
    }
    static final class Hooks implements NetworkRecoveryCoordinator.Hooks {
        long generation;
        int clears;
        Runnable clearDone;
        final ArrayDeque<Runnable> queue=new ArrayDeque<>();
        final Runnable refresh;
        Hooks(Runnable refresh) { this.refresh=refresh; }
        public long generation() { return generation; }
        public void cancelRequests() { }
        public void resetApiAndDns() { }
        public void clearSpiders(Runnable after) { clears++; clearDone=after; }
        public boolean networkReady() { return true; }
        public void schedule(Runnable r,long delay) { queue.add(r); }
        public void unschedule(Runnable r) { queue.removeIf(x -> x==r); }
        public void showProgress() { }
        public void refreshHome() { refresh.run(); }
        void finishClear() { Runnable r=clearDone; clearDone=null; r.run(); }
        void drain() {
            int max=50;
            while (!queue.isEmpty() && max-->0) queue.remove().run();
            if (max<=0) throw new AssertionError("Polling did not settle");
        }
    }
    public static void main(String[] args) {
        int failed=0, total=0;
        for (String action: new String[]{"MAIN","SEND","VIEW","SEARCH"}) {
            for (int cycles: new int[]{1,3}) {
                total++;
                HomeRecoveryIntentHarness h=new HomeRecoveryIntentHarness();
                h.intent=new Intent(action,"synthetic-local-test",new Object());
                h.showContent();
                int initial=h.launches;
                if (initial != (action.equals("MAIN")?0:1)) throw new AssertionError("Initial action lost");
                Hooks hooks=new Hooks(h.recoveryCallback());
                NetworkRecoveryCoordinator c=new NetworkRecoveryCoordinator(0,hooks);
                for (int i=1;i<=cycles;i++) {
                    hooks.generation=i; c.check(); c.check();
                    hooks.finishClear(); hooks.drain(); c.check();
                }
                boolean pass=h.launches==initial && h.refreshes==cycles
                        && h.focuses==cycles+1 && hooks.clears==cycles
                        && h.mBinding.progressLayout.shown==cycles+1;
                System.out.println((pass?"PASS":"FAIL")+" action="+action+" cycles="+cycles
                        +" extraLaunches="+(h.launches-initial)+" refreshes="+h.refreshes);
                if (!pass) failed++;
                c.close();
            }
        }
        System.out.println("Home callback cases="+total+" failures="+failed);
        if (failed>0) throw new AssertionError("Recovery replayed the original launch Intent");
    }
}
'''.replace("CALLBACK", callbacks[0]).replace("SHOW", show).replace("ACTION\n", action+"\n")
    with tempfile.TemporaryDirectory(prefix="tv-intent-audit-") as directory:
        temp=Path(directory)
        harness=temp / "HomeRecoveryIntentHarness.java"
        harness.write_text(java,encoding="utf-8")
        subprocess.run(["javac","-encoding","UTF-8","-d",str(temp),str(coordinator),str(harness)],check=True)
        subprocess.run(["java","-cp",str(temp),"HomeRecoveryIntentHarness"],check=True)

if __name__ == "__main__":
    main()
