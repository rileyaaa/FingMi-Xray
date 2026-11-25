#!/usr/bin/env python3
"""Compile/link only the pinned public MPEG-H JNI for both supported ABIs.

No media playback, patent clearance, distribution, or complete TV AAR claim.
The native decoder is built from the exact source named in Media3 README.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from prepare_candidate import ROOT, LOCK, blob, guard_fork, git, verified_checkout


def run(*args):
    subprocess.run(list(map(str,args)),check=True)


def output(*args):
    return subprocess.check_output(list(map(str,args)),text=True)


def audit_elf(path,abi,expected,toolchain):
    data=path.read_bytes()
    assert data[:4]==b"\x7fELF" and data[5]==1,abi
    e_type,e_machine=struct.unpack_from("<HH",data,16)
    assert e_type==3 and (data[4],e_machine)==((1,40) if abi=="armeabi-v7a" else (2,183)),abi
    headers=output(toolchain/"llvm-readelf","--program-headers","--wide",path)
    loads=[line.split() for line in headers.splitlines() if line.lstrip().startswith("LOAD ")]
    assert loads,headers
    for line in loads:
        offset,addr,align=int(line[1],16),int(line[2],16),int(line[-1],16)
        assert align>=16384 and (addr-offset)%16384==0,(abi,line)
    syms=output(toolchain/"llvm-nm","-D","--defined-only",path)
    names={line.split()[-1] for line in syms.splitlines() if line.strip()}
    actual={name for name in names if name.startswith("Java_androidx_media3_decoder_mpegh_")}
    assert actual==expected,(abi,sorted(expected-actual),sorted(actual-expected))
    assert "JNI_OnLoad" in names,abi
    dynamic=output(toolchain/"llvm-readelf","--dynamic",path)
    needed=re.findall(r"\(NEEDED\).*?\[(.*?)\]",dynamic)
    assert not any(x in dynamic for x in ("(RPATH)","(RUNPATH)","TEXTREL")),dynamic
    assert set(needed)<=set(("libandroid.so","liblog.so","libm.so","libdl.so","libc.so","libc++_shared.so")),needed
    # No packaged AAR or redistribution; the standalone shared library is
    # just a compile/link proof from the pinned public module.
    print("VERIFIED_NATIVE_MPEGH",abi,len(data),hashlib.sha256(data).hexdigest(),
          "JNI",len(actual),"PT_LOAD",len(loads),"NEEDED",",".join(needed),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media",type=Path,required=True)
    parser.add_argument("--mpegh",type=Path,required=True)
    a=parser.parse_args()
    media,mpegh=a.media.resolve(),a.mpegh.resolve()
    guard_fork()
    verified_checkout(media,"media")
    verified_checkout(mpegh,"mpegh")
    lock=LOCK["public_native_build"]["mpegh"]
    module=media/lock["module"]
    assert git(media,"rev-parse","HEAD:"+lock["module"])==lock["tree"]
    assert blob(mpegh/"LICENSE.txt")==lock["license_blob"]
    expected=set()
    j=module/"src/main/java/androidx/media3/decoder/mpegh"
    for name in ("MpeghDecoderJni","MpeghUiManagerJni"):
        text=(j/(name+".java")).read_text()
        natives=re.findall(r"\bnative\s+\w+\s+(\w+)\s*\(",text)
        assert len(natives)==(9 if name=="MpeghDecoderJni" else 7),(name,natives)
        expected.update("Java_androidx_media3_decoder_mpegh_"+name+"_"+n for n in natives)
    sdk=Path(os.environ["ANDROID_HOME"])
    ndk=sdk/"ndk"/lock["ndk"]
    cmake=sdk/"cmake"/lock["cmake"]/"bin"
    assert re.search(r"Pkg.Revision\s*=\s*"+re.escape(lock["ndk"])+r"\s*$",(ndk/"source.properties").read_text(),re.M)
    toolchain=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    with tempfile.TemporaryDirectory(prefix="fingmi-590-mpegh-") as d:
        root=Path(d)
        src=root/"decoder_mpegh"
        shutil.copytree(module,src)
        jni=src/"src/main/jni"
        shutil.copytree(mpegh,jni/"libmpegh",ignore=shutil.ignore_patterns(".git"))
        assert blob(jni/"libmpegh/LICENSE.txt")==lock["license_blob"]
        for abi in lock["abis"]:
            build=root/abi
            # The consumer adds the decoder as a subdirectory, so demo
            # binaries are OFF by its own documented default. No source
            # modifications; keep both decoder and UI manager ON.
            run(cmake/"cmake","-S",jni,"-B",build,"-G","Ninja",
                "-DCMAKE_MAKE_PROGRAM="+str(cmake/"ninja"),
                "-DCMAKE_TOOLCHAIN_FILE="+str(ndk/"build/cmake/android.toolchain.cmake"),
                "-DANDROID_ABI="+abi,"-DANDROID_PLATFORM=android-"+str(lock["android_platform"]),
                "-DANDROID_STL=c++_static","-DCMAKE_BUILD_TYPE=Release",
                "-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON",
                "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
                "-DCMAKE_POSITION_INDEPENDENT_CODE=ON","-DBUILD_SHARED_LIBS=OFF",
                "-Dmpeghdec_BUILD_DECODER=ON","-Dmpeghdec_BUILD_UIMANAGER=ON",
                "-Dmpeghdec_BUILD_BINARIES=OFF","-Dmpeghdec_BUILD_DOC=OFF",
                "-DFETCHCONTENT_FULLY_DISCONNECTED=ON")
            run(cmake/"cmake","--build",build,"--target","mpeghJNI","--parallel","2")
            paths=list(build.rglob("libmpeghJNI.so"))
            assert len(paths)==1,paths
            audit_elf(paths[0],abi,expected,toolchain)
        print("PASS public MPEG-H JNI compile/link and dual ABI ELF/symbol/16KB checks; no APK, AAR, playback or distribution",flush=True)


if __name__=="__main__":
    main()
