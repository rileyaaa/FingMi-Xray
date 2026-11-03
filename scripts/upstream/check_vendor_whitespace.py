#!/usr/bin/env python3
"""Keep the one reviewed upstream asset whitespace exception byte-identical.

The public FongMi/TV ESTree bundle contains template literal lines ending in
spaces. Git's diff --cached --check rejects the unchanged public blob unless
its *one exact path* has whitespace checks disabled. All other paths retain
normal Git checks. A modified vendor blob is never accepted by the exception.
"""
import argparse
from pathlib import Path
import re
import subprocess

ASSET = "app/src/main/assets/js/spider-format/estree-L5DZKXBH.js"
RULE = ASSET + " -whitespace"


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.PIPE).decode("utf-8").strip()


def verify(root: Path, upstream: Path, target: str) -> None:
    root = root.resolve()
    upstream = upstream.resolve()
    if re.fullmatch(r"[0-9a-f]{40}", target) is None:
        raise ValueError("Unreviewed public FongMi target commit")
    attributes = root / ".gitattributes"
    rules = [line.strip() for line in attributes.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if rules != [RULE]:
        raise ValueError("Git whitespace exception must name only the approved upstream asset")
    file = root / ASSET
    if not file.is_file() or file.is_symlink():
        raise ValueError("Expected public FongMi ESTree asset is absent or a symlink")
    actual_attr = git(root, "check-attr", "whitespace", "--", ASSET)
    if actual_attr != f"{ASSET}: whitespace: unset":
        raise ValueError("The approved asset lacks its narrow Git whitespace exception")
    try:
        upstream_blob = git(upstream, "rev-parse", "--verify", f"{target}:{ASSET}")
        kind = git(upstream, "cat-file", "-t", upstream_blob)
    except subprocess.CalledProcessError as exc:
        raise ValueError("Asset is absent from the selected public upstream Git tree") from exc
    if kind != "blob":
        raise ValueError("Public ESTree path does not identify a Git blob")
    actual_blob = git(root, "hash-object", "--", ASSET)
    if actual_blob != upstream_blob:
        raise ValueError("ESTree asset changed from the selected public upstream bytes")
    print(f"PASS public ESTree exception: exactly one path, original upstream Git blob {upstream_blob}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    verify(args.root, args.upstream, args.target)


if __name__ == "__main__":
    main()
