#!/usr/bin/env python3
"""Verify changed host/side-request source and actual Android downloader only."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from prepare_candidate import ROOT, LOCK, blob, guard_fork, overlay, verified_checkout


def run(*args,cwd=None):
    subprocess.run(list(map(str,args)),cwd=cwd,check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-tv",type=Path,required=True)
    parser.add_argument("--tv",type=Path,required=True)
    parser.add_argument("--android",action="store_true")
    a=parser.parse_args()
    old,tv=a.old_tv.resolve(),a.tv.resolve()
    guard_fork()
    verified_checkout(old,"old_tv")
    verified_checkout(tv,"tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-player-batch-") as temp:
        root=Path(temp)
        candidate=root/"candidate"
        conflicts,manual=overlay(old,tv,candidate)
        for r in LOCK["fork_scope"]:
            if r["strategy"] in ("reviewed-media-host","reviewed-live-host"):
                assert blob(candidate/r["path"])==r["resolved"],r["path"]
                assert r["path"] not in conflicts and r["path"] not in manual
        run(sys.executable,ROOT/"tests/test-upstream-player-host.py","--candidate",candidate)
        run(sys.executable,ROOT/"tests/test-upstream-side-requests.py","--candidate",candidate)
        if a.android:
            project=root/"catvod-project"
            project.mkdir()
            shutil.copytree(tv/"gradle",project/"gradle")
            shutil.copytree(candidate/"catvod",project/"catvod")
            for name in ("gradlew","gradle.properties","build.gradle"):
                shutil.copyfile(tv/name,project/name)
            settings=re.sub(r"(?m)^include .*$","",(tv/"settings.gradle").read_text())
            (project/"settings.gradle").write_text(settings+"\ninclude ':catvod'\n")
            test="UpstreamDownloadTransportTest"
            dest=project/"catvod/src/test/java/com/github/catvod/net"/(test+".java")
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/"scripts/upstream-adaptation/tests"/(test+".java"),dest)
            run("bash",project/"gradlew","--no-daemon","-Porg.gradle.java.installations.auto-download=false",":catvod:assembleDebug",":catvod:testDebugUnitTest","--tests","com.github.catvod.net."+test,cwd=project)
            results=list((project/"catvod/build/test-results").rglob("TEST-com.github.catvod.net."+test+".xml"))
            assert len(results)==1,results
            suite=ET.parse(results[0]).getroot()
            assert suite.get("tests")=="3" and suite.get("failures")=="0" and suite.get("errors")=="0" and suite.get("skipped")=="0",suite.attrib
            print("PASS actual 5.9 Android catvod and 3 Download transport/real-file/Range tests; synthetic HTTP exchange",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review; complete app/player/native gate not passed",flush=True)


if __name__=="__main__":
    main()
