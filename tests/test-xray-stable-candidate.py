#!/usr/bin/env python3
"""Branch-only official stable libXray candidate audit; never signs or publishes.

The frozen Android client is not changed by this test. Compare its actual Java
normalizer/TOFU request preparation with the complete official AAR, then probe
the new native dispatcher on both ARM ABIs. All requests are synthetic; no
certificate network probe, external ping, or real node is used. QEMU's C
gomobile bridge is not ART, Binder, or TV hardware execution.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "recovery/native-tests"
VERSION = "26.11.9"
LIB_COMMIT = "5a0f7d8d1c28b34afb5727b04b26a10f6dbac7e3"
CORE_COMMIT = "676eaf66f8f05d4d558ee7a74b4736623d3feeb9"
CORE_MODULE = "v1.260327.1-0.20261109052709-676eaf66f8f0"
ZIP_SHA = "1b1aa12124a7112af983a6cea74c77f27aadc6b650acf3c5a57019619ba9fa48"
ZIP_URL = "https://github.com/XTLS/libXray/releases/download/v" + VERSION + "/libxray-android.zip"
JSON_URL = "https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar"
JSON_SHA = "3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(url, digest, dest):
    subprocess.run(["curl", "-fL", "--retry", "2", "--max-time", "300",
                    url, "-o", str(dest)], check=True)
    if sha(dest) != digest:
        raise RuntimeError("Pinned public download digest mismatch: " + dest.name)


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True)


def one(archive, name):
    if archive.namelist().count(name) != 1:
        raise RuntimeError("Missing or duplicate archive entry: " + name)
    return archive.read(name)


def module(path):
    spec = importlib.util.spec_from_file_location("candidate_prepare", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def capture(cases, jni, work, abi, digest):
    if sha(jni) != digest:
        raise RuntimeError("Candidate JNI changed after official archive extraction")
    # Reuse the existing pinned Debian/Android API24 runtime preparation.
    # Override the expected JNI hash only in this imported test module, with
    # the exact member extracted from the SHA-pinned official complete AAR.
    # The golden harness source and golden pins are not changed.
    prep = module(ROOT / "scripts/recovery/prepare-native-converter-harness.py")
    if abi == "armeabi-v7a":
        prep.JNI_SHA = digest
    else:
        prep.ARM64_JNI_SHA = digest
    old_argv = sys.argv
    try:
        sys.argv = [str(prep.__file__), "--abi", abi, "--workdir", str(work),
                    "--jni", str(jni)]
        prep.main()
    finally:
        sys.argv = old_argv
    bridge = work / "invoke-bridge"
    if f"Shared library: [{jni}]" not in run("readelf", "-d", bridge):
        raise RuntimeError("Native harness is not linked to verified candidate JNI")
    arm64 = abi == "arm64-v8a"
    qemu = work / "qemu/usr/bin" / ("qemu-aarch64-static" if arm64 else "qemu-arm-static")
    android = work / "android/root"
    payload = b""
    for _, req in cases:
        raw = json.dumps(req, ensure_ascii=True).encode("utf-8")
        payload += struct.pack("<I", len(raw)) + raw
    dest = work / "candidate-responses"
    # Do not forward CI credentials or arbitrary environment to native code.
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "TMPDIR") if k in os.environ}
    env["NATIVE_CAPTURE"] = str(dest)
    subprocess.run(["sh", "-c", 'exec "$@" 3>"$NATIVE_CAPTURE"', "sh", str(qemu),
                    "-L", str(android), "-E", "LD_LIBRARY_PATH=" +
                    str(android / "system" / ("lib64" if arm64 else "lib")), str(bridge)],
                   input=payload, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   env=env, check=True, timeout=180)
    result = {}
    data = io.BytesIO(dest.read_bytes())
    for label, _ in cases:
        n = data.read(4)
        if len(n) != 4:
            raise RuntimeError("Missing native response: " + label)
        length = struct.unpack("<I", n)[0]
        if length > 16 * 1024 * 1024 or length % 2:
            raise RuntimeError("Invalid native response size: " + label)
        raw = data.read(length)
        if len(raw) != length:
            raise RuntimeError("Truncated native response: " + label)
        result[label] = json.loads(raw.decode("utf-16le"))
    if data.read(1):
        raise RuntimeError("Unexpected additional native response")
    return result


def request(method, payload=None, api=3):
    out = {"apiVersion": api, "method": method}
    if payload is not None:
        out["payload"] = payload
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--abi", choices=["armeabi-v7a", "arm64-v8a"], required=True)
    abi = parser.parse_args().abi
    with tempfile.TemporaryDirectory(prefix="xray-stable-candidate-") as directory:
        tmp = Path(directory).resolve()
        archive = tmp / "official.zip"
        download(ZIP_URL, ZIP_SHA, archive)
        with ZipFile(archive) as z:
            entries = [n for n in z.namelist() if n.split("/")[-1] == "libXray.aar"]
            if len(entries) != 1:
                raise RuntimeError("Expected exactly one complete official AAR")
            aar = tmp / "libXray.aar"
            aar.write_bytes(one(z, entries[0]))
        classes = tmp / "classes.jar"
        jni = tmp / "libgojni.so"
        with ZipFile(aar) as z:
            classes.write_bytes(one(z, "classes.jar"))
            jni.write_bytes(one(z, "jni/" + abi + "/libgojni.so"))
        digest = sha(jni)
        print("VERIFIED official ZIP SHA256", ZIP_SHA, flush=True)
        print("AAR SHA256", sha(aar), "classes.jar SHA256", sha(classes), flush=True)
        print(abi, "JNI SHA256", digest, flush=True)
        header = run("readelf", "-h", jni)
        if not re.search(r"Machine:\s+" + ("ARM" if abi == "armeabi-v7a" else "AArch64") + r"\s*$",
                         header, re.M):
            raise RuntimeError("Wrong ELF machine")
        expected_class = "ELF32" if abi == "armeabi-v7a" else "ELF64"
        if not re.search(r"Class:\s+" + expected_class + r"\s*$", header, re.M):
            raise RuntimeError("Wrong ELF class")
        info = run("go", "version", "-m", jni)
        if "github.com/xtls/xray-core\t" + CORE_MODULE not in info:
            raise RuntimeError("Official AAR embedded Core dependency mismatch")
        print("VERIFIED embedded Core", CORE_MODULE, "official tag commit", CORE_COMMIT, flush=True)
        symbols = run("readelf", "-W", "--dyn-syms", jni)
        if "proxylibXray__Invoke" not in symbols or "Java_libXray_LibXray_invoke" not in symbols:
            raise RuntimeError("Required JNI/gomobile Invoke symbol missing")
        binding = run("javap", "-classpath", classes, "-s", "libXray.LibXray")
        if "invoke(java.lang.String)" not in binding or "(Ljava/lang/String;)Ljava/lang/String;" not in binding:
            raise RuntimeError("Required Java Invoke signature missing")
        jar = tmp / "json.jar"
        download(JSON_URL, JSON_SHA, jar)
        src = ROOT / "xray/src/main/java/com/fingmi/xray"
        subprocess.run(["javac", "--release", "17", "-cp", os.pathsep.join(map(str, [classes, jar])),
                        "-d", str(tmp / "real-binding-compile"), str(src / "core/LibXrayBridge.java")], check=True)
        print("PASS actual Java bridge compiles against official bindings; ART init not tested", flush=True)

        # Run the current real Java normalize/security path with the repository's
        # synthetic pin/probe stubs. No JNI/probe network call occurs in this JVM.
        support = ROOT / "tests/xray-current-chain"
        java_sources = [support / "CurrentNativeChain.java", support / "libXray/LibXray.java",
                        support / "com/fingmi/xray/security/XrayCertificatePins.java",
                        src / "config/XrayShareLinkNormalizer.java", src / "config/XrayConfigFactory.java",
                        src / "core/LibXrayBridge.java", src / "security/XrayShareLinkSecurity.java"]
        compiled = tmp / "normalizer-classes"
        subprocess.run(["javac", "--release", "17", "-cp", str(jar), "-d", str(compiled),
                        *map(str, java_sources)], check=True)
        normalized = tmp / "normalized.json"
        subprocess.run(["java", "-cp", os.pathsep.join(map(str, [jar, compiled])),
                        "CurrentNativeChain", "normalize", str(FIX / "chain-inputs.json"),
                        str(normalized)], check=True)
        rows = json.loads(normalized.read_text())
        if len(rows) != 26:
            raise RuntimeError("Frozen synthetic chain count changed")
        old_conversion = {x["id"]: x["response"] for x in
                          json.loads((FIX / "published-v7-chain.json").read_text())["cases"]}
        old_runtime = json.loads((FIX / "published-v7-runtime-validation.json").read_text())["cases"]
        if len(old_runtime) != 26:
            raise RuntimeError("Frozen runtime count changed")
        cases = [("version-v3", request("xrayVersion")),
                 ("version-v2", request("xrayVersion", api=2)),
                 ("ports-v3", request("getFreePorts", {"count": 1})),
                 ("probe-tls", request("probeTLSCertificate", {})),
                 ("probe-hy2", request("probeHysteria2Certificate", {}))]
        for row in rows:
            original = row["request"]
            cases += [("v2:" + row["id"], original),
                      ("v3:" + row["id"], dict(original, apiVersion=3))]
        for row in old_runtime:
            cases.append(("runtime:" + row["id"], dict(row["request"], apiVersion=3)))
        # Only start a local no-listener blackhole configuration. No outbound
        # node, ping URL or certificate server is supplied.
        blackhole = json.dumps({"log": {"loglevel": "warning"},
                                "inbounds": [],
                                "outbounds": [{"protocol": "blackhole", "tag": "blocked", "settings": {}}]})
        cases += [("before", request("getXrayState")),
                  ("test-local", request("testXray", {"xrayJson": blackhole})),
                  ("run-local", request("runXray", {"xrayJson": blackhole})),
                  ("running", request("getXrayState")),
                  ("stop-local", request("stopXray")),
                  ("after", request("getXrayState"))]
        result = capture(cases, jni, tmp / "native", abi, digest)
        if not result["version-v3"].get("success") or VERSION not in str(result["version-v3"].get("data")):
            raise RuntimeError("Native API v3 did not identify the official Core version")
        print("PASS native candidate identifies", VERSION, flush=True)
        blocked = []
        if not result["version-v2"].get("success"):
            blocked.append("existing API v2 rejected")
        for key in ("probe-tls", "probe-hy2"):
            if result[key].get("error") == "unknown method":
                blocked.append(key + " absent (TOFU contract)")
        v2 = v3 = equal = valid = 0
        for row in rows:
            ident = row["id"]
            a, b = result["v2:" + ident], result["v3:" + ident]
            v2 += bool(a.get("success"))
            v3 += bool(b.get("success"))
            same = b == old_conversion[ident]
            equal += same
            print("CONVERTER", ident, "v2=" + str(a.get("success")),
                  "v3=" + str(b.get("success")), "golden_exact=" + str(same))
            if old_conversion[ident].get("success") and not b.get("success"):
                blocked.append("previously accepted import rejected: " + ident)
        for row in old_runtime:
            ident = row["id"]
            ok = bool(result["runtime:" + ident].get("success"))
            valid += ok
            print("RUNTIME", ident, "v3_validation=" + str(ok))
            if not ok:
                blocked.append("existing runtime rejected: " + ident)
        lifecycle = (result["before"].get("data", {}).get("running") is False
                     and all(result[k].get("success") for k in ("test-local", "run-local", "stop-local"))
                     and result["running"].get("data", {}).get("running") is True
                     and result["after"].get("data", {}).get("running") is False)
        print("SUMMARY", abi, "v2_imports", v2, "/26", "v3_imports", v3, "/26",
              "exact_golden", equal, "/26", "existing_runtime_valid", valid, "/26",
              "local_core_lifecycle", lifecycle, flush=True)
        if not lifecycle:
            blocked.append("local Core lifecycle not verified")
        if equal != len(rows):
            blocked.append("API v3 converter differs from frozen behavior; field-by-field review required")
        for reason in blocked:
            print("INCOMPATIBLE:", reason, flush=True)
        if blocked or v2 != len(rows):
            raise SystemExit("CANDIDATE NOT ELIGIBLE: do not replace the current Core")
        print("Native candidate checks passed; ART/device and security probe compatibility remain separate.")


if __name__ == "__main__":
    main()
