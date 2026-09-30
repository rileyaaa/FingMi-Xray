#!/usr/bin/env python3
"""Verify a locally rebuilt FongMi/media player AAR candidate bundle."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

SOURCE_COMMIT = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
DOLBY_OVERLAY_ID = "fongmi-tv-5.6.8-dolby-release-overlay-v1"
EXPECTED_AAR_COUNT = 17
REQUIRED_AARS = {
    "lib-common-release.aar",
    "lib-extractor-release.aar",
    "lib-decoder-ffmpeg-release.aar",
    "lib-decoder-mpegh-release.aar",
    "lib-mpvplayer-release.aar",
}
REQUIRED_CLASSES = {
    "androidx/media3/mpvplayer/MpvPlayer.class",
    "androidx/media3/exoplayer/trackselection/DecodeTrackSelector.class",
    "androidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier.class",
    "androidx/media3/decoder/mpegh/MpeghAudioRenderer.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5MappingPolicy.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5Native.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5Renderer.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5VideoSink.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP7Converter.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP7Converter$Factory.class",
    "androidx/media3/exoplayer/video/DolbyVisionP7Converter.class",
    "androidx/media3/exoplayer/video/DolbyVisionP7Converter$Factory.class",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_verified_candidate(path: Path) -> dict[str, bytes]:
    try:
        with ZipFile(path) as bundle:
            names = bundle.namelist()
            if len(names) != len(set(names)):
                raise ValueError("candidate bundle contains duplicate ZIP entries")

            aar_names = {
                name
                for name in names
                if name.endswith(".aar")
                and "/" not in name
                and name.startswith("lib-")
                and name.endswith("-release.aar")
            }
            if len(aar_names) != EXPECTED_AAR_COUNT:
                raise ValueError(
                    f"candidate bundle must contain exactly {EXPECTED_AAR_COUNT} root lib-*-release.aar files"
                )
            if set(names) != aar_names | {"BUILD_MANIFEST.txt"}:
                raise ValueError("candidate bundle contains unexpected files")
            missing_aars = REQUIRED_AARS - aar_names
            if missing_aars:
                raise ValueError(
                    "candidate bundle is missing required AARs: "
                    + ", ".join(sorted(missing_aars))
                )

            manifest = bundle.read("BUILD_MANIFEST.txt").decode("utf-8")
            manifest_lines = manifest.splitlines()
            first = manifest_lines[0] if manifest_lines else ""
            if first != f"FongMi/media @ {SOURCE_COMMIT}":
                raise ValueError("candidate manifest points at an unexpected FongMi/media commit")
            second = manifest_lines[1] if len(manifest_lines) > 1 else ""
            if second != f"Dolby overlay: {DOLBY_OVERLAY_ID}":
                raise ValueError("candidate manifest is missing the pinned Dolby release overlay")

            expected: dict[str, str] = {}
            for line in manifest.splitlines():
                if "  " not in line:
                    continue
                digest, filename = line.split("  ", 1)
                if filename not in aar_names:
                    continue
                if len(digest) != 64 or filename in expected:
                    raise ValueError(f"invalid candidate manifest entry: {line}")
                expected[filename] = digest

            if set(expected) != aar_names:
                raise ValueError(
                    f"candidate manifest does not pin all {EXPECTED_AAR_COUNT} rebuilt AARs"
                )

            payload: dict[str, bytes] = {}
            found: set[str] = set()
            for filename in sorted(aar_names):
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
