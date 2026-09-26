#!/usr/bin/env python3
"""Replace only libXray's Go JNI entries from two verified release APKs.

The official AAR is the input; the output must be a new file. Every non-JNI
entry remains byte-identical after repacking.
"""

import argparse
from copy import copy
import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile


APK_SHA256 = {
    "armeabi-v7a": "cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda",
    "arm64-v8a": "b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_jni(apk_path, abi):
    data = apk_path.read_bytes()
    if digest(data) != APK_SHA256[abi]:
        raise ValueError(f"{apk_path}: APK SHA-256 differs from published {abi} release")
    with ZipFile(BytesIO(data)) as apk:
        name = f"lib/{abi}/libgojni.so"
        if apk.namelist().count(name) != 1:
            raise ValueError(f"{apk_path}: expected exactly one {name}")
        result = apk.read(name)
    if not result:
        raise ValueError(f"{apk_path}: empty {name}")
    return result


def restore(aar_path, apk_paths, output_path):
    if output_path.exists():
        raise ValueError("refusing to overwrite an existing output")
    if not output_path.parent.is_dir():
        raise ValueError("output parent directory does not exist")
    replacement = {
        f"jni/{abi}/libgojni.so": verified_jni(apk_paths[abi], abi)
        for abi in APK_SHA256
    }
    with ZipFile(aar_path) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError("official AAR contains duplicate ZIP entries")
        if any(names.count(name) != 1 for name in replacement):
            raise ValueError("official AAR lacks exactly one Go JNI entry per ABI")
        output = BytesIO()
        with ZipFile(output, "w") as target:
            for info in source.infolist():
                name = info.filename
                data = replacement[name] if name in replacement else source.read(info)
                target.writestr(copy(info), data)
        with ZipFile(BytesIO(output.getvalue())) as rebuilt:
            if rebuilt.namelist() != names:
                raise ValueError("AAR ZIP entry order changed")
            for name in names:
                expected = replacement[name] if name in replacement else source.read(name)
                if rebuilt.read(name) != expected:
                    raise ValueError(f"unexpected AAR entry change: {name}")
    output_path.write_bytes(output.getvalue())
    return {abi: digest(replacement[f"jni/{abi}/libgojni.so"]) for abi in APK_SHA256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-aar", required=True, type=Path)
    parser.add_argument("--v7-apk", required=True, type=Path)
    parser.add_argument("--v8-apk", required=True, type=Path)
    parser.add_argument("--to", required=True, type=Path)
    args = parser.parse_args()
    try:
        hashes = restore(args.official_aar, {
            "armeabi-v7a": args.v7_apk,
            "arm64-v8a": args.v8_apk,
        }, args.to)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    for abi, value in hashes.items():
        print(f"published {abi} libgojni.so SHA-256 {value}")
    print(f"restored AAR SHA-256 {digest(args.to.read_bytes())}")


if __name__ == "__main__":
    main()
