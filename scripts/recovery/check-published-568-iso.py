#!/usr/bin/env python3
"""Verify an extractor AAR matches the pinned FongMi 5.6.8 native ISO payload."""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import sys
from zipfile import ZipFile

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from published_568_iso_contract import NATIVE_SHA256  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aar", required=True, type=Path)
    args = parser.parse_args()
    if not args.aar.is_file():
        parser.error(f"missing AAR: {args.aar}")

    try:
        with ZipFile(args.aar) as archive:
            names = archive.namelist()
            if names.count("classes.jar") != 1:
                raise ValueError("extractor AAR must contain exactly one classes.jar")
            with ZipFile(BytesIO(archive.read("classes.jar"))) as classes:
                if classes.namelist().count(
                    "androidx/media3/extractor/iso/udf/NativeUdfFileSystem.class"
                ) != 1:
                    raise ValueError("extractor AAR lacks NativeUdfFileSystem.class")
            for abi, expected in NATIVE_SHA256.items():
                for soname, wanted in expected.items():
                    entry = f"jni/{abi}/{soname}"
                    if names.count(entry) != 1:
                        raise ValueError(f"expected exactly one {entry}")
                    observed = sha256(archive.read(entry))
                    if observed != wanted:
                        raise ValueError(f"{entry}: expected {wanted}, observed {observed}")
                    print(f"PASS {abi} {soname} {observed}")
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
