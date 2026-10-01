#!/usr/bin/env python3
"""Import the locally rebuilt pinned FongMi/media player AAR bundle into app/libs."""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from player_candidate import SOURCE_COMMIT, read_verified_candidate  # noqa: E402

RECOVERY_DIR = ROOT / "scripts" / "recovery"
sys.path.insert(0, str(RECOVERY_DIR))
from published_568_ffmpeg_contract import NATIVE_SHA256  # noqa: E402
from published_568_mpv_contract import NATIVE_SHA256 as MPV_NATIVE_SHA256  # noqa: E402
from published_568_iso_contract import NATIVE_SHA256 as ISO_NATIVE_SHA256  # noqa: E402


DECODER_NAME = "lib-decoder-ffmpeg-release.aar"
MPV_NAME = "lib-mpvplayer-release.aar"
ISO_NAME = "lib-extractor-release.aar"
PUBLISHED_CLOSURE = {
    f"jni/{abi}/{soname}": digest
    for abi, libraries in NATIVE_SHA256.items()
    for soname, digest in libraries.items()
}
DOVI_JNI = {
    "jni/armeabi-v7a/libffmpegDoviJNI.so",
    "jni/arm64-v8a/libffmpegDoviJNI.so",
}
PUBLISHED_MPV = {
    f"jni/{abi}/{soname}": digest
    for abi, libraries in MPV_NATIVE_SHA256.items()
    for soname, digest in libraries.items()
}
PUBLISHED_ISO = {
    f"jni/{abi}/{soname}": digest
    for abi, libraries in ISO_NATIVE_SHA256.items()
    for soname, digest in libraries.items()
}


def verified_decoder_replacement(candidate: bytes, replacement: bytes) -> bytes:
    """Accept only the immutable FongMi 5.6.8 FFmpeg native closure mutation."""
    with ZipFile(BytesIO(candidate)) as original, ZipFile(BytesIO(replacement)) as restored:
        before = original.namelist()
        after = restored.namelist()
        if len(before) != len(set(before)) or len(after) != len(set(after)):
            raise ValueError("decoder AAR contains duplicate ZIP entries")

        before_set = set(before)
        after_set = set(after)
        required_existing = set(PUBLISHED_CLOSURE) - DOVI_JNI
        missing_existing = sorted(required_existing - before_set)
        if missing_existing:
            raise ValueError(
                "candidate decoder AAR lacks FFmpeg closure entries: "
                + ", ".join(missing_existing)
            )

        expected_added = set(PUBLISHED_CLOSURE) - before_set
        if not expected_added.issubset(DOVI_JNI):
            raise ValueError("candidate decoder is missing non-Dolby FFmpeg closure entries")
        if after_set != before_set | expected_added:
            raise ValueError("restored decoder changed the archive entry inventory unexpectedly")

        for name in before:
            data = restored.read(name)
            if name in PUBLISHED_CLOSURE:
                if hashlib.sha256(data).hexdigest() != PUBLISHED_CLOSURE[name]:
                    raise ValueError(
                        f"restored decoder has unverified 5.6.8 native entry: {name}"
                    )
            elif data != original.read(name):
                raise ValueError(f"restored decoder changed non-native entry: {name}")

        for name in expected_added:
            data = restored.read(name)
            if hashlib.sha256(data).hexdigest() != PUBLISHED_CLOSURE[name]:
                raise ValueError(f"restored decoder added unverified native entry: {name}")

        missing_after = sorted(set(PUBLISHED_CLOSURE) - after_set)
        if missing_after:
            raise ValueError(
                "restored decoder lacks pinned 5.6.8 FFmpeg closure entries: "
                + ", ".join(missing_after)
            )
    return replacement


