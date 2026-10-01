#!/usr/bin/env python3
"""Verify that pinned native libraries survive final APK packaging unchanged at runtime."""

import argparse
import importlib.util
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "elf_runtime", ROOT / "scripts/build/check-elf-runtime.py"
)
elf_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(elf_runtime)

NATIVES = (
    ("Xray", "libxray/libs/libXray.aar", "libgojni.so"),
    ("FFmpeg", "app/libs/lib-decoder-ffmpeg-release.aar", "libffmpegJNI.so"),
    ("MPEG-H", "app/libs/lib-decoder-mpegh-release.aar", "libmpeghJNI.so"),
    ("Libass", "app/libs/lib-exoplayer-libass-reconstructed.aar", "libmedia3ass.so"),
)
ABIS = ("armeabi-v7a", "arm64-v8a")


def unique_read(path: Path, entry: str) -> bytes:
    if not path.is_file():
        raise ValueError(f"missing archive: {path}")
    with ZipFile(path) as archive:
        names = archive.namelist()
        if names.count(entry) != 1:
            raise ValueError(f"{path}: expected exactly one {entry}")
        data = archive.read(entry)
    if not data:
        raise ValueError(f"{path}: empty entry {entry}")
    return data


def find_apk(apk_dir: Path, abi: str) -> Path:
    matches = sorted(apk_dir.rglob(f"app-leanback-{abi}-debug.apk"))
    if len(matches) != 1:
        raise ValueError(f"expected one Leanback {abi} APK in {apk_dir}, found {len(matches)}")
    return matches[0]


def verify(root: Path, apk_dir: Path):
    results = []
    for abi in ABIS:
        apk = find_apk(apk_dir, abi)
        for label, aar_rel, soname in NATIVES:
            aar = root / aar_rel
            reference = unique_read(aar, f"jni/{abi}/{soname}")
            candidate = unique_read(apk, f"lib/{abi}/{soname}")
            ref_fp = elf_runtime._fingerprint_bytes(reference)
            apk_fp = elf_runtime._fingerprint_bytes(candidate)
            if ref_fp != apk_fp:
                raise ValueError(
                    f"{label}-{abi}: final APK runtime PT_LOAD differs from verified AAR"
                )
            results.append((label, abi, len(ref_fp["segments"]), apk.name))
    return results


def self_test():
    elf_runtime.self_test()
    expected = {name for name, _aar, _so in NATIVES}
    if expected != {"Xray", "FFmpeg", "MPEG-H", "Libass"}:
        raise AssertionError("native final-packaging inventory changed unexpectedly")
    if ABIS != ("armeabi-v7a", "arm64-v8a"):
        raise AssertionError("TV ABI inventory changed unexpectedly")
    with tempfile.TemporaryDirectory(prefix="final-apk-native-") as directory:
        apk_dir = Path(directory)
        nested = apk_dir / "debug"
        nested.mkdir()
        for abi in ABIS:
            expected = nested / f"app-leanback-{abi}-debug.apk"
            expected.touch()
            if find_apk(apk_dir, abi) != expected:
                raise AssertionError(f"recursive APK discovery failed for {abi}")
    print("PASS final native packaging inventory self-test")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--apk-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        if args.apk_dir:
            parser.error("--self-test cannot be combined with --apk-dir")
        self_test()
        return
    if not args.apk_dir:
        parser.error("--apk-dir is required")

    try:
        results = verify(args.root, args.apk_dir)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    for label, abi, segments, apk_name in results:
        print(
            f"PASS {label}-{abi}: runtime PT_LOAD matches verified AAR "
            f"({segments} load segments) in {apk_name}"
        )


if __name__ == "__main__":
    main()
