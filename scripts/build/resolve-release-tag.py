#!/usr/bin/env python3
"""Derive the formal release tag from the checked-out source, never workflow YAML.

GitHub Actions' built-in token is not allowed to rewrite workflow definitions.
Every manual build must instead bind the release name to app/build.gradle and
the pinned public FongMi baseline.
"""
import json
from pathlib import Path
import re


def resolve(root: Path) -> str:
    root = root.resolve()
    source = (root / "app/build.gradle").read_text(encoding="utf-8")
    versions = re.findall(
        r'(?m)^\s*versionName\s+"(v(\d+\.\d+\.\d+)-xray\.(\d+))"',
        source,
    )
    codes = re.findall(r"(?m)^\s*versionCode\s+(\d+)\b", source)
    if len(versions) != 1 or len(codes) != 1:
        raise ValueError("Expected exactly one fork versionName and versionCode")
    tag, public_version, revision = versions[0]
    revision = int(revision)
    code = int(codes[0])
    if not 1 <= revision <= 999 or code <= 0:
        raise ValueError("Invalid fork revision/versionCode")
    baseline = json.loads((root / "scripts/upstream/baseline.json").read_text(encoding="utf-8"))
    if baseline.get("version") != public_version:
        raise ValueError("Fork versionName does not match pinned public source")
    if "version_code" in baseline and code != int(baseline["version_code"]) * 1000 + revision:
        raise ValueError("Fork versionCode differs from pinned upstream code and revision")
    return tag


def main() -> None:
    try:
        print(resolve(Path(__file__).resolve().parents[2]))
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit("BLOCKED: Cannot resolve signed release tag: " + str(error))


if __name__ == "__main__":
    main()
