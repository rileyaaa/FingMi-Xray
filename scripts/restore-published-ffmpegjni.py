#!/usr/bin/env python3
"""Produce a new decoder AAR using FFmpeg JNI from both verified release APKs.

Requires the *original* published APKs, not a JADX artifact. Does not overwrite
the candidate AAR or install the result into app/libs automatically.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import runpy
from zipfile import ZipFile


SCRIPT_DIR = Path(__file__).resolve().parent
V7_APK_SHA256 = runpy.run_path(str(SCRIPT_DIR / "extract-v7-player-native.py"))[
    "APK_SHA256"
]
V8_APK_SHA256 = "b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d"
CANDIDATE_SHA256 = runpy.run_path(str(SCRIPT_DIR / "import-player-aar-candidate.py"))[
    "ARTIFACT_SHA256"
]
JNI_SHA256 = {
    "armeabi-v7a": "3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42",
    "arm64-v8a": "26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c",
}
NAME = "lib-decoder-ffmpeg-release.aar"


def verified_apk_binary(path: Path, apk_hash: str, abi: str) -> bytes:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != apk_hash:
        raise ValueError(f"{path}: APK SHA-256 is not the pinned published release")
    with ZipFile(path) as archive:
        data = archive.read(f"lib/{abi}/libffmpegJNI.so")
    if hashlib.sha256(data).hexdigest() != JNI_SHA256[abi]:
        raise ValueError(f"{path}: published FFmpeg JNI hash differs")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--v7-apk", required=True, type=Path)
    parser.add_argument("--v8-apk", required=True, type=Path)
    parser.add_argument("--to", required=True, type=Path,
                        help="new, non-existing output AAR path")
    args = parser.parse_args()
    if args.to.exists():
        parser.error("refusing to overwrite an existing output")
    if not args.to.parent.is_dir():
        parser.error("output parent directory must exist")

    try:
        replacement = {
            f"jni/{abi}/libffmpegJNI.so": verified_apk_binary(
                path, digest, abi)
            for abi, path, digest in (
                ("armeabi-v7a", args.v7_apk, V7_APK_SHA256),
                ("arm64-v8a", args.v8_apk, V8_APK_SHA256),
            )
        }
        if hashlib.sha256(args.candidate.read_bytes()).hexdigest() != CANDIDATE_SHA256:
            raise ValueError("candidate artifact SHA-256 differs from verified AC run")
        with ZipFile(args.candidate) as outer:
            aar_bytes = outer.read(NAME)
        with ZipFile(BytesIO(aar_bytes)) as source:
            names = source.namelist()
            if any(names.count(name) != 1 for name in replacement):
                raise ValueError("candidate AAR lacks a unique JNI entry for each ABI")
            output = BytesIO()
            with ZipFile(output, "w") as target:
                for info in source.infolist():
                    target.writestr(info, replacement.get(info.filename,
                                                         source.read(info.filename)))
            with ZipFile(BytesIO(output.getvalue())) as restored:
                if set(restored.namelist()) != set(names) or len(restored.namelist()) != len(names):
                    raise ValueError("restored AAR entry set changed")
                for name in names:
                    wanted = replacement.get(name, source.read(name))
                    if restored.read(name) != wanted:
                        raise ValueError(f"unexpected entry change: {name}")
        args.to.write_bytes(output.getvalue())
    except (KeyError, ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Verified {len(replacement)} published JNI binaries; wrote {args.to}")
    print(f"AAR SHA-256 {hashlib.sha256(output.getvalue()).hexdigest()}")


if __name__ == "__main__":
    main()
