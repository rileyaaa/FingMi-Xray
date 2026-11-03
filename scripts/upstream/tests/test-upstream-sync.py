#!/usr/bin/env python3
"""Fixture-based offline regression for the upstream-first, fail-closed sync engine."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

MODULE = Path(__file__).resolve().parents[3] / "scripts/upstream/sync.py"
spec = importlib.util.spec_from_file_location("fingmi_sync", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.PIPE).strip()


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def fixture(tmp):
    up = tmp / "up"
    up.mkdir()
    git(up, "init")
    git(up, "config", "user.name", "test")
    git(up, "config", "user.email", "test@example.invalid")
    original = {
        "app/build.gradle": 'versionCode 563\nversionName "5.6.3"\n',
        "app/src/main/java/A.java": "top\nkeep\nbottom\n",
        "catvod/del.txt": "old\n",
        "catvod/conflict.txt": "alpha\nbeta\n",
        "catvod/official.txt": "old upstream implementation\n",
        "catvod/unchanged.txt": "baseline only\n",
        "README.md": "public README\n",
    }
    for name, content in original.items():
        put(up, name, content)
    git(up, "add", ".")
    git(up, "commit", "-m", "base")
    base = git(up, "rev-parse", "HEAD")
    put(up, "app/build.gradle", 'versionCode 587\nversionName "5.8.7"\n')
    put(up, "app/src/main/java/A.java", "top changed\nkeep\nbottom\n")
    put(up, "catvod/conflict.txt", "alpha changed upstream\nbeta\n")
    put(up, "catvod/official.txt", "new upstream implementation\n")
    (up / "catvod/del.txt").unlink()
    put(up, "nodejs/build.gradle", "new module\n")
    git(up, "add", "-A")
    git(up, "commit", "-m", "target")
    target = git(up, "rev-parse", "HEAD")

    local = tmp / "local"
    local.mkdir()
    put(local, mod.BASELINE, json.dumps({"repository": "FongMi/TV", "branch": "fongmi",
                                        "commit": base, "version": "5.6.3"}))
    for name, content in original.items():
        put(local, name, content)
    put(local, "app/src/main/java/A.java", "top\nkeep\nbottom changed fork\n")
    put(local, "catvod/official.txt", "old fork subtitle-only workaround\n")
    put(local, "README.md", "private fork README\n")
    put(local, "signing/private.properties", "secret stays local\n")

    manifest = {
        "schema": 1, "upstream_repository": "FongMi/TV", "baseline_commit": base,
        "files": {
            "app/build.gradle": {"strategy": "generate", "scope": "build"},
            "app/src/main/java/A.java": {"strategy": "rebase", "scope": "xray"},
            "catvod/official.txt": {"strategy": "upstream", "scope": "upstream"},
            "catvod/conflict.txt": {"strategy": "rebase", "scope": "xray"},
            "README.md": {"strategy": "project", "scope": "repository"},
        },
    }
    put(local, mod.SCOPE_MANIFEST, json.dumps(manifest))
    return up, local, target


# Standard update: rebase independent Xray edits, drop obsolete fork workaround,
# apply upstream added/removed files, preserve private files and policy docs.
with tempfile.TemporaryDirectory() as td:
    up, local, target = fixture(Path(td))
    report = Path(td) / "report.json"
    assert mod.sync(local, up, target, report) == 0
    assert (local / "app/src/main/java/A.java").read_text() == "top changed\nkeep\nbottom changed fork\n"
    assert (local / "catvod/official.txt").read_text() == "new upstream implementation\n"
    assert (local / "app/build.gradle").read_text() == 'versionCode 563\nversionName "5.6.3"\n'
    assert not (local / "catvod/del.txt").exists()
    assert (local / "nodejs/build.gradle").read_text() == "new module\n"
    assert (local / "README.md").read_text() == "private fork README\n"
    assert (local / "signing/private.properties").read_text() == "secret stays local\n"
    assert json.loads((local / mod.BASELINE).read_text())["commit"] == target
    assert json.loads((local / mod.SCOPE_MANIFEST).read_text())["baseline_commit"] == target
    result = json.loads(report.read_text())
    assert result["status"] == "prepared"
    assert result["upstream_first_paths"] == ["catvod/official.txt"]
    assert result["unreviewed_fork_drift"] == []

# Conflicts must not write even the unrelated upstream-only source.
with tempfile.TemporaryDirectory() as td:
    up, local, target = fixture(Path(td))
    report = Path(td) / "blocked.json"
    put(local, "catvod/conflict.txt", "alpha changed fork\nbeta\n")
    before = [(local / p).read_bytes() for p in (
        mod.BASELINE, mod.SCOPE_MANIFEST, "catvod/official.txt", "app/build.gradle")]
    assert mod.sync(local, up, target, report) == 2
    assert [(local / p).read_bytes() for p in (
        mod.BASELINE, mod.SCOPE_MANIFEST, "catvod/official.txt", "app/build.gradle")] == before
    assert not (local / "nodejs/build.gradle").exists()
    assert json.loads(report.read_text())["conflicts"]

# A fork edit to a path NOT in the reviewed scope must never be silently
# carried into the new baseline, including a file untouched by upstream.
with tempfile.TemporaryDirectory() as td:
    up, local, target = fixture(Path(td))
    report = Path(td) / "unreviewed.json"
    put(local, "catvod/unchanged.txt", "unknown local change\n")
    assert mod.sync(local, up, target, report) == 2
    result = json.loads(report.read_text())
    assert result["unreviewed_fork_drift"] == ["catvod/unchanged.txt"]
    assert not (local / "nodejs/build.gradle").exists()
    assert (local / "catvod/unchanged.txt").read_text() == "unknown local change\n"

# A stale or unclassified manifest must stop before any write.
with tempfile.TemporaryDirectory() as td:
    up, local, target = fixture(Path(td))
    path = local / mod.SCOPE_MANIFEST
    broken = json.loads(path.read_text())
    broken["baseline_commit"] = "0" * 40
    path.write_text(json.dumps(broken))
    try:
        mod.sync(local, up, target, Path(td) / "stale.json")
        raise AssertionError("stale scope baseline allowed")
    except ValueError as error:
        assert "stale" in str(error)
    assert not (local / "nodejs/build.gradle").exists()

print("PASS: upstream-first replacement, fork three-way rebase, private preservation, and fail-closed scope drift")
