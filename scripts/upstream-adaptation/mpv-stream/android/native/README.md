# ABI-matched MPV native consumer probe (isolated, not product)

The independent Android Media3/OkHttp adapter already passed real device
instrumentation 5/5 in [45752877349 / 139684568777](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45752877349/job/139684568777).
See [the completed record](../README.md). Do not rerun those five tests for
this batch. This directory is a separate native acceptance candidate; no
prepare_candidate, ordinary player, Exo/Xray, TV recovery, release, or
existing ARM ELF gate is changed.

## Input and license gate

The pinned official producer is FongMi/mpv-android@1bf892e3271e73d8649f2d209027f1fb17515d15,
MIT JNI source; its successful original run 44885769496 and native artifact
14699804350 (SHA256 f07422157e0f18409084e1bf50352f142d56fca2a7cf71802b6e95621cb9d4f4)
cover armv7l and arm64, not the x86_64 Android emulator. NDK r30
30.0.16248370, MPV f964d1495355d5c6626df3de1d3eeb90ddee2aba,
FFmpeg 963c8cbbebb0250f747f0019516bda55bc638da9,
libplacebo dc98e2fceb82233b3bb75e9c6249e581c57f3f2d,
dav1d 2a0775ca5ea055450bdfbfe81758a3c9e001f58a and
libass a6613d2554daff9e1b5ddf2dbfb3fc31b61b9448 are the resolved
producer inputs. The dependency and license closure is not implied by
these pins. No available, authorized ARM device/runner or matching legal
x86_64 binary input was established; do not substitute ARM libraries.

