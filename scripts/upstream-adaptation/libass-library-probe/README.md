# Libass 3-method JNI consumer probe (isolated host only)

This is a real implementation of three reference JNI methods, not a stub for
the other 15 and not an Android Media3 AAR. It is not wired into the product,
prepare_candidate, the existing Libass Java controller, or the TV build.

## Fixed source and license boundary

- libass/libass@a6613d2554daff9e1b5ddf2dbfb3fc31b61b9448,
  `libass/ass.h` Git blob 851ca7cb9614f8d5d3175bbcc2925dfb6521bc27.
  This is the libass commit resolved by the fixed official MPV producer
  1bf892e3271e73d8649f2d209027f1fb17515d15, run 44885769496.
- The author's `buildscripts/patches/libass-font-size-em.patch` was applied
  with zero fuzz, SHA256
  fa6d0d3a00cb7896525a707407daad4d51e807d65d0692d6d33cc565d30ea9fa.
  The libass COPYING SHA256 is
  f7e30699d02798351e7f839e3d3bfeb29ce65e44efa7735c225464c4fd7dfe9c.
  Preserve libass ISC notices, patch provenance and the licenses of the
  actual dependencies. New probe source is Apache-2.0.
- Reference Java declarations: dlgt7/media@3382803f
  LibassNative.java blob a08a6b94b48f2582048dda07ae6ffebf8c801dc2,
  previously reviewed. Only descriptor/consumer reference; no claim of
  an authenticated, complete author's 18-method Java/JNI contract or
  redistribution grant for a third-party AAR.
- The build uses Ubuntu 24.04 development packages (freetype, fontconfig,
  fribidi, harfbuzz, unibreak), nasm, JDK 21 and the packaged DejaVu font
  for a local fixture. These are not the producer's Android libraries;
  host package versions can differ. No Android shared library or font
  binary is vendored or published.

## Implementation and actual terminal evidence (2026-11-26)

