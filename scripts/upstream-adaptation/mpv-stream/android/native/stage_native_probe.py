#!/usr/bin/env python3
"""Only stage rebuilt official x86_64 SOs after the existing 16 KiB gate.
This probe neither changes ARM acceptance nor exports an AAR/release."""
import hashlib
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

PRODUCER = "1bf892e3271e73d8649f2d209027f1fb17515d15"
EXPECTED = {"libffmpeg.so", "libmpv.so", "libplayer.so", "libc++_shared.so"}

def out(*args):
    return subprocess.check_output([str(a) for a in args], text=True)

def require(ok, reason):
    if not ok:
        raise SystemExit(reason)

def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: stage_native_probe.py producer media sdk")
    producer, media, sdk = [Path(x).resolve() for x in sys.argv[1:]]
    require(out("git", "-C", producer, "rev-parse", "HEAD").strip()==PRODUCER, "producer revision")
    require(not out("git", "-C", producer, "diff", "HEAD", "--", "app/src/main/jni", "buildscripts").strip(), "producer sources changed")
    ndk = sdk / "ndk/30.0.16248370"
    tc = ndk / "toolchains/llvm/prebuilt/linux-x86_64"
    readelf, nm = tc/"bin/llvm-readelf", tc/"bin/llvm-nm"
    syslib=tc/"sysroot/usr/lib/x86_64-linux-android/24"
    require(syslib.is_dir(), "NDK API 24 sysroot missing")
    src=producer/"app/src/main/libs/x86_64"
    files={p.name for p in src.glob("*.so")}
    require(files==EXPECTED, "unexpected x86_64 shared library set: "+str(files))
    exports={}
    imports={}
    for name in sorted(files):
        path=src/name; data=path.read_bytes()
        require(data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(3,62), "wrong ELF64 x86_64: "+name)
        ph=out(readelf,"--program-headers","--wide",path)
        loads=[l.split() for l in ph.splitlines() if l.strip().startswith("LOAD ")]
        require(loads and all(int(l[-1],16)>=16384 and (int(l[1],16)-int(l[2],16))%16384==0 for l in loads), "existing 16KiB ELF gate: "+name)
        dyn=out(readelf,"--dynamic",path)
        needed=set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]",dyn))
        require(all(n in files or (syslib/n).is_file() for n in needed), "missing dynamic dependency: "+name+" "+str(needed))
        require(not re.search(r"\((?:RPATH|RUNPATH|TEXTREL)\)",dyn), "unexpected dynamic path/text relocation: "+name)
        if name in ("libmpv.so","libplayer.so"):
            require("libffmpeg.so" in needed, "not unified FFmpeg: "+name)
        if name=="libplayer.so":
            require("libmpv.so" in needed, "missing libmpv linkage")
        exports[name]={l.split()[-1].split("@")[0] for l in out(nm,"-D","--defined-only",path).splitlines() if l.strip()}
        imports[name]={l.split()[-1].split("@")[0] for l in out(nm,"-D","--undefined-only",path).splitlines() if l.strip()}
        print("NATIVE_ELF",name,"x86_64","16KiB",len(data),hashlib.sha256(data).hexdigest(),"NEEDED",",".join(sorted(needed)),flush=True)
    require({s for s in imports["libplayer.so"] if s.startswith("mpv_")} <= exports["libmpv.so"], "unresolved mpv symbols")
    for name in ("libmpv.so","libplayer.so"):
        ff={s for s in imports[name] if re.match(r"^(av_|avcodec_|avformat_|avfilter_|avutil_|avdevice_|swr_|sws_)",s)}
        require(ff and ff <= exports["libffmpeg.so"], "unresolved FFmpeg symbols: "+name)
    module=media/"mpv-stream-probe"
    bridge=module/"src/main/java/is/xyz/mpv/MPVLib.java"
    jni={"Java_is_xyz_mpv_MPVLib_"+n for n in re.findall(r"public static native [^;\n]+?\s+(\w+)\(",bridge.read_text())}
    actual={s for s in exports["libplayer.so"] if s.startswith("Java_is_xyz_mpv_MPVLib_")}
    require(len(jni)==24 and actual==jni,"native JNI exports mismatch: "+str(jni^actual))
    dst=module/"src/main/jniLibs/x86_64"
    dst.mkdir(parents=True)
    for name in sorted(files):
        shutil.copyfile(src/name,dst/name)
    here=Path(__file__).resolve().parent
    shutil.copyfile(here/"NativeMpvStreamAndroidTest.java",module/"src/androidTest/java/org/fingmi/mpvprobe/NativeMpvStreamAndroidTest.java")
    shutil.copyfile(here/"MpvNativeRequestGate.java",module/"src/main/java/androidx/media3/mpvplayer/media/MpvNativeRequestGate.java")
    with (module/"build.gradle.kts").open("a") as f:
        f.write('\nandroid { packaging { jniLibs.keepDebugSymbols += "**/*.so" } }\n')
    print("PASS_REBUILT_X86_64_ELF_JNI_STAGE",len(jni),"JNI exports",flush=True)

if __name__=="__main__":
    main()
