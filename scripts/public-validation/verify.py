#!/usr/bin/env python3
"""Frozen source public validation. No production key or publication path."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
L = json.loads((ROOT / "scripts/public-validation/lock.json").read_text())
A = "{http://schemas.android.com/apk/res/android}"


def run(*args, env=None):
    return subprocess.check_output(list(map(str, args)), text=True, env=env).strip()


def scope():
    assert not (ROOT / "signing").exists()
    assert os.environ["GITHUB_REF"] == "refs/heads/dev/frozen-public-validation"
    assert run("git", "-C", ROOT, "rev-parse", "--is-shallow-repository") == "true"
    blobs = {}
    for row in subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "-r", "-z", "HEAD"]).split(b"\0"):
        if not row:
            continue
        meta, name = row.split(b"\t", 1)
        name = name.decode()
        assert not name.startswith("signing/")
        if name not in L["allowed_changed"]:
            blobs[name] = meta.decode().split()[2]
    assert blobs == L["unchanged"], "Frozen production/dependency blobs changed"
    for path in L["formal_workflows"]:
        s = (ROOT / path).read_text()
        assert "if: $" + "{{ false }}" in s
        assert not re.search(r"\b(?:contents|actions):\s*write", s)
    s = (ROOT / L["validation_workflow"]).read_text()
    assert not re.search(r"contents:\s*write|actions:\s*write|secrets\.|upload-artifact|GH_TOKEN|gh release|scripts/build/(?:publish-current-release|resume-verified-release)\.py", s)
    g = (ROOT / "app/build.gradle").read_text()
    # The ABI finalizer explicitly reads android.signingConfigs.release.
    # Its name is a Gradle contract, not permission to use a formal key.
    # Require the exact test-only definition, with no second storeFile.
    assert """def testKeystorePath = System.getenv('FINGMI_TEST_KEYSTORE')
if (!testKeystorePath || !file(testKeystorePath).isFile()) throw new GradleException('CI-only test keystore required')""" in g
    assert """    signingConfigs {
        release {
            storeFile file(testKeystorePath)
            storeType 'JKS'
            keyAlias 'androiddebugkey'
            keyPassword 'android'
            storePassword 'android'
        }
    }""" in g
    assert g.count("signingConfigs {") == 1 and g.count("storeFile") == 1
    assert g.count("signingConfig = signingConfigs.release") == 2
    assert "signingConfig = signingConfigs.debug" not in g
    assert "signing/release-signing.properties" not in g and "releaseSigning" not in g
    assert 'versionName "v5.6.3-xray.2"' in g and "versionCode 563002" in g
    print("PASS frozen source scope:", len(blobs), "unchanged tracked blobs")


def metadata(apk):
    sdk = Path(os.environ.get("ANDROID_HOME", "/usr/local/lib/android/sdk"))
    tools = sdk / "build-tools/37.0.0"
    out = run(tools / "apksigner", "verify", "--verbose", "--print-certs", apk)
    signers = set(re.findall(r"(?m)^(?:Signer #\d+:?|V\d+(?:\.\d+)? Signer:) certificate SHA-256 digest: ([0-9a-f]+)", out))
    assert len(signers) == 1 and "Number of signers: 1" in out
    assert re.search(r"(?im)^Verified using v2 scheme .*:\s*true", out)
    run(tools / "zipalign", "-c", "-P", "16", "-v", "4", apk)
    env = dict(os.environ)
    env["JAVA_OPTS"] = env.get("JAVA_OPTS", "") + " " + env.pop("JAVA_TOOL_OPTIONS", "")
    xml = ET.fromstring(run(sdk / "cmdline-tools/latest/bin/apkanalyzer", "manifest", "print", apk, env=env))
    app = xml.find("application")
    assert app is not None and app.get(A + "debuggable", "false") == "false" and app.get(A + "testOnly", "false") == "false"
    with ZipFile(apk) as z:
        vcs = z.read("META-INF/version-control-info.textproto").decode()
    return xml.get("package"), xml.get(A + "versionName"), int(xml.get(A + "versionCode")), next(iter(signers)), vcs


def reference(paths):
    assert len(paths) == 2
    for abi, apk in zip(("v7", "v8"), paths):
        ref = L["installed_reference"]["assets"][abi]
        assert apk.stat().st_size == ref["size"] and hashlib.sha256(apk.read_bytes()).hexdigest() == ref["sha"]
        package, name, code, cert, vcs = metadata(apk)
        assert (package, name, code, cert) == ("com.fongmi.android.tv", "v5.6.3-xray.1", 563001, L["installed_reference"]["certificate"])
        assert 'revision: "' + L["installed_reference"]["source"] + '"' in vcs
        print("VERIFIED installed .1 reference", abi, package, name, code, "public certificate", cert)


def test_apk(apk):
    package, name, code, cert, vcs = metadata(apk)
    expected = os.environ["FINGMI_TEST_CERT_SHA"]
    assert cert == expected and cert != L["installed_reference"]["certificate"]
    assert (package, name, code) == ("com.fongmi.android.tv", "v5.6.3-xray.2", 563002)
    sha = run("git", "-C", ROOT, "rev-parse", "HEAD")
    assert sha == os.environ["GITHUB_SHA"] and 'revision: "' + sha + '"' in vcs
    print("PASS test APK", apk.name, package, name, code, "test certificate", cert, "revision", sha, "16 KB alignment")
    print("NOT install-compatible with .1: test certificate differs. Package/version ordering only is compatible.")


if __name__ == "__main__":
    if sys.argv[1:] == ["scope"]:
        scope()
    elif sys.argv[1] == "reference":
        reference([Path(x) for x in sys.argv[2:]])
    elif sys.argv[1] == "test-apk" and len(sys.argv) == 3:
        test_apk(Path(sys.argv[2]))
    else:
        raise SystemExit("Invalid validation mode")
