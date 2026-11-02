#!/usr/bin/env python3
"""Fixture-based offline tests of the fail-closed FongMi upstream sync engine."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

MODULE = Path(__file__).resolve().parents[1] / "scripts/upstream/sync.py"
spec = importlib.util.spec_from_file_location("fingmi_sync", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def put(root, name, value):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8")


def fixture(tmp):
    up = tmp / "up"
    up.mkdir()
    git(up, "init")
    git(up, "config", "user.name", "test")
    git(up, "config", "user.email", "test@example.invalid")
    put(up, "app/build.gradle", 'versionCode 563\nversionName "5.6.3"\n')
    put(up, "app/src/main/java/A.java", "top\nkeep\nbottom\n")
    put(up, "catvod/del.txt", "old\n")
    put(up, "catvod/conflict.txt", "alpha\nbeta\n")
    put(up, "README.md", "old upstream README\n")
    git(up, "add", ".")
    git(up, "commit", "-m", "base")
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=up, text=True).strip()
    put(up, "app/build.gradle", 'versionCode 587\nversionName "5.8.7"\n')
    put(up, "app/src/main/java/A.java", "top changed\nkeep\nbottom\n")
    put(up, "catvod/conflict.txt", "alpha changed upstream\nbeta\n")
    (up / "catvod/del.txt").unlink()
    put(up, "nodejs/build.gradle", "new module\n")
    put(up, "README.md", "new upstream README\n")
    git(up, "add", "-A")
    git(up, "commit", "-m", "target")
    target = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=up, text=True).strip()
    local = tmp / "local"
    local.mkdir()
    put(local, mod.BASELINE, json.dumps({"repository": "FongMi/TV", "branch": "fongmi", "commit": base, "version": "5.6.3"}))
    put(local, "app/build.gradle", 'versionCode 563\nversionName "5.6.3"\n')
    put(local, "app/src/main/java/A.java", "top\nkeep\nbottom changed fork\n")
    put(local, "catvod/del.txt", "old\n")
    put(local, "catvod/conflict.txt", "alpha\nbeta\n")
    put(local, "README.md", "fork README\n")
    put(local, "signing/private.properties", "secret stays local\n")
    return up, local, target


with tempfile.TemporaryDirectory() as td:
    up, local, target = fixture(Path(td))
    report = Path(td) / "report.json"
    assert mod.sync(local, up, target, report) == 0
    assert (local / "app/src/main/java/A.java").read_text() == "top changed\nkeep\nbottom changed fork\n"
    assert not (local / "catvod/del.txt").exists()
    assert (local / "nodejs/build.gradle").read_text() == "new module\n"
    assert (local / "README.md").read_text() == "fork README\n"
    assert (local / "signing/private.properties").read_text() == "secret stays local\n"
    assert json.loads((local / mod.BASELINE).read_text())["commit"] == target
    assert json.loads(report.read_text())["status"] == "prepared"

with tempfile.TemporaryDirectory() as td:
    up, local, target = fixture(Path(td))
    report = Path(td) / "blocked.json"
    put(local, "catvod/conflict.txt", "alpha changed fork\nbeta\n")
    old_lock = (local / mod.BASELINE).read_bytes()
    old_app = (local / "app/build.gradle").read_bytes()
    assert mod.sync(local, up, target, report) == 2
    assert (local / mod.BASELINE).read_bytes() == old_lock
    assert (local / "app/build.gradle").read_bytes() == old_app
    assert not (local / "nodejs/build.gradle").exists()
    assert json.loads(report.read_text())["conflicts"]

print("PASS: no-conflict sync, fork overlay, excluded files, and fail-closed atomic conflict")
