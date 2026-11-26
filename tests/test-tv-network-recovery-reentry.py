#!/usr/bin/env python3
"""Real JVM test of TV network recovery teardown/reentrancy, without Android.

Compiles the actual NetworkRecoveryCoordinator.java with javac --release 17,
plus a deterministic scheduler/owner-lifecycle test double. A green result
is not a real device, DLNA, Activity, Home UI or Gradle integration proof.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java'
HARNESS = HERE / 'tv-recovery/RecoveryReentryHarness.java'

MUTATIONS = (
    ('ignore initial generation close',
     '        long next = hooks.generation();\n        if (closed) return;',
     '        long next = hooks.generation();'),
    ('continue after owner close during unschedule',
     '        hooks.unschedule(poll);\n        if (closed) return;',
     '        hooks.unschedule(poll);'),
    ('continue after progress closed owner',
     '        hooks.showProgress();\n        if (closed) return;',
     '        hooks.showProgress();'),
    ('continue after request cancellation closed owner',
     '        hooks.cancelRequests();\n        if (closed) return;',
     '        hooks.cancelRequests();'),
    ('continue after resetting DNS closed owner',
     '        hooks.resetApiAndDns();\n        if (closed) return;',
     '        hooks.resetApiAndDns();'),
    ('orphan immediate stability poll on close',
     '            hooks.schedule(poll, 0);\n            // schedule() may synchronously retire Home before posting.\n            if (closed) hooks.unschedule(poll);',
     '            hooks.schedule(poll, 0);'),
    ('read network state after generation callback retired owner',
     '        long latest = hooks.generation();\n        if (closed || !recovering) return;',
     '        long latest = hooks.generation();'),
    ('schedule after network readiness callback retired owner',
     '        boolean ready = hooks.networkReady();\n        if (closed || !recovering) return;',
     '        boolean ready = hooks.networkReady();'),
    ('orphan delayed stability poll on close',
     '            hooks.schedule(poll, 500L);\n            if (closed) hooks.unschedule(poll);',
     '            hooks.schedule(poll, 500L);'),
    ('read Home state after commit generation callback retired owner',
     '        long commitGeneration = hooks.generation();\n        if (closed) return;',
     '        long commitGeneration = hooks.generation();'),
    ('accept duplicate spider completion',
     '            if (closed || !recovering || pendingGeneration != next || !awaitingSpiderCompletion) return;',
     '            if (closed || !recovering || pendingGeneration != next) return;'),
    ('repeat unschedule on duplicate close',
     '    @Override public void close() {\n        if (closed) return;',
     '    @Override public void close() {'),
    ('start recovery while Home is hidden',
     '        if (!hooks.canRecoverHome() || closed) return;\n        pendingGeneration = next;',
     '        pendingGeneration = next;'),
    ('poll hidden Home',
     '        if (deferForHome()) return;\n        if (latest != pendingGeneration) {',
     '        if (latest != pendingGeneration) {'),
    ('commit hidden Home',
     '        if (deferForHome()) return;\n        appliedGeneration = pendingGeneration;',
     '        appliedGeneration = pendingGeneration;'),
    ('resume deferred poll while Home is hidden',
     '            if (!waitingForHome || !hooks.canRecoverHome() || closed) return;',
     '            if (!waitingForHome || closed) return;'),
    ('reuse pre-pause stability sample',
     '            waitingForHome = false;\n            checks = 0;\n            stableChecks = 0;',
     '            waitingForHome = false;\n            checks = 0;'),
    ('commit stale generation after readiness callback',
     '        if (commitGeneration != pendingGeneration) {',
     '        if (false) {'),
)


def run(candidate: str | None = None) -> subprocess.CompletedProcess[str]:
    for path in (SOURCE, HARNESS):
        if not path.is_file():
            raise AssertionError('Missing actual TV recovery source/fixture: ' + str(path))
    with tempfile.TemporaryDirectory(prefix='fingmi-tv-recovery-jvm-') as folder:
        root = Path(folder)
        actual = SOURCE
        if candidate is not None:
            actual = root / 'NetworkRecoveryCoordinator.java'
            actual.write_text(candidate, encoding='utf-8')
        classes = root / 'classes'
        classes.mkdir()
        compiled = subprocess.run(
            ['javac', '--release', '17', '-Xlint:all', '-d', str(classes), str(actual), str(HARNESS)],
            capture_output=True, text=True)
        if compiled.returncode:
            raise AssertionError('TV network recovery JDK compile failed:\n' + compiled.stderr)
        return subprocess.run(
            ['java', '-ea', '-cp', str(classes),
             'com.fingmi.tvrecovery.RecoveryReentryHarness'],
            capture_output=True, text=True, timeout=25)


def main() -> None:
    version = subprocess.run(['javac', '-version'], capture_output=True, text=True, check=True)
    if not re.search(r'\b21\.', version.stdout + version.stderr):
        raise RuntimeError('JDK21 required for the TV recovery source regression')
    base = run()
    match = re.fullmatch(
        r'PASS: (\d+) owner teardown/TV network recovery lifecycle assertions with actual Java Coordinator',
        base.stdout.strip())
    if base.returncode or not match or int(match.group(1)) < 143:
        raise AssertionError('TV recovery baseline failed:\n' + base.stdout + base.stderr)
    print(base.stdout.strip())
    original = SOURCE.read_text(encoding='utf-8')
    for label, before, _ in MUTATIONS:
        if original.count(before) != 1:
            raise AssertionError('TV recovery mutation anchor missing/ambiguous: ' + label)
    accepted = []
    for label, before, after in MUTATIONS:
        try:
            broken = run(original.replace(before, after))
        except (AssertionError, subprocess.TimeoutExpired) as error:
            accepted.append(label + ': did not execute cleanly: ' + str(error))
            continue
        if broken.returncode == 0 or 'AssertionError' not in broken.stderr:
            accepted.append(label + ': not rejected by a JVM assertion: '
                            + (broken.stderr or broken.stdout)[-1200:])
    if accepted:
        raise AssertionError(f'{len(MUTATIONS)-len(accepted)}/{len(MUTATIONS)} mutations rejected: '
                             + '\n'.join(accepted))
    print(f'PASS: {len(MUTATIONS)} TV network recovery lifecycle mutations rejected '
          '(real Java / deterministic JDK scheduler, no Android)')


if __name__ == '__main__':
    main()
