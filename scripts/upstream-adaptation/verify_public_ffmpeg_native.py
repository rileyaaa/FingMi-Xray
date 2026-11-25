#!/usr/bin/env python3
"""Rebuild actual public FFmpeg JNI, not its historical producer binaries."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
from prepare_candidate import LOCK, blob, git, guard_fork, verified_checkout

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def output(*args):return subprocess.check_output(list(map(str,args)),text=True)
def run(*args):subprocess.run(list(map(str,args)),check=True)
def check_sha(p,s):
    assert p.is_file() and re.fullmatch("[0-9a-f]{64}",s),("missing input or invalid digest",str(p))
    actual=sha(p)
    assert actual==s,("binary digest",str(p),"actual",actual,"expected",s)

def check_text_sha(p,s):
    """Only an exact CRLF/LF equivalence on the pinned textual source."""
    assert p.is_file() and re.fullmatch("[0-9a-f]{64}",s),p
    data=p.read_bytes()
    actual=hashlib.sha256(data).hexdigest()
    if actual==s:return
    assert b"\0" not in data,p
    data.decode("utf-8",errors="strict")
    lf=data.replace(b"\r\n",b"\n")
    assert b"\r" not in lf,p
    assert data in (lf,lf.replace(b"\n",b"\r\n")),p
    crlf=lf.replace(b"\n",b"\r\n")
    alternatives={hashlib.sha256(lf).hexdigest(),hashlib.sha256(crlf).hexdigest()}
    assert s in alternatives,("text digest mismatch",str(p),actual,s)
    print("VERIFIED_PINNED_TEXT_LINE_ENDINGS",str(p),actual,s,flush=True)

def elf(p,abi,tc):
    d=p.read_bytes()
    assert d[:4]==b"\x7fELF" and d[5]==1,p
    typ,machine=struct.unpack_from("<HH",d,16)
    assert typ==3 and (d[4],machine)==((1,40) if abi=="armeabi-v7a" else (2,183)),p
    headers=output(tc/"llvm-readelf","--program-headers","--wide",p)
    loads=[line.split() for line in headers.splitlines() if line.lstrip().startswith("LOAD ")]
    assert loads,p
    for line in loads:
        off,addr,align=int(line[1],16),int(line[2],16),int(line[-1],16)
        assert align>=16384 and (addr-off)%16384==0,(p,line)
    dyn=output(tc/"llvm-readelf","--dynamic",p)
    assert not any(x in dyn for x in ("(RPATH)","(RUNPATH)","TEXTREL")),p
    assert re.findall(r"\(SONAME\).*?\[(.*?)\]",dyn)==[p.name],p
    return set(re.findall(r"\(NEEDED\).*?\[(.*?)\]",dyn)),len(loads)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--media",type=Path,required=True)
    media=p.parse_args().media.resolve();guard_fork();verified_checkout(media,"media")
    g=LOCK["public_native_build"]["ffmpeg"];module=media/g["module"];main=module/"src/main"
    for rel,key in (("","tree"),("/src/main/jni","jni_tree"),("/src/main/ffmpeg","headers_tree"),("/src/main/renderer-sdk","renderer_tree"),("/src/main/jniLibs","jni_libs_tree")):
        assert git(media,"rev-parse","HEAD:"+g["module"]+rel)==g[key],rel
    manifest=main/"resources/META-INF/androidx.media3.decoder.ffmpeg/native-dependencies.properties"
    assert blob(manifest)==g["manifest_blob"] and blob(main/"jni/CMakeLists.txt")==g["cmake_blob"]
    m={}
    for line in manifest.read_text().splitlines():
        if not line or line.startswith("#"):continue
        k,v=line.split("=",1);assert k not in m,k;m[k]=v
    for k,v in {"schema.version":"3","manifest.kind":"decoder-ffmpeg-consumer","mpv-android.commit":g["producer"],"artifact.github.run.id":str(g["producer_run"]),"mpv-android.source.dirty":"false","ffmpeg.commit":g["ffmpeg"],"dav1d.commit":g["dav1d"],"libplacebo.commit":g["libplacebo"],"libplacebo.source.dirty":"false","libplacebo.opengl":"true","libplacebo.vulkan":"false","android.ndk.version":g["ndk"],"abi.list":",".join(g["abis"]),"renderer-sdk.abi.list":",".join(g["abis"])}.items():
        assert m[k]==v,(k,m.get(k))
    libs=m["library.list"].split(",")
    assert set(libs)=={"libavcodec.so","libavdevice.so","libavfilter.so","libavformat.so","libavutil.so","libswresample.so","libswscale.so"}
    sdk=Path(os.environ["ANDROID_HOME"]);ndk=sdk/"ndk"/g["ndk"];cmake=sdk/"cmake"/g["cmake"]/"bin"
    assert re.search(r"Pkg.Revision\s*=\s*"+re.escape(g["ndk"])+r"\s*$",(ndk/"source.properties").read_text(),re.M)
    tc=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    license=main/"renderer-sdk/LICENSE"
    evidence=g["license_line_endings"]
    assert blob(license)==evidence["producer_and_consumer_git_blob"]
    assert sha(license)==evidence["checkout_lf_sha256"]
    assert m["sha256.renderer-sdk.LICENSE"]==evidence["manifest_crlf_sha256"]
    check_text_sha(license,m["sha256.renderer-sdk.LICENSE"])
    expected=set();j=main/"java/androidx/media3/decoder/ffmpeg"
    for cls,count in (("FfmpegAudioDecoder",8),("FfmpegVideoDecoder",10),("FfmpegLibrary",4)):
        methods=re.findall(r"\bnative\s+\w+\s+(\w+)\s*\(",(j/(cls+".java")).read_text())
        assert len(methods)==count,(cls,methods)
        expected.update("Java_androidx_media3_decoder_ffmpeg_"+cls+"_"+n for n in methods)
    assert len(expected)==22
    failures=[]
    with tempfile.TemporaryDirectory(prefix="fingmi-590-ffmpeg-jni-") as tmp:
        for abi in g["abis"]:
            try:
                libdir=main/"jniLibs"/abi;renderer=main/"renderer-sdk"/abi
                assert {x.name for x in libdir.iterdir()}==set(libs)
                for n in libs:check_sha(libdir/n,m["sha256."+abi+"."+n])
                for n,rel in (("libplacebo.a","lib/libplacebo.a"),("config.h","include/libplacebo/config.h"),("headers.sha256","headers.sha256")):
                    (check_sha if n=="libplacebo.a" else check_text_sha)(renderer/rel,m["sha256.renderer-sdk."+abi+"."+n])
                listed=set()
                for line in (renderer/"headers.sha256").read_text().splitlines():
                    digest,n=line.split();rel=Path(n)
                    assert not rel.is_absolute() and ".." not in rel.parts and n not in listed
                    check_text_sha(renderer/"include"/rel,digest);listed.add(n)
                assert listed=={x.relative_to(renderer/"include").as_posix() for x in (renderer/"include").rglob("*") if x.is_file()}
                print("VERIFIED_PUBLIC_FFMPEG_INPUTS",abi,len(libs),len(listed),"headers + renderer archive; producer not rebuilt",flush=True)
                build=Path(tmp)/abi
                run(cmake/"cmake","-S",main/"jni","-B",build,"-G","Ninja","-DCMAKE_MAKE_PROGRAM="+str(cmake/"ninja"),"-DCMAKE_TOOLCHAIN_FILE="+str(ndk/"build/cmake/android.toolchain.cmake"),"-DANDROID_ABI="+abi,"-DANDROID_PLATFORM=android-"+str(g["min_sdk"]),"-DANDROID_STL=c++_shared","-DCMAKE_BUILD_TYPE=Release","-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON","-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384 -Wl,--no-undefined")
                run(cmake/"cmake","--build",build,"--target","ffmpegJNI","--parallel","2")
                paths=list(build.rglob("libffmpegJNI.so"));assert len(paths)==1,paths;path=paths[0]
                needed,loads=elf(path,abi,tc)
                names={line.split()[-1] for line in output(tc/"llvm-nm","-D","--defined-only",path).splitlines() if line.strip()}
                actual={n for n in names if n.startswith("Java_androidx_media3_decoder_ffmpeg_")}
                assert actual==expected,(sorted(expected-actual),sorted(actual-expected))
                assert "JNI_OnLoad" in names and {"libavcodec.so","libavutil.so","libswresample.so"}<=needed,needed
                print("VERIFIED_PUBLIC_FFMPEG_JNI",abi,path.stat().st_size,sha(path),"JNI",len(actual),"PT_LOAD",loads,"NEEDED",",".join(sorted(needed)),flush=True)
                triple="arm-linux-androideabi" if abi=="armeabi-v7a" else "aarch64-linux-android"
                syslib=tc.parent/"sysroot/usr/lib"/triple
                all_needed=set(needed)
                for n in libs:
                    deps,_=elf(libdir/n,abi,tc);all_needed.update(deps)
                missing={n for n in all_needed if n not in libs and n!="libc++_shared.so" and not (syslib/str(g["min_sdk"])/n).is_file()}
                assert not missing,("unresolved dynamic dependency",abi,sorted(missing))
                assert (syslib/"libc++_shared.so").is_file()
                print("VERIFIED_PUBLIC_FFMPEG_DEPENDENCY_CLOSURE",abi,",".join(sorted(all_needed)),flush=True)
            except (AssertionError,subprocess.CalledProcessError,OSError,KeyError,ValueError) as e:
                failures.append((abi,repr(e)));print("BLOCKED_PUBLIC_FFMPEG_JNI",abi,repr(e),flush=True)
    assert not git(media,"status","--porcelain")
    if failures:raise SystemExit("Partial FFmpeg JNI result: "+repr(failures))
    print("PASS actual dual ABI public FFmpeg JNI and ELF/22 JNI exports; consumer dependencies not rebuilt; no AAR/APK or runtime decode claim",flush=True)

if __name__=="__main__":main()
