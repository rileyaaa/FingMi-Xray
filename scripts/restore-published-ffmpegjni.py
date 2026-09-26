#!/usr/bin/env python3
"""Produce a new decoder AAR using FFmpeg JNI from verified release evidence.

Each ABI may come from either:
- the original published APK with its pinned whole-file SHA-256; or
- the persisted full JADX ZIP produced only after that published APK passed its
  whole-file SHA-256 gate, with the JADX ZIP's own SHA-256 pinned here.

In both cases the extracted libffmpegJNI.so must still match the exact published
per-library SHA-256. The script never overwrites the candidate AAR or installs
the result into app/libs automatically.
"""

import argparse
from copy import copy
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
V7_JADX_SHA256 = "7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d"
V8_JADX_SHA256 = "8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b"
CANDIDATE_SHA256 = runpy.run_path(str(SCRIPT_DIR / "import-player-aar-candidate.py"))[
    "ARTIFACT_SHA256"
]
JNI_SHA256 = {
    "armeabi-v7a": "3af1fcaa21f28071994fc51936889e2441edec57d5009e7a4043bf9f06435d42",
    "arm64-v8a": "26594d573765fc86a3d242c81e11369ced639d76cb4465cdf4b31a7c2d9da91c",
}
NAME = "lib-decoder-ffmpeg-release.aar"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verified_apk_binary(path: Path, apk_hash: str, abi: str) -> bytes:
    archive_bytes = path.read_bytes()
    if digest(archive_bytes) != apk_hash:
        raise ValueError(f"{path}: APK SHA-256 is not the pinned published release")
    with ZipFile(BytesIO(archive_bytes)) as archive:
        member = f"lib/{abi}/libffmpegJNI.so"
        if archive.namelist().count(member) != 1:
            raise ValueError(f"{path}: expected exactly one {member}")
        data = archive.read(member)
    if digest(data) != JNI_SHA256[abi]:
        raise ValueError(f"{path}: published FFmpeg JNI hash differs")
    return data


def verified_jadx_binary(path: Path, jadx_hash: str, abi: str) -> bytes:
    archive_bytes = path.read_bytes()
    if digest(archive_bytes) != jadx_hash:
        raise ValueError(f"{path}: JADX artifact SHA-256 differs from pinned evidence")
    with ZipFile(BytesIO(archive_bytes)) as archive:
        member = f"resources/lib/{abi}/libffmpegJNI.so"
        if archive.namelist().count(member) != 1:
            raise ValueError(f"{path}: expected exactly one {member}")
        data = archive.read(member)
    if digest(data) != JNI_SHA256[abi]:
        raise ValueError(f"{path}: published FFmpeg JNI hash differs")
    return data


def verified_source_binary(
        apk: Path | None,
        jadx: Path | None,
        abi: str,
        apk_hash: str,
        jadx_hash: str) -> bytes:
    if apk is not None:
        return verified_apk_binary(apk, apk_hash, abi)
    if jadx is not None:
        return verified_jadx_binary(jadx, jadx_hash, abi)
    raise ValueError(f"{abi}: no verified source was supplied")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)

    v7 = parser.add_mutually_exclusive_group(required=True)
    v7.add_argument("--v7-apk", type=Path)
    v7.add_argument("--v7-jadx", type=Path)

    v8 = parser.add_mutually_exclusive_group(required=True)
    v8.add_argument("--v8-apk", type=Path)
    v8.add_argument("--v8-jadx", type=Path)

    parser.add_argument("--to", required=True, type=Path,
                        help="new, non-existing output AAR path")
    args = parser.parse_args()
    if args.to.exists():
        parser.error("refusing to overwrite an existing output")
    if not args.to.parent.is_dir():
        parser.error("output parent directory must exist")

    try:
        replacement = {
            "jni/armeabi-v7a/libffmpegJNI.so": verified_source_binary(
                args.v7_apk,
                args.v7_jadx,
                "armeabi-v7a",
                V7_APK_SHA256,
                V7_JADX_SHA256),
            "jni/arm64-v8a/libffmpegJNI.so": verified_source_binary(
                args.v8_apk,
                args.v8_jadx,
                "arm64-v8a",
                V8_APK_SHA256,
                V8_JADX_SHA256),
        }
        if digest(args.candidate.read_bytes()) != CANDIDATE_SHA256:
            raise ValueError("candidate artifact SHA-256 differs from verified AC run")
        with ZipFile(args.candidate) as outer:
            if outer.namelist().count(NAME) != 1:
                raise ValueError(f"candidate artifact must contain exactly one {NAME}")
            aar_bytes = outer.read(NAME)
        with ZipFile(BytesIO(aar_bytes)) as source:
            names = source.namelist()
            if len(names) != len(set(names)):
                raise ValueError("candidate AAR contains duplicate ZIP entries")
            if any(names.count(name) != 1 for name in replacement):
                raise ValueError("candidate AAR lacks a unique JNI entry for each ABI")
            output = BytesIO()
            with ZipFile(output, "w") as target:
                for info in source.infolist():
                    # writestr updates the passed ZipInfo CRC/size in place;
                    # retain the source object's metadata for verification.
                    data = (replacement[info.filename] if info.filename in replacement
                            else source.read(info.filename))
                    target.writestr(copy(info), data)
            with ZipFile(BytesIO(output.getvalue())) as restored:
                if restored.namelist() != names:
                    raise ValueError("restored AAR entry names/order changed")
                for name in names:
                    wanted = replacement[name] if name in replacement else source.read(name)
                    if restored.read(name) != wanted:
                        raise ValueError(f"unexpected entry change: {name}")
        args.to.write_bytes(output.getvalue())
    except (KeyError, ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Verified {len(replacement)} published JNI binaries; wrote {args.to}")
    print(f"AAR SHA-256 {digest(output.getvalue())}")


if __name__ == "__main__":
    main()
