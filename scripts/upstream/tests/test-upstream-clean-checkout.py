#!/usr/bin/env python3
"""Prevent Python adapter tests from dirtying an Actions preview checkout.

Regression for failed run 41491400912: all 13 local adapter tests passed,
then the next step silently exited before fetching the public upstream.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
adapter = (ROOT / "scripts/upstream/build_policy_adapters.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/04-上游一键升级.yml").read_text(encoding="utf-8")

for pattern in ("__pycache__/", "*.py[cod]"):
    assert pattern in ignore.splitlines(), "Current checkout does not ignore " + pattern
    assert '"' + pattern + '"' in adapter, "Upgraded checkout does not preserve " + pattern
assert 'PYTHONDONTWRITEBYTECODE: "1"' in workflow, "Manual preview still emits Python bytecode"
assert "BLOCKED: local upgrade tests modified or left files" in workflow
assert "git status --short --untracked-files=all" in workflow

with tempfile.TemporaryDirectory(prefix="fingmi-clean-checkout-") as td:
    root = Path(td)
    (root / ".gitignore").write_text(ignore, encoding="utf-8")
    (root / "helper.py").write_text("value = 42\n", encoding="utf-8")
    (root / "runner.py").write_text("import helper\nassert helper.value == 42\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=check@example.invalid",
                    "commit", "-qm", "baseline"], cwd=root, check=True)

    # Reproduce the previous failure path: Python normally creates caches.
    # They must never make a Git checkout appear modified.
    child_env = os.environ.copy()
    child_env.pop("PYTHONDONTWRITEBYTECODE", None)
    subprocess.run([sys.executable, "runner.py"], cwd=root, env=child_env, check=True)
    assert (root / "__pycache__").is_dir(), "Control did not generate Python bytecode"
    status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root)
    assert not status, "Python cache dirties checkout: " + status.decode()

    shutil.rmtree(root / "__pycache__")
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run([sys.executable, "runner.py"], cwd=root, env=child_env, check=True)
    assert not (root / "__pycache__").exists(), "Bytecode prevention did not work"
    status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root)
    assert not status, "Preview checkout no longer remains clean: " + status.decode()

print("PASS upgrade preview checkout: ignored Python caches, suppressed bytecode, clean Git status")
