#!/usr/bin/env python3
"""5.9 actual side-request APIs with existing deterministic UI/HTTP fixtures.

Download is deliberately a boundary double in these lifecycle tests.
The actual downloader's initial/continuation factory handoff is checked against
its reviewed source; actual range/resume IO needs the isolated Android tests.
"""
import argparse
import ast
import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
PATHS={
    "app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java":"200ebcb58a2dcfa7c6bb9bdac6d4443b068870d5",
    "app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java":"290690f333f45ea8e5985059e6fe5d947093dddd",
    "app/src/main/java/com/fongmi/android/tv/impl/ApiCallback.java":"07771e1a6aad8e8c2bf5b5a11a8b9786edad19fc",
    "catvod/src/main/java/com/github/catvod/net/Download.java":"0ef776e8eda553b40fbc6eccff9df84dd99620aa",
}


def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate",type=Path,required=True)
    candidate=p.parse_args().candidate
    for path,sha in PATHS.items():
        assert blob((candidate/path).read_bytes())==sha,path
    download=(candidate/next(p for p in PATHS if p.endswith("/Download.java"))).read_text()
    assert "this.requestedClient = Objects.requireNonNull(client);" in download
    assert "Call.Factory client = requestedClient == null ? OkHttp.client() : requestedClient;" in download
    assert "call = client.newCall(request(client));" in download
    assert "this.factory = factory;" in download and "next = factory.newCall(request);" in download
    assert download.count("OkHttp.client()")==1
    tree=ast.parse((ROOT/"tests/test-xray-side-request-lifecycle.py").read_text())
    stubs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=="STUBS" for t in n.targets))
    # In 5.9, Download and Task moved from app to catvod. Keep all prior
    # lifecycle scenarios; only replace those fixture boundary package names.
    for old,new in (("com.fongmi.android.tv.utils.Download","com.github.catvod.net.Download"),
                    ("com.fongmi.android.tv.utils.Task","com.github.catvod.utils.Task")):
        oldpath=old.replace(".","/")+".java"
        newpath=new.replace(".","/")+".java"
        package=old.rsplit(".",1)[0]
        stubs[newpath]=stubs.pop(oldpath).replace("package "+package+";","package "+new.rsplit(".",1)[0]+";")
        stubs["SideRequestTest.java"]=stubs["SideRequestTest.java"].replace(old,new)
    archive="com/fongmi/android/tv/utils/SubtitleArchive.java"
    stubs[archive]=stubs[archive].replace("public class SubtitleArchive","import com.github.catvod.net.Download; public class SubtitleArchive")
    path="com/github/catvod/net/Download.java"
    stubs[path]=stubs[path].replace("public Download client(okhttp3.OkHttpClient c) { return this; }","public okhttp3.OkHttpClient bound; public Download client(okhttp3.OkHttpClient c) { bound=c; return this; }")
    stubs[path]=stubs[path].replace("public void cancel() { canceled=true; }","public Download cancel() { canceled=true; return this; }")
    harness=stubs["SideRequestTest.java"]
    marker='        System.out.println("PASS Xray side-request lifecycle: "+count+" scenarios");'
    assert harness.count(marker)==1
    harness=harness.replace(marker,"""        reset();
        OkHttpClient firstClient=new OkHttpClient(), nextClient=new OkHttpClient();
        int firstId=SubtitleApi.loadSubtitle(firstClient,new SubtitleSearchItem(),v->delivered++,e->delivered++,()->completed++);
        Download retired=Download.last;
        check(retired.bound==firstClient,"download selected client lost");
        SubtitleApi.loadSubtitle(nextClient,new SubtitleSearchItem(),v->delivered++,e->delivered++,()->completed++);
        Download replacement=Download.last;
        check(retired.canceled && replacement.bound==nextClient,"replacement download route or old cancellation lost");
        SubtitleApi.cancel(firstId);
        retired.callback.success(new java.io.File("retired.srt"));
        check(!replacement.canceled,"old dialog canceled new download");
        SubtitleApi.cancelForXrayTransition();
        replacement.callback.success(new java.io.File("new.srt"));
        check(replacement.canceled,"transition left active download");
        canceled("download client ownership");
        System.out.println("PASS 5.9 side-request lifecycle: "+count+" scenarios");""")
    stubs["SideRequestTest.java"]=harness
    with tempfile.TemporaryDirectory(prefix="fingmi-590-side-requests-") as temp:
        root=Path(temp)
        for name,data in stubs.items():
            dst=root/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_text(data,encoding="utf-8")
        sources=list(root.rglob("*.java"))+[candidate/path for path in PATHS if not path.endswith("/Download.java")]
        subprocess.run(["javac","--release","17","-d",str(root/"classes"),*map(str,sources)],check=True)
        subprocess.run(["java","-cp",str(root/"classes"),"SideRequestTest"],check=True,timeout=20)
    print("PASS downloader factory handoff source checks; actual IO and service binding not tested")


if __name__=="__main__":
    main()
