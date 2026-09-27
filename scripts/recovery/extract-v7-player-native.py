#!/usr/bin/env python3
"""Recover the exact v7 player native dependencies from a verified release APK/JADX ZIP.

Usage: python3 scripts/recovery/extract-v7-player-native.py --apk release-v7.apk --to /tmp/native
   or: python3 scripts/recovery/extract-v7-player-native.py --jadx v7-jadx.zip --to /tmp/native

The ZIP variant independently verifies every extracted binary against the
published-v7 APK evidence; its archive itself does not need to be trusted.
"""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile


APK_SHA256 = "cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda"
PLAYER_BINARIES = {
    "libmpv.so": "a1251ce2b22160cbc218889231ab990a68047a5264ebc650b5cc9abec0d4b237",
    "libplayer.so": "76b7ed911d362ada779e194bbe6dbb8af146dc52d18c790725ea1786b9f48a46",
    "libavcodec.so": "1de6984959ece4fc684bb42356c20c200c7b92f9e8b56bb09dcbde91eb75eb8a",
    "libavdevice.so": "87512ec224f420d9e9b8530cc05ca7dae45e6803d8cb3228e9a1d1ecaa9397a6",
    "libavfilter.so": "014a4e78d47ecc1c881c9f274eb9d9640fd5903b46aaea2b74b35966d145ad83",
    "libavformat.so": "6673cdfd05e0eede63cf9a9e038a8d3271f7937fd0b1e7a10cb76b1c775eba86",
    "libavutil.so": "01fbcd13ee61c5b6a23a9c4b650f3e08b263f0aa8f6d580d1c6d7d908587695c",
    "libswresample.so": "7ee3052b57204fbdc7e4500e8c73338c02bfe13be5ead157bfc7e8fe14ab4f3b",
    "libswscale.so": "89d34e966ae9420e3f7a91a8545ac509aaa1b8b8059df9d055d7e0bcead59ea4",
    "libc++_shared.so": "af383654daf4cf0829615460419a180f84edd9d8bf51aa0f81ed0db811bf8491",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--apk", type=Path, help="published armeabi-v7a APK")
    source.add_argument("--jadx", type=Path, help="JADX ZIP containing resources/lib")
    parser.add_argument("--to", required=True, type=Path, help="destination for v7 .so files")
    args = parser.parse_args()

    archive_path = args.apk or args.jadx
    if args.apk and sha256(archive_path.read_bytes()) != APK_SHA256:
        parser.error("APK SHA-256 is not the published v7 release")
    prefix = "lib/armeabi-v7a/" if args.apk else "resources/lib/armeabi-v7a/"
    verified = {}
    with ZipFile(archive_path) as archive:
        for name, expected in PLAYER_BINARIES.items():
            data = archive.read(prefix + name)
            if sha256(data) != expected:
                parser.error(f"{name} differs from the published v7 binary")
            verified[name] = data

    args.to.mkdir(parents=True, exist_ok=True)
    for name, data in verified.items():
        (args.to / name).write_bytes(data)
    print(f"Verified and extracted {len(verified)} published-v7 player libraries to {args.to}")


if __name__ == "__main__":
    main()
