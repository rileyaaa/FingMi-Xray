#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Source-backed alternative, staged only in the disposable FongMi/media tree."""
import json, os, re, shutil, struct, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"libass-library-probe"))
import build_reference_android as common
from reduced_ffmpeg_diagnostic import run,out,need,sha,symbols
from headless_native_diagnostic import mark,env_run,git
from make_fixture import build as fixture
from alpha8_candidate import stage_alpha8
PIN="504f64a325059ab5188c4c9d0eddc99c9356a23a"
MIT="da5ff16aa97b20ed185424bda125b1ca65f7183a"
NATIVE="lib_ass_kt/src/main/cpp/AssKt.c"
NATIVE_BLOB="c6913278e244c87e4abe30ebcf633d681284fa97"
ADAPTER="lib_ass_media/src/main/java/io/github/peerless2012/ass/media/text/AssTrackOutput.kt"

def check_peerless(src):
    root=src/"peerless"
    need(git(root,"rev-parse","HEAD")==PIN and not git(root,"status","--porcelain","--ignore-submodules=all"),"peerless pin")
    need(git(root,"hash-object","LICENSE")==MIT,"peerless MIT")
    need(git(root,"hash-object",NATIVE)==NATIVE_BLOB,"peerless C pin")
    manifest=json.loads((HERE/"source-pins.json").read_text())
    for path,blob in manifest.items():
        need(git(root,"hash-object",path)==blob,"peerless Kotlin source "+path)
    mark("PASS_PEERLESS_SOURCE_PINS",PIN,MIT,NATIVE_BLOB,len(manifest))
    return root,manifest

def stage(src):
    root,manifest=check_peerless(src)
    media=src/"media"
    need(git(media,"rev-parse","HEAD")==common.MEDIA and not git(media,"status","--porcelain"),"media pin")
    need(git(media,"hash-object","LICENSE")=="d645695673349e3947e8e5ae42332d0ac3164cd7","media license")
    module=media/"peerless-ass-probe";module.mkdir()
    for path,blob in manifest.items():
        name=path.split("/src/main/java/",1)[1]
        dst=module/"src/main/java"/name;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(HERE/"AssTrackOutput.kt" if path==ADAPTER else root/path,dst)
        mark("PEERLESS_STAGED",path,blob,sha(dst),"reviewed adapter" if path==ADAPTER else "unchanged")
    assets=module/"src/main/assets";assets.mkdir(parents=True)
    font=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    notice=Path("/usr/share/doc/fonts-dejavu-core/copyright")
    need(font.is_file() and notice.is_file(),"fixture font and notice")
    (assets/"timed.mkv").write_bytes(fixture(font.read_bytes()))
    shutil.copyfile(notice,assets/"DejaVu-LICENSE.txt")
    shutil.copyfile(root/"LICENSE",assets/"peerless-MIT.txt")
    shutil.copyfile(HERE/"NOTICE",assets/"peerless-adapter-NOTICE.txt")
    mark("PEERLESS_FIXTURE",sha(font),sha(notice),sha(assets/"timed.mkv"))
    test=module/"src/androidTest/java/org/fingmi/peerlessprobe";test.mkdir(parents=True)
    shutil.copyfile(HERE/"PeerlessMatroskaTest.java",test/"PeerlessMatroskaTest.java")
    (module/"src/main/AndroidManifest.xml").write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:label="Isolated ASS alternative" android:allowBackup="false"/></manifest>\n')
    (module/"build.gradle.kts").write_text('''plugins { id("media3.android-application") }
android {
    namespace = "org.fingmi.peerlessprobe"
    defaultConfig {
        applicationId = "org.fingmi.peerlessprobe"
        minSdk = 24
        targetSdk = 34
        testApplicationId = "org.fingmi.peerlessprobe.test"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    testOptions.execution = "HOST"
    packaging { jniLibs.keepDebugSymbols += "**/*.so"; jniLibs.useLegacyPackaging = false }
}
dependencies {
    implementation(project(":lib-common"))
    implementation(project(":lib-exoplayer"))
    implementation(project(":lib-extractor"))
    implementation(project(":lib-ui"))
    implementation(project(":lib-effect"))
    implementation(libs.androidx.annotation)
    implementation(libs.androidx.annotation.experimental)
    implementation(libs.guava)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.junit)
}
''')
    with (media/"settings.gradle.kts").open("a") as f:f.write('\ninclude(":peerless-ass-probe")\n')
    mark("PASS_PEERLESS_MEDIA_SOURCE_STAGE",len(manifest),"actual Kotlin files","one reviewed replacement adapter")

def native(src,ndk,work,prefix,env,bindir,sysroot,sys_triple,flags):
    root=src/"peerless"
    native=work/"libasskt.so"
    cc=bindir/"x86_64-linux-android24-clang"
    staged=work/"AssKt.alpha8.c"
    staged_sha=stage_alpha8(root/NATIVE,staged)
    mark("PEERLESS_ALPHA8_STAGED",NATIVE_BLOB,sha(HERE/"alpha8_candidate.py"),staged_sha)
    env_run(env,cc,"-fPIC","-shared",staged,*flags,"-lc++_shared","-lGLESv2","-ljnigraphics","-landroid","-llog",
        "-Wl,--no-undefined","-Wl,-z,max-page-size=16384","-Wl,-soname,libasskt.so","-o",native)
    files={native.name:native,"libc++_shared.so":sysroot/"usr/lib"/sys_triple/"libc++_shared.so"}
    syslib=sysroot/"usr/lib"/sys_triple/"24"
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
        mark("PEERLESS_ELF",name,len(data),sha(path),sorted(needed))
    need("JNI_OnLoad" in symbols(bindir/"llvm-nm",native,True,True),"real registration entry")
    methods=re.findall(r'\{"(native\w+)",\s*"([^"]+)"',(root/NATIVE).read_text())
    need(len(methods)==19 and len(set(methods))==19,"19 real registered JNI signatures")
    need(re.findall(r'\{"(native\w+)",\s*"([^"]+)"',staged.read_text())==methods,"staged registration unchanged")
    mark("PEERLESS_REGISTERED_SOURCE",methods)
    dst=src/"media/peerless-ass-probe/src/main/jniLibs/x86_64";dst.mkdir(parents=True)
    for name,path in files.items():shutil.copyfile(path,dst/name)
    mark("PASS_PEERLESS_NATIVE_STAGE",len(files),"SO",len(methods),"registered signatures","not original AAR ABI")

if __name__=="__main__":
    src,ndk,work=map(lambda p:Path(p).resolve(),sys.argv[1:])
    # Common builder verifies clean media/source inputs. The callback stages
    # our new JNI only; no previous reference JNI rebuilt or prior tests run.
    check_peerless(src)
    common.build(src,ndk,work,font_profile=True,consumer=native)
    # Native staging creates the module's jniLibs first. Move it temporarily
    # outside the clean source tree before staging Kotlin/Gradle.
    module=src/"media/peerless-ass-probe"
    held=work/"staged-jni"
    shutil.move(module,held)
    stage(src)
    shutil.move(held/"src/main/jniLibs",module/"src/main/jniLibs")
