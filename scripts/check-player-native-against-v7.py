#!/usr/bin/env python3
"""Compare candidate Media3 AAR native libraries against the shipped v7 APK.

Usage: python3 scripts/check-player-native-against-v7.py --artifact candidate.zip
   or: python3 scripts/check-player-native-against-v7.py --aar-dir app/libs

Only the ten published-v7 player binaries listed in extract-v7-player-native.py
are checked. This does not establish Java ABI or whole-APK compatibility.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import runpy
from zipfile import ZipFile


SCRIPTS = Path(__file__).resolve().parent
PUBLISHED = runpy.run_path(str(SCRIPTS / "extract-v7-player-native.py"))["PLAYER_BINARIES"]
ARTIFACT_SHA256 = runpy.run_path(str(SCRIPTS / "import-player-aar-candidate.py"))[
    "ARTIFACT_SHA256"
]
NATIVE_AARS = ("lib-mpvplayer-release.aar", "lib-decoder-ffmpeg-release.aar")
ABI = "armeabi-v7a"


def verify_native(aar_bytes: dict[str, bytes]) -> None:
    found = {}
    for aar_name in NATIVE_AARS:
        with ZipFile(BytesIO(aar_bytes[aar_name])) as aar:
            for entry in aar.namelist():
                prefix = f"jni/{ABI}/"
                if not entry.startswith(prefix):
                    continue
                name = entry[len(prefix):]
                if name not in PUBLISHED:
                    continue
                digest = hashlib.sha256(aar.read(entry)).hexdigest()
                if name in found and found[name] != digest:
                    raise ValueError(f"Conflicting copies of {name}")
                found[name] = digest

    missing = set(PUBLISHED) - set(found)
    different = {name: (PUBLISHED[name], found[name]) for name in PUBLISHED
                 if name in found and PUBLISHED[name] != found[name]}
    if missing or different:
        raise ValueError(f"v7 native mismatch: missing={sorted(missing)}, different={different}")
    print(f"EXACT: {len(found)} published-v7 player .so files match SHA-256 byte-for-byte")
    for name in sorted(found):
        print(f"{found[name]}  {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--artifact", type=Path)
    source.add_argument("--aar-dir", type=Path)
    args = parser.parse_args()

    if args.artifact:
        if hashlib.sha256(args.artifact.read_bytes()).hexdigest() != ARTIFACT_SHA256:
            parser.error("Candidate artifact SHA-256 differs from the verified AC run")
        with ZipFile(args.artifact) as archive:
            aar_bytes = {name: archive.read(name) for name in NATIVE_AARS}
    else:
        aar_bytes = {name: (args.aar_dir / name).read_bytes() for name in NATIVE_AARS}
    try:
        verify_native(aar_bytes)
    except (KeyError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
