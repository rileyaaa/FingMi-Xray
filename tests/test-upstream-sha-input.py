#!/usr/bin/env python3
"""Offline regression for tab/whitespace in the workflow_dispatch SHA input."""
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
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

print("PASS upstream SHA: trim pasted leading/trailing whitespace, reject inner whitespace/bad hex")
