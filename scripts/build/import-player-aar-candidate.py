#!/usr/bin/env python3
"""Import the pinned FongMi/media candidate AAR artifact into app/libs."""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_SHA256 = "0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee"
SOURCE_COMMIT = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
DECODER_NAME = "lib-decoder-ffmpeg-release.aar"
PUBLISHED_JNI = {
    "jni/armeabi-v7a/libffmpegJNI.so": "3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42",
    "jni/arm64-v8a/libffmpegJNI.so": "26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c",
}


def verified_decoder_replacement(candidate: bytes, replacement: bytes) -> bytes:
    """Accept only the two published JNI changes to the pinned decoder AAR."""
    with ZipFile(BytesIO(candidate)) as original, ZipFile(BytesIO(replacement)) as restored:
        before, after = original.namelist(), restored.namelist()
        if len(before) != len(set(before)) or before != after:
            raise ValueError("restored decoder AAR entry names/order differ or are duplicated")
        if not set(PUBLISHED_JNI).issubset(before):
            raise ValueError("decoder AAR lacks the two expected JNI entries")
        for name in before:
            data = restored.read(name)
            if name in PUBLISHED_JNI:
                if hashlib.sha256(data).hexdigest() != PUBLISHED_JNI[name]:
                    raise ValueError(f"restored decoder has unverified published JNI: {name}")
            elif data != original.read(name):
                raise ValueError(f"restored decoder changed another entry: {name}")
    return replacement


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Downloaded candidate ZIP from AC run 36124817040")
    parser.add_argument("--restored-decoder", type=Path,
                        help="decoder AAR restored from both SHA-verified published APKs")
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

    if args.restored_decoder:
        try:
            payload[DECODER_NAME] = verified_decoder_replacement(
                payload[DECODER_NAME], args.restored_decoder.read_bytes())
        except (BadZipFile, KeyError, ValueError, OSError) as error:
            parser.error(str(error))

    dest = ROOT / "app" / "libs"
    dest.mkdir(parents=True, exist_ok=True)
    for filename, data in payload.items():
        (dest / filename).write_bytes(data)
    print(f"Imported {len(payload)} verified FongMi/media candidate AARs to {dest}")
    print("Run scripts/recovery/check-faithful-player-aars.py and the FFmpeg JNI gate next; full ABI is not yet verified.")


if __name__ == "__main__":
    main()