def verified_mpv_replacement(candidate: bytes, replacement: bytes) -> bytes:
    """Accept only the immutable FongMi 5.6.8 libplayer/libmpv mutation."""
    with ZipFile(BytesIO(candidate)) as original, ZipFile(BytesIO(replacement)) as restored:
        before = original.namelist()
        after = restored.namelist()
        if len(before) != len(set(before)) or before != after:
            raise ValueError("restored MPV AAR entry names/order differ or are duplicated")
        missing = sorted(set(PUBLISHED_MPV) - set(before))
        if missing:
            raise ValueError(
                "candidate MPV AAR lacks pinned native bridge entries: " + ", ".join(missing)
            )
        for name in before:
            data = restored.read(name)
            if name in PUBLISHED_MPV:
                if hashlib.sha256(data).hexdigest() != PUBLISHED_MPV[name]:
                    raise ValueError(
                        f"restored MPV AAR has unverified 5.6.8 native entry: {name}"
                    )
            elif data != original.read(name):
                raise ValueError(f"restored MPV AAR changed another entry: {name}")
    return replacement


def verified_iso_replacement(candidate: bytes, replacement: bytes) -> bytes:
    """Accept only addition of immutable FongMi 5.6.8 libisoJNI.so entries."""
    with ZipFile(BytesIO(candidate)) as original, ZipFile(BytesIO(replacement)) as restored:
        before = original.namelist()
        after = restored.namelist()
        if len(before) != len(set(before)) or len(after) != len(set(after)):
            raise ValueError("extractor AAR contains duplicate ZIP entries")
        before_set = set(before)
        if before_set.intersection(PUBLISHED_ISO):
            raise ValueError("candidate extractor unexpectedly already contains native ISO entries")
        if set(after) != before_set | set(PUBLISHED_ISO):
            raise ValueError("restored extractor changed archive inventory unexpectedly")
        for name in before:
            if restored.read(name) != original.read(name):
                raise ValueError(f"restored extractor changed candidate entry: {name}")
        for name, wanted in PUBLISHED_ISO.items():
            observed = hashlib.sha256(restored.read(name)).hexdigest()
            if observed != wanted:
                raise ValueError(f"restored extractor has unverified native ISO entry: {name}")
    return replacement


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifact",
        type=Path,
        help=f"candidate ZIP rebuilt from FongMi/media@{SOURCE_COMMIT}",
    )
    parser.add_argument(
        "--restored-decoder",
        type=Path,
        help="decoder AAR restored from both SHA-verified published APKs",
    )
    parser.add_argument(
        "--restored-mpv",
        type=Path,
        help="MPV AAR restored from both SHA-verified published APKs",
    )
    parser.add_argument(
        "--restored-iso",
        type=Path,
        help="extractor AAR with pinned libisoJNI restored from both published APKs",
    )
    args = parser.parse_args()

    try:
        payload = read_verified_candidate(args.artifact)
        if args.restored_decoder:
            payload[DECODER_NAME] = verified_decoder_replacement(
                payload[DECODER_NAME],
                args.restored_decoder.read_bytes(),
            )
        if args.restored_mpv:
            payload[MPV_NAME] = verified_mpv_replacement(
                payload[MPV_NAME],
                args.restored_mpv.read_bytes(),
            )
        if args.restored_iso:
            payload[ISO_NAME] = verified_iso_replacement(
                payload[ISO_NAME],
                args.restored_iso.read_bytes(),
            )
    except (BadZipFile, KeyError, ValueError, OSError) as error:
        parser.error(str(error))

    dest = ROOT / "app" / "libs"
    dest.mkdir(parents=True, exist_ok=True)
    for filename, data in payload.items():
        (dest / filename).write_bytes(data)

    print(
        f"Imported {len(payload)} verified FongMi/media@{SOURCE_COMMIT} "
        f"candidate AARs to {dest}"
    )
    print(
        "Run scripts/recovery/check-faithful-player-aars.py and the 5.6.8 FFmpeg closure gate next; "
        "full APK packaging is not yet verified."
    )


if __name__ == "__main__":
    main()
