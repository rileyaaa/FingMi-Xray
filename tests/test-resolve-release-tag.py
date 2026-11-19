#!/usr/bin/env python3
"""Offline release-tag selection regression: never trust workflow hard-coded tags."""
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build/resolve-release-tag.py"
spec = importlib.util.spec_from_file_location("fingmi_release_tag", SCRIPT)
tag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tag)


def write(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def rejected(root):
    try:
        tag.resolve(root)
    except ValueError:
        return
    raise AssertionError("Unverified or incompatible signed APK version accepted")


with tempfile.TemporaryDirectory(prefix="fingmi-release-tag-test-") as td:
    root = Path(td)
    write(root, "app/build.gradle", 'versionCode 563001\nversionName "v5.6.3-xray.1"\n')
    write(root, "scripts/build/source-baseline.json", json.dumps({"version": "5.6.3"}))
    assert tag.resolve(root) == "v5.6.3-xray.1"
    write(root, "app/build.gradle", 'versionCode 587001\nversionName "v5.8.7-xray.1"\n')
    write(root, "scripts/build/source-baseline.json", json.dumps({"version": "5.8.7", "version_code": 587}))
    assert tag.resolve(root) == "v5.8.7-xray.1"
    write(root, "app/build.gradle", 'versionCode 587002\nversionName "v5.8.7-xray.1"\n')
    rejected(root)
    write(root, "app/build.gradle", 'versionCode 587001\nversionName "v5.8.8-xray.1"\n')
    rejected(root)
    write(root, "app/build.gradle", 'versionCode 587001\nversionName "v5.8.7-xray.0"\n')
    rejected(root)
    write(root, "app/build.gradle", 'versionCode 587001\nversionName "v5.8.7-xray.1"\nversionName "v5.8.7-xray.2"\n')
    rejected(root)

assert tag.resolve(ROOT).startswith("v" + json.loads((ROOT / "scripts/build/source-baseline.json").read_text())["version"] + "-xray."), "Current source tag and pinned public baseline disagree"
print("PASS: signed release tags come from app/build.gradle and pinned upstream, not workflow YAML")
