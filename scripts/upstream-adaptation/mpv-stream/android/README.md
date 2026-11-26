# Android Media3 MPV stream probe

Only for the isolated development branch. Never stage this module into TV,
prepare_candidate, product Gradle, release or signing. No real account,
server, proxy, node, or media is used.

## Reproduction and limits

Use disposable source checkouts of FongMi/media at
3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d and FongMi/mpv-android at
1bf892e3271e73d8649f2d209027f1fb17515d15, JDK 21, official Android SDK
platform 36/build-tools 36.0.0, and the upstream Gradle wrapper 9.1.0 /
AGP 9.0.1. Stage the isolated app:

    python3 scripts/upstream-adaptation/mpv-stream/android/stage_android_probe.py /tmp/media /tmp/mpv
    cd /tmp/media
    bash gradlew --no-daemon --max-workers=2 -PexternalBuildDir=/tmp/mpv-probe-build :mpv-stream-probe:assembleDebug :mpv-stream-probe:assembleDebugAndroidTest
    bash gradlew -PexternalBuildDir=/tmp/mpv-probe-build :mpv-stream-probe:dependencyInsight --configuration debugAndroidTestRuntimeClasspath --dependency com.squareup.okhttp3:okhttp

The real Media3 project supplies DataSpec, OkHttpDataSource, and dependencies;
OkHttp and MockWebServer are strictly 4.12.0. The isolated test uses the
generated Java MPVLib bridge (fixed source/license), not the previous
host-JNI probe or a substitute native implementation. A real API 34 x86_64
emulator runs both debug APKs and the AndroidJUnitRunner class
org.fingmi.mpvprobe.Media3MpvInputAndroidTest. The exact staging/SDK/
instrumentation commands are retained in workflow history:
[7648c8b5 workflow](https://github.com/rileyaaa/FingMi-Xray/blob/7648c8b5f0ef1ee4558bf54da71947dbfbb93cb7/.github/workflows/93-mpv-stream-android-once.yml).

Instrumentation covers WAV byte comparisons, 206/416 and 200 range fallback,
forward/backward/end seek, identity encoding, basic challenge,
same-origin Authorization preservation and cross-origin Authorization
removal (port changes), synthetic custom header retention, cancellation
during header/body wait and before the Call is published, unrelated Call
survival, old URI retirement, truncated/malformed ranges, real OkHttp
terminal events, connection release, and dispatcher/pool state.
Authorization behavior is for the isolated OkHttp client, not proof that
arbitrary custom credential headers, cookies, TLS, TV Auth.Context,
disc/cache/ISO sources, or upstream host integration are safe or complete.
The tests do not assign untagged MPV callbacks to a session. No native
request ID, no native execution, no native attribution claim.

## Run evidence

- [45750113813](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45750113813),
  3f3856ef: workflow syntax failure before a job was created (unquoted
  colon in a plain YAML if scalar); no build or runtime result.
- [45750156365](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45750156365),
  7648c8b5: corrected folded scalar; job 139675715611. As of this record
  source checkouts, SDK install and stage step completed successfully;
  compile step in progress. Do not infer further results from this record.

## Native/remaining dependency route, not a replacement build

Official producer [44885769496](https://github.com/FongMi/mpv-android/actions/runs/44885769496),
job 136790596601 at 1bf892e3271e73d8649f2d209027f1fb17515d15, used
MPV_ANDROID_ARCHES=armv7l arm64, with resolved inputs from original log:

| Input | Commit |
| --- | --- |
| FongMi/mpv | f964d1495355d5c6626df3de1d3eeb90ddee2aba |
| FongMi/FFmpeg | 963c8cbbebb0250f747f0019516bda55bc638da9 |
| FongMi/libplacebo (producer input) | dc98e2fceb82233b3bb75e9c6249e581c57f3f2d |
| dav1d | 2a0775ca5ea055450bdfbfe81758a3c9e001f58a |
| libass | a6613d2554daff9e1b5ddf2dbfb3fc31b61b9448 |

The run metadata still reports nonexpired native artifact 14699804350
SHA256 f07422157e0f18409084e1bf50352f142d56fca2a7cf71802b6e95621cb9d4f4.
It is the previously checked two ARM ABIs, not x86_64. The official
Application.mk (0c26848ddd938352781fdf32e4e7301be356edf5) has a PREFIX_X64
case; ci.sh (b22f34750afdc8db9997b94e1b5c9e128e22c0cd) accepts
MPV_ANDROID_ARCHES, while the actual workflow build.yml
(f9ecb50ecd40cedeff77a689aa604cbc0549ca48) fixes ARM only.
NDK r30/30.0.16248370 from depinfo.sh 2b9b3e40ccbcc8934f751d596959414306db67c2.
No matching x86_64 native artifact is established. The shortest next
native probe requires an ABI-matched Android device or a real, pinned
x86_64 rebuild of that producer and all its dependencies. Do not assume
the mere makefile case proves the full x86_64 build. Verify hashes, ELF
dependencies, JNI registration, actual media3iso callback I/O and
request-ID correlation before attempting a player integration. Existing
ARMv7 project alignment gate and native distribution/license requirements
remain unchanged. No binary downloaded or loaded in this batch.

- **Motion/FFmpeg:** official renderer SDK artifact 14700635872 digest
  d05798ac705e10172fd517b0d0ee718c9bb3e2a0073cd5f0d1baf807dbf8e010,
  export-renderer-sdk.sh ad7d2cfc37b4931644d28fcd6303a458d0731340
  records motion.c/header/license, archive and libplacebo provenance;
  fixed mpv motion.h 496976cec08a30dd64aaaac89b69441d1b000dd7
  is LGPL-2.1-or-later and declares create/reset/capture/render_views,
  owned-frame and shader paths. Real native core is available. The next
  missing piece is matching Media3 FfmpegMotionRenderersFactory,
  FfmpegMotionInterpolationController and renderer/JNI consumer, with
  Surface/PTS/flush/reset/renderer lifecycle, unified libffmpegJNI
  signatures and link closure; test independent renderer before AAR.
  FFmpeg recipe 90e6de21643a374285a90fdde3a1369b32311451 enables GPL and
  version3. Preserve motion/libplacebo notices and source/build recipe
  obligations, verify AVS-related and other component rights separately;
  public artifact alone is not a distribution license.
- **Libass:** resolved libass commit above, public ass.h
  851ca7cb9614f8d5d3175bbcc2925dfb6521bc27 provides library/renderer/track
  lifetime, process_chunk, fonts, style overrides, frame/storage size,
  margins, pixel aspect and rendering APIs. Author download-deps.sh
  415a027b2097375d8425aea144e8d93a6cbb245f applies libass-font-size-em.patch.
  Use actual source and preserve its license and patch notices; the
  existing old JNI register table does not match the new 18-method
  contract. Obtain matching Java frame/font/timed-data/style/color and
  JNI definitions before porting; validate library/track ownership,
  timed render, positioning, fonts and secondary subtitles, not only
  JNI registration. No assumption that the public libass C API is the
  missing Media3 bridge.
- **Disc:** official libbluray-bdj artifact 14699869160 digest
  3730c648dcf2e6bfa69e59dda68e33414b9201d1485337f685f8571d713888cd.
  libbluray 1.4.1 recipe b9e01a5ddc0595b402c1d9151ced6f996ba54f56 uses
  external udfread, freetype, and aarch64 JRE path correction; BD-J
  recipe 232f7e49daac3c08f7c28853793e6f2bdb55f78b checks source version,
  JDK8/Ant, and uses fallback tarball SHA256
  76b5dc40097f28dca4ebb009c98ed51321b2927453f75cc72cf74acd09b9f449.
  patch-libbluray.sh 5004cc07ef6d63768f17700db63e5d553ff8504d applies
  four fixed still-EOF/checked-seek/menu-info/BD-J pointer patches.
  For reproducibility verify the archive even when supplied by
  download-deps.sh (its native download pipeline does not check that
  digest), pin udfread and all dependencies, retain LGPL and applicable
  third-party source/notice obligations. Matching Media3 isoJNI
  NativeUdfFileSystem/IsoNavigationSession and BD-J integration remain
  independent missing consumer contracts. Validate local authored
  disc fixture, UDF traversal/read/seek and navigation lifecycle, not
  the previously tested bdj-runtime facade or just a libbluray jar.

No additional FFmpeg/Libass/ISO product code, binary, or dependency
introduced; source provenance and contract gaps above are scoped to
existing 5.9 functions.
