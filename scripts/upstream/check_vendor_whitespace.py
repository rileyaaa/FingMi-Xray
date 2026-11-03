#!/usr/bin/env python3
"""Allow only audited, byte-for-byte official FongMi bundled JS whitespace.

The bundled spider editor and AST formatter contain literal spaces at line
ends. Git correctly rejects these by default even though the files are
unmodified official upstream. Exempt only the exact reviewed asset paths;
reject missing files, upstream drift, local edits, or broadened attributes.
"""
import argparse
from pathlib import Path
import re
import subprocess

ASSETS = (
    "app/src/main/assets/js/spider-editor.js",
    "app/src/main/assets/js/spider-format/chunk-RBBTUEK2.js",
    "app/src/main/assets/js/spider-format/dist-SPW7IUL4.js",
    "app/src/main/assets/js/spider-format/estree-L5DZKXBH.js",
)
RULES = [name + " -whitespace" for name in ASSETS]


def git(cwd, *args):
    return subprocess.check_output(
        ["git", *args], cwd=cwd, stderr=subprocess.PIPE
    ).decode("utf-8").strip()


def verify(root: Path, upstream: Path, target: str) -> None:
    root = root.resolve()
    upstream = upstream.resolve()
    if re.fullmatch(r"[0-9a-f]{40}", target) is None:
        raise ValueError("Unreviewed public FongMi target commit")
    attributes = root / ".gitattributes"
    rules = [line.strip() for line in attributes.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if rules != RULES:
        raise ValueError("Git whitespace exceptions must be exactly the four reviewed public JS paths")

    for name in ASSETS:
        path = root / name
        if not path.is_file() or path.is_symlink() or any(
            parent.is_symlink() for parent in path.parents if parent != root and root in parent.parents
        ):
            raise ValueError("Expected public FongMi JS asset is absent or a symlink: " + name)
        actual_attr = git(root, "check-attr", "whitespace", "--", name)
        if actual_attr != f"{name}: whitespace: unset":
            raise ValueError("Reviewed Git whitespace exception missing for: " + name)
        try:
            upstream_blob = git(upstream, "rev-parse", "--verify", f"{target}:{name}")
            kind = git(upstream, "cat-file", "-t", upstream_blob)
        except subprocess.CalledProcessError as exc:
            raise ValueError("Asset absent from selected public upstream Git tree: " + name) from exc
        if kind != "blob":
            raise ValueError("Upstream asset is not a Git blob: " + name)
        if git(root, "hash-object", "--", name) != upstream_blob:
            raise ValueError("Official JS asset modified or drifted: " + name)
        print("PASS public bundled JS original blob: " + name + " " + upstream_blob)

    # This function is run before both Git source checks, and a malicious
    # additional .gitattributes rule would be rejected by the exact list above.
    print(f"PASS public JS whitespace exceptions: {len(ASSETS)} verified, no broad source exemption")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    verify(args.root, args.upstream, args.target)


if __name__ == "__main__":
    main()
