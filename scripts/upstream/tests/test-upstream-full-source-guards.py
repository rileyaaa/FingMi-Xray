#!/usr/bin/env python3
"""Exercise the full-build SDK-free source-guard collector with injected failures.

The production workflow runs this stage before Android SDK installation/native
reconstruction. It must attempt every guard, report all independent failures,
and never let a failed guard proceed to costly packaging or publication.
"""
import os
from pathlib import Path
import re
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / '.github/workflows/04-上游一键升级.yml'
EXPECTED = (
    'tests/test-xray-android-runtime-compat.py',
    'tests/test-xray-core-parity.py',
    'tests/test-xray-playback-parity.py',
    'scripts/upstream/tests/test-xray-guarded-data-source.py',
    'scripts/upstream/tests/test-xray-playback-routing.py',
    'scripts/upstream/tests/test-xray-artwork-loader.py',
    'scripts/upstream/tests/test-upstream-playback-contract.py',
    'tests/test-xray-playback-address-parity.py',
    'tests/test-xray-session-races.py',
    'tests/test-xray-service-client-lifecycle.py',
    'tests/test-xray-normalizer-parity.py',
    'tests/test-xray-transport-security-parity.py',
    'tests/test-xray-tls-fragment.py',
    'tests/test-upstream-update-disabled.py',
    'scripts/build/check-elf-runtime.py',
    'scripts/build/check-final-apk-native.py',
    'scripts/build/check-final-apk-manifest.py',
    'tests/test-build-hygiene.py',
    'tests/test-resolve-release-tag.py',
    'tests/test-release-publication.py',
    'tests/test-resume-verified-release.py',
    'tests/test-media3-dex-linkage.py',
    'tests/test-player-candidate-linkage.py',
    'tests/test-libass-native-input.py',
    'tests/test-tv-network-recovery.py',
    'tests/test-xray-error-sanitizer.py',
    'tests/test-tv-recovery-intent-replay.py',
    'tests/test-xray-recovery-state-audit.py',
)

workflow = WORKFLOW.read_text(encoding='utf-8')
start = '      - name: 运行项目源码检查\n'
finish = '\n      - name: 准备 Android SDK 36 与 37\n'
assert workflow.count(start) == workflow.count(finish) == 1
step = workflow.split(start, 1)[1].split(finish, 1)[0]
assert 'if: ${{ inputs.apply_to_main || inputs.build_without_publish }}' in step
assert step.count('        run: |\n') == 1
script = textwrap.dedent(step.split('        run: |\n', 1)[1])
assert tuple(re.findall(r'^run_source_guard python3 ((?:scripts|tests)/[^\s]+\.py)(?: .*)?$', script, re.M)) == EXPECTED
assert script.count('source_guard_failed=0') == 1
assert 'if "$@"; then' in script
assert script.index('run_source_guard python3') < script.index('if [[ "$source_guard_failed" != "0" ]]')
assert 'No Android SDK/native build or publication.' in script
assert subprocess.run(['bash', '-n'], text=True, input=script, capture_output=True).returncode == 0

mock = '''python3() {
  printf 'CALLED %s\\n' "$1"
  if [[ ":$FAIL_TESTS:" == *":$1:"* ]]; then return 9; fi
  return 0
}
'''
for failures in ('', EXPECTED[1] + ':' + EXPECTED[19], EXPECTED[0] + ':' + EXPECTED[-1]):
    result = subprocess.run(
        ['bash', '-e', '-o', 'pipefail', '-c', mock + script],
        env={**os.environ, 'FAIL_TESTS': failures}, capture_output=True, text=True)
    called = re.findall(r'^CALLED (.+)$', result.stdout, re.M)
    assert called == list(EXPECTED), f'Incomplete source guard collection: {called}'
    assert (result.returncode == 0) == (not failures), result.stdout + result.stderr
    if failures:
        assert result.stdout.count('::error file=') == 2, result.stdout
        assert 'BLOCKED: full build source guards failed' in result.stderr
        assert 'No Android SDK/native build or publication' in result.stderr
    else:
        assert '::error' not in result.stdout
        assert 'BLOCKED:' not in result.stderr

print(f'PASS: {len(EXPECTED)} full-build source guards all run with simultaneous failures; fail closed before SDK/native')
