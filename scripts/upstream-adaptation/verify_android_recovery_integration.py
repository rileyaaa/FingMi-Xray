#!/usr/bin/env python3
"""Build actual staged Android libraries and exercise full network classes."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from prepare_candidate import ROOT,LOCK,blob,guard_fork,overlay,verified_checkout

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-tv",type=Path,required=True);p.add_argument("--tv",type=Path,required=True)
    a=p.parse_args();old,tv=a.old_tv.resolve(),a.tv.resolve()
    guard_fork();verified_checkout(old,"old_tv");verified_checkout(tv,"tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-recovery-integration-") as d:
        work=Path(d);candidate=work/"candidate";conflicts,manual=overlay(old,tv,candidate)
        prefix="app/src/main/java/com/fongmi/android/tv/"
        selector="catvod/src/main/java/com/github/catvod/net/OkProxySelector.java"
        proxytest="catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java"
        loaders=[prefix+"api/loader/"+n+".java" for n in ("JarLoader","JsLoader","PyLoader","SpiderLoader")]
        for path in [selector]+loaders:
            assert path not in conflicts+manual and blob(candidate/path)==blob(tv/path),path
        row=next(x for x in LOCK["fork_scope"] if x["path"]==proxytest)
        assert proxytest not in conflicts+manual and blob(candidate/proxytest)==row["resolved"]
        project=work/"android-integration";project.mkdir()
        shutil.copytree(tv/"gradle",project/"gradle")
        for n in ("catvod","tv-recovery"):shutil.copytree(candidate/n,project/n)
        for n in ("gradlew","gradle.properties","build.gradle"):shutil.copyfile(tv/n,project/n)
        settings=re.sub(r"(?m)^include .*$","",(tv/"settings.gradle").read_text())
        (project/"settings.gradle").write_text(settings+"\ninclude ':catvod'\ninclude ':tv-recovery'\n")
        with (project/"catvod/build.gradle").open("a") as f:f.write("\ndependencies { testImplementation project(':tv-recovery') }\n")
        tests=project/"catvod/src/test/java"
        for n in ("XrayHttpClient.java","XrayProxySocketFactory.java","PublicPlaybackDestinationInterceptor.java"):
            rel="xray/src/main/java/com/fingmi/xray/network/"+n
            assert blob(candidate/rel)==blob(ROOT/rel)
            dst=tests/"com/fingmi/xray/network"/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate/rel,dst)
        for rel in ("api/loader/SpiderLoader.java","exception/SpiderLoadException.java"):
            dst=tests/"com/fongmi/android/tv"/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate/(prefix+rel),dst)
        for n,pkg in (("UpstreamRecoveryIntegrationTest.java","com/github/catvod/net"),("UpstreamSpiderLifecycleTest.java","com/fongmi/android/tv/api/loader")):
            dst=tests/pkg/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/"scripts/upstream-adaptation/tests"/n,dst)
        classes=["com.github.catvod.net.OkProxySelectorTest","com.github.catvod.net.UpstreamRecoveryIntegrationTest","com.fongmi.android.tv.api.loader.UpstreamSpiderLifecycleTest"]
        cmd=["bash",str(project/"gradlew"),"--no-daemon","-Porg.gradle.java.installations.auto-download=false",":catvod:assembleDebug",":tv-recovery:assembleDebug",":catvod:testDebugUnitTest"]
        for c in classes:cmd+=["--tests",c]
        subprocess.run(cmd,cwd=project,check=True)
        for c in classes:
            reports=list((project/"catvod/build/test-results").rglob("TEST-"+c+".xml"));assert len(reports)==1,reports
            suite=ET.parse(reports[0]).getroot();count=int(suite.get("tests","0"))
            assert count>0 and all(suite.get(x)=="0" for x in ("failures","errors","skipped")),suite.attrib
            print("VERIFIED_ANDROID_INTEGRATION",c,count,flush=True)
        for n in ("catvod","tv-recovery"):
            aar=list((project/n/"build/outputs/aar").glob("*-debug.aar"));assert len(aar)==1,aar
            print("VERIFIED_ANDROID_LIBRARY",n,aar[0].stat().st_size,flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review",flush=True)
        print("PASS actual Android libraries, recovery lifecycle, upstream SpiderLoader and real loopback HTTP; not full TV host or APK",flush=True)
if __name__=="__main__":main()
