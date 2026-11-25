#!/usr/bin/env python3
"""Rebuild the upstream public Hook/TVBus Java wrappers and recovery library.

An isolated Android library build (not the TV app). No signing config or APK
packaging is loaded. TVBus's externally supplied native engine is NOT rebuilt
or used; the wrapper AAR alone does not establish runtime completeness.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
LOCK = json.loads((ROOT / "scripts/upstream-adaptation/lock.json").read_text())


def run(*args, cwd=None):
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)


def public_api(aar, scratch):
    with ZipFile(aar) as z:
        data = z.read("classes.jar")
    jar = scratch / (aar.stem + ".jar")
    jar.write_bytes(data)
    with ZipFile(jar) as z:
        names = sorted(n[:-6].replace("/", ".") for n in z.namelist()
                       if n.endswith(".class") and not n.endswith("BuildConfig.class")
                       and not n.endswith("/R.class") and "/R$" not in n)
    # Include public/protected JVM descriptors for all published class files.
    output = subprocess.check_output(["javap", "-classpath", str(jar),
                                      "-public", "-s", *names], text=True)
    return re.sub(r'(?m)^Compiled from "[^"]+"\n', "", output)


def main():
    upstream = Path(sys.argv[1]).resolve()
    if (ROOT / "signing").exists():
        raise RuntimeError("Signing files must not be present")
    def git(*args):
        return subprocess.check_output(["git", "-C", str(upstream), *args], text=True).strip()
    if git("rev-parse", "HEAD") != LOCK["upstream"]["tv"]["ref"] or \
       git("rev-parse", "HEAD^{tree}") != LOCK["upstream"]["tv"]["tree"]:
        raise RuntimeError("Unverified wrapper source")
    with tempfile.TemporaryDirectory(prefix="upstream-java-libraries-") as work:
        p = Path(work)
        for name in ("gradle", "hook", "tvbus", "catvod"):
            shutil.copytree(upstream / name, p / name)
        shutil.copytree(ROOT / "tv-recovery", p / "tv-recovery")
        for name in ("gradlew", "gradle.properties", "build.gradle"):
            shutil.copyfile(upstream / name, p / name)
        settings = (upstream / "settings.gradle").read_text()
        settings = re.sub(r"(?m)^include .*$", "", settings)
        settings += "\ninclude ':hook', ':tvbus', ':catvod', ':tv-recovery'\n"
        (p / "settings.gradle").write_text(settings)
        # No app/build.gradle, no local.properties or key material. The public
        # upstream SDK and dependency catalog are used without lowering versions.
        assert not (p / "app").exists()
        run("bash", p / "gradlew", "--no-daemon", "-Porg.gradle.java.installations.auto-download=false",
            ":hook:assembleRelease", ":tvbus:assembleRelease",
            ":tv-recovery:assembleDebug", ":tv-recovery:testDebugUnitTest", cwd=p)
        for name in ("hook", "tvbus"):
            rebuilt = p / name / "build/outputs/aar" / (name + "-release.aar")
            official = upstream / "app/libs" / (name + "-release.aar")
            api1 = public_api(official, p)
            api2 = public_api(rebuilt, p)
            print("REBUILT_WRAPPER", name, "official_sha256",
                  hashlib.sha256(official.read_bytes()).hexdigest(), "rebuilt_sha256",
                  hashlib.sha256(rebuilt.read_bytes()).hexdigest(), "public_api_equal", api1 == api2, flush=True)
            if api1 != api2:
                raise RuntimeError(name + " wrapper API differs; not a verified replacement")
        print("PASS public wrapper API and actual TV recovery library build/test; no full app or native TVBus claim")


if __name__ == "__main__":
    main()
