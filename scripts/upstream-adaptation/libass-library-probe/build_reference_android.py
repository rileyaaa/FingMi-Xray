#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""New isolated Android libass consumer only; no MPV/FFmpeg rebuild."""
import os, re, shutil, struct, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"mpv-stream/android/native"))
from reduced_ffmpeg_diagnostic import run,out,need,sha,symbols
from headless_native_diagnostic import PINS,ASS,ASS_LICENSE,PATCH,ABI,mark,env_run,git

REFERENCE="3382803f11e129af8676a0a775f98293b079797f"
MEDIA="3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
FONT_PINS={
 "fontconfig":("0f236723a3c26bd9745e32ba2b3ee21e5f809295","COPYING","cd5fca1a03b03a815bfb8c4e8ea40a022b38507d"),
 "libxml2":("96498992efa48d52b0e8b83058bd88dbdaf153c1","Copyright","8c0b7c15dd9b66501511f5971ec9cae971997a0d"),
 "unibreak":("28a2756b864c343f438cd22537d49d394d4666a5","LICENCE","6b4137ca2158ffb57a112d54726dd11b6a2a06db"),
 "meson":("6ac66b9cbe36e861a4b10cf62d75ec181dfb291a","COPYING","d645695673349e3947e8e5ae42332d0ac3164cd7"),
}
JAVA={
 "LibassNative.java":"a08a6b94b48f2582048dda07ae6ffebf8c801dc2",
 "LibassTrackSession.java":"bfbbdf79cfd83951c5ba7298308678f6ac1bf654",
 "LibassNativeLibrary.java":"1be15772a8dacebe37270298ebe597bf2fb51211",
 "LibassLibrary.java":"6ec82056ee170094557d4a31d606ef424be56159",
 "LibassFrame.java":"a6504f47296d992556a2dd8ae2f71a35ff4ee7fa",
 "LibassImage.java":"921185b97e3a7e86717f55eafa02aa4ebca60a31",
 "LibassGlImage.java":"f52b1eca9f2daea069b8b851ef68e7094bedc03f",
 "LibassStyleOverride.java":"5074a7e5d283c429a53f0f1a073ab1eac1101187",
}

def check_inputs(src,ndk):
    for name in ("producer","freetype","fribidi","harfbuzz"):
        commit,license_file,blob=PINS[name]
        root=src/name
        need(git(root,"rev-parse","HEAD")==commit and not git(root,"diff","HEAD","--ignore-submodules=all"),"source "+name)
        need(git(root,"hash-object",license_file)==blob,"license "+name)
        mark("ASS_ANDROID_SOURCE",name,commit,blob,sha(root/license_file))
    need(git(src/"ass","rev-parse","HEAD")==ASS and not git(src/"ass","status","--porcelain"),"ass source")
    need(sha(src/"ass/COPYING")==ASS_LICENSE,"ass license")
    need(git(src/"reference","rev-parse","HEAD")==REFERENCE and not git(src/"reference","status","--porcelain"),"reference source")
    need(git(src/"media","rev-parse","HEAD")==MEDIA and not git(src/"media","status","--porcelain"),"media source")
    need("30.0.16248370" in (ndk/"source.properties").read_text(),"NDK revision")
