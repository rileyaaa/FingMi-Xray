#!/usr/bin/env python3
"""Isolated reduced FFmpeg / missing ninth JNI object. Never stage as exact producer."""
import hashlib
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

FF="963c8cbbebb0250f747f0019516bda55bc638da9"
MPV="f964d1495355d5c6626df3de1d3eeb90ddee2aba"
PRODUCER="1bf892e3271e73d8649f2d209027f1fb17515d15"

def run(*args,cwd=None):
    subprocess.run([str(a) for a in args],check=True,cwd=cwd)

def out(*args):
    return subprocess.check_output([str(a) for a in args],text=True)

def need(ok,msg):
    if not ok: raise SystemExit(msg)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def symbols(nm,path,defined,dynamic):
    args=["--defined-only" if defined else "--undefined-only"]
    if dynamic: args+=["-D"]
    return {l.split()[-1].split("@")[0] for l in out(nm,*args,path).splitlines() if l.strip()}

def main():
    if len(sys.argv)!=6: raise SystemExit("usage: reduced_ffmpeg_diagnostic.py producer mpv_headers ffmpeg_sparse ndk output")
    producer,mpv,ff,ndk,dst=map(lambda p:Path(p).resolve(),sys.argv[1:])
    for repo,ref in ((producer,PRODUCER),(mpv,MPV),(ff,FF)):
        need(out("git","-C",repo,"rev-parse","HEAD").strip()==ref,"wrong source revision")
        need(not out("git","-C",repo,"status","--porcelain").strip(),"dirty source")
    for repo,path,expected in ((ff,"configure","ec3bc586e623ac2c4a0bcf05ecfbef374b7e45dc"),(ff,"LICENSE.md","0e75dd3030844784ae339fb51300bd1a3b1e6207"),(ff,"libswscale/swscale.h","c913e76985b7fcf656f266498905cfcd689b8454"),(mpv,"include/mpv/client.h","f970b9ab5dc792a20c8a5d4eca5a4526fbadb594"),(producer,"app/src/main/jni/thumbnail.cpp","ac5af164a68ed7d36b39e9732fd850beac5579ca")):
        need(out("git","-C",repo,"hash-object",path).strip()==expected,"wrong input "+path)
        print("DIAGNOSTIC_PIN",path,expected,flush=True)
    need(not (ff/"dependency").exists(),"external dependency source directory present")
    forbidden=re.compile(r"avs3|arcdav3a|av3a",re.I)
    for root,dirs,files in os.walk(ff):
        dirs[:]=[d for d in dirs if d!=".git"]
        for n in dirs+files:
            need(not forbidden.search(n),"excluded codec source materialized: "+n)
    need("30.0.16248370" in (ndk/"source.properties").read_text(),"NDK pin")
    print("DIAGNOSTIC_LICENSE",sha(ff/"COPYING.LGPLv2.1"),"no dependency/ or AVS3/AV3A sources",flush=True)
    tc=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    cc=tc/"x86_64-linux-android24-clang"
    cxx=tc/"x86_64-linux-android24-clang++"
    dst.mkdir(parents=True,exist_ok=False)
    build=dst/"build";build.mkdir()
    run(ff/"configure","--target-os=android","--enable-cross-compile","--arch=x86_64","--cpu=generic",
        "--cc="+str(cc),"--cxx="+str(cxx),"--ld="+str(cc),"--ar="+str(tc/"llvm-ar"),
        "--ranlib="+str(tc/"llvm-ranlib"),"--nm="+str(tc/"llvm-nm"),"--strip="+str(tc/"llvm-strip"),
        "--pkg-config=false","--disable-autodetect","--disable-everything","--disable-network",
        "--disable-gpl","--disable-nonfree","--disable-version3","--disable-libarcdav3a","--disable-libuavs3d",
        "--disable-avdevice","--disable-avfilter","--disable-swresample","--disable-programs","--disable-doc",
        "--disable-asm","--disable-static","--enable-shared","--enable-pic","--enable-jni",
        "--enable-demuxer=wav","--enable-decoder=pcm_s16le","--enable-protocol=file",
        "--extra-ldflags=-Wl,-z,max-page-size=16384",cwd=build)
    config=(build/"config.h").read_text()+"\n"+(build/"config_components.h").read_text()
    for flag in ("LIBARCDAV3A","LIBUAVS3D","LIBARCDAV3A_DECODER","LIBUAVS3D_DECODER","AVS3_PARSER","GPL","NONFREE","VERSION3"):
        need(not re.search(r"(?m)^#define CONFIG_"+flag+r"\s+1\b",config),"forbidden enabled feature "+flag)
    for flag in ("JNI","WAV_DEMUXER","PCM_S16LE_DECODER","FILE_PROTOCOL"):
        need(re.search(r"(?m)^#define CONFIG_"+flag+r"\s+1\b",config),"missing required feature "+flag)
    avconfig=build/"libavutil/avconfig.h"
    need(avconfig.is_file(),"configure did not generate avconfig.h")
    print("DIAGNOSTIC_GENERATED_AVCONFIG",sha(avconfig),avconfig.read_text(),flush=True)
    # New work only: compile ninth official object, not the eight already evidenced.
    jni=producer/"app/src/main/jni";obj=dst/"thumbnail.o"
    run(cxx,"-std=c++11","-fPIC","-Werror","-I"+str(mpv/"include"),"-I"+str(build),"-I"+str(ff),"-I"+str(jni),"-c",jni/"thumbnail.cpp","-o",obj)
    data=obj.read_bytes()
    need(data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(1,62),"wrong ELF object ABI")
    nm=tc/"llvm-nm";readelf=tc/"llvm-readelf"
    required={"sws_getContext","sws_scale","sws_freeContext"}
    need("Java_is_xyz_mpv_MPVLib_grabThumbnail" in symbols(nm,obj,True,False),"missing JNI export")
    need(required <= symbols(nm,obj,False,False),"missing actual swscale imports")
    print("PASS_NINTH_WRAPPER_OBJECT_REDUCED_HEADER",len(data),sha(obj),flush=True)
    run("make","-j2",cwd=build)
    files=[build/("lib"+name)/("lib"+name+".so") for name in ("avutil","avcodec","avformat","swscale")]
    def dynamic(path):return out(readelf,"--dynamic",path)
    names=set()
    for path in files:
        need(path.is_file(),"missing diagnostic SO "+str(path))
        m=re.search(r"\(SONAME\).*\[([^]]+)\]",dynamic(path))
        need(m,"missing SONAME "+str(path));names.add(m.group(1))
    syslib=tc.parent/"sysroot/usr/lib/x86_64-linux-android/24"
    for path in files:
        data=path.read_bytes()
        need(data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(3,62),"wrong diagnostic SO ABI")
        loads=[l.split() for l in out(readelf,"--program-headers","--wide",path).splitlines() if l.strip().startswith("LOAD ")]
        need(loads and all(int(l[-1],16)>=16384 and (int(l[1],16)-int(l[2],16))%16384==0 for l in loads),"16KiB gate "+str(path))
        dyn=dynamic(path);deps=set(re.findall(r"\(NEEDED\).*?\[([^]]+)\]",dyn))
        need(all(d in names or (syslib/d).is_file() for d in deps),"unknown NEEDED "+str(deps))
        need(not re.search(r"\((RPATH|RUNPATH|TEXTREL)\)",dyn),"dynamic path/text relocation")
        print("DIAGNOSTIC_ELF",path.name,len(data),sha(path),"NEEDED",sorted(deps),flush=True)
    need(required<=symbols(nm,files[3],True,True),"missing swscale exports")
    need("av_jni_set_java_vm" in symbols(nm,files[1],True,True),"missing actual JNI FFmpeg export")
    need(not out("git","-C",ff,"status","--porcelain").strip(),"source changed by build")
    print("PASS_REDUCED_SPLIT_FFMPEG_DIAGNOSTIC four SOs; ninth wrapper object; NO libmpv/libplayer/Android runtime",flush=True)

if __name__=="__main__":main()
