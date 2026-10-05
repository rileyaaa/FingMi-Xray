#!/usr/bin/env python3
"""Verify the persistent private-project key and signed release APK identity."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
A = "{http://schemas.android.com/apk/res/android}"


def capture(command, env=None):
    result = subprocess.run(command, capture_output=True, env=env, check=False)
    if result.returncode:
        # Never echo signing properties/passwords or failed keytool arguments.
        raise SystemExit(f"{Path(command[0]).name} verification failed (exit {result.returncode})")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path)
    parser.add_argument("--sdk", type=Path)
    parser.add_argument("--source-sha", help="Expected packaged Git revision; defaults to HEAD")
    args = parser.parse_args()
    expected = (ROOT / "signing/release-certificate.sha256").read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise SystemExit("Invalid pinned release certificate digest")
    properties = dict(line.split("=", 1) for line in
                      (ROOT / "signing/release-signing.properties").read_text().splitlines()
                      if line and not line.startswith("#"))
    env = dict(os.environ)
    env["FINGMI_VERIFY_STORE_PASSWORD"] = properties["storePassword"]
    certificate = capture([
        shutil.which("keytool") or "keytool", "-exportcert",
        "-keystore", str(ROOT / properties["storeFile"]),
        "-alias", properties["keyAlias"],
        "-storepass:env", "FINGMI_VERIFY_STORE_PASSWORD",
    ], env)
    if hashlib.sha256(certificate).hexdigest() != expected:
        raise SystemExit("Release keystore does not match the pinned certificate")
    print("PASS persistent release certificate:", expected)
    if not args.apk:
        return
    if not args.sdk:
        parser.error("--sdk is required with --apk")
    sdk = args.sdk
    tools = sdk / "build-tools/37.0.0"
    output = capture([str(tools / "apksigner"), "verify", "--verbose", "--print-certs",
                      str(args.apk)]).decode()
    # Build Tools 37 reports "V2 Signer:"; older tools use "Signer #1".
    signers = re.findall(
        r"(?m)^(?:Signer #\d+:?|V\d+(?:\.\d+)? Signer:) "
        r"certificate SHA-256 digest: ([0-9a-f]+)", output)
    if set(signers) != {expected} or "Number of signers: 1" not in output:
        raise SystemExit("APK is not signed solely by the persistent release certificate")
    capture([str(tools / "zipalign"), "-c", "-P", "16", "-v", "4", str(args.apk)])
    # apkanalyzer's launcher can merge JAVA_TOOL_OPTIONS into stdout. Preserve
    # those JVM options via JAVA_OPTS so manifest output remains valid XML.
    manifest_env = dict(os.environ)
    inherited = manifest_env.pop("JAVA_TOOL_OPTIONS", "")
    manifest_env["JAVA_OPTS"] = manifest_env.get("JAVA_OPTS", "") + " " + inherited
    manifest = ET.fromstring(capture([
        str(sdk / "cmdline-tools/latest/bin/apkanalyzer"), "manifest", "print", str(args.apk)
    ], manifest_env).decode())
    gradle = (ROOT / "app/build.gradle").read_text()
    name = re.search(r'versionName "([^"]+)"', gradle).group(1)
    code = re.search(r'versionCode (\d+)', gradle).group(1)
    application = manifest.find("application")
    if (manifest.get("package") != "com.fongmi.android.tv"
            or manifest.get(A + "versionName") != name
            or manifest.get(A + "versionCode") != code
            or application is None
            or application.get(A + "debuggable", "false") != "false"
            or application.get(A + "testOnly", "false") != "false"):
        raise SystemExit("APK package/version or non-debuggable release contract failed")
    source_sha = args.source_sha or capture([
        "git", "-C", str(ROOT), "rev-parse", "HEAD"
    ]).decode().strip()
    with ZipFile(args.apk) as archive:
        vcs = archive.read("META-INF/version-control-info.textproto").decode()
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha) or f'revision: "{source_sha}"' not in vcs:
        raise SystemExit("APK embedded Git revision differs from expected build source")
    print(f"PASS {args.apk.name}: {name}, versionCode={code}, source={source_sha}, "
          "release signature and 16 KB alignment")


if __name__ == "__main__":
    main()