def build(src, ndk, work, abi="x86_64", font_profile=False):
    triple, sys_triple, ffarch, ffcpu, family, cpu, elfclass, machine = ABI[abi]
    arm_build = abi != "x86_64"
    need(abi=="x86_64","only official emulator ABI for this consumer probe")
    mark("ASS_ANDROID_TARGET",abi,"API24")
    check_inputs(src, ndk)
    if font_profile:
        for name,(commit,notice,blob) in FONT_PINS.items():
            root=src/name
            need(git(root,"rev-parse","HEAD")==commit and not git(root,"status","--porcelain"),"source "+name)
            need(git(root,"hash-object",notice)==blob,"notice "+name)
            mark("ASS_FONT_PROFILE_SOURCE",name,commit,blob,sha(root/notice))
        version=out("meson","--version").strip()
        need(version=="1.11.0","fixed Meson 1.11.0, got "+repr(version))
        mark("ASS_FONT_PROFILE_MESON",version)
    work.mkdir(parents=True, exist_ok=False)
    prefix=work/"prefix"; prefix.mkdir()
    tc=ndk/"toolchains/llvm/prebuilt/linux-x86_64"
    bindir=tc/"bin"
    cc=bindir/(triple+"24-clang"); cxx=bindir/(triple+"24-clang++")
    ar=bindir/"llvm-ar"; ranlib=bindir/"llvm-ranlib"; nm=bindir/"llvm-nm"; strip=bindir/"llvm-strip"
    sysroot=tc/"sysroot"; syslib=sysroot/"usr/lib"/sys_triple/"24"
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
        "[host_machine]\nsystem = 'android'\ncpu_family = "+repr(family)+"\ncpu = "+repr(cpu)+"\nendian = 'little'\n"
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

    mark("HEADLESS_STAGE","freetype")
    ft=work/"build-freetype"
    env_run(env,"cmake","-S",src/"freetype","-B",ft,"-G","Ninja",
        "-DCMAKE_TOOLCHAIN_FILE="+str(ndk/"build/cmake/android.toolchain.cmake"),
        "-DANDROID_ABI="+abi,"-DANDROID_PLATFORM=android-24","-DCMAKE_BUILD_TYPE=Release",
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
    if font_profile:
        # Exact official producer XML backend/profile; only xml2 and xmllint
        # are built, not the unrelated testdso target.
        x=work/"build-libxml2"
        env_run(env,"meson","setup",x,src/"libxml2","--cross-file",cross,"--prefix",prefix,
            "--libdir","lib","--wrap-mode=nodownload","--buildtype=release",
            "--default-library=static","-Dauto_features=disabled","-Db_lundef=true",
            "-Dminimum=true",*[f"-D{k}=enabled" for k in ("push","reader","sax1","iso8859x","pattern","output")])
        env_run(env,"meson","compile","-C",x,"-j",jobs,"xml2","xmllint")
        env_run(env,"meson","install","-C",x,"--no-rebuild")
        mark("PASS_ASS_FONT_PROFILE_BUILD","libxml2")
        meson("fontconfig",src/"fontconfig","static","-Dxml-backend=libxml2",
            "-Dtests=disabled","-Ddoc=disabled","-Dtools=disabled","-Dnls=disabled",
            "-Dcache-build=disabled","-Dtests-external-fonts=disabled",
            "-Dadditional-fonts-dirs=no","-Dfontations=disabled")
        ub=src/"unibreak"
        env_run(env,"autoreconf","-fi",cwd=ub)
        u=work/"build-unibreak";u.mkdir()
        uenv=dict(env,CC=str(cc),CXX=str(cxx),AR=str(ar),NM=str(nm),RANLIB=str(ranlib),STRIP=str(strip),
            CFLAGS="-O2 -fPIC",LDFLAGS="-Wl,-z,max-page-size=16384 -Wl,--no-undefined",PKG_CONFIG="/usr/bin/pkg-config")
        env_run(uenv,ub/"configure","--build=x86_64-linux-gnu","--host="+sys_triple,
            "--prefix="+str(prefix),"--libdir="+str(prefix/"lib"),"--with-pic","--enable-static","--disable-shared",cwd=u)
        env_run(uenv,"make","-j"+jobs,cwd=u)
        env_run(uenv,"make","install",cwd=u)
        mark("PASS_ASS_FONT_PROFILE_BUILD","libunibreak")

    mark("HEADLESS_STAGE","libass")
    patch=src/"producer/buildscripts/patches/libass-font-size-em.patch"
    need(sha(patch)==PATCH,"author patch hash")
    ass=src/"ass"
    run("patch","--batch","--forward","--fuzz=0","-d",ass,"-p1","-i",patch)
    env_run(env,"autoreconf","-fi",cwd=ass)
    a=work/"build-ass"; a.mkdir()
    assenv=dict(env,CC=str(cc),CXX=str(cxx),AR=str(ar),NM=str(nm),RANLIB=str(ranlib),STRIP=str(strip),
        CFLAGS="-O2 -fPIC",CXXFLAGS="-O2 -fPIC",LDFLAGS="-lc++_shared",PKG_CONFIG="/usr/bin/pkg-config")
    env_run(assenv,ass/"configure","--build=x86_64-linux-gnu","--host="+sys_triple,
        "--prefix="+str(prefix),"--libdir="+str(prefix/"lib"),"--with-pic","--enable-static","--disable-shared",
        "--disable-asm",*(["--enable-fontconfig","--enable-libunibreak"] if font_profile else ["--disable-fontconfig","--disable-libunibreak"]),
        "--disable-require-system-font-provider",cwd=a)
    env_run(assenv,"make","-j"+jobs,cwd=a)
    env_run(assenv,"make","install",cwd=a)
    mark("PASS_HEADLESS_BUILD","libass")

    for dep in ("libass","harfbuzz","freetype2","fribidi")+(("fontconfig","libxml-2.0","libunibreak") if font_profile else ()):
        value=subprocess.check_output(["pkg-config","--variable=prefix",dep],text=True,env=env).strip()
        need(Path(value).resolve()==prefix,"unexpected dependency origin "+dep)
        mark("ASS_PKG_ORIGIN",dep,value,subprocess.check_output(["pkg-config","--modversion",dep],text=True,env=env).strip())
    flags=subprocess.check_output(["pkg-config","--static","--cflags","--libs","libass"]+(["fontconfig"] if font_profile else []),text=True,env=env).split()
    native=work/"libmedia3ass.so"
    env_run(env,cxx,"-std=c++17","-Wall","-Wextra","-Werror","-fPIC","-shared",
        *(["-DLIBASS_REFERENCE_FONT_PROFILE"] if font_profile else []),HERE/"libass_library.cpp",*flags,"-lc++_shared","-Wl,--no-undefined","-Wl,-z,max-page-size=16384",
        "-Wl,-soname,libmedia3ass.so","-o",native)
    files={native.name:native,"libc++_shared.so":sysroot/"usr/lib"/sys_triple/"libc++_shared.so"}
    for name,path in sorted(files.items()):
        data=path.read_bytes()
        need(data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(3,62),"ELF ABI "+name)
        ph=out(bindir/"llvm-readelf","--program-headers","--wide",path)
        loads=[l.split() for l in ph.splitlines() if l.strip().startswith("LOAD ")]
        need(loads and all(int(l[-1],16)>=16384 and (int(l[1],16)-int(l[2],16))%16384==0 for l in loads),"16KiB gate "+name)
        dyn=out(bindir/"llvm-readelf","--dynamic",path)
        needed=set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]",dyn))
        need(all(n in files or (syslib/n).is_file() for n in needed),"NEEDED "+name+" "+str(needed))
        need(re.findall(r"\(SONAME\).*?\[([^\]]+)\]",dyn)==[name],"SONAME "+name)
        need(not re.search(r"\((RPATH|RUNPATH|TEXTREL)\)",dyn),"relocation/path "+name)
        mark("ASS_ANDROID_ELF",name,len(data),sha(path),sorted(needed))
    exports=symbols(bindir/"llvm-nm",native,True,True)
    expected={"nativeCreateLibrary","nativeReleaseLibrary","nativeAddFont","nativeCreate","nativeRelease",
        "nativeProcessCodecPrivate","nativeProcessChunk","nativeProcessData","nativeSetStorageSize","nativeSetCacheLimits",
        "nativeSetFrameSize","nativeRenderFrame"}
    if font_profile: expected|={"nativeSetFonts","nativeSetFontScale"}
    actual={s.removeprefix("Java_androidx_media3_exoplayer_libass_LibassNative_") for s in exports
        if s.startswith("Java_androidx_media3_exoplayer_libass_LibassNative_")}
    need(actual==expected,"JNI export set "+str(actual^expected))
    media=src/"media"; module=media/"libass-reference-probe";module.mkdir()
    package=module/"src/main/java/androidx/media3/exoplayer/libass";package.mkdir(parents=True)
    refpath=src/"reference/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/libass"
    java=dict(JAVA)
    if font_profile: java["LibassFontConfig.java"]="a65938f9a4627678f7aa1bfe6292b4a8db52d3e0"
    for name,blob in java.items():
        p=refpath/name
        need(git(src/"reference","hash-object",p)==blob,"reference blob "+name)
        need("Licensed under the Apache License, Version 2.0" in p.read_text(),"reference license "+name)
        shutil.copyfile(p,package/name)
        mark("ASS_REFERENCE_UNCHANGED",name,blob,sha(package/name))
    # Compile the actual reference 18 declarations; do NOT fill the six
    # unresolved methods. Exercise only the two new plus real setup/close.
    srcjava=(package/"LibassNative.java").read_text()
    declarations=set(re.findall(r"public static native [\w.]+\s+(\w+)\(",srcjava))
    need(len(declarations)==18 and actual<=declarations,"reference JNI contract")
    dst=module/"src/main/jniLibs/x86_64";dst.mkdir(parents=True)
    for name,path in files.items():shutil.copyfile(path,dst/name)
    assets=module/"src/main/assets";assets.mkdir()
    font=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    notice=Path("/usr/share/doc/fonts-dejavu-core/copyright")
    need(font.is_file() and notice.is_file(),"fixture font and license")
    shutil.copyfile(font,assets/font.name);shutil.copyfile(notice,assets/"DejaVu-LICENSE.txt")
    if font_profile:
        serif=font.with_name("DejaVuSerif.ttf")
        need(serif.is_file(),"second fixture font")
        shutil.copyfile(serif,assets/serif.name)
        mark("ASS_FONT_SECOND_FIXTURE",sha(serif),sha(notice))
        # Actual sources/notices remain independently pinned; test only, not a release bundle.
    mark("ASS_FONT_FIXTURE",sha(font),sha(notice))
    tests=module/"src/androidTest/java/androidx/media3/exoplayer/libass";tests.mkdir(parents=True)
    for name in (("LibassFontTimingAndroidTest.java","LibassFontTimingChecks.java","LibassLibraryProbe.java") if font_profile else ("LibassReferenceAndroidTest.java",)):
        shutil.copyfile(HERE/name,tests/name)
    (module/"src/main/AndroidManifest.xml").write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:label="Isolated Libass consumer" android:allowBackup="false"/></manifest>\n')
    (module/"build.gradle.kts").write_text('''plugins { id("media3.android-application") }
android {
    namespace = "org.fingmi.assprobe"
    defaultConfig {
        applicationId = "org.fingmi.assprobe"
        minSdk = 24
        targetSdk = 34
        testApplicationId = "org.fingmi.assprobe.test"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    testOptions.execution = "HOST"
    packaging { jniLibs.keepDebugSymbols += "**/*.so"; jniLibs.useLegacyPackaging = false }
}
dependencies {
    implementation(project(":lib-common"))
    implementation(libs.androidx.annotation)
    implementation(libs.guava)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.junit)
}
''')
    with (media/"settings.gradle.kts").open("a") as f:f.write('\ninclude(":libass-reference-probe")\n')
    mark("PASS_REFERENCE_ANDROID_ELF_STAGE",len(files),"SO",len(actual),"JNI",len(declarations),"declarations")

if __name__=="__main__":
    if len(sys.argv) not in (4,5) or (len(sys.argv)==5 and sys.argv[4]!="--font-profile"):
        raise SystemExit("usage: build_reference_android.py inputs ndk work [--font-profile]")
    build(*(Path(x).resolve() for x in sys.argv[1:4]),font_profile=len(sys.argv)==5)
