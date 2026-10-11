#!/usr/bin/env python3
"""Execute real recovery lifecycle registration after a cold external Activity."""
from pathlib import Path
import ast
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# Reuse only the Android/platform boundary doubles. Compile the current core
# and real host adapters again; the lifecycle algorithm is never copied here.
module_test = ast.parse((ROOT / 'tests/test-fork-module-boundaries.py').read_text())
stubs = next(ast.literal_eval(node.value) for node in module_test.body
             if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == 'STUBS'
                     for target in node.targets))
stubs.pop('RecoveryIntegrationTest.java')

HARNESS = r'''
import android.app.*;
import android.content.*;
import com.fingmi.integration.recovery.FongMiNetworkRecovery;
import com.fingmi.tvrecovery.TvNetworkLifecycle;
import com.fongmi.android.tv.App;
import com.fongmi.android.tv.api.loader.BaseLoader;
import com.fongmi.android.tv.service.DLNARendererService;

public class RecoveryColdEntryTest {
    static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    static void screenPair(Application app) {
        app.receiver.onReceive(app, new Intent(Intent.ACTION_SCREEN_OFF));
        app.receiver.onReceive(app, new Intent(Intent.ACTION_SCREEN_ON));
    }
    static int refreshes;
    static class EqualActivity extends Activity {
        @Override public boolean equals(Object other) { return other instanceof Activity; }
        @Override public int hashCode() { return 1; }
    }
    public static void main(String[] args) {
        boolean tv = args[0].equals("leanback");
        Application app = new Application();
        Activity coldLive = new Activity(), home = new Activity();
        // Exported Live starts without Home. It launches Home on Back; Home
        // registers the monitor before its own START, after Live's old START.
        check(app.lifecycle == null, "cold playback has not created Home's adapter");
        FongMiNetworkRecovery recovery = new FongMiNetworkRecovery(
                app, () -> {}, () -> {}, () -> true, () -> refreshes++);
        app.lifecycle.onActivityStarted(home);
        app.lifecycle.onActivityResumed(home);
        app.lifecycle.onActivityStopped(coldLive);
        app.lifecycle.onActivityDestroyed(coldLive);
        check(DLNARendererService.stops == 0, "unobserved Live STOP must not background visible Home");
        screenPair(app);
        check(TvNetworkLifecycle.generation() == 1, "visible Home must consume SCREEN OFF/ON after cold playback entry");
        check(DLNARendererService.stops == (tv ? 1 : 0), "only screen OFF stops the renderer");
        recovery.check(); BaseLoader.get().after.run(); app.network.capabilities.ready = true;
        App.tick(); App.tick();
        check(refreshes == 1 && TvNetworkLifecycle.recoveredGeneration() == 1,
                "cold-entry Home still performs and completes actual network recovery");

        // Distinct Activity identities stay counted even if equals/hashCode match.
        Activity a = new EqualActivity(), b = new EqualActivity();
        app.lifecycle.onActivityStarted(a); app.lifecycle.onActivityStarted(b);
        app.lifecycle.onActivityStopped(home); app.lifecycle.onActivityStopped(a);
        app.lifecycle.onActivityDestroyed(a);
        app.lifecycle.onActivityResumed(b);
        int stops = DLNARendererService.stops;
        app.lifecycle.onActivityStopped(a); // Duplicate retired callback.
        check(DLNARendererService.stops == stops, "duplicate STOP cannot consume another Activity");
        screenPair(app);
        check(TvNetworkLifecycle.generation() == 2, "distinct equal Activity remains foreground");

        app.lifecycle.onActivityStarted(b); // Duplicate START must not require two STOPs.
        app.lifecycle.onActivityStopped(b);
        app.lifecycle.onActivityDestroyed(b);
        app.lifecycle.onActivityStarted(home);
        app.lifecycle.onActivityResumed(home);
        check(TvNetworkLifecycle.generation() == 3, "one STOP retires a duplicate START");
        stops = DLNARendererService.stops;
        app.lifecycle.onActivityDestroyed(b);
        check(DLNARendererService.stops == stops, "late DESTROY cannot retire new owner");

        // Configuration recreation is still not a new background generation.
        home.changing = true;
        app.lifecycle.onActivityStopped(home); app.lifecycle.onActivityDestroyed(home);
        Activity recreated = new Activity();
        app.lifecycle.onActivityStarted(recreated); app.lifecycle.onActivityResumed(recreated);
        check(TvNetworkLifecycle.generation() == 3, "configuration recreation does not advance generation");

        // Defensive teardown releases an observed owner even if STOP was absent.
        // This does not add a callback for an unknown/non-started owner.
        app.lifecycle.onActivityDestroyed(recreated);
        app.lifecycle.onActivityStarted(home); home.changing = false;
        check(TvNetworkLifecycle.generation() == 4, "DESTROY retires a still-started reference");
        app.lifecycle.onActivityStopped(home); app.lifecycle.onActivityDestroyed(home);
        screenPair(app);
        check(TvNetworkLifecycle.generation() == 4, "no retained Activity makes background screen ON foreground");
        recovery.close();
        check(App.queue.isEmpty(), "closing Home removes its recovery poll");
        System.out.println("PASS " + args[0] + " cold external playback -> first Home, identity ownership, duplicate callbacks, configuration recreation and destroy cleanup");
    }
}
'''

with tempfile.TemporaryDirectory(prefix='tv-recovery-cold-entry-') as directory:
    work = Path(directory)
    sources = []
    for name, text in {**stubs, 'RecoveryColdEntryTest.java': HARNESS}.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        sources.append(str(path))
    core = ROOT / 'tv-recovery/src/main/java/com/fingmi/tvrecovery'
    adapter = ROOT / 'app/src/main/java/com/fingmi/integration/recovery/FongMiNetworkRecovery.java'
    for flavor in ('leanback', 'mobile'):
        classes = work / flavor
        subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '17', '-d', str(classes),
                        *sources, *(str(p) for p in core.glob('*.java')), str(adapter),
                        str(ROOT / f'app/src/{flavor}/java/com/fingmi/integration/recovery/TvDlnaLifecycle.java')], check=True)
        subprocess.run(['java', '-cp', str(classes), 'RecoveryColdEntryTest', flavor], check=True)
