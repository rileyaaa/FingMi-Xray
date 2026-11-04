#!/usr/bin/env python3
"""Offline regression for tab/whitespace in the workflow_dispatch SHA input."""
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/upstream/normalize_sha.py"
spec = importlib.util.spec_from_file_location("normalize_sha", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SHA = "305dff233cde512e2c83f71529b7c3ecfd61fefc"

for raw in ("", " \t\r\n "):
    assert module.normalize_sha(raw) == ""
for raw in (SHA, "\t" + SHA, " \t" + SHA + "\r\n ", SHA.upper()):
    assert module.normalize_sha(raw) == SHA, repr(raw)
    run = subprocess.run([sys.executable, str(SCRIPT), raw], text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == SHA
for bad in ("0" * 39, "0" * 41, "not a SHA", "123 " + SHA,
            SHA[:20] + "\t" + SHA[20:], SHA[:-1] + "g", "refs/heads/fongmi"):
    try:
        module.normalize_sha(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("accepted malformed SHA: " + repr(bad))
    run = subprocess.run([sys.executable, str(SCRIPT), bad], text=True, capture_output=True)
    assert run.returncode != 0, repr(bad)
    assert "BLOCKED:" in run.stderr, (bad, run.stderr)

# The working Actions step must actually consume the normalizer. Merely
# shipping a tested helper must not count as protecting workflow_dispatch.
workflow = (ROOT / ".github/workflows/04-上游一键升级.yml").read_text(encoding="utf-8")
normalized_command = 'EXPECTED_SHA="$(python3 scripts/upstream/normalize_sha.py "$EXPECTED_SHA")"'
assert workflow.count(normalized_command) == 1
start = workflow.index("- name: 获取公开 FongMi/TV 基线及最新源码")
end = workflow.index("- name: 三方同步上游并重新生成适配代码", start)
fetch_step = workflow[start:end]
assert fetch_step.index(normalized_command) < fetch_step.index('if [[ -n "$EXPECTED_SHA"')
assert fetch_step.index(normalized_command) < fetch_step.index("git -C \"$upstream\" fetch")

# Exercise the exact Bash assignment + SHA comparison with the real pasted-tab
# value from failed run 41554240822. This is not an AC job.
bash_script = normalized_command + '\n[[ "$EXPECTED_SHA" == "$TARGET_SHA" ]]\n'
for raw in (SHA, "\t" + SHA, " \t" + SHA + "\r\n "):
    run = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", bash_script],
                         cwd=ROOT, env={**__import__("os").environ, "EXPECTED_SHA": raw,
                                        "TARGET_SHA": SHA}, text=True, capture_output=True)
    assert run.returncode == 0, (repr(raw), run.stderr)
for raw in (SHA[:20] + "\t" + SHA[20:], "not-a-sha"):
    run = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", bash_script],
                         cwd=ROOT, env={**__import__("os").environ, "EXPECTED_SHA": raw,
                                        "TARGET_SHA": SHA}, text=True, capture_output=True)
    assert run.returncode != 0, repr(raw)

print("PASS upstream SHA: pasted-tab regression, invalid inputs, and actual workflow Bash wiring")