New specific blocker, before executing the full producer: the fixed
[FFmpeg recipe](https://github.com/FongMi/mpv-android/blob/1bf892e3271e73d8649f2d209027f1fb17515d15/buildscripts/scripts/ffmpeg.sh)
(blob 90e6de21643a374285a90fdde3a1369b32311451) requires dependency/avs3a,
builds arcdav3a, enables libarcdav3a and GPL/version3. The actual
[avs3_dec_lib.c](https://github.com/FongMi/FFmpeg/blob/963c8cbbebb0250f747f0019516bda55bc638da9/dependency/avs3a/src/avs3_dec_lib.c)
(blob 0b18d0352e5ba35bb357a616fd33cef23b7ec698) bears Huawei 2023
copyright and an explicit UWA Code Sharing Policy notice, not a blanket
GPL grant. The [UWA published policy v1.0](https://www.uhd-world-association.com/uwa-regulations/)
(Arts. 2, 6, 7, 9, 11) limits code licenses to eligible applicants and
conditional forwarding. No applicable separate permission for this
project or compatible full combined distribution rights have been verified.
Public repository visibility, the FFmpeg license elsewhere in the tree,
or a producer artifact cannot establish that permission. This is an
unresolved project authorization gate, not a legal ruling on upstream
or a claim that all FFmpeg sources have restricted licenses.

Reproducing this blocker requires inspecting those two exact blobs and
the policy, not downloading or executing the restricted codec. Full
x86_64 producer rebuild was deliberately NOT started. No changed
configuration disabling AVS3A was built and represented as the fixed
producer, no APK extraction, no substitute binaries. Resume the exact
build only with verified applicable source/build/use rights and combined
license closure, pinned remaining dependency revisions and receipts.
Keep diagnostic profiles separate from fixed-producer acceptance.

## Actual native source compilation (terminal, 2026-11-26)

[Run 45755692922 / job 139693660966](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45755692922/job/139693660966)
completed **failure** at thumbnail.cpp. The
[historical workflow](https://github.com/rileyaaa/FingMi-Xray/blob/eda49ed557a9de477fa796beebdfad79b8cecd5b/.github/workflows/94-native-consumer-probes-once.yml)
is the exact recipe, including sparse checkout of the public headers
only. Official inputs were not modified. Header Git blobs:
client.h f970b9ab5dc792a20c8a5d4eca5a4526fbadb594,
stream_cb.h 9ae6f31a16847d9a695886a78bc1b7a2c9942a27,
libavcodec/jni.h 955cd28096b7eceafefce306681d9225673bb459.
The last is the public LGPL header. dependency/avs3a was absent in
the checkout. NDK x86_64-linux-android23-clang++ -std=c++11 -fPIC -Werror
compiled eight actual official JNI translation units; script checked
ELF64 x86_64 ET_REL and read symbols.

| Official JNI unit | Git blob | Object bytes |
| --- | --- | ---: |
| main.cpp | 0abeaf6b3146f41b7fbd9f961aa78f134f7179ce | 78216 |
| stream.cpp | a4ebe55984fa12de9b0a354da4a98cfcfa634d5d | 17216 |
| render.cpp | 9ddee412d1860da16902f615eecc31a02672acf9 | 3544 |
| request.cpp | 56d0d1cef76b582f472e21557cfee8a3d600c60b | 286400 |
| log.cpp | b5dad1a8b5c6ee3b8d7af2b226ff6dd09ed80166 | 6616 |
| jni_utils.cpp | 51a1ebfbf69ec871300a281a009f805a925d8f47 | 54856 |
| property.cpp | f39455b1152d0854a0d72c9aa95c8d4d7d36e0d6 | 19456 |
| event.cpp | 9cf6e2ee4ebb835dad5547d2fc62af118b66d68c | 17776 |
| thumbnail.cpp | ac5af164a68ed7d36b39e9732fd850beac5579ca | not compiled |

Exact first diagnostic: `thumbnail.cpp:9:14: fatal error:
'libswscale/swscale.h' file not found` (missing header, not established
source incompatibility). The selected
FFmpeg sparse input was insufficient for this ninth unit. swscale.h
blob c913e76985b7fcf656f266498905cfcd689b8454 includes public libavutil
headers whose closure also needs the real generated libavutil/avconfig.h
from the matching configured build. Do not synthesize it or import an
unrelated SDK header. Reproduce using compile_official_wrapper.py with
the exact historical checkout/SDK command. The final aggregate 24 JNI
export/import assertion was not reached; no libplayer.so link, full
16KiB SO gate, symbol resolution, or native runtime pass. The eight
successful objects are evidence at object level only. The downstream
Java compile was skipped in this job, not failed Java source.

## Request ID attribution and executable runtime candidate

MpvNativeRequestGate.java and NativeRequestGateHostTest.java implement
positive monotonic 64-bit IDs in one class loader across gate/context
recreation, reservation against a current owner, atomic removal on reply
delivery, rechecking owner at publication, rejection of duplicate,
retired, forgotten or unrelated request IDs. Overflow is rejected instead
of reuse. Final local JDK 21.0.12.1 javac --release 8 and five repeated
test executions passed with blobs e8de37af937f0247e686a8b147166abb89c6a2cb
and 96fe16ca3a33e0c6234712ca3d6044e113283b02 respectively, owner
fbdd87af5d0e82b64742729a8ffc2341aefaac02. The earlier gate in CI
45755692922 passed before cross-context hardening. Host test uses
synthetic replies, not a fabricated native player or real native
request delivery. Run from repo root with a clean temp directory:

```sh
base=scripts/upstream-adaptation/mpv-stream
out=$(mktemp -d)
javac --release 8 -d "$out" "$base/MpvStreamOwner.java" \
  "$base/android/native/MpvNativeRequestGate.java" \
  "$base/android/native/NativeRequestGateHostTest.java"
java -cp "$out" NativeRequestGateHostTest
```

NativeMpvStreamAndroidTest.java (blob 7764a830f45a574ca2d066be2c1539a06be4f85b)
defines three actual library-dependent runtime tests, not host substitutes:
stream-dump byte-for-byte synthetic loopback WAV/EOF/close; native forward
and backward seek, HTTP range and old tagged reply held until owner
replacement then dropped (actual native reply when executed, no assertion
of native late-arrival timing); native stop cancelling a delayed HTTP body
and closing the real stream, with balanced per-Call OkHttp connection
acquire/release. Only explicit request IDs can publish. FILE_LOADED is
a single-file setup latch and SHUTDOWN a context lifetime latch; global
END_FILE is diagnostic, and none of these are owner-tagged. Tests require
real System.loadLibrary of all four native libraries; no fallback mock.

After lawful, pinned x86_64 rebuild, run stage_android_probe.py first,
then stage_native_probe.py producer media sdk. The latter checks pinned
producer source revision, exactly libffmpeg.so/libmpv.so/libplayer.so/
libc++_shared.so, ELF64 x86_64 ET_DYN, every PT_LOAD 16KiB alignment and
offset/address congruence, NEEDED names against set and actual NDK
API24 sysroot, relevant libmpv/FFmpeg symbol imports and exact 24 JNI
export names, rejects RPATH/RUNPATH/TEXTREL. It prints sizes/hashes
and stages only in a disposable probe; it cannot prove dependency
source/license provenance by ELF inspection alone. Verified build
receipts and legal inputs remain preconditions. It has not run with a
real four-SO set. Do not weaken it or any product gates. Only then
build the isolated debug/test APKs and run
`org.fingmi.mpvprobe.NativeMpvStreamAndroidTest` on an ABI-matched
authorized Android device. The proven API34 x86_64 official TCG runner
recipe is in ../README.md; no new emulator run was made here.

The independent Libass 3-method host native renderer now has actual
terminal success: [Libass probe](../../../libass-library-probe/README.md).
Motion/FFmpeg and ISO consumer remain unimplemented; no new search or
empty contract methods were added.

## New native instrumentation source compilation (terminal)

[Run 45755965950 / job 139694526161](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45755965950/job/139694526161)
completed **success** at 148b56d29d4c1abc7088d873a12f46e6539c17fe.
The [exact narrow workflow](https://github.com/rileyaaa/FingMi-Xray/blob/148b56d29d4c1abc7088d873a12f46e6539c17fe/.github/workflows/94-native-consumer-probes-once.yml)
compiled the new instrumentation source against fixed real Media3
3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d, official Java bridge and
OkHttp adapter. Final gate/test blobs e8de37af937f0247e686a8b147166abb89c6a2cb
and 7764a830f45a574ca2d066be2c1539a06be4f85b confirmed in raw log.
The disposable module had no jniLibs. Actual Gradle task
:mpv-stream-probe:compileDebugAndroidTestJavaWithJavac completed,
BUILD SUCCESSFUL in 2m 32s, PASS_NEW_NATIVE_PROBE_JAVA_COMPILE_ONLY.
No emulator, original five-test rerun, Libass rerun, eight-object rerun,
SO linking, APK assembly or native runtime. Native instrumentation 0/3
executed, all pending. Both historical runs and raw logs retained;
remove only the temporary push trigger at the end of this batch.
