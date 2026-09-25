#!/usr/bin/env python3
"""Import the pinned FongMi/media candidate AAR artifact into app/libs."""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_SHA256 = "0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee"
SOURCE_COMMIT = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Downloaded candidate ZIP from AC run 36124817040")
    args = parser.parse_args()
    archive = args.artifact
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARTIFACT_SHA256:
        parser.error("Artifact SHA-256 does not match the verified run")

    with ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        manifest = bundle.read("BUILD_MANIFEST.txt").decode("utf-8")
        if not manifest.startswith(f"FongMi/media @ {SOURCE_COMMIT}\n"):
            parser.error("Unexpected FongMi/media commit in manifest")
        expected = {}
        for line in manifest.splitlines():
            if "  lib-" not in line:
                continue
            digest, filename = line.split("  ", 1)
            if (len(digest) != 64 or not filename.startswith("lib-")
                    or not filename.endswith("-release.aar") or "/" in filename):
                parser.error(f"Unexpected manifest entry: {line}")
            expected[filename] = digest
        if len(expected) != 16 or names != set(expected) | {"BUILD_MANIFEST.txt"}:
            parser.error("Expected exactly 16 pinned AARs and one manifest")

        # Validate the whole artifact before changing the project working tree.
        payload = {}
        for filename, digest in expected.items():
            data = bundle.read(filename)
            if hashlib.sha256(data).hexdigest() != digest:
                parser.error(f"AAR SHA-256 mismatch: {filename}")
            payload[filename] = data

    dest = ROOT / "app" / "libs"
    dest.mkdir(parents=True, exist_ok=True)
    for filename, data in payload.items():
        (dest / filename).write_bytes(data)
    print(f"Imported {len(payload)} verified FongMi/media candidate AARs to {dest}")
    print("Run scripts/check-faithful-player-aars.py next; full ABI is not yet verified.")


if __name__ == "__main__":
    main()
