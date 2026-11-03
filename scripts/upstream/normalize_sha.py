#!/usr/bin/env python3
"""Validate and canonicalize an optional public upstream Git commit SHA.

GitHub workflow_dispatch text fields may contain leading/trailing whitespace
(e.g. a pasted tab). Do not silently remove whitespace within a SHA.
"""
import re
import sys


def normalize_sha(raw: str) -> str:
    sha = raw.strip().lower()
    if sha and not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("expected_upstream_sha must be exactly 40 hex characters (or blank)")
    return sha


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("BLOCKED: expected exactly one optional SHA argument")
    try:
        print(normalize_sha(sys.argv[1]))
    except ValueError as exc:
        raise SystemExit("BLOCKED: " + str(exc)) from exc


if __name__ == "__main__":
    main()
