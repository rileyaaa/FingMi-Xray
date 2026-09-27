#!/usr/bin/env python3
"""Replace only libXray's v7/v8 Go JNI entries from verified release evidence.

Each ABI may come from either the original published APK or the persisted full
JADX ZIP which was produced only after the published APK passed its whole-file
SHA-256 gate. The official libXray AAR remains the base: every entry except the
two Android JNI files must stay byte-identical after repacking.
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
JADX_SHA256 = {
    "armeabi-v7a": "7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d",
    "arm64-v8a": "8d6e2a335a442b9bc2e53f12ec7ab646ebef51df69ae8c54674d25f37035056b",
}
JNI_SHA256 = {
    "armeabi-v7a": "6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e",
    "arm64-v8a": "40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece",
}
OFFICIAL_AAR_SHA256 = "4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_apk_jni(path, abi):
    data = path.read_bytes()
    if digest(data) != APK_SHA256[abi]:
        raise ValueError(f"{path}: APK SHA-256 differs from published {abi} release")
    with ZipFile(BytesIO(data)) as apk:
        name = f"lib/{abi}/libgojni.so"
        if apk.namelist().count(name) != 1:
            raise ValueError(f"{path}: expected exactly one {name}")
        result = apk.read(name)
    if digest(result) != JNI_SHA256[abi]:
        raise ValueError(f"{path}: Go JNI SHA-256 differs from published {abi} library")
    return result


def verified_jadx_jni(path, abi):
    data = path.read_bytes()
    if digest(data) != JADX_SHA256[abi]:
        raise ValueError(f"{path}: JADX artifact SHA-256 differs from pinned evidence")
    with ZipFile(BytesIO(data)) as archive:
        name = f"resources/lib/{abi}/libgojni.so"
        if archive.namelist().count(name) != 1:
            raise ValueError(f"{path}: expected exactly one {name}")
        result = archive.read(name)
    if digest(result) != JNI_SHA256[abi]:
        raise ValueError(f"{path}: Go JNI SHA-256 differs from published {abi} library")
    return result


def verified_source_jni(path, abi, kind):
    if kind == "apk":
        return verified_apk_jni(path, abi)
    if kind == "jadx":
        return verified_jadx_jni(path, abi)
    raise ValueError(f"unsupported source kind: {kind}")


def restore(aar_path, source_paths, source_kinds, output_path):
    if output_path.exists():
        raise ValueError("refusing to overwrite an existing output")
    if not output_path.parent.is_dir():
        raise ValueError("output parent directory does not exist")

    aar_bytes = aar_path.read_bytes()
    if digest(aar_bytes) != OFFICIAL_AAR_SHA256:
        raise ValueError("official libXray AAR SHA-256 differs from pinned v26.7.28 build")

    replacement = {
        f"jni/{abi}/libgojni.so": verified_source_jni(
            source_paths[abi], abi, source_kinds[abi])
        for abi in APK_SHA256
    }

    with ZipFile(BytesIO(aar_bytes)) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError("official AAR contains duplicate ZIP entries")
        if any(names.count(name) != 1 for name in replacement):
            raise ValueError("official AAR lacks exactly one Go JNI entry per restored ABI")

        output = BytesIO()
        with ZipFile(output, "w") as target:
            for info in source.infolist():
                name = info.filename
                data = replacement[name] if name in replacement else source.read(info)
                target.writestr(copy(info), data)

        with ZipFile(BytesIO(output.getvalue())) as rebuilt:
            if rebuilt.namelist() != names:
                raise ValueError("AAR ZIP entry names/order changed")
            for name in names:
                expected = replacement[name] if name in replacement else source.read(name)
                if rebuilt.read(name) != expected:
                    raise ValueError(f"unexpected AAR entry change: {name}")

    output_path.write_bytes(output.getvalue())
    return {abi: digest(replacement[f"jni/{abi}/libgojni.so"]) for abi in APK_SHA256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-aar", required=True, type=Path)

    v7 = parser.add_mutually_exclusive_group(required=True)
    v7.add_argument("--v7-apk", type=Path)
    v7.add_argument("--v7-jadx", type=Path)

    v8 = parser.add_mutually_exclusive_group(required=True)
    v8.add_argument("--v8-apk", type=Path)
    v8.add_argument("--v8-jadx", type=Path)

    parser.add_argument("--to", required=True, type=Path)
    args = parser.parse_args()

    paths = {
        "armeabi-v7a": args.v7_apk or args.v7_jadx,
        "arm64-v8a": args.v8_apk or args.v8_jadx,
    }
    kinds = {
        "armeabi-v7a": "apk" if args.v7_apk else "jadx",
        "arm64-v8a": "apk" if args.v8_apk else "jadx",
    }

    try:
        hashes = restore(args.official_aar, paths, kinds, args.to)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))

    for abi, value in hashes.items():
        print(f"published {abi} libgojni.so SHA-256 {value}")
    print(f"restored AAR SHA-256 {digest(args.to.read_bytes())}")


if __name__ == "__main__":
    main()
