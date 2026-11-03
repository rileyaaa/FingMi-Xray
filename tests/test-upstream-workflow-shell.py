#!/usr/bin/env python3
"""Fail before spending AC time on malformed workflow Bash or broken preflight iteration.

Uses only Python stdlib and bash, and executes an extracted workflow test loop
with mocked subprocesses, never contacting GitHub or changing source files.
"""
import os
from pathlib import Path
import re
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/manual-upstream-sync.yml'
EXPECTED = (
    'tests/test-upstream-exo-adapters.py',
    'tests/test-upstream-side-requests.py',
    'tests/test-upstream-live-metadata.py',
    'tests/test-upstream-xray-resources.py',
    'tests/test-upstream-activity-adapters.py',
    'tests/test-upstream-build-policy.py',
    'tests/test-upstream-phone-import.py',
    'tests/test-upstream-real-hooks.py',
)


def run_blocks(yaml):
    """Get literal run: | YAML blocks without a third-party YAML dependency."""
    lines = yaml.splitlines()
    blocks = []
    for i, line in enumerate(lines):
        m = re.fullmatch(r'( *)run: \|\s*', line)
        if not m:
            continue
        width = len(m[1]) + 2
        result = []
        for original in lines[i + 1:]:
            if not original.strip():
                result.append('')
                continue
            indent = len(original) - len(original.lstrip(' '))
            if indent < width:
                break
            result.append(original[width:])
        blocks.append((i + 1, '\n'.join(result) + '\n'))
    return blocks


def validate(yaml):
    blocks = run_blocks(yaml)
    assert len(blocks) >= 15, f'Expected many workflow shell blocks, got {len(blocks)}'
    for line, script in blocks:
        check = subprocess.run(['bash', '-n'], text=True, input=script,
                               capture_output=True)
        assert check.returncode == 0, f'Bash syntax at YAML run: | line {line}: {check.stderr}'

    start = '          upstream_preflight_failed=0\n'
    end = '          python3 scripts/upstream/sync.py'
    assert yaml.count(start) == 1 and yaml.count(end) == 1
    body = yaml.split(start, 1)[1].split(end, 1)[0]
    script = textwrap.dedent(start + body)
    assert tuple(re.findall(r'^  (tests/test-upstream-[^\s]+\.py)$', script, re.M)) == EXPECTED
    for fail in ('', 'tests/test-upstream-side-requests.py:tests/test-upstream-build-policy.py'):
        wrapper = (
            'python3() {\n'
            '  printf "CALLED %s\\n" "$1"\n'
            '  if [[ ":$FAIL_TESTS:" == *":$1:"* ]]; then return 9; fi\n'
            '  return 0\n'
            '}\n'
        )
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', wrapper + script],
                                env={**os.environ, 'FAIL_TESTS': fail,
                                     'UPSTREAM_DIRECTORY': '/unused', 'UPSTREAM_TARGET': '0' * 40},
                                text=True, capture_output=True)
        called = re.findall(r'^CALLED (.+)$', result.stdout, re.M)
        assert called == list(EXPECTED), f'Not every public adapter tested once: {called}'
        assert (result.returncode == 0) == (not fail), (
            'Preflight should fail only when some adapter check fails', result.stdout, result.stderr
        )
        if fail:
            assert result.stdout.count('::error file=') == 2, result.stdout
            assert 'BLOCKED: public upstream adapter preflight found errors' in result.stderr

    # The second collector runs only after candidate generation. Simulate it
    # separately to ensure all independent source gates are attempted.
    guard_start = '          generated_guard_failed=0\n'
    guard_end = '          git diff --check'
    assert yaml.count(guard_start) == 1 and yaml.count(guard_end) == 1
    guard_body = yaml.split(guard_start, 1)[1].split(guard_end, 1)[0]
    guard_script = textwrap.dedent(guard_start + guard_body)
    expected_guards = (
        'scripts/upstream/verify_playback.py',
        'tests/test-upstream-playback-contract.py',
        'tests/test-upstream-playback-ownership.py',
        'tests/test-upstream-update-disabled.py',
        'tests/test-build-hygiene.py',
        'tests/test-tv-network-recovery.py',
    )
    assert tuple(re.findall(r'^  ((?:scripts|tests)/[^\s]+\.py)$', guard_script, re.M)) == expected_guards
    for fail in ('', 'tests/test-upstream-playback-contract.py:tests/test-build-hygiene.py'):
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', wrapper + guard_script],
                                env={**os.environ, 'FAIL_TESTS': fail}, text=True, capture_output=True)
        called = re.findall(r'^CALLED (.+)$', result.stdout, re.M)
        assert called == list(expected_guards), f'Not all candidate source gates were run: {called}'
        assert (result.returncode == 0) == (not fail), result.stdout + result.stderr
        if fail:
            assert result.stdout.count('::error file=') == 2, result.stdout
            assert 'BLOCKED: upgraded source gates found errors' in result.stderr

    return len(blocks)


if __name__ == '__main__':
    print(f'PASS: {validate(WORKFLOW.read_text(encoding="utf-8"))} Bash run blocks parse; '
          'all 8 upstream API checks and 6 candidate source guards execute under simultaneous failures')
