#!/usr/bin/env python3
"""Build the real public Media3 MPEG-H AAR in an isolated CI checkout.

This is the Gradle consumer and Java/JNI packaging gate, not a rerun of the
standalone CMake audit. Do not stage in TV app/libs or distribute this AAR.
The Fraunhofer license is separate and no patent rights are asserted.
"""
import argparse
import hashlib
from io import BytesIO
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

from prepare_candidate import LOCK, blob, git, guard_fork, verified_checkout
from verify_public_mpegh_native import audit_elf

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--mpegh", type=Path, required=True)
    a = parser.parse_args()
    media, mpegh = a.media.resolve(), a.mpegh.resolve()
    guard_fork()
    verified_checkout(media, "media")
    verified_checkout(mpegh, "mpegh")
    lock = LOCK["public_native_build"]["mpegh"]
    gate = lock["aar_candidate"]
    assert git(media, "rev-parse", "HEAD:"+lock["module"]) == lock["tree"]
    assert blob(mpegh/"LICENSE.txt") == lock["license_blob"]
    module = media/lock["module"]
    gradle = module/"build.gradle.kts"
    assert blob(gradle) == gate["consumer_gradle_blob"]
    sdk = Path(os.environ["ANDROID_HOME"])
    ndk = sdk/"ndk"/gate["ndk"]
    cmake = sdk/"cmake"/gate["cmake"]
    assert re.search(r"Pkg.Revision\s*=\s*"+re.escape(gate["ndk"])+r"\s*$",
                     (ndk/"source.properties").read_text(), re.M)
    assert (cmake/"bin/cmake").is_file()
    assert (sdk/"platforms"/("android-"+str(gate["compile_sdk"]))/"android.jar").is_file()
    toolchain = ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin"
    package = "androidx/media3/decoder/mpegh/"
    j = module/"src/main/java"/package
    expected = set()
    java_names = ("MpeghDecoderJni", "MpeghUiManagerJni")
    for name in java_names:
        natives = re.findall(r"\bnative\s+\w+\s+(\w+)\s*\(", (j/(name+".java")).read_text())
        assert len(natives) == (9 if name == java_names[0] else 7)
        expected.update("Java_androidx_media3_decoder_mpegh_"+name+"_"+n for n in natives)
    required_classes = {package+n+".class" for n in (
        "MpeghAudioRenderer", "MpeghDecoder", "MpeghDecoderException",
        "MpeghDecoderJni", "MpeghLibrary", "MpeghUiCommandHelper", "MpeghUiManagerJni")}
    # Use the exact public Gradle module and its existing dependencies. Only
    # append build constraints for TV's API 24 and the two supported ABIs,
    # keeping the native implementation and decoder/UI manager enabled.
    # The checkout is ephemeral; restore the only tracked file in finally.
    raw = gradle.read_bytes()
    source = module/"src/main/jni/libmpegh"
    assert not source.exists(), "unexpected pre-existing decoder input"
    extra = '''
android {
  ndkVersion = "29.0.14206865"
  defaultConfig {
    minSdk = 24
    ndk { abiFilters.addAll(setOf("armeabi-v7a", "arm64-v8a")) }
    externalNativeBuild {
      cmake {
        arguments.addAll(listOf(
          "-DANDROID_STL=c++_static",
          "-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON",
          "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384",
          "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
          "-DBUILD_SHARED_LIBS=OFF",
          "-Dmpeghdec_BUILD_DECODER=ON",
          "-Dmpeghdec_BUILD_UIMANAGER=ON",
          "-Dmpeghdec_BUILD_BINARIES=OFF",
          "-Dmpeghdec_BUILD_DOC=OFF",
          "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"
        ))
      }
    }
  }
  externalNativeBuild.cmake.version = "3.22.1"
}
'''
    assert gate["abis"] == lock["abis"] == ["armeabi-v7a", "arm64-v8a"]
    assert gate["min_sdk"] == lock["android_platform"] == 24
    assert gate["ndk"] == lock["ndk"] and gate["cmake"] == lock["cmake"]
    try:
        shutil.copytree(mpegh, source, ignore=shutil.ignore_patterns(".git"))
        assert blob(source/"LICENSE.txt") == lock["license_blob"]
        gradle.write_bytes(raw+extra.encode())
        with tempfile.TemporaryDirectory(prefix="fingmi-590-mpegh-aar-") as d:
            work = Path(d)
            subprocess.run(["bash", "gradlew", "--no-daemon", "--max-workers=2",
                            "-Dorg.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=768m",
                            "-PexternalNativeBuildDir="+str(work/"native"),
                            ":lib-decoder-mpegh:assembleRelease"], cwd=media, check=True)
            candidates = [p for p in module.rglob("lib-decoder-mpegh-release.aar")
                          if "outputs" in p.parts]
            assert len(candidates) == 1, candidates
            aar = candidates[0]
            with ZipFile(aar) as z:
                assert len(z.namelist()) == len(set(z.namelist())), "duplicate AAR entries"
                assert "AndroidManifest.xml" in z.namelist()
                jar_bytes = z.read("classes.jar")
                with ZipFile(BytesIO(jar_bytes)) as classes:
                    assert required_classes <= set(classes.namelist()), sorted(required_classes-set(classes.namelist()))
                jar = work/"classes.jar"
                jar.write_bytes(jar_bytes)
                # Check native methods in the actual compiled classes too.
                actual = set()
                for name in java_names:
                    out = subprocess.check_output(["javap", "-classpath", str(jar), "-private", "-s",
                                                   package.replace("/",".")+name], text=True)
                    for native in re.findall(r"\bnative\s+[\w.\[\]]+\s+(\w+)\(", out):
                        actual.add("Java_androidx_media3_decoder_mpegh_"+name+"_"+native)
                assert actual == expected, (sorted(expected-actual),sorted(actual-expected))
                native = {n for n in z.namelist() if n.startswith("jni/") and n.endswith(".so")}
                required = {"jni/"+abi+"/libmpeghJNI.so" for abi in gate["abis"]}
                assert native == required, (native,required)
                for abi in gate["abis"]:
                    path = work/abi/"libmpeghJNI.so"
                    path.parent.mkdir()
                    path.write_bytes(z.read("jni/"+abi+"/libmpeghJNI.so"))
                    audit_elf(path, abi, expected, toolchain)
                    # The isolated candidate must not introduce another copy
                    # of the TV's shared C++ runtime or rely on missing libs.
                    dynamic = subprocess.check_output([str(toolchain/"llvm-readelf"), "--dynamic", str(path)], text=True)
                    assert "libc++_shared.so" not in dynamic, abi
                print("VERIFIED_PUBLIC_MPEGH_AAR", aar.stat().st_size,
                      hashlib.sha256(aar.read_bytes()).hexdigest(), "classes", len(required_classes),
                      "jni_methods", len(actual), "both_abi", flush=True)
            # Remove compiled AAR; the runner performs no upload/distribution.
            aar.unlink()
        print("PASS actual Gradle MPEG-H AAR Java/JNI/ELF packaging on both ABIs; not complete customized TV linkage", flush=True)
    finally:
        gradle.write_bytes(raw)
        if source.exists():
            shutil.rmtree(source)
        assert blob(gradle) == gate["consumer_gradle_blob"]

if __name__ == "__main__":
    main()
