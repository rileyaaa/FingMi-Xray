#!/usr/bin/env python3
"""Inspect published libXray Go JNI evidence without executing Android code."""

import argparse
import hashlib
import re
import subprocess
import tempfile
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
XRAY_CORE = "v1.260327.1-0.20260728075948-5ca6f4b7d4dc"
REQUIRED_SYMBOLS = (
    "github.com/xtls/libxray.Invoke",
    "github.com/xtls/libxray.invokeProbeTLSCertificate",
    "github.com/xtls/libxray.invokeProbeHysteria2Certificate",
    "github.com/xtls/libxray.invokeTestXray",
    "github.com/xtls/libxray.invokeRunXray",
    "github.com/xtls/libxray.invokePingBatch",
    "github.com/xtls/libxray/share.transportFieldsFromURLQuery",
    "github.com/xtls/libxray/share.transportFieldsFromVmessQR",
    "github.com/xtls/libxray/share.buildStreamFromTransportFields",
    "github.com/xtls/libxray/share.buildHy2FinalMask",
    "github.com/xtls/libxray/share.xrayShareLink.hysteriaOutbound",
    "github.com/xtls/libxray/share.xrayShareLink.trojanOutbound",
    "github.com/xtls/libxray/share.normalizeHysteriaMultiPortLink",
    "github.com/xtls/libxray/share.normalizeHysteriaPinSHA256",
    "github.com/xtls/libxray/share.normalizeLegacyShadowsocksLink",
    "github.com/xtls/libxray/share.legacyKCPMTU",
    "github.com/xtls/libxray/share.legacyKCPFinalMask",
    "github.com/xtls/libxray/share.parseSharePort",
    "github.com/xtls/libxray/share.parseShareALPN",
    "github.com/xtls/libxray/share.decodeShareUserInfo",
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE).stdout


def extract_apk(path, abi):
    data = path.read_bytes()
    if sha256(data) != APK_SHA256[abi]:
        raise ValueError(f"{path}: APK SHA-256 differs from pinned {abi} release")
    name = f"lib/{abi}/libgojni.so"
    with ZipFile(path) as archive:
        if archive.namelist().count(name) != 1:
            raise ValueError(f"{path}: expected exactly one {name}")
        return archive.read(name)


def extract_jadx(path, abi):
    data = path.read_bytes()
    if sha256(data) != JADX_SHA256[abi]:
        raise ValueError(f"{path}: JADX ZIP SHA-256 differs from pinned {abi} evidence")
    name = f"resources/lib/{abi}/libgojni.so"
    with ZipFile(path) as archive:
        if archive.namelist().count(name) != 1:
            raise ValueError(f"{path}: expected exactly one {name}")
        return archive.read(name)


def inspect(data, abi):
    observed = sha256(data)
    if observed != JNI_SHA256[abi]:
        raise ValueError(f"{abi} libgojni.so SHA-256 differs: {observed}")
    with tempfile.TemporaryDirectory() as tmp:
        so = Path(tmp) / "libgojni.so"
        so.write_bytes(data)
        build = run("go", "version", "-m", str(so))
        nm = run("go", "tool", "nm", "-size", "-sort", "name", str(so))
        invoke = run("go", "tool", "objdump", "-s", "github.com/xtls/libxray.Invoke", str(so))
        test = run("go", "tool", "objdump", "-s", "github.com/xtls/libxray.invokeTestXray", str(so))
        runx = run("go", "tool", "objdump", "-s", "github.com/xtls/libxray.invokeRunXray", str(so))

    if f"dep\tgithub.com/xtls/xray-core\t{XRAY_CORE}" not in build:
        raise ValueError(f"{abi}: unexpected Xray-core build dependency")
    if "github.com/xtls/libxray" not in build or "libXray-final" not in build:
        raise ValueError(f"{abi}: custom local libXray replacement path is missing")
    missing = [symbol for symbol in REQUIRED_SYMBOLS if symbol not in nm]
    if missing:
        raise ValueError(f"{abi}: missing native symbols: {', '.join(missing)}")

    # The shipped custom invoke.go validates API v2 at source line 95. Both
    # architectures preserve source line tables; accept architecture-specific
    # compare spellings but require the line-95 compare against literal 2.
    api_v2_lines = [line for line in invoke.splitlines() if "invoke.go:95" in line]
    if not any(re.search(r"(?:CMP|CMN).*\$2(?:\D|$)", line) for line in api_v2_lines):
        raise ValueError(f"{abi}: native Invoke does not show the API v2 compare")

    for label, dump in (("testXray", test), ("runXray", runx)):
        if 'XrayJson string "json:\\"xrayJson,omitempty\\""' not in dump:
            raise ValueError(f"{abi}: {label} does not decode inline xrayJson")

    return {
        "abi": abi,
        "jni_sha256": observed,
        "api": "v2",
        "xray_core": XRAY_CORE,
        "custom_probes": True,
        "inline_xray_json": True,
        "share_transport_symbols": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    v7 = parser.add_mutually_exclusive_group(required=True)
    v7.add_argument("--v7-apk", type=Path)
    v7.add_argument("--v7-jadx", type=Path)
    v8 = parser.add_mutually_exclusive_group(required=True)
    v8.add_argument("--v8-apk", type=Path)
    v8.add_argument("--v8-jadx", type=Path)
    args = parser.parse_args()
    inputs = (
        ("armeabi-v7a", args.v7_apk or args.v7_jadx, extract_apk if args.v7_apk else extract_jadx),
        ("arm64-v8a", args.v8_apk or args.v8_jadx, extract_apk if args.v8_apk else extract_jadx),
    )
    for abi, path, extractor in inputs:
        result = inspect(extractor(path, abi), abi)
        print(" ".join(f"{key}={value}" for key, value in result.items()))

if __name__ == "__main__":
    main()
