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
