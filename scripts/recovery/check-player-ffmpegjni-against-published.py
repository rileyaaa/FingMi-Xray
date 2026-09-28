#!/usr/bin/env python3
"""Block faithful builds with a mismatched Media3 FFmpeg JNI binary.

v7 reference: published armeabi-v7a APK (see extract-v7-player-native.py).
v8 reference: historical JADX artifact 10825963688; independently verify
the fixed v8 APK SHA-256 before treating that provenance as final.
Unlike the ten matching native libraries, this JNI library currently differs.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import sys
from zipfile import ZipFile

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD_DIR))
from player_candidate import read_verified_candidate  # noqa: E402


PUBLISHED = {
    "armeabi-v7a": "3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42",
    "arm64-v8a": "26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c",
}
NAME = "lib-decoder-ffmpeg-release.aar"


def check(data: bytes) -> bool:
    good = True
    with ZipFile(BytesIO(data)) as aar:
        for abi, wanted in PUBLISHED.items():
            path = f"jni/{abi}/libffmpegJNI.so"
            observed = hashlib.sha256(aar.read(path)).hexdigest()
            matches = observed == wanted
            good &= matches
            print(f"{abi}: {'MATCH' if matches else 'MISMATCH'}")
            print(f"  published {wanted}")
            print(f"  candidate {observed}")
    return good


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--artifact", type=Path)
    source.add_argument("--aar-dir", type=Path)
    args = parser.parse_args()
    if args.artifact:
        try:
            data = read_verified_candidate(args.artifact)[NAME]
        except ValueError as error:
            parser.error(str(error))
    else:
        data = (args.aar_dir / NAME).read_bytes()
    if not check(data):
        parser.exit(1, "Faithful native dependency gate failed; obtain the published JNI binary.\n")


if __name__ == "__main__":
    main()
