#!/usr/bin/env python3
"""Compile the exact official native wrapper to Android x86_64 ELF objects only.
No restricted codec source or fabricated SO, no full link/runtime claim."""
import re
import struct
import subprocess
import sys
from pathlib import Path

def run(*args):
    subprocess.run([str(a) for a in args],check=True)

def out(*args):
    return subprocess.check_output([str(a) for a in args],text=True)

def require(ok,msg):
    if not ok:
        raise SystemExit(msg)

def main():
    if len(sys.argv)!=6:
        raise SystemExit("usage: compile_official_wrapper.py producer mpv-header-checkout ffmpeg-header-checkout ndk out")
    producer,mpv,ffmpeg,ndk,dst=map(lambda x:Path(x).resolve(),sys.argv[1:])
    for repo,ref in ((producer,"1bf892e3271e73d8649f2d209027f1fb17515d15"),(mpv,"f964d1495355d5c6626df3de1d3eeb90ddee2aba"),(ffmpeg,"963c8cbbebb0250f747f0019516bda55bc638da9")):
        require(out("git","-C",repo,"rev-parse","HEAD").strip()==ref,"wrong source commit")
        require(not out("git","-C",repo,"status","--porcelain").strip(),"dirty input")
    for repo,path,sha in ((mpv,"include/mpv/client.h","f970b9ab5dc792a20c8a5d4eca5a4526fbadb594"),(mpv,"include/mpv/stream_cb.h","9ae6f31a16847d9a695886a78bc1b7a2c9942a27"),(ffmpeg,"libavcodec/jni.h","955cd28096b7eceafefce306681d9225673bb459")):
        require(out("git","-C",repo,"hash-object",path).strip()==sha,"wrong header "+path)
        print("PINNED_HEADER",path,sha,flush=True)
    require(not (ffmpeg/"dependency/avs3a").exists(),"restricted codec present")
    tc=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    require("30.0.16248370" in (ndk/"source.properties").read_text(),"NDK pin")
    dst.mkdir(parents=True,exist_ok=False)
    jni=producer/"app/src/main/jni"
    names=("main","stream","render","request","log","jni_utils","property","event","thumbnail")
    exports=set()
    undefined=set()
    for name in names:
        obj=dst/(name+".o")
        run(tc/"x86_64-linux-android23-clang++","-std=c++11","-fPIC","-Werror","-I"+str(mpv/"include"),"-I"+str(ffmpeg),"-I"+str(jni),"-c",jni/(name+".cpp"),"-o",obj)
        data=obj.read_bytes()
        require(data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(1,62),"wrong ELF object")
        for line in out(tc/"llvm-nm","--defined-only",obj).splitlines():
            if line.strip():exports.add(line.split()[-1])
        for line in out(tc/"llvm-nm","--undefined-only",obj).splitlines():
            if line.strip():undefined.add(line.split()[-1])
        print("OFFICIAL_ANDROID_OBJECT",name,out("git","-C",producer,"hash-object",str(jni/(name+".cpp"))).strip(),len(data),flush=True)
    actual={n for n in exports if n.startswith("Java_is_xyz_mpv_MPVLib_")}
    require(len(actual)==24,"expected 24 JNI entry names")
    require("mpv_stream_cb_add_ro" in undefined and "mpv_command_node_async" in undefined and "av_jni_set_java_vm" in undefined,"real native imports missing")
    print("PASS_OFFICIAL_WRAPPER_OBJECTS",len(names),"x86_64 objects",len(actual),"JNI exports; unresolved external link intentionally NOT accepted",flush=True)
if __name__=="__main__":
    main()
