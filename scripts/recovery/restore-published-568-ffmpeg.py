#!/usr/bin/env python3
"""Restore the complete FongMi 5.6.8 Media3 FFmpeg native closure into a rebuilt decoder AAR.

The public FongMi/media source currently available for reconstruction predates
release-only Dolby Vision P5/P7 support.  Current TV builds therefore compile
Java from the pinned public source plus the checked-in release overlay, then
replace the decoder module's native payload with the immutable 5.6.8 Leanback
payload as one coherent ABI closure.

This script never installs the AAR automatically.
"""

import argparse
from copy import copy
import hashlib
from io import BytesIO
from pathlib import Path
import sys
from zipfile import ZIP_STORED, ZipFile, ZipInfo

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
sys.path.insert(0, str(BUILD_DIR))
from player_candidate import read_verified_candidate  # noqa: E402

NAME = "lib-decoder-ffmpeg-release.aar"
APK_SHA256 = {
    "armeabi-v7a": "2859ebef12bf0fa0dfec023d410df478ac5e5a82a72ef2be48f6e4fa09a24761",
    "arm64-v8a": "948df594843e304c332476a380163dc1cc74f964be5ea1539ff0465a9dd936eb",
}
NATIVE_SHA256 = {
    "armeabi-v7a": {
        "libavcodec.so": "7fab9da98f11982a7680fbb233f113eab71cbbdde2c4f3f28765476a77006291",
        "libavdevice.so": "c047cac5c39741b60179f70a7ce40471f38a2585dd4783f14ecbfb5ce0196243",
        "libavfilter.so": "d3e4546af917e23afd5cbf91980764d705eeca7f07c9915e414fc3efb9414f8d",
        "libavformat.so": "b3ec7b4ab759a5a7041192370396f8ec15ff1b04fdb64633d58bffaaf83147ee",
        "libavutil.so": "d8f11cc7bffd02492edee47d4e27f9cf0808b322ff5fe07489c52d40e5f7dbb1",
        "libffmpegDoviJNI.so": "aa916dfbe76db03860bc46992fa33d08b63885dfd32347c80335860987a4dd2a",
        "libffmpegJNI.so": "5739717ab9b6219ee9bc649145ef562de9e25d8c410c15014cec9d38fc4e42e6",
        "libswresample.so": "d53475df1a2a3d90e365cc86b16737994fdfefabe9f6c7d25bf6b313edec4ab0",
        "libswscale.so": "02cef04c153cf533108c9a9273e1192dfca7b02ed9d0f307ca959cff1e8912c4",
    },
    "arm64-v8a": {
        "libavcodec.so": "ac5580105c9adde952c653e3019ebf8d092671ac1455f2bb84badb3d3dcf8108",
        "libavdevice.so": "0f8da05577441c5a11915b99a5e1c29d166bae1760b8347a8e49d0e6d66b3b61",
        "libavfilter.so": "2d85b83fb544a1548a352c8faa12d0c92dbd6e385067305ed0e939b93453103f",
        "libavformat.so": "16046eb6ec0bd48d835e736a8372313db963dc67ec4fce72b2c59d8d822b844f",
        "libavutil.so": "843c5e024d0b707cbe345a80414951c0e0ddfa1fe938e5d0105d164c8d393305",
        "libffmpegDoviJNI.so": "f7c4d628426a175ca8f9827661010666daf074ce45370c84dcffb4dd47b268d6",
        "libffmpegJNI.so": "891dccc0e4fd70ddccbaba00dfc74c29de87bf7bf0b62a4ec5c399a868081eb1",
        "libswresample.so": "0316873890ab774e247d120bd92d3ece9b7606fbc33fe49371407f7488141770",
        "libswscale.so": "aafb333e845f795268f90ee0fe27743a7652c1567d48b8898c086409b554ec4d",
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_published_closure(apk: Path, abi: str) -> dict[str, bytes]:
    raw = apk.read_bytes()
    if digest(raw) != APK_SHA256[abi]:
        raise ValueError(f"{apk}: APK SHA-256 is not the pinned FongMi 5.6.8 Leanback release")
    expected = NATIVE_SHA256[abi]
    result: dict[str, bytes] = {}
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        for soname, wanted in expected.items():
            member = f"lib/{abi}/{soname}"
            if names.count(member) != 1:
                raise ValueError(f"{apk}: expected exactly one {member}")
            data = archive.read(member)
            observed = digest(data)
            if observed != wanted:
                raise ValueError(f"{apk}: {soname} SHA-256 differs: {observed}")
            result[f"jni/{abi}/{soname}"] = data
    return result


def added_info(name: str) -> ZipInfo:
    info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_STORED
    info.external_attr = 0o644 << 16
    return info


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
        replacement.update(read_published_closure(args.v7_apk, "armeabi-v7a"))
        replacement.update(read_published_closure(args.v8_apk, "arm64-v8a"))

        payload = read_verified_candidate(args.candidate)
        aar_bytes = payload[NAME]
        with ZipFile(BytesIO(aar_bytes)) as source:
            names = source.namelist()
            if len(names) != len(set(names)):
                raise ValueError("candidate AAR contains duplicate ZIP entries")

            expected_existing = set(replacement) - {
                "jni/armeabi-v7a/libffmpegDoviJNI.so",
                "jni/arm64-v8a/libffmpegDoviJNI.so",
            }
            missing = sorted(name for name in expected_existing if names.count(name) != 1)
            if missing:
                raise ValueError("candidate AAR lacks FFmpeg closure entries: " + ", ".join(missing))
            for added in set(replacement) - expected_existing:
                if names.count(added) not in (0, 1):
                    raise ValueError(f"candidate AAR has duplicate optional entry: {added}")

            output = BytesIO()
            with ZipFile(output, "w") as target:
                written = set()
                for info in source.infolist():
                    data = replacement.get(info.filename, source.read(info.filename))
                    target.writestr(copy(info), data)
                    written.add(info.filename)
                for name in sorted(set(replacement) - written):
                    target.writestr(added_info(name), replacement[name])

        out = output.getvalue()
        with ZipFile(BytesIO(out)) as restored:
            restored_names = restored.namelist()
            if len(restored_names) != len(set(restored_names)):
                raise ValueError("restored AAR contains duplicate ZIP entries")
            for name, wanted in replacement.items():
                observed = restored.read(name)
                if observed != wanted:
                    raise ValueError(f"restored AAR entry differs: {name}")

        args.to.write_bytes(out)
    except (KeyError, OSError, ValueError) as error:
        parser.error(str(error))

    print(f"PASS: restored {len(replacement)} FongMi 5.6.8 FFmpeg native entries")
    for abi in ("armeabi-v7a", "arm64-v8a"):
        for soname in sorted(NATIVE_SHA256[abi]):
            print(f"{abi} {soname} {NATIVE_SHA256[abi][soname]}")
    print(f"AAR SHA-256 {digest(out)}")


if __name__ == "__main__":
    main()
