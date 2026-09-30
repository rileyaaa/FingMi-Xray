#!/usr/bin/env python3
"""Restore the pinned FongMi 5.6.8 MPV native bridge into the rebuilt MPV AAR."""

import argparse
from copy import copy
import hashlib
from io import BytesIO
from pathlib import Path
import sys
from zipfile import ZipFile

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD_DIR))
from player_candidate import read_verified_candidate  # noqa: E402

from published_568_mpv_contract import APK_SHA256, NATIVE_SHA256

NAME = "lib-mpvplayer-release.aar"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_published_native(apk: Path, abi: str) -> dict[str, bytes]:
    raw = apk.read_bytes()
    if digest(raw) != APK_SHA256[abi]:
        raise ValueError(f"{apk}: APK SHA-256 is not the pinned FongMi 5.6.8 Leanback release")
    result: dict[str, bytes] = {}
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        for soname, wanted in NATIVE_SHA256[abi].items():
            member = f"lib/{abi}/{soname}"
            if names.count(member) != 1:
                raise ValueError(f"{apk}: expected exactly one {member}")
            data = archive.read(member)
            observed = digest(data)
            if observed != wanted:
                raise ValueError(f"{apk}: {soname} SHA-256 differs: {observed}")
            result[f"jni/{abi}/{soname}"] = data
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--v7-apk", required=True, type=Path)
    parser.add_argument("--v8-apk", required=True, type=Path)
    parser.add_argument("--to", required=True, type=Path)
    args = parser.parse_args()

    if args.to.exists():
        parser.error("refusing to overwrite an existing output")
    if not args.to.parent.is_dir():
        parser.error("output parent directory must exist")

    try:
        replacement = {}
        replacement.update(read_published_native(args.v7_apk, "armeabi-v7a"))
        replacement.update(read_published_native(args.v8_apk, "arm64-v8a"))

        payload = read_verified_candidate(args.candidate)
        aar_bytes = payload[NAME]
        with ZipFile(BytesIO(aar_bytes)) as source:
            names = source.namelist()
            if len(names) != len(set(names)):
                raise ValueError("candidate MPV AAR contains duplicate ZIP entries")
            missing = sorted(name for name in replacement if names.count(name) != 1)
            if missing:
                raise ValueError(
                    "candidate MPV AAR lacks native bridge entries: " + ", ".join(missing)
                )

            output = BytesIO()
            with ZipFile(output, "w") as target:
                for info in source.infolist():
                    target.writestr(
                        copy(info),
                        replacement.get(info.filename, source.read(info.filename)),
                    )

        out = output.getvalue()
        with ZipFile(BytesIO(out)) as restored:
            restored_names = restored.namelist()
            if len(restored_names) != len(set(restored_names)) or restored_names != names:
                raise ValueError("restored MPV AAR changed archive inventory/order")
            for name, wanted in replacement.items():
                if restored.read(name) != wanted:
                    raise ValueError(f"restored MPV AAR entry differs: {name}")
        args.to.write_bytes(out)
    except (KeyError, OSError, ValueError) as error:
        parser.error(str(error))

    print(f"PASS: restored {len(replacement)} FongMi 5.6.8 MPV native bridge entries")
    for abi in ("armeabi-v7a", "arm64-v8a"):
        for soname in sorted(NATIVE_SHA256[abi]):
            print(f"{abi} {soname} {NATIVE_SHA256[abi][soname]}")
    print(f"AAR SHA-256 {digest(out)}")


if __name__ == "__main__":
    main()
