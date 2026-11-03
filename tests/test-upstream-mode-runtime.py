#!/usr/bin/env python3
"""Execute the *actual workflow Bash* for preview/build-only/formal modes.

No network, Android SDK, Actions credentials, release or remote Git push.
The candidate-commit tail is run in disposable local Git repositories.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/manual-upstream-sync.yml'


def shell(script, cwd, env, ok=True):
    result = subprocess.run(['bash', '-euo', 'pipefail', '-c', script], cwd=cwd,
                            env=env, text=True, capture_output=True)
    if ok and result.returncode:
        raise AssertionError(f'Workflow Bash failed: {result.stderr}\n{result.stdout}')
    return result


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


workflow = WORKFLOW.read_text(encoding='utf-8')
start = '      - name: Three-way merge and regenerate approved fork adapters\n'
finish = '\n      - name: Run fork source guards\n'
assert workflow.count(start) == 1 and workflow.count(finish) == 1
full = workflow.split(start, 1)[1].split(finish, 1)[0]
marker = '          git status --short\n'
assert full.count(marker) == 1, 'Candidate stage-commit anchor changed'
source = full.split(marker, 1)[1]
source = textwrap.dedent(source)
candidate = 'set -euo pipefail\ngit status --short\n' + source
assert candidate.count('git add -A') == 1
assert candidate.count('git diff --cached --check') == 1
assert candidate.index('git diff --cached --check') < candidate.index('if [[ "$BUILD_CANDIDATE" != "true" ]]')
assert candidate.index('if [[ "$BUILD_CANDIDATE" != "true" ]]') < candidate.index('git commit -m')
assert 'git push ' not in candidate and 'gh release ' not in candidate

preflight_start = '          if [[ "$APPLY_TO_MAIN" == "true" && "$BUILD_WITHOUT_PUBLISH" == "true" ]]; then\n'
assert workflow.count(preflight_start) == 1, 'Mode-exclusivity guard disappeared'
preflight_body = workflow.split(preflight_start, 1)[1].split('\n          fi\n', 1)[0]
preflight_script = 'set -euo pipefail\n' + textwrap.dedent(preflight_start + preflight_body + '\n          fi\n')

with tempfile.TemporaryDirectory(prefix='fingmi-upgrade-mode-runtime-') as directory:
    base = Path(directory)
    for apply, build_only in ((False, False), (False, True), (True, False)):
        name = f'apply-{apply}-buildonly-{build_only}'.lower()
        cwd = base / name
        cwd.mkdir()
        git(cwd, 'init', '-q')
        git(cwd, 'config', 'user.name', 'Integration Fixture')
        git(cwd, 'config', 'user.email', 'ci@example.invalid')
        (cwd / 'candidate.txt').write_text('old release\n', encoding='utf-8')
        git(cwd, 'add', '-A')
        git(cwd, 'commit', '-qm', 'previous source')
        original = git(cwd, 'rev-parse', 'HEAD')
        (cwd / 'candidate.txt').write_text('reviewed upstream\n', encoding='utf-8')
        temp = base / (name + '-runner-temp')
        temp.mkdir()
        (temp / 'fingmi-upstream-release-plan.json').write_text(
            json.dumps({'release_tag': 'v5.8.7-xray.1'}), encoding='utf-8')
        envfile = base / (name + '-github-env.txt')
        env = {**os.environ, 'APPLY_TO_MAIN': str(apply).lower(),
               'BUILD_WITHOUT_PUBLISH': str(build_only).lower(),
               'BUILD_CANDIDATE': str(apply or build_only).lower(),
               'UPSTREAM_TARGET': '3' * 40, 'RUNNER_TEMP': str(temp),
               'GITHUB_ENV': str(envfile)}
        first = shell(preflight_script, cwd, env)
        assert first.returncode == 0, name
        result = shell(candidate, cwd, env)
        sha = git(cwd, 'rev-parse', 'HEAD')
        if not apply and not build_only:
            assert sha == original, 'Preview committed candidate'
            assert git(cwd, 'diff', '--cached', '--name-only') == 'candidate.txt'
            assert not envfile.exists(), 'Preview requested build/release environment'
            assert 'Preview mode:' in result.stdout
        else:
            assert sha != original, 'Build-enabled mode skipped candidate commit'
            assert not git(cwd, 'diff', '--cached', '--name-only')
            assert git(cwd, 'log', '-1', '--format=%s') == 'chore(upstream): integrate FongMi TV ' + '3' * 40
            contents = envfile.read_text(encoding='utf-8')
            assert f'BUILD_SOURCE_SHA={sha}\n' in contents
            assert 'RELEASE_TAG=v5.8.7-xray.1\n' in contents
    invalid = {'APPLY_TO_MAIN': 'true', 'BUILD_WITHOUT_PUBLISH': 'true'}
    invalid_result = shell(preflight_script, base, {**os.environ, **invalid}, ok=False)
    assert invalid_result.returncode != 0 and 'Select only one' in invalid_result.stderr

print('PASS extracted workflow Bash: preview stages without commit; build-only/formal commit; invalid double-select rejected')
