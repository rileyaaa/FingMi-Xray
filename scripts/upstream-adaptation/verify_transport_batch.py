#!/usr/bin/env python3
"""Stage the reviewed 5.9 source and independently test transport boundaries."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from prepare_candidate import ROOT, LOCK, blob, guard_fork, overlay, verified_checkout
from verify_recovery_batch import method


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
    with tempfile.TemporaryDirectory(prefix="fingmi-590-transport-") as temp:
        root=Path(temp)
        candidate=root/"candidate"
        conflicts,manual=overlay(old,tv,candidate)
        rows=[r for r in LOCK["fork_scope"] if r["strategy"] in ("reviewed-media-host","reviewed-live-host")]
        assert not {r["path"] for r in rows}.intersection(conflicts+manual)
        for r in rows:
            assert blob(candidate/r["path"])==r["resolved"],r["path"]
        p="app/src/main/java/com/fongmi/android/tv/player/"
        http="catvod/src/main/java/com/github/catvod/net/OkHttp.java"
        media=p+"exo/ExoMediaSourceFactory.java"
        engine=p+"exo/ExoPlayerEngine.java"
        session=p+"exo/ExoPlayerSession.java"
        subtitle=p+"subtitle/SubtitleFileContent.java"
        factory=p+"engine/PlayerEngineFactory.java"
        def source(path): return (candidate/path).read_text()
        def original(path): return (tv/path).read_text()
        for path,sigs in (
            (http,("public static Call.Factory player(Auth.Context auth)","static Request applyAuth(Request request, Auth.Context auth)","public static synchronized OkHttpClient player()","private static OkHttpClient.Builder getBuilder()")),
            (media,("static DataSource.Factory createUpstreamDataSourceFactory(Map<String, String> headers, Auth.Context auth)","public static DataSource.Factory createDataSourceFactory(Map<String, String> headers, Auth.Context auth)","public static synchronized Cache getCache()","static DefaultExtractorsFactory createDefaultExtractorsFactory()")),
            (factory,("static boolean requiresExo(PlaySpec spec)","private static boolean isMpvReady()")),
        ):
            for sig in sigs:
                assert method(source(path),sig)==method(original(path),sig),(path,sig)
        route=method(source(media),"public static DataSource.Factory createDataSourceFactory(Map<String, String> headers, Auth.Context auth, XrayHttpClient proxy)")
        assert "OkHttp.player(proxy.client(), auth)" in route and "new GuardedPlaybackDataSource" in route and "getCache()" not in route
        assert "get().client = null;" in method(source(http),"public static void resetApiNetworkForResume()")
        assert "player" not in method(source(http),"public static void resetApiNetworkForResume()")
        for needle in ("drm.setDrmHttpDataSourceFactory(dataSourceFactory)",".setSocketFactory(proxy.rtspSocketFactory())","new ContentTypeResolvingMediaSource.Factory(factory, dataSourceFactory)"):
            assert needle in source(media),needle
        assert "new SubtitleFileContent(proxy)" in source(session)
        assert source(session).count("ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession, proxy)")==2
        assert source(engine).count("if (proxy == null) preload.start(player, item);")==2
        assert "if (proxy != null || navigation.isStarted()" in source(engine)
        assert "ExoMediaSourceFactory.createDataSourceFactory(this.spec.getHeaders(), this.spec.getAuth(), proxy)" in source(engine)
        assert "ExoMediaSourceFactory.createDataSourceFactory(ExoUtil.extractHeaders(item), ExoUtil.extractAuth(item), proxy)" in source(subtitle)
        print("PASS exact candidate transport source; direct Auth/cache/selector/decoder unchanged; no player activation",flush=True)
        run(sys.executable,ROOT/"tests/test-upstream-live-host.py","--candidate",candidate)
        run(sys.executable,ROOT/"tests/test-upstream-transport-host.py","--candidate",candidate)
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
            tests=project/"catvod/src/test/java"
            xray="xray/src/main/java/com/fingmi/xray/network/"
            for name in ("XrayHttpClient.java","XrayProxySocketFactory.java","PublicPlaybackDestinationInterceptor.java"):
                src=candidate/(xray+name)
                assert blob(src)==blob(ROOT/(xray+name)),name
                dest=tests/"com/fingmi/xray/network"/name
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(src,dest)
            dest=tests/"com/github/catvod/net/UpstreamPlaybackAuthTest.java"
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/"scripts/upstream-adaptation/tests/UpstreamPlaybackAuthTest.java",dest)
            run("bash",project/"gradlew","--no-daemon","-Porg.gradle.java.installations.auto-download=false",":catvod:assembleDebug",":catvod:testDebugUnitTest","--tests","com.github.catvod.net.UpstreamPlaybackAuthTest",cwd=project)
            import xml.etree.ElementTree as ET
            results=list((project/"catvod/build/test-results").rglob("TEST-com.github.catvod.net.UpstreamPlaybackAuthTest.xml"))
            assert len(results)==1,results
            suite=ET.parse(results[0]).getroot()
            assert suite.get("tests")=="3" and suite.get("failures")=="0" and suite.get("errors")=="0" and suite.get("skipped")=="0",suite.attrib
            print("PASS actual Android catvod compile and 3 real OkHttp/Auth/Xray client tests; HTTP terminal exchange synthetic; no APK",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review; complete app/player/native gate not passed",flush=True)


if __name__=="__main__":
    main()
