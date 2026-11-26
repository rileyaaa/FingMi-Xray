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

## Reduced FFmpeg diagnostic (terminal 2026-11-26)

[45757353929 / 139698993565](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45757353929/job/139698993565)
success at 9a12f408a1eb84b11198901119adb8f9f448edea. Reproduce with the
[one-time recipe](https://github.com/rileyaaa/FingMi-Xray/blob/9a12f408a1eb84b11198901119adb8f9f448edea/.github/workflows/95-reduced-native-track-once.yml)
and reduced_ffmpeg_diagnostic.py (blob ae07efaff18b5f2b9ef07efc94f48e43a0124ef9).
Only a reduced LGPL diagnostic, not the exact producer: fixed FFmpeg
963c8cbbebb0250f747f0019516bda55bc638da9, NDK 30.0.16248370,
x86_64 API24. Sparse working tree excludes dependency/ and filenames
containing avs3/arcdav3a/av3a; verifies absence before configure, disables
autodetection, GPL/nonfree/version3 and network, explicitly enables
WAV/PCM_s16le/file/JNI. No unverified codec built, no product Gradle.
Configure reports LGPL version 2.1 or later. LGPL COPYING SHA256
246041b6ecf9bc32d718a62c57877c78b5eb397b6467e74ed7ae2626ab189c30.
Actual generated avconfig.h SHA256
6d78a911a2128e926262114c9904209209674e3bc1a18c208c850ecbfc3393ec.
The original thumbnail.cpp blob ac5af164a68ed7d36b39e9732fd850beac5579ca
compiles to an ELF64 x86_64 ET_REL, 17280 bytes, SHA256
05a91139a6f8e141e0df866003be914af7cec76ff18044b436ab79835664878c,
with Java_is_xyz_mpv_MPVLib_grabThumbnail and sws_getContext/sws_scale/
sws_freeContext imports, all resolved by diagnostic swscale exports.
This is the ninth source unit under a different diagnostic configuration;
not a common 9/9 exact-producer link. The eight previous objects were not rerun.

| Actual split SO | Bytes | SHA256 |
| --- | ---: | --- |
| libavutil.so | 2649008 | 125ca36f6015a8a12d7822b339fc866633d3da8ff06f8743aea285f0d7d693fc |
| libavcodec.so | 1550112 | 5d097478396626767241685374a56433a96d94cec384e9336d1c48c7f6df925f |
| libavformat.so | 1467832 | 682187c8e10fa4a079249b26fd8a35ab80f87cbd5637392436515194a53429b8 |
| libswscale.so | 4709400 | 8140ab68a1331a34aeba814de59d9806fe19032f0ec46ca034597b756f272417 |

All four are ELF64 ET_DYN x86_64, PT_LOAD alignment and address/offset
congruence >=16KiB, NEEDED closure against the split set and actual NDK
sysroot, no RPATH/RUNPATH/TEXTREL, real av_jni_set_java_vm exported.
Raw markers PASS_NINTH_WRAPPER_OBJECT_REDUCED_HEADER and
PASS_REDUCED_SPLIT_FFMPEG_DIAGNOSTIC. No libmpv/libplayer or emulator runtime.

### Remaining diagnostic dependency closure (source inspection, not build)

Fixed FongMi/mpv@f964d1495355d5c6626df3de1d3eeb90ddee2aba
meson.build d0baed522c25485521b70cb88a44a9589ae4d8a5:23-44 requires
avcodec,avfilter,avformat,avutil,swresample,swscale,libplacebo>=7.387.0,
libass>=0.12.2; current split set lacks avfilter/swresample/libplacebo/
libass. Exact producer mpv.sh d641ebb6526c471c3301793271e6667a5c3bbd and
libplacebo.sh aefb98393edd3e2d94bfe9b2f66d0ef0b8c911af require additional
features and dependencies; no full authorized exact producer yet.
For a possible headless diagnostic only, pinned FongMi/libplacebo@
dc98e2fceb82233b3bb75e9c6249e581c57f3f2d LICENSE blob
20fb9c7da21cb5a29e10f614a03661a935181652 is LGPL2.1; src/meson.build
01356e269307a6054f91ec9c4e68ce9226bf376c:176-187 allows no graphics
backend with a warning. meson_options.txt 95a96c73fe90c29359df8cf3e6eb4d55acf9c5af
permits disabling Vulkan/OpenGL/D3D11/shaderc/glslang. This is not
evidence that the resulting core links or renders. Its pinned
submodules (Vulkan-Headers 74d8a6cb930c68ef617b202c3ff3c59d919e086b,
fast_float 97b54ca9e75f5303507699d27c6b4f4efe4641a1,
glad 73db193f853e2ee079bf3ca8a64aa2eaf6459043,
jinja 15206881c006c79667fe5154fe80c01c65410679,
markupsafe 297fc8e356e6836a62087949245d09a28e9f1b13)
need further used-source/license/build closure.
libass configure.ac 27676b3e953c8ba5d18622b99df27b496ff9c66c
requires FreeType/FriBidi/HarfBuzz; fontconfig and unibreak can be
disabled in a strictly embedded-font diagnostic. Resolved author recipe
versions to fixed source commits and inspected license blobs:
FreeType 2.15.0 freetype/freetype@37515cf56ba3349656049edbed89ffc6f6466f2d
(FTL b9e8cbd66ffff526113350953f4a2f4252a92f49, GPLv2 b2fe7b6af3535ebc1e018dd2fe6c993330c031fa);
FriBidi 1.0.17 fribidi/fribidi@b93119f5fdc7ea47672cc304c1455ffa6dfe7536
(COPYING f6683e74e0f0130f246dbf7054f4cacc88ca84b0);
HarfBuzz 15.0.0 harfbuzz/harfbuzz@35f656a1a2bab548ea7f54a6dd3fba2b09680d14
(COPYING 1dd917e9f2e72167de69e3b5dadbc4e7db417da1).
These are candidate source/license pins, not verified Android rebuilds.
Exact producer gate and ARM ELF/ZIP gates remain unchanged.

## Actual reduced headless Android runtime (terminal 2026-11-26)

[45758162089 / 139701600685](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45758162089/job/139701600685) completed success at 6e37175d26f500df6fd2a31e816c491c3c36bd3b. [Exact recipe](https://github.com/rileyaaa/FingMi-Xray/blob/6e37175d26f500df6fd2a31e816c491c3c36bd3b/.github/workflows/96-headless-native-once.yml); headless_native_diagnostic.py blob c50b2392d73f0dee21ebacb6c844b19f6f42eca5. Actual pinned-source build, six split FFmpeg libraries, static font and placebo dependencies, unchanged nine official wrapper units linked. LGPL FFmpeg configuration; no excluded codec compiled. Nine SOs ELF64 x86_64 ET_DYN, actual SONAME, NEEDED closure, 16KiB PT_LOAD and 24 exact Java JNI exports passed. APK ZIP alignment and uncompressed native byte equality passed. Original SO receipts (name, bytes, SHA256, NEEDED):

```text
libavcodec.so 417520 2b5161075016d99b9628aee9cc438b27e036f88ec5e8dd050184e41bdd9f2718 ['libavutil.so', 'libc.so']
libavfilter.so 169520 9ad1bbe0beeaf7f470b2ccb561eadfb69c48d380ed5e32d02ded2f1c69b27219 ['libavutil.so', 'libc.so', 'libswresample.so']
libavformat.so 302928 6714def2ecb092dbe6dc3bd2713f2058efc51870cbc490abd83806458a5880f7 ['libavcodec.so', 'libavutil.so', 'libc.so']
libavutil.so 735368 dbbabce0432b8a1ad5c08e663eb35d02bbb9d04c80e8ddad31c37f43d25f6979 ['libc.so', 'libm.so']
libc++_shared.so 9091400 7918ebd0b8074c312d0c610205d49760b98c008026e6b817cd92103a3e12241b ['libc.so', 'libdl.so', 'libm.so']
libmpv.so 9221008 c2320398808ad3cd40989f499a662d154d0bd4e982517d07c5cfd0c6bd2410c5 ['libEGL.so', 'libGLESv2.so', 'libandroid.so', 'libavcodec.so', 'libavfilter.so', 'libavformat.so', 'libavutil.so', 'libc++_shared.so', 'libc.so', 'libm.so', 'libswresample.so', 'libswscale.so']
libplayer.so 256368 95a01c9d80ad49ab6f300428d941c589cd641b5a4618ac8d5bafee3984eacf60 ['libavcodec.so', 'libc++_shared.so', 'libc.so', 'libdl.so', 'liblog.so', 'libm.so', 'libmpv.so', 'libswscale.so']
libswresample.so 116744 8a67aa68e59eed7e39975064cd2e8a9284358b1240f3165b571329b8e9d7429b ['libavutil.so', 'libc.so', 'libm.so']
libswscale.so 1345352 ecd4fa7f5b3ad4267676bdbf1769836c8842a9fb27ec8cf82673badb64428394 ['libavutil.so', 'libc.so', 'libm.so']
```

Original isolated APK receipts:
```text
2026-11-26T05:06:41.3609646Z 72af292636a80aa57186c3fc49de154b6cd3a798b88d4a32c236edf39f7e50a2  /home/runner/work/_temp/mpv-build/mpv-stream-probe/outputs/apk/debug/mpv-stream-probe-debug.apk
2026-11-26T05:06:41.3612194Z bacf1e4abb804297f0b45f5e7ba4972c81503084df1286a698d7b6fa67cd00d0  /home/runner/work/_temp/mpv-build/mpv-stream-probe/outputs/apk/androidTest/debug/mpv-stream-probe-debug-androidTest.apk
```

Official Android API34 x86_64 emulator, TCG (no permission changes), boot 304s. Actual mpv v0.42.0-dev-gf964d1495, instrumentation OK (3 tests), code -1. Dump fixture 32044 bytes, 6 reads, 2 EOF, 1 open/close; seek old owner 73728 bytes, 9 reads, 3 seeks, 12 size calls, 1 cancel/close; new owner 1 read, 1 seek, 1 cancel/close. Stop blocked body 1 read, 0 bytes, 1 cancel/close. Actual tagged replies 1099511627777..1099511627785, old 1099511627780 and new 1099511627784; old reply deliberately held before Java owner delivery, not claimed late native arrival. Six real OkHttp Calls and six connection releases (1+1+4); cleanup log repeats not double counted. All three PASS_NATIVE_* tests and PASS_REDUCED_HEADLESS_ANDROID_NATIVE_STREAM_ONLY present. Prior 5/5 NO_NATIVE tests not rerun. This proves reduced-profile runtime only, not exact producer, ARM runtime, complete Media3 consumers, video/ISO/disc support, or TV APK. No artifact upload; delete only temporary 96 trigger and retain history.

See [exact producer feature/license delta and remaining artifacts](PRODUCER_DELTA.md). This does not grant release approval.

## Independent reduced ARM build feasibility (terminal 2026-11-26)

[45760464596](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45760464596), source d0f7e9ea4fdb24bb0f1594ce56c971bd219b1f33, [exact recipe](https://github.com/rileyaaa/FingMi-Xray/blob/d0f7e9ea4fdb24bb0f1594ce56c971bd219b1f33/.github/workflows/97-arm-native-once.yml), headless_native_diagnostic.py blob edcc51d3b6b1be662361964c1dce61645c95fb4c. Separate matrix runners, same fixed inputs and license receipts, NDK30 API24 for both, no x86 replay. Builds six split FFmpeg SOs, static font/placebo, exact nine original JNI units and MPV. ARM64 ET_DYN ELF64 machine=183, ARMv7 ET_DYN ELF32 machine=40; actual per-SO SONAME and NEEDED against real same-ABI API24 NDK sysroot, no RPATH/RUNPATH/TEXTREL, actual imported MPV/FFmpeg symbol closure, 24 Java native exports. Temporary uncompressed diagnostic ZIP aligned with official build-tools36 zipalign -P 16 and checked by zipalign -c, independent raw local-header data-offset check and original SHA256 equality for all entries. No Android APK or runtime, no uploads; no production staging.

- [ARMv7 139708965183](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45760464596/job/139708965183): all nine SOs built/identified and 24 JNI symbols; eight SOs PT_LOAD 0x4000; unchanged original NDK libc++_shared.so all three LOAD alignments 0x1000. ZIP 9/9 and bytes pass, independent of ELF gate. Explicit BLOCK_ARM_ELF_16K and job failure, no APK staged. This is a project acceptance failure, not Android platform incompatibility. No ELF edit or alignment relaxation. Recovery requires a traceable compatible, legitimately built ARMv7 shared C++ runtime with 16KiB PT_LOAD, matching NDK C++ ABI and actual device regression (or a separately approved project requirement change, NOT in this dev scope); do not rerun same NDK bytes, change e.g. shared-to-static STL or rename another ABI as a shortcut.
- [ARM64 139708965493](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45760464596/job/139708965493): success, all nine SOs PT_LOAD 0x4000, actual SONAME/NEEDED/24 JNI, ZIP data offsets and bytes 9/9. PASS_ARM_BUILD_ELF_ZIP_ONLY arm64-v8a NO_DEVICE_NO_PRODUCT. No actual ARM device available, no runtime claim. x86 3/3 remains separate.

### ARMv7 raw receipts
```text
PASS_HEADLESS_BUILD ffmpeg-six 975611ad5eba15212d9e1d5fca9d4fdf0daec6d2269b2fcab8e29af8667164bc
ARM_PT_LOAD armeabi-v7a libavcodec.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavcodec.so 310120 a73ab58ebabc1294ddb10fc00e516eac17a04bb45f6b11a8686155e348db1eb1 ['libavutil.so', 'libc.so', 'libm.so']
ARM_PT_LOAD armeabi-v7a libavfilter.so alignments 0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavfilter.so 135156 814fc754a1528bda1b04162506f723e64e55d446ea0381929d2149eed0a5a317 ['libavutil.so', 'libc.so', 'libswresample.so']
ARM_PT_LOAD armeabi-v7a libavformat.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavformat.so 270496 384e6ab298ce2e9feb0495e46f98bdd2107dd25ca8b15f7efe0b70ad3820210e ['libavcodec.so', 'libavutil.so', 'libc.so', 'libm.so']
ARM_PT_LOAD armeabi-v7a libavutil.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavutil.so 647152 e8592e935cd0ddb34e311df44bb1dcd8aae1fd4d8fec6077675447b8f10979c1 ['libc.so', 'libm.so']
ARM_PT_LOAD armeabi-v7a libc++_shared.so alignments 0x1000,0x1000,0x1000 16KiB FAIL
HEADLESS_ELF libc++_shared.so 7567040 2ee592c9ba3372da027384deb1070def5ae76f3ea2246bd447360faa73ac22f4 ['libc.so', 'libdl.so', 'libm.so']
ARM_PT_LOAD armeabi-v7a libmpv.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libmpv.so 7761312 77f86bd32709e14d33d3d72e7aa50f148471a7ab9d58766a6eea15415a9d31eb ['libEGL.so', 'libGLESv2.so', 'libandroid.so', 'libavcodec.so', 'libavfilter.so', 'libavformat.so', 'libavutil.so', 'libc++_shared.so', 'libc.so', 'libm.so', 'libswresample.so', 'libswscale.so']
ARM_PT_LOAD armeabi-v7a libplayer.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libplayer.so 217292 49a8b5e10b1b7a0081d825ed1542c826a5d33e39f114372103d87a8c2077d5b2 ['libavcodec.so', 'libc++_shared.so', 'libc.so', 'libdl.so', 'liblog.so', 'libm.so', 'libmpv.so', 'libswscale.so']
ARM_PT_LOAD armeabi-v7a libswresample.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libswresample.so 94040 4220922fa522569e32c88a194f65232fbcf3c7f0ccbb62e633e1672465963394 ['libavutil.so', 'libc.so', 'libm.so']
ARM_PT_LOAD armeabi-v7a libswscale.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libswscale.so 995832 8879fd6aab9cb346eff8f48c721aa313faaa99fb61ebf694eae156c1c2763785 ['libavutil.so', 'libc.so', 'libm.so']
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libavcodec.so 16384 a73ab58ebabc1294ddb10fc00e516eac17a04bb45f6b11a8686155e348db1eb1
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libavfilter.so 327680 814fc754a1528bda1b04162506f723e64e55d446ea0381929d2149eed0a5a317
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libavformat.so 475136 384e6ab298ce2e9feb0495e46f98bdd2107dd25ca8b15f7efe0b70ad3820210e
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libavutil.so 753664 e8592e935cd0ddb34e311df44bb1dcd8aae1fd4d8fec6077675447b8f10979c1
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libc++_shared.so 1409024 2ee592c9ba3372da027384deb1070def5ae76f3ea2246bd447360faa73ac22f4
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libmpv.so 8978432 77f86bd32709e14d33d3d72e7aa50f148471a7ab9d58766a6eea15415a9d31eb
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libplayer.so 16744448 49a8b5e10b1b7a0081d825ed1542c826a5d33e39f114372103d87a8c2077d5b2
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libswresample.so 16973824 4220922fa522569e32c88a194f65232fbcf3c7f0ccbb62e633e1672465963394
ARM_ZIP_ENTRY armeabi-v7a lib/armeabi-v7a/libswscale.so 17072128 8879fd6aab9cb346eff8f48c721aa313faaa99fb61ebf694eae156c1c2763785
PASS_ARM_DIAGNOSTIC_ZIP_16K armeabi-v7a d56ba05b4f6a481344c3646242d806e3a0aeba7b0916bc366e0ab76b07e82915
ARM_BUILD_AND_SYMBOLS armeabi-v7a 9 SO 24 JNI
BLOCK_ARM_ELF_16K armeabi-v7a libc++_shared.so
```

### ARM64 raw receipts
```text
PASS_HEADLESS_BUILD ffmpeg-six 6d78a911a2128e926262114c9904209209674e3bc1a18c208c850ecbfc3393ec
ARM_PT_LOAD arm64-v8a libavcodec.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavcodec.so 391440 08beaafc9b465f33e176003369b834446b57a8ae6253636a84e82922086d49eb ['libavutil.so', 'libc.so']
ARM_PT_LOAD arm64-v8a libavfilter.so alignments 0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavfilter.so 157752 e84e06e7c024e46e7450ae94aec873d0404e1467bf22ebd70671b6420de2dbbb ['libavutil.so', 'libc.so', 'libswresample.so']
ARM_PT_LOAD arm64-v8a libavformat.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavformat.so 288096 d22bba1147e651f106faa0503ec4f8a27caf2ac1378fd70b29f3deb6941d2bc5 ['libavcodec.so', 'libavutil.so', 'libc.so']
ARM_PT_LOAD arm64-v8a libavutil.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libavutil.so 678152 3b113568990852176814926286d726a7b849fea417c580c8c6c9ce4bbce9958a ['libc.so', 'libm.so']
ARM_PT_LOAD arm64-v8a libc++_shared.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libc++_shared.so 9485032 7466ed097631a564ed6bff0b47768caa76bf03270d2047b5a65c03f497b824df ['libc.so', 'libdl.so', 'libm.so']
ARM_PT_LOAD arm64-v8a libmpv.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libmpv.so 9138472 2c2da5bdcb01799def15ae5c0eac9d5b72012c905fc8a9ce554f022baab2fa18 ['libEGL.so', 'libGLESv2.so', 'libandroid.so', 'libavcodec.so', 'libavfilter.so', 'libavformat.so', 'libavutil.so', 'libc++_shared.so', 'libc.so', 'libm.so', 'libswresample.so', 'libswscale.so']
ARM_PT_LOAD arm64-v8a libplayer.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libplayer.so 294208 cfe03c0e363931a8fa75d7e13069c169471183c36b512bd09565b93f2f30bb35 ['libavcodec.so', 'libc++_shared.so', 'libc.so', 'libdl.so', 'liblog.so', 'libm.so', 'libmpv.so', 'libswscale.so']
ARM_PT_LOAD arm64-v8a libswresample.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libswresample.so 96776 abc3d2224760f2d8f103a61f56dd87f19ddf073173036d80134b2367b54f15fd ['libavutil.so', 'libc.so', 'libm.so']
ARM_PT_LOAD arm64-v8a libswscale.so alignments 0x4000,0x4000,0x4000 16KiB PASS
HEADLESS_ELF libswscale.so 1134248 3160836b0e174c8efbffbbf2d5a3da5b5db84b2d4d16334cd644748c86b09a04 ['libavutil.so', 'libc.so', 'libm.so']
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libavcodec.so 16384 08beaafc9b465f33e176003369b834446b57a8ae6253636a84e82922086d49eb
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libavfilter.so 409600 e84e06e7c024e46e7450ae94aec873d0404e1467bf22ebd70671b6420de2dbbb
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libavformat.so 573440 d22bba1147e651f106faa0503ec4f8a27caf2ac1378fd70b29f3deb6941d2bc5
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libavutil.so 868352 3b113568990852176814926286d726a7b849fea417c580c8c6c9ce4bbce9958a
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libc++_shared.so 1556480 7466ed097631a564ed6bff0b47768caa76bf03270d2047b5a65c03f497b824df
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libmpv.so 11042816 2c2da5bdcb01799def15ae5c0eac9d5b72012c905fc8a9ce554f022baab2fa18
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libplayer.so 20185088 cfe03c0e363931a8fa75d7e13069c169471183c36b512bd09565b93f2f30bb35
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libswresample.so 20480000 abc3d2224760f2d8f103a61f56dd87f19ddf073173036d80134b2367b54f15fd
ARM_ZIP_ENTRY arm64-v8a lib/arm64-v8a/libswscale.so 20578304 3160836b0e174c8efbffbbf2d5a3da5b5db84b2d4d16334cd644748c86b09a04
PASS_ARM_DIAGNOSTIC_ZIP_16K arm64-v8a a798ddcbdebfa3212cb5d9ab00407c5ccff024f460047c91a471c2c60085a9b9
ARM_BUILD_AND_SYMBOLS arm64-v8a 9 SO 24 JNI
PASS_ARM_BUILD_ELF_ZIP_ONLY arm64-v8a NO_DEVICE_NO_PRODUCT
```

Keep exact producer and full product gates in place. See [feature and source/license delta](PRODUCER_DELTA.md); no unchanged CI rerun.

See [ARMv7 runtime support boundary](ARMV7_RUNTIME_BOUNDARY.md): no matching supported alternative established; stop unchanged rebuilds, continue consumer work.

[5.9.0 public consumer stop point](CONSUMER_STOP_POINT.md): final targeted source recheck and independent recovery gates; no repeat ARM/native probe.