[Run 45755692922 / job 139693660621](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45755692922/job/139693660621)
completed **success**, source commit eda49ed557a9de477fa796beebdfad79b8cecd5b.
The [exact build/test recipe](https://github.com/rileyaaa/FingMi-Xray/blob/eda49ed557a9de477fa796beebdfad79b8cecd5b/.github/workflows/94-native-consumer-probes-once.yml)
remains in history after temporary trigger cleanup.

`PASS_PINNED_LIBASS_HOST_BUILD`: actual autoreconf/configure/make/install,
libass 0.17.5 (API 0x1705000), patched source reports known -dirty state.
`ldd` resolves libass.so.9 from the isolated ass-prefix, not the runner's
system copy. Probe SO SHA256
027a7b9314a777b4d7fbbeed1f02b82312acc0fb1e30b05784cc9da2e6bc1294.
Tested Git blobs: C++ bb7d948630fb3de7fcf63280bfc8dc9a499598e9,
LibassNative.java a1f6575a2e843541fbc17d146eb5424038cadbaa,
LibassLibraryProbe.java c80abc3649696b6839161bfcdb61223c046d9219.

| Reference method | JNI descriptor |
| --- | --- |
| nativeCreateLibrary | (Ljava/lang/String;)J |
| nativeReleaseLibrary | (J)V |
| nativeAddFont | (JLjava/lang/String;[B)V |

The new C++ uses real ass_library_init/ass_add_font/ass_library_done with
opaque handles, shared ownership and a per-library mutex. Fixture JNI names
are deliberately separate from the missing production track/frame methods.
Two real ASS_Renderer/ASS_Track instances parse timed ASS packets and
render actual ASS_Image coverage bytes, checking distinct nonempty bitmap
hashes and absence outside both time windows. Embedded font rendering
continues after overwriting the Java source byte array; the fixture sets
ASS_FONTPROVIDER_NONE. Retiring the library handle twice rejects stale
font additions while both tracks still render. Closing one track twice
preserves the other and rejects the retired track handle; closing the last
track destroys the library. JDK ran with -Xcheck:jni.

```text
PASS_LIBASS_3_JNI_REAL_RENDER shared_library=1 tracks=2 distinct_bitmaps=2 time_windows=2 live_libraries=0
PASS_LIBASS_HOST_JNI_ONLY
```

Scope: three method descriptors with real host JNI and timed render/lifetime
evidence. The fixture is not a concurrency stress test or validation of
Android font configuration, frame/color/position conversion, seek/reset,
the remaining 15 declarations, subtitle controller integration, or a device
playback test. Preserve those gates; do not fill them with empty implementations.

## Extended track subset (terminal 2026-11-26)

[45757353929 / 139698993930](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45757353929/job/139698993930)
success at 9a12f408a1eb84b11198901119adb8f9f448edea; exact historical recipe
[95-reduced-native-track-once.yml](https://github.com/rileyaaa/FingMi-Xray/blob/9a12f408a1eb84b11198901119adb8f9f448edea/.github/workflows/95-reduced-native-track-once.yml).
Actual same pinned libass 0.17.5 source build and verified font-size-em
patch/COPYING hashes; ldd resolves isolated prefix. JNI SO SHA256
5ad47d57b8a4de0f6a5da44e976568d23c9b5282fb6bf3925752e527bfddedfe.
C++ blob 858a2786041f38bb21c202dd5e93f92657e15e39,
LibassNative.java 714875c2fca136dc04aec529fce1d22ac6f6e471,
LibassTrackProbe.java 6c7c58f76d27d41e7d7cefbdf490018c0fa8b6e1,
LibassLibraryProbe.java 1af5877437d950c8cbbafb8a31f1955406073f2d.
Prior three-method test not rerun; new tests use library/font setup.

| New reference method | JNI descriptor |
| --- | --- |
| nativeCreate | (JLjava/lang/String;Ljava/lang/String;)J |
| nativeRelease | (J)V |
| nativeProcessCodecPrivate | (J[BII)V |
| nativeProcessChunk | (J[BIIJJ)V |

Reference dlgt7/media@3382803f LibassTrackSession.java blob
bfbbdf79cfd83951c5ba7298308678f6ac1bf654:102-108 checks a nonnegative
duration and forwards start/duration; last chunk argument is duration,
despite Java name endTimeMs. Historical official media3ass.c blob
949c5b0db7ca8a5867e52e895920518d82651376 has an MIT permission notice,
not Apache-2.0 as previously recorded. Newly implemented probe code
is Apache-2.0. Embedded-font profile only: nonempty fonts directory
or library font config rejected. Real track lifetime, range validation,
timed chunk ingestion, two independent tracks, exact time-window
boundaries and backward render. Snapshot is test-only, copies real
ASS_Image coverage row by row, with geometry and RRGGBBAA inverted alpha
matching the actual reference LibassGlImage.java blob
f52b1eca9f2daea069b8b851ef68e7094bedc03f channel extraction (not the
misleading ARGB comment in LibassImage). Snapshot DTO constructor
(IIIII[BI)V is test-only; not nativeRenderFrame, GL texture or Android
consumer. Checked copied pixel ownership, stale handles and final
library release with -Xcheck:jni.

```text
PASS_LIBASS_TRACK_SUBSET four_new_descriptors tracks=2 timed_windows=2 copied_pixels=2 stale_handles_rejected live_libraries=0
PASS_NEW_LIBASS_TRACK_HOST_ONLY
```

Cumulative 7/18 scoped host implementations with real evidence; not
seven complete Android methods, nor complete authenticated author
contract. Remaining eleven declarations, font config/style/viewport,
full nativeRenderFrame, GL ownership, Android AAR and subtitle controller
are unverified. No placeholders, product integration or release.

## Full data, storage geometry and cache subset (terminal 2026-11-26)

[45760568036 / 139709302562](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45760568036/job/139709302562) success at 6c0c1a42f791c96732a3488222cacead7c67e3d7, [exact recipe](https://github.com/rileyaaa/FingMi-Xray/blob/6c0c1a42f791c96732a3488222cacead7c67e3d7/.github/workflows/98-libass-data-once.yml). Actual source/author patch and license checks; libass 0.17.5 isolated host link, -Xcheck:jni. SO SHA256 f65a82901290c46598c9518c5ccd70c2943d19c51f9b93a1efa36396981c1b36. Tested blobs C++ a5690fe422fc4a399667b71106edf0a8ac107a80, LibassNative.java 8be968909fe51e196ee317ad8236bb54b2c1c880, LibassTrackProbe.java 18079e5881f88d456251647657d3fbfd4c8e9b99, LibassDataGeometryProbe.java 4d15d96bdb29b02bd7e658bd35ea3c3c0a041e19.

| New reference JNI method | Descriptor | Actual C API |
| --- | --- | --- |
| nativeProcessData | (J[BII)V | ass_process_data |
| nativeSetStorageSize | (JII)V | ass_set_storage_size |
| nativeSetCacheLimits | (JII)V | ass_set_cache_limits |

Historical official media3ass.c blob 949c5b0db7ca8a5867e52e895920518d82651376 lines 192-218,254-261,271-278 and registry 359-374; fixed reference LibassTrackSession blob bfbbdf79cfd83951c5ba7298308678f6ac1bf654 confirms embedded timestamps, positive storage sizes, nonnegative cache limits. Pinned ass.h (851ca7cb9614f8d5d3175bbcc2925dfb6521bc27) explicitly distinguishes full lines and Matroska chunks; do not mix them on one track (duplicate check limitations), separate fixture here. Actual ass_render_api.c ee1620ad1d1e26d232e96de8182fb84a018e1041 sets storage and cache limits, ass_render.c ff51510c95b6807b94541c946580563f1552a9fb cuts cache at frame start. New JNI rejects invalid range/overflow, stale handles, nonpositive dimensions and invalid limits. Actual full ASS embedded timestamps (not processChunk), two distinct image windows; storage 320x180 -> 160x180 changes rendered width 181 -> 209 and restores original pixel digest. Cache limits 1 glyph/1 MB followed by 40 real alternating renders with unchanged correct pixels, defaults 0/0 restore; no measured cache eviction counts or memory bound claim. Last library released. Prior test cases not repeated. Original markers:

```text
PASS_LIBASS_DATA_GEOMETRY_CACHE three_new_descriptors self_timed_windows=2 storage_widths=181,209 cache_limited_renders=40 live_libraries=0
PASS_NEW_LIBASS_DATA_GEOMETRY_HOST_ONLY
```

Cumulative 10/18 scoped host JNI implementations, not Android AAR or full consumer. Remaining 8: nativeProcessTimedData (sample timestamp mapping), nativeRenderFrame (allowPartial/renderLast and texture/bitmap ownership), nativeSetBottomPositionFraction, nativeSetFontScale (boolean/style contract), nativeSetFonts (actual Android font directories/config), nativeSetFrameSize (viewport/pixel aspect), nativeSetStyleOverride, nativeSetVideoColorInfo. Need matching caller and actual behavior, no stub. No new product integration.


## Actual reference frame ownership, concurrent host test (terminal 2026-11-26)

[45761932045 / 139713727766](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45761932045/job/139713727766) success at ba68010c033fe15cbfdebf526103300a0c82cec7. [Exact historical recipe](https://github.com/rileyaaa/FingMi-Xray/blob/ba68010c033fe15cbfdebf526103300a0c82cec7/.github/workflows/100-libass-frame-ownership-once.yml). New native C++ blob c9bdbc4a759ae207772a4b2c428039b90de28d41; test blob 5da91e33f8628a13b42543e795f7a427da6eac42; staging blob 809007d8b2e9892aae6756226c61dc1b65f8add0. Pinned libass/author patch/COPYING checked and built; ldd resolves isolated ass-prefix libass.so.9. JNI probe SO SHA256 f467b269375266ac8762876cdc80e8327bee997bef9b2c5b597d919c78a0c703.

This is actual reference LibassNative/Frame/Image, with only Nullable/UnstableApi annotations/imports removed and line endings normalized for host javac; actual Guava 32.0.1-1 (jar SHA256 5435201cc390913baed355e07a6b790a7901129d90c7cd2288df151666425751, copyright SHA256 a5ddffb98e49bd460c7f315e66bb5aa8ff4c8ad0e094552db343100c0466947f). The exact unchanged input blobs were checked before staging. JDK -Xcheck:jni, actual native methods and copied ASS_Image coverage, not former fixture DTOs.

```text
PASS_REFERENCE_CONCURRENT_FRAME_OWNERSHIP renders=242 tracks=2 retired_handles=2 saved_arrays=2 live_libraries=0
PASS_REFERENCE_CONCURRENT_HOST_ONLY
```

Two threads each perform 60 visible/empty render pairs, mutate returned Java bitmap bytes and verify independent saved arrays; the library retires while tracks remain usable, then concurrent track release/render may resolve in either valid order, stale handles rejected and saved data remain after last native library release. This is not proof of all interleavings or an Android/TV result. No re-execution of the previous ten-method host suites.

### Remaining consumer contract boundary (source review, not runtime)

The fixed reference is dlgt7/media@3382803f11e129af8676a0a775f98293b079797f, not an authenticated current author AAR/source or complete distribution grant. Apache-2.0 headers checked on staged source; do not publish the dependency combination without closing its actual licenses.

- LibassTrackSession.java bfbbdf79cfd83951c5ba7298308678f6ac1bf654:170-190,213-220: actual caller requires frame size, passes width/height/viewport/PAR, and always calls renderLast=true. A complete synchronous CPU frame is allowed for either allowPartial value; no partial/asynchronous policy or renderLast=false semantics are established. Actual LibassFrame a6504f47296d992556a2dd8ae2f71a35ff4ee7fa and LibassImage 921185b97e3a7e86717f55eafa02aa4ebca60a31 constructors are used, including empty/changed frames and textureId=0 byte arrays.
- LibassMediaSession.java f0edf43c6e60cafcc6796775a8360920f7c8820f:129-132 initializes nativeSetVideoColorInfo, nativeSetFontScale and nativeSetBottomPositionFraction before usable session startup. These are still missing; do not wire the probe into that consumer. Lines 314-325 forward storage then frame geometry. LibassPlaybackSession.java 15de85d2304a3fda38d5c3783b690ca6d1c8deb5:315-328 distinguishes video size, render storage size and viewport. Only equal storage/video dimensions and in-bounds viewport are currently supported in this probe; do not guess scaled/cropped coordinates. Libass header 851ca7cb9614f8d5d3175bbcc2925dfb6521bc27 documents actual frame, storage, margins and PAR.
- Timed data: LibassTrackSession:87-99 deduplicates by bytes/length/timeMs and forwards the sample timestamp; LibassSubtitleParserFactory.java ec1a767738f330a8beeb7a677bc1a9b074cef34d:140 uses processData for ASS. Neither establishes relative vs absolute embedded cue timestamps, duration/format conversion or reset semantics for nativeProcessTimedData. No fake conversion added. Keep other five unimplemented contracts (bottom fraction, font scale/apply, fonts/config, style override, video color).
- LibassGlRenderer.java f1ec9479e043e0a2ea4f33ddc5a71e880b219746:135-191 retains layer for unchanged frame, clears and uploads CPU bitmap if textureId=0 or uses provided texture; :226-261 deletes layer and unconsumed frame textures. LibassRenderThread.java 53d2342493b91538a51373404a14bf7cea4bfb2f:210-216 renders, updates, swaps, releases on its GL thread. The selected reference shader derives vTexCoord from screen positions and the two source files do not show glUseProgram; this is a static review concern, not a proven runtime defect or basis to rewrite it here. Real GL pixel output, texture transfer, context loss, partial/fallback behavior, actual MediaSession/controller integration, ARM/TV remain unvalidated. CPU ownership/geometry cannot substitute for them.
- Author media branch tips rechecked: release-1.11.0-fongmi 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d, release 2bc207851df311340767e913931ca7b28cab1794; mpv-android fongmi c92728c62336070c191032f22ba7473d95f276d2, no new matching consumer. FFmpeg motion: fixed FongMi/mpv@f964d149 video/out/gpu_next/motion.h blob 496976cec08a30dd64aaaac89b69441d1b000dd7 specifies GPU identity, color/phase, borrowed vs owned textures; motion.c b078f6c6c200c42dabc5a6c4af7b179bb9f3e402 and motion_clock.h 8b41b4e039e6207911cad6ca57da86995b38e88c are producer-side. Not the absent actual FFmpeg Java/JNI controller. ISO: public bdj-runtime probe still requires external media ISO AAR; no native IsoNavigationPlayerController consumer implementation established. No speculative motion/ISO implementation or repeated producer test.
