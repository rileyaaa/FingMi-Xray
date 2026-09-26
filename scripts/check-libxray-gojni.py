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


def check(path):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aar", type=Path, default=ROOT.parent / "libxray/libs/libXray.aar")
    args = parser.parse_args()
    try:
        check(args.aar)
    except (KeyError, ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
