#!/usr/bin/env python3
"""Verify a locally rebuilt FongMi/media player AAR candidate bundle."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

SOURCE_COMMIT = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
EXPECTED_AARS = {
    "lib-common-release.aar",
    "lib-database-release.aar",
    "lib-datasource-release.aar",
    "lib-datasource-okhttp-release.aar",
    "lib-extractor-release.aar",
    "lib-exoplayer-release.aar",
    "lib-exoplayer-rtsp-release.aar",
    "lib-exoplayer-hls-release.aar",
    "lib-exoplayer-dash-release.aar",
    "lib-exoplayer-smoothstreaming-release.aar",
    "lib-decoder-ffmpeg-release.aar",
    "lib-effect-release.aar",
    "lib-mpvplayer-release.aar",
    "lib-session-release.aar",
    "lib-ui-release.aar",
    "lib-ui-danmaku-release.aar",
}
REQUIRED_CLASSES = {
    "androidx/media3/mpvplayer/MpvPlayer.class",
    "androidx/media3/exoplayer/trackselection/DecodeTrackSelector.class",
    "androidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier.class",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_verified_candidate(path: Path) -> dict[str, bytes]:
    try:
        with ZipFile(path) as bundle:
            names = bundle.namelist()
            if len(names) != len(set(names)):
                raise ValueError("candidate bundle contains duplicate ZIP entries")
            if set(names) != EXPECTED_AARS | {"BUILD_MANIFEST.txt"}:
                raise ValueError("candidate bundle does not contain exactly the 16 pinned AARs and manifest")

            manifest = bundle.read("BUILD_MANIFEST.txt").decode("utf-8")
            first = manifest.splitlines()[0] if manifest else ""
            if first != f"FongMi/media @ {SOURCE_COMMIT}":
                raise ValueError("candidate manifest points at an unexpected FongMi/media commit")

            expected: dict[str, str] = {}
            for line in manifest.splitlines():
                if "  lib-" not in line:
                    continue
                digest, filename = line.split("  ", 1)
                if (
                    len(digest) != 64
                    or filename not in EXPECTED_AARS
                    or filename in expected
                ):
                    raise ValueError(f"invalid candidate manifest entry: {line}")
                expected[filename] = digest

            if set(expected) != EXPECTED_AARS:
                raise ValueError("candidate manifest does not pin all 16 expected AARs")

            payload: dict[str, bytes] = {}
            found: set[str] = set()
            for filename in sorted(EXPECTED_AARS):
                data = bundle.read(filename)
                if sha256(data) != expected[filename]:
                    raise ValueError(f"AAR SHA-256 mismatch: {filename}")
                payload[filename] = data

                with ZipFile(BytesIO(data)) as aar:
                    classes = aar.read("classes.jar")
                with ZipFile(BytesIO(classes)) as jar:
                    found.update(REQUIRED_CLASSES.intersection(jar.namelist()))

            missing = REQUIRED_CLASSES - found
            if missing:
                raise ValueError(
                    "candidate is missing required player classes: "
                    + ", ".join(sorted(missing))
                )
            return payload
    except (BadZipFile, KeyError, UnicodeDecodeError, OSError) as error:
        raise ValueError(f"invalid candidate bundle: {error}") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    payload = read_verified_candidate(args.candidate)
    print(f"PASS: verified {len(payload)} AARs from FongMi/media@{SOURCE_COMMIT}")
    print(f"bundle_sha256={sha256(args.candidate.read_bytes())}")


if __name__ == "__main__":
    main()
