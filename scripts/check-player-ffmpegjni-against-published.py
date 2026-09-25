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
import runpy
from zipfile import ZipFile


PUBLISHED = {
    "armeabi-v7a": "3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42",
    "arm64-v8a": "26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c",
}
ARTIFACT_SHA256 = runpy.run_path(
    str(Path(__file__).resolve().parent / "import-player-aar-candidate.py")
)["ARTIFACT_SHA256"]
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
        with ZipFile(args.artifact) as archive:
            if hashlib.sha256(args.artifact.read_bytes()).hexdigest() != ARTIFACT_SHA256:
                parser.error("Candidate artifact SHA-256 differs from the verified AC run")
            data = archive.read(NAME)
    else:
        data = (args.aar_dir / NAME).read_bytes()
    if not check(data):
        parser.exit(1, "Faithful native dependency gate failed; obtain the published JNI binary.\n")


if __name__ == "__main__":
    main()
