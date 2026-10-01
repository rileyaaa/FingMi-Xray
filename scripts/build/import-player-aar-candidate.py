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
    args = parser.parse_args()

    try:
        payload = read_verified_candidate(args.artifact)
        if args.restored_decoder:
            payload[DECODER_NAME] = verified_decoder_replacement(
                payload[DECODER_NAME],
                args.restored_decoder.read_bytes(),
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
        "Run scripts/recovery/check-faithful-player-aars.py and the FFmpeg JNI gate next; "
        "full ABI is not yet verified."
    )


if __name__ == "__main__":
    main()
