#!/usr/bin/env python3
"""Build a libXray AAR whose Java gomobile bindings match the published Go JNI.

The current Xray API v2 native libraries come from the verified v5.6.0-xray.5
release. They must not be combined with the older official v26.7.28 generated
Java bindings: gomobile initializes Java model classes from native code, so the
Java binding set and libgojni.so form one ABI unit.

This builder keeps the pinned official v26.7.28 AAR as the outer container,
reconstructs the published libXray/go Java bindings from the verified ARMv7
APK, and restores the verified v7/v8 libgojni.so payloads from the matching
published APKs. All other AAR entries remain byte-identical to the official
container.
"""

import argparse
from copy import copy
import hashlib
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


APK_SHA256 = {
    "armeabi-v7a": "cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda",
    "arm64-v8a": "b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d",
}
JNI_SHA256 = {
    "armeabi-v7a": "6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e",
    "arm64-v8a": "40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece",
}
OFFICIAL_AAR_SHA256 = "4708a361a74f7e955635dbe3661cefb459bdc867423c3b1826a2c5a6ea4ac77d"

# These classes are known from published API-v2 evidence. AgeDecryptConfig is
# also the class whose absence caused the Android 12 CheckJNI abort.
REQUIRED_BINDINGS = {
    "libXray/LibXray.class",
    "libXray/AgeDecryptConfig.class",
    "libXray/GenerateAgeKeyPairResponse.class",
    "libXray/ProbeTLSCertificateRequest.class",
    "libXray/ProbeHysteria2CertificateRequest.class",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_apk(path, abi):
    data = path.read_bytes()
    observed = digest(data)
    wanted = APK_SHA256[abi]
    if observed != wanted:
        raise ValueError(
            f"{path}: APK SHA-256 differs for {abi}: {observed} != {wanted}")
    return data


def verified_jni(path, abi):
    data = verified_apk(path, abi)
    with ZipFile(BytesIO(data)) as apk:
        name = f"lib/{abi}/libgojni.so"
        if apk.namelist().count(name) != 1:
            raise ValueError(f"{path}: expected exactly one {name}")
        result = apk.read(name)
    observed = digest(result)
    wanted = JNI_SHA256[abi]
    if observed != wanted:
        raise ValueError(
            f"{path}: Go JNI SHA-256 differs for {abi}: {observed} != {wanted}")
    return result


def decompile_published_bindings(jadx, apk_path, work_dir):
    jadx_out = work_dir / "jadx"
    if jadx_out.exists():
        shutil.rmtree(jadx_out)
    jadx_out.mkdir(parents=True)

    command = [
        str(jadx),
        "--comments-level", "warn",
        "--no-res",
        "-d", str(jadx_out),
        str(apk_path),
    ]
    completed = subprocess.run(command, check=False)
    sources = jadx_out / "sources"

    # JADX may return non-zero for unrelated application classes. The binding
    # packages are the acceptance gate; never silently continue without them.
    for package in ("libXray", "go"):
        if not (sources / package).is_dir():
            raise ValueError(
                f"JADX exit {completed.returncode}: published {package} sources are missing")

    required_sources = {
        sources / entry.replace(".class", ".java")
        for entry in REQUIRED_BINDINGS
    }
    missing = sorted(str(path.relative_to(sources))
                     for path in required_sources if not path.is_file())
    if missing:
        raise ValueError(
            "published APK lacks required gomobile binding sources: "
            + ", ".join(missing))

    java_sources = sorted(
        list((sources / "libXray").rglob("*.java"))
        + list((sources / "go").rglob("*.java"))
    )
    if not java_sources:
        raise ValueError("published APK produced no libXray/go Java sources")
    return java_sources, completed.returncode


def compile_bindings(java_sources, android_jar, work_dir):
    classes_dir = work_dir / "classes"
    if classes_dir.exists():
        shutil.rmtree(classes_dir)
    classes_dir.mkdir(parents=True)

    command = [
        "javac",
        "-encoding", "UTF-8",
        "-source", "8",
        "-target", "8",
        "-Xlint:-options",
        "-classpath", str(android_jar),
        "-d", str(classes_dir),
        *[str(path) for path in java_sources],
    ]
    subprocess.run(command, check=True)

    compiled = {}
    for package in ("libXray", "go"):
        package_dir = classes_dir / package
        if not package_dir.is_dir():
            raise ValueError(f"compiled {package} binding package is missing")
        for path in sorted(package_dir.rglob("*.class")):
            compiled[path.relative_to(classes_dir).as_posix()] = path.read_bytes()

    missing = sorted(REQUIRED_BINDINGS - compiled.keys())
    if missing:
        raise ValueError(
            "compiled published bindings lack required classes: " + ", ".join(missing))
    return compiled


def rebuilt_classes_jar(official_classes, published_classes):
    output = BytesIO()
    with ZipFile(BytesIO(official_classes)) as source:
        names = source.namelist()
        if len(names) != len(set(names)):
            raise ValueError("official libXray classes.jar has duplicate entries")

        with ZipFile(output, "w", compression=ZIP_DEFLATED) as target:
            for info in source.infolist():
                name = info.filename
                if name.startswith("libXray/") or name.startswith("go/"):
                    continue
                target.writestr(copy(info), source.read(info))
            for name in sorted(published_classes):
                target.writestr(name, published_classes[name])

    with ZipFile(BytesIO(output.getvalue())) as rebuilt:
        present = set(rebuilt.namelist())
        missing = sorted(REQUIRED_BINDINGS - present)
        if missing:
            raise ValueError(
                "rebuilt classes.jar lacks required published bindings: "
                + ", ".join(missing))
    return output.getvalue()


def build(official_aar, v7_apk, v8_apk, jadx, android_jar, work_dir, output_path):
    if output_path.exists():
        raise ValueError("refusing to overwrite an existing output")
    if not output_path.parent.is_dir():
        raise ValueError("output parent directory does not exist")
    if not jadx.is_file():
        raise ValueError(f"JADX executable is missing: {jadx}")
    if not android_jar.is_file():
        raise ValueError(f"Android platform jar is missing: {android_jar}")

    official_bytes = official_aar.read_bytes()
    observed_official = digest(official_bytes)
    if observed_official != OFFICIAL_AAR_SHA256:
        raise ValueError(
            "official libXray AAR SHA-256 differs from pinned v26.7.28 build: "
            f"{observed_official}")

    # The Java binding is ABI-independent. Recover it from the verified v7 APK,
    # then pair it with each ABI's verified native library from the same release.
    verified_apk(v7_apk, "armeabi-v7a")
    java_sources, jadx_status = decompile_published_bindings(jadx, v7_apk, work_dir)
    published_classes = compile_bindings(java_sources, android_jar, work_dir)

    native = {
        "jni/armeabi-v7a/libgojni.so": verified_jni(v7_apk, "armeabi-v7a"),
        "jni/arm64-v8a/libgojni.so": verified_jni(v8_apk, "arm64-v8a"),
    }

    with ZipFile(BytesIO(official_bytes)) as official:
        names = official.namelist()
        if len(names) != len(set(names)):
            raise ValueError("official libXray AAR contains duplicate entries")
        if names.count("classes.jar") != 1:
            raise ValueError("official libXray AAR lacks exactly one classes.jar")
        for name in native:
            if names.count(name) != 1:
                raise ValueError(f"official libXray AAR lacks exactly one {name}")

        classes_jar = rebuilt_classes_jar(
            official.read("classes.jar"), published_classes)

        output = BytesIO()
        with ZipFile(output, "w") as target:
            for info in official.infolist():
                name = info.filename
                if name == "classes.jar":
                    data = classes_jar
                elif name in native:
                    data = native[name]
                else:
                    data = official.read(info)
                target.writestr(copy(info), data)

    output_path.write_bytes(output.getvalue())

    # Final contract check: only classes.jar and the two v7/v8 native entries
    # may differ from the official container.
    with ZipFile(BytesIO(official_bytes)) as official, ZipFile(output_path) as rebuilt:
        if rebuilt.namelist() != official.namelist():
            raise ValueError("rebuilt libXray AAR entry names/order changed")
        allowed = {"classes.jar", *native.keys()}
        for name in official.namelist():
            if name not in allowed and rebuilt.read(name) != official.read(name):
                raise ValueError(f"unexpected libXray AAR entry change: {name}")
        with ZipFile(BytesIO(rebuilt.read("classes.jar"))) as classes:
            missing = sorted(REQUIRED_BINDINGS - set(classes.namelist()))
            if missing:
                raise ValueError(
                    "final AAR lacks required published bindings: " + ", ".join(missing))

    return {
        "jadx_status": jadx_status,
        "java_source_count": len(java_sources),
        "class_count": len(published_classes),
        "aar_sha256": digest(output_path.read_bytes()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-aar", required=True, type=Path)
    parser.add_argument("--v7-apk", required=True, type=Path)
    parser.add_argument("--v8-apk", required=True, type=Path)
    parser.add_argument("--jadx", required=True, type=Path)
    parser.add_argument("--android-jar", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--to", required=True, type=Path)
    args = parser.parse_args()

    args.work_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = build(
            args.official_aar,
            args.v7_apk,
            args.v8_apk,
            args.jadx,
            args.android_jar,
            args.work_dir,
            args.to,
        )
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))

    print(
        "rebuilt libXray with published gomobile bindings: "
        f"{result['java_source_count']} Java sources -> "
        f"{result['class_count']} classes; JADX exit={result['jadx_status']}")
    for abi, value in JNI_SHA256.items():
        print(f"published {abi} libgojni.so SHA-256 {value}")
    print(f"rebuilt libXray AAR SHA-256 {result['aar_sha256']}")


if __name__ == "__main__":
    main()
