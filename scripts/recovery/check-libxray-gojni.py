#!/usr/bin/env python3
"""Verify the published Go JNI for both ABIs before a faithful build."""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from runpy import run_path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
PUBLISHED = run_path(str(ROOT / "restore-published-libxrayjni.py"))["JNI_SHA256"]


def check(path, official_path=None):
    methods = run_path(str(ROOT / "check-player-java-api.py"))["class_methods"]
    with ZipFile(path) as aar:
        names = aar.namelist()
        if len(names) != len(set(names)):
            raise ValueError("libXray AAR contains duplicate ZIP entries")
        with ZipFile(BytesIO(aar.read("classes.jar"))) as jar:
            actual = methods(jar.read("libXray/LibXray.class"))
            if ("invoke", "(Ljava/lang/String;)Ljava/lang/String;") not in actual:
                raise ValueError("libXray Java invoke(String): String is missing")
        for abi, wanted in PUBLISHED.items():
            name = f"jni/{abi}/libgojni.so"
            if names.count(name) != 1:
                raise ValueError(f"libXray AAR lacks a unique {name}")
            observed = hashlib.sha256(aar.read(name)).hexdigest()
            if observed != wanted:
                raise ValueError(f"{abi} Go JNI SHA-256 differs: {observed}")
            print(f"{abi} Go JNI matches published APK: {observed}")
        if official_path is not None:
            with ZipFile(official_path) as official:
                if official.namelist() != names or len(set(official.namelist())) != len(names):
                    raise ValueError("libXray AAR entry names/order differ from official build")
                replacements = {f"jni/{abi}/libgojni.so" for abi in PUBLISHED}
                for name in names:
                    if name not in replacements and aar.read(name) != official.read(name):
                        raise ValueError(f"libXray AAR changed a non-JNI entry: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aar", type=Path, default=ROOT.parents[1] / "libxray/libs/libXray.aar")
    parser.add_argument("--official-aar", type=Path,
                        help="official AAR extracted from the pinned v26.7.28 ZIP")
    args = parser.parse_args()
    try:
        check(args.aar, args.official_aar)
    except (KeyError, ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
