#!/usr/bin/env python3
"""Check 10 arm64-v8a player libraries against published-v8 JADX evidence.

The digest inventory was read from historical workflow artifact 10825963688,
original-v8-jadx.zip SHA-256 8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b.
Only the ten selected files are checked; no Java ABI/build claim is made.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import runpy
from zipfile import ZipFile


PUBLISHED = {
    "libavcodec.so": "54c02b9013743ed58b5eff5673e800b3552bf6beab301ef8bee788e067d40f79",
    "libavdevice.so": "d522c475d5d5157d3101946fda17d45fb054fc98da12d792c3778d45b19618f0",
    "libavfilter.so": "c4b47f3fb22ff72ccf03611f26fe9418714886d9023b91475538ca0d811a4e24",
    "libavformat.so": "805443787223a4f6c15876aeb9f505c7bdfb8c754bb22418d7b515bf88077717",
    "libavutil.so": "8b5dd5d6d1cf3a162709630439b39ac8acdc8831a83955345c733c1a6d3f3529",
    "libc++_shared.so": "c4c2fe5cbcb1fba0003a31fc7ab29a9bb12df6cc187ec45a806462540e83d93b",
    "libmpv.so": "b1f2061e4868731236d407fdb7ac494a472d937fa9ce909f982cec82f9b96802",
    "libplayer.so": "3113925b69fbe077f73433c04a601ec21be40aa20db764efb552bc9bb1f18d3a",
    "libswresample.so": "aeab0a7a36fbb7ce5a8f341509d35e45a2017cc3b78f49ad3df964303e522059",
    "libswscale.so": "bccbfe95f2b3456410c2931805d370afaa16a3fef2ed43ff6e31b1859065a8ef",
}

SCRIPTS = Path(__file__).resolve().parent
ARTIFACT_SHA256 = runpy.run_path(str(SCRIPTS / "import-player-aar-candidate.py"))[
    "ARTIFACT_SHA256"
]
NATIVE_AARS = ("lib-mpvplayer-release.aar", "lib-decoder-ffmpeg-release.aar")


def verify_native(aar_bytes: dict[str, bytes]) -> None:
    found = {}
    for aar_name in NATIVE_AARS:
        with ZipFile(BytesIO(aar_bytes[aar_name])) as aar:
            for entry in aar.namelist():
                prefix = "jni/arm64-v8a/"
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
        raise ValueError(f"v8 native mismatch: missing={sorted(missing)}, different={different}")
    print(f"EXACT: {len(found)} published-v8 player .so files match SHA-256 byte-for-byte")
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
