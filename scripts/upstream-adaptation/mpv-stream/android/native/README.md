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
