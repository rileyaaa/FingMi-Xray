#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Ephemeral headless x86_64 stream diagnostic. NOT the exact producer or product.
No copied/replaced ELF, no restricted codec build, no production Gradle.
Only source-built dependencies, unchanged official wrapper, existing 3 tests.
"""
import hashlib
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from reduced_ffmpeg_diagnostic import run, out, need, sha, symbols

# Each input is checked at its immutable source revision and license blob.
PINS = {
    "producer": ("1bf892e3271e73d8649f2d209027f1fb17515d15", "LICENSE", "81d2ff31ab3e434d6f67fa5ac1e15e345f175db6"),
    "mpv": ("f964d1495355d5c6626df3de1d3eeb90ddee2aba", "LICENSE.LGPL", "d35234e4098a1401c1b730aeede8d091d458815e"),
    "ffmpeg": ("963c8cbbebb0250f747f0019516bda55bc638da9", "LICENSE.md", "0e75dd3030844784ae339fb51300bd1a3b1e6207"),
    "placebo": ("dc98e2fceb82233b3bb75e9c6249e581c57f3f2d", "LICENSE", "20fb9c7da21cb5a29e10f614a03661a935181652"),
    "placebo/3rdparty/fast_float": ("97b54ca9e75f5303507699d27c6b4f4efe4641a1", "LICENSE-MIT", "2fb2a37ad7fda521092c8b7b16911176c3f8a81b"),
    "placebo/3rdparty/Vulkan-Headers": ("74d8a6cb930c68ef617b202c3ff3c59d919e086b", "LICENSE.md", "d6a0648b652ade1defb1eb481643d2f8d14828b5"),
    "placebo/3rdparty/jinja": ("15206881c006c79667fe5154fe80c01c65410679", "LICENSE.txt", "c37cae49ec77ad6ebb25568c1605f1fee5313cfb"),
    "placebo/3rdparty/markupsafe": ("297fc8e356e6836a62087949245d09a28e9f1b13", "LICENSE.txt", "9d227a0cc43c3268d15722b763bd94ad298645a1"),
    "freetype": ("37515cf56ba3349656049edbed89ffc6f6466f2d", "docs/FTL.TXT", "b9e8cbd66ffff526113350953f4a2f4252a92f49"),
    "fribidi": ("b93119f5fdc7ea47672cc304c1455ffa6dfe7536", "COPYING", "f6683e74e0f0130f246dbf7054f4cacc88ca84b0"),
    "harfbuzz": ("35f656a1a2bab548ea7f54a6dd3fba2b09680d14", "COPYING", "1dd917e9f2e72167de69e3b5dadbc4e7db417da1"),
}
ASS = "a6613d2554daff9e1b5ddf2dbfb3fc31b61b9448"
ASS_LICENSE = "f7e30699d02798351e7f839e3d3bfeb29ce65e44efa7735c225464c4fd7dfe9c"
PATCH = "fa6d0d3a00cb7896525a707407daad4d51e807d65d0692d6d33cc565d30ea9fa"
FF_NAMES = ("avutil", "swresample", "avcodec", "avformat", "swscale", "avfilter")
WRAPPER = ("main", "stream", "render", "request", "log", "jni_utils", "property", "event", "thumbnail")


def mark(*parts):
    print(*parts, flush=True)


def env_run(env, *args, cwd=None):
    subprocess.run([str(a) for a in args], check=True, cwd=cwd, env=env)


def git(root, *args):
    return out("git", "-C", root, *args).strip()


def check_inputs(src, ndk):
    for name, (commit, license_file, blob) in PINS.items():
        root = src / name
        need(git(root, "rev-parse", "HEAD") == commit, "source revision " + name)
        # Uninitialized, unused submodules are allowed. Checked out source is not dirty.
        need(not git(root, "diff", "HEAD", "--ignore-submodules=all"), "modified source " + name)
        need(git(root, "hash-object", license_file) == blob, "license blob " + name)
        mark("HEADLESS_SOURCE_LICENSE", name, commit, license_file, blob, sha(root/license_file))
        if name.startswith("placebo/"):
            rel = name.removeprefix("placebo/")
            need(git(src/"placebo", "ls-tree", "HEAD", rel).split()[2] == commit, "gitlink "+name)
    need(git(src/"ass", "rev-parse", "HEAD")==ASS and not git(src/"ass","status","--porcelain"), "libass revision")
    need(sha(src/"ass/COPYING")==ASS_LICENSE, "libass license")
    mark("HEADLESS_SOURCE_LICENSE", "ass", ASS, ASS_LICENSE)
    ff=src/"ffmpeg"
    need(not (ff/"dependency").exists(), "excluded external sources present")
    for root, dirs, files in os.walk(ff):
        dirs[:] = [d for d in dirs if d != ".git"]
        need(not any(re.search(r"avs3|arcdav3a|av3a", n, re.I) for n in dirs+files), "excluded codec filename "+root)
    need(not (src/"placebo/3rdparty/glad/glad").exists(), "unused graphics generator unexpectedly materialized")
    need("30.0.16248370" in (ndk/"source.properties").read_text(), "NDK revision")
    need(git(src/"mpv", "hash-object", "Copyright")=="61d3a038e75a28fdf40ec229b2c38f98d8ee8c16", "mpv license scope")
    mark("PASS_HEADLESS_INPUTS_ONLY")


def build(src, ndk, work, media):
    check_inputs(src, ndk)
    work.mkdir(parents=True, exist_ok=False)
    prefix=work/"prefix"; prefix.mkdir()
    tc=ndk/"toolchains/llvm/prebuilt/linux-x86_64"
    bindir=tc/"bin"
    cc=bindir/"x86_64-linux-android24-clang"; cxx=bindir/"x86_64-linux-android24-clang++"
    ar=bindir/"llvm-ar"; ranlib=bindir/"llvm-ranlib"; nm=bindir/"llvm-nm"; strip=bindir/"llvm-strip"
    sysroot=tc/"sysroot"; syslib=sysroot/"usr/lib/x86_64-linux-android/24"
    need(syslib.is_dir(), "actual NDK sysroot")
    jobs=str(min(4, os.cpu_count() or 2))
    pcdir=str(prefix/"lib/pkgconfig")
    env=os.environ.copy()
    for key in ("PKG_CONFIG_PATH","PKG_CONFIG_SYSROOT_DIR","CFLAGS","CPPFLAGS","CXXFLAGS","LDFLAGS","LD_LIBRARY_PATH","CPATH","C_INCLUDE_PATH","CPLUS_INCLUDE_PATH","LIBRARY_PATH"):
        env.pop(key,None)
    env["PKG_CONFIG_LIBDIR"]=pcdir
    cross=work/"android.cross"
    cross.write_text("[binaries]\nc = "+repr(str(cc))+"\ncpp = "+repr(str(cxx))+
        "\nar = "+repr(str(ar))+"\nstrip = "+repr(str(strip))+"\npkg-config = '/usr/bin/pkg-config'\n"
        "[host_machine]\nsystem = 'android'\ncpu_family = 'x86_64'\ncpu = 'x86_64'\nendian = 'little'\n"
        "[properties]\nneeds_exe_wrapper = true\npkg_config_libdir = ["+repr(pcdir)+"]\n"
        "[built-in options]\nc_args = ['-fPIC']\ncpp_args = ['-fPIC']\n"
        "c_link_args = ['-Wl,-z,max-page-size=16384', '-Wl,--no-undefined', '-lc++_shared']\n"
        "cpp_link_args = ['-Wl,-z,max-page-size=16384', '-Wl,--no-undefined']\n")
    def meson(name, source, kind, *opts):
        b=work/("build-"+name)
        mark("HEADLESS_STAGE", name)
        env_run(env,"meson","setup",b,source,"--cross-file",cross,"--prefix",prefix,
                "--libdir","lib","--wrap-mode=nodownload","--buildtype=release",
                "--default-library="+kind,"-Dauto_features=disabled","-Db_lundef=true",*opts)
        env_run(env,"meson","compile","-C",b,"-j",jobs)
        env_run(env,"meson","install","-C",b,"--no-rebuild")
        mark("PASS_HEADLESS_BUILD",name)

    # First close the missing FFmpeg dependency profile; no rerun of the prior
    # object-only test. New avfilter and swresample are required by real MPV.
    b=work/"build-ffmpeg"; b.mkdir()
    mark("HEADLESS_STAGE","ffmpeg-six")
    env_run(env,src/"ffmpeg/configure","--prefix="+str(prefix),"--libdir="+str(prefix/"lib"),
        "--target-os=android","--enable-cross-compile","--arch=x86_64","--cpu=generic",
        "--cc="+str(cc),"--cxx="+str(cxx),"--ld="+str(cc),"--ar="+str(ar),"--ranlib="+str(ranlib),
        "--nm="+str(nm),"--strip="+str(strip),"--pkg-config=false",
        "--disable-autodetect","--disable-everything","--disable-network","--disable-gpl","--disable-nonfree",
        "--disable-version3","--disable-libarcdav3a","--disable-libuavs3d","--disable-avdevice",
        "--enable-avfilter","--enable-swresample","--disable-programs","--disable-doc","--disable-asm",
        "--disable-static","--enable-shared","--enable-pic","--enable-jni","--enable-demuxer=wav",
        "--enable-decoder=pcm_s16le","--enable-protocol=file","--enable-filter=anull,aresample,aformat,format,null",
        "--extra-ldflags=-Wl,-z,max-page-size=16384",cwd=b)
    config=(b/"config.h").read_text()+"\n"+(b/"config_components.h").read_text()
    for flag in ("LIBARCDAV3A","LIBUAVS3D","LIBARCDAV3A_DECODER","LIBUAVS3D_DECODER","AVS3_PARSER","GPL","NONFREE","VERSION3"):
        need(not re.search(r"(?m)^#define CONFIG_"+flag+r"\s+1\b",config),"forbidden enabled "+flag)
    for flag in ("JNI","WAV_DEMUXER","PCM_S16LE_DECODER","FILE_PROTOCOL","AVFILTER","SWRESAMPLE"):
        need(re.search(r"(?m)^#define CONFIG_"+flag+r"\s+1\b",config),"missing enabled "+flag)
    env_run(env,"make","-j"+jobs,cwd=b)
    env_run(env,"make","install",cwd=b)
    mark("PASS_HEADLESS_BUILD","ffmpeg-six",sha(b/"libavutil/avconfig.h"))

    mark("HEADLESS_STAGE","freetype")
    ft=work/"build-freetype"
    env_run(env,"cmake","-S",src/"freetype","-B",ft,"-G","Ninja",
        "-DCMAKE_TOOLCHAIN_FILE="+str(ndk/"build/cmake/android.toolchain.cmake"),
        "-DANDROID_ABI=x86_64","-DANDROID_PLATFORM=android-24","-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX="+str(prefix),"-DCMAKE_INSTALL_LIBDIR=lib","-DBUILD_SHARED_LIBS=OFF",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        *["-DFT_DISABLE_"+x+"=ON" for x in ("ZLIB","BZIP2","PNG","HARFBUZZ","BROTLI","HVF")])
    env_run(env,"cmake","--build",ft,"--parallel",jobs)
    env_run(env,"cmake","--install",ft)
    mark("PASS_HEADLESS_BUILD","freetype")
    meson("fribidi",src/"fribidi","static","-Dbin=false","-Ddocs=false","-Dtests=false")
    meson("harfbuzz",src/"harfbuzz","static","-Dfreetype=enabled",
        "-Draster=disabled","-Dvector=disabled","-Dgpu=disabled","-Dsubset=disabled",
        "-Dtests=disabled","-Ddocs=disabled","-Dutilities=disabled",
        "-Dglib=disabled","-Dgobject=disabled","-Dcairo=disabled","-Dicu=disabled","-Dgraphite2=disabled")
    mark("HEADLESS_STAGE","libass")
    patch=src/"producer/buildscripts/patches/libass-font-size-em.patch"
    need(sha(patch)==PATCH,"author patch hash")
    ass=src/"ass"
    run("patch","--batch","--forward","--fuzz=0","-d",ass,"-p1","-i",patch)
    env_run(env,"autoreconf","-fi",cwd=ass)
    a=work/"build-ass"; a.mkdir()
    assenv=dict(env,CC=str(cc),CXX=str(cxx),AR=str(ar),NM=str(nm),RANLIB=str(ranlib),STRIP=str(strip),
        CFLAGS="-O2 -fPIC",CXXFLAGS="-O2 -fPIC",LDFLAGS="-lc++_shared",PKG_CONFIG="/usr/bin/pkg-config")
    env_run(assenv,ass/"configure","--build=x86_64-linux-gnu","--host=x86_64-linux-android",
        "--prefix="+str(prefix),"--libdir="+str(prefix/"lib"),"--with-pic","--enable-static","--disable-shared",
        "--disable-asm","--disable-fontconfig","--disable-libunibreak","--disable-require-system-font-provider",cwd=a)
    env_run(assenv,"make","-j"+jobs,cwd=a)
    env_run(assenv,"make","install",cwd=a)
    mark("PASS_HEADLESS_BUILD","libass")
    # Upstream's own no-graphics configuration; no substitute library or API.
    meson("libplacebo",src/"placebo","static","-Dopengl=disabled","-Dvulkan=disabled",
        "-Dd3d11=disabled","-Dshaderc=disabled","-Dglslang=disabled","-Dlcms=disabled","-Ddovi=disabled",
        "-Dlibdovi=disabled","-Dunwind=disabled","-Dxxhash=disabled","-Ddemos=false","-Dtests=false")
    # Verify each required dependency was installed in our prefix. pkg-config
    # never resolves against the runner's host libraries.
    for dep in (*("lib"+n for n in FF_NAMES),"libass","libplacebo","harfbuzz","freetype2","fribidi"):
        value=subprocess.check_output(["pkg-config","--variable=prefix",dep],text=True,env=env).strip()
        need(Path(value).resolve()==prefix,"unexpected dependency origin "+dep+" "+value)
        mark("HEADLESS_PREFIX_DEP",dep,subprocess.check_output(["pkg-config","--modversion",dep],text=True,env=env).strip())
    meson("mpv",src/"mpv","shared","-Dgpl=false","-Dlibmpv=true","-Dcplayer=false",
        "-Dgl=disabled","-Dvulkan=disabled","-Dlua=disabled","-Dlibavdevice=disabled",
        "-Dmanpage-build=disabled","-Dprefer_static=true")
    libdir=prefix/"lib"
    jni=src/"producer/app/src/main/jni"
    player=libdir/"libplayer.so"
    # Same nine upstream units; a new link in the single reduced configuration,
    # not a repeat of prior object-only CI or the exact four-SO producer.
    mark("HEADLESS_STAGE","official-wrapper-link")
    env_run(env,cxx,"-shared","-std=c++11","-fPIC","-Werror","-I"+str(prefix/"include"),
        "-I"+str(jni),*(jni/(n+".cpp") for n in WRAPPER),"-L"+str(libdir),
        "-Wl,--no-undefined","-Wl,-z,max-page-size=16384","-Wl,-soname,libplayer.so",
        "-lmpv","-lavcodec","-lswscale","-llog","-lc++_shared","-o",player)
    need(not git(src/"producer","diff","HEAD","--","app/src/main/jni"), "wrapper altered")
    mark("PASS_HEADLESS_BUILD","official-wrapper-link")
    names={"lib"+n+".so" for n in FF_NAMES}|{"libmpv.so","libplayer.so","libc++_shared.so"}
    files={n:libdir/n for n in names}
    files["libc++_shared.so"]=sysroot/"usr/lib/x86_64-linux-android/libc++_shared.so"
    readelf=bindir/"llvm-readelf"
    exports={}; imports={}
    for name,path in sorted(files.items()):
        need(path.is_file(),"missing "+str(path))
        data=path.read_bytes()
        need(data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(3,62),"ABI "+name)
        ph=out(readelf,"--program-headers","--wide",path)
        loads=[l.split() for l in ph.splitlines() if l.strip().startswith("LOAD ")]
        need(loads and all(int(l[-1],16)>=16384 and (int(l[1],16)-int(l[2],16))%16384==0 for l in loads),"16KiB ELF gate "+name)
        dyn=out(readelf,"--dynamic",path)
        soname=re.findall(r"\(SONAME\).*?\[([^\]]+)\]",dyn)
        need(soname==[name],"actual SONAME not Android package name "+name+" "+str(soname))
        needed=set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]",dyn))
        need(all(n in names or (syslib/n).is_file() for n in needed),"dependency closure "+name+" "+str(needed))
        need(not re.search(r"\((RPATH|RUNPATH|TEXTREL)\)",dyn),"dynamic relocation/path "+name)
        exports[name]=symbols(nm,path,True,True); imports[name]=symbols(nm,path,False,True)
        mark("HEADLESS_ELF",name,len(data),sha(path),sorted(needed))
    mpvimports={x for x in imports["libplayer.so"] if x.startswith("mpv_")}
    need({"mpv_stream_cb_add_ro","mpv_command_node_async"}<=mpvimports<=exports["libmpv.so"],"actual mpv symbol closure")
    ffexports=set().union(*(exports["lib"+n+".so"] for n in FF_NAMES))
    for name in ("libmpv.so","libplayer.so"):
        ffimports={s for s in imports[name] if re.match(r"^(av_|avcodec_|avformat_|avfilter_|avutil_|swr_|sws_)",s)}
        need(ffimports and ffimports<=ffexports,"FFmpeg symbol closure "+name+" "+str(ffimports-ffexports))
    need("av_jni_set_java_vm" in imports["libplayer.so"], "JNI setup import")
    module=media/"mpv-stream-probe"
    bridge=module/"src/main/java/is/xyz/mpv/MPVLib.java"
    jni_names={"Java_is_xyz_mpv_MPVLib_"+n for n in re.findall(r"public static native [^;\n]+?\s+(\w+)\(",bridge.read_text())}
    actual={s for s in exports["libplayer.so"] if s.startswith("Java_is_xyz_mpv_MPVLib_")}
    need(len(jni_names)==24 and jni_names==actual,"24 actual JNI exports mismatch "+str(jni_names^actual))
    dst=module/"src/main/jniLibs/x86_64"
    dst.mkdir(parents=True,exist_ok=False)
    for name,path in files.items(): shutil.copyfile(path,dst/name)
    here=Path(__file__).resolve().parent
    tests=module/"src/androidTest/java/org/fingmi/mpvprobe"
    old=(here/"NativeMpvStreamAndroidTest.java").read_text()
    needle='        System.loadLibrary("ffmpeg");'
    need(old.count(needle)==1,"exact loader substitution")
    replacement="\n".join('        System.loadLibrary("'+name+'");' for name in FF_NAMES)
    # Only the disposable test's library loading differs; all 3 assertions
    # and existing owner/Media3 stream implementation remain unchanged.
    (tests/"NativeMpvStreamAndroidTest.java").write_text(old.replace(needle,replacement))
    (tests/"Media3MpvInputAndroidTest.java").unlink()
    shutil.copyfile(here/"MpvNativeRequestGate.java",module/"src/main/java/androidx/media3/mpvplayer/media/MpvNativeRequestGate.java")
    with (module/"build.gradle.kts").open("a") as f:
        f.write('\nandroid { packaging { jniLibs.keepDebugSymbols += "**/*.so"; jniLibs.useLegacyPackaging = false } }\n')
    mark("PASS_REDUCED_HEADLESS_ELF_JNI_STAGE",len(names),"SO",len(actual),"JNI", "NOT_EXACT_PRODUCER")


if __name__=="__main__":
    if len(sys.argv)!=5: raise SystemExit("usage: headless_native_diagnostic.py inputs ndk work disposable_media")
    build(*(Path(x).resolve() for x in sys.argv[1:]))
