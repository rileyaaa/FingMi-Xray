# Isolated MPV HTTP stream input (5.9 adaptation)

This is a source-only candidate, not part of prepare_candidate, app, or Gradle.
No product player selection, Exo/Xray, recovery, ordinary MPV, or release changes.

## Fixed source contracts

- FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d (Apache-2.0):
  DataSource fc93269055c2a260549ed348b50c18cdb0879c4d, DataSpec
  5d0e52cee49672ab418d4c14bacda64ec39b34aa, OkHttpDataSource
  2c1f61cc2d3148d1e3986480504d8d057fd18825.
  The generic DataSource has no concurrent cancellation method. The real
  OkHttpDataSource accepts a Call.Factory, creates one Call per open, and
  exposes read/close and response metadata. Capture and cancel that Call,
  not the client dispatcher; serialize DataSource close after I/O.
- FongMi/mpv-android@1bf892e3271e73d8649f2d209027f1fb17515d15 (MIT):
  stream.cpp a4ebe55984fa12de9b0a354da4a98cfcfa634d5d registers media3iso,
  supplies up to 64 KiB direct buffers, maps zero to EOF and negative to error.
  Use the existing stage_mpv_jni_bridge.py output, not a second MPVLib.
- TV@d3a0b84b24cf6628d72a4dbc2be453875b005536: MpvPlayerEngine
  cdd833c714e878850c2a192d1fe426c3f0b5a532 and ExoMediaSourceFactory
  d2fdb8706c3261feb5687d676278c676e12289c1 use OkHttp.player(auth),
  default headers, DefaultDataSource, CacheDataSource and ProgressiveIsoCache.
  The isolated adapter accepts the caller's authenticated Call.Factory
  and immutable DataSpec; it does NOT implement or substitute the complete
  disc/cache/ISO/BD-J path. Do not replace that path with this candidate.

## Actual local host run (2026-11-26)

From this directory, JDK 21:

    mkdir -p /tmp/mpv-owner-classes
    javac --release 8 -d /tmp/mpv-owner-classes MpvStreamOwner.java
    javac -cp /tmp/mpv-owner-classes -d /tmp/mpv-owner-classes MpvStreamOwnerHttpTest.java
    java -cp /tmp/mpv-owner-classes MpvStreamOwnerHttpTest

Final source repeated five times, all exit 0:

    PASS range seek size EOF direct buffer auth headers and idempotent close
    PASS distinct owner URI, stale callback and retirement isolation
    PASS cancel while waiting HTTP headers
    PASS cancel blocked HTTP read on owner switch; new owner still reads
    PASS 401 premature EOF cancel-before-open and failure cleanup
    PASS HOST_HTTP sources=11 closed=11 authenticatedRequests=10

Synthetic PCM WAV 32812 bytes, actual loopback HTTP 206/416/401, blocked
headers/body, forward/backward/EOF seek, direct-buffer byte comparisons,
wrong auth, truncated response and stale retirement. Test transport is real
JDK Socket, not Media3, OkHttp, JNI, Android or actual playback.
MpvStreamOwner blob fbdd87af5d0e82b64742729a8ffc2341aefaac02; test blob
b4059644416510662c1ce10e7e04002e8e0ba183; Media3MpvInput candidate blob
20566fc6c45e7edcd54aa9c3a391ad8371171393 (not compiled in this environment).
No local Android SDK/Media3/OkHttp jars; Google Maven DNS lookup failed.
Do not represent host results as the adapter/native runtime passing.

The lease gate only handles callbacks already tagged with the originating
lease (check again at delivery); the upstream MPV global untagged event
callbacks cannot be assigned to the current lease at receipt. Their actual
player command/request-id attribution and lifecycle still need evidence.
Only ordinary identity HTTP GET byte resources are accepted here.
A full native/Android test must exercise real Media3 and OkHttp including
auth, redirect policy, invalid ranges, cancellation, resource release, and
the actual registered native protocol, before any host integration.
Neither same-length resource mutation nor arbitrary disc/cache sources
are validated. Full dual ABI APK, native license closure, existing ELF gate,
and real player/TV integration remain independent gates.

## Other source search

Author repository search for FFmpeg/libass/bluray/motion/udf/iso found
FongMi/FFmpeg and TV for FFmpeg; no matching separate repositories for
the other terms. FFmpeg release-9.0-fongmi bdf17191d55d78984ea742fe858fbf9b9aaa5775
(10646 entries) and release-9.1-fongmi 1a6411b6cadf99c897598fa594ad62c51d4804ed
(11182 entries) checked full nontruncated trees; 9.1 includes
libavfilter/vulkan/fruc_interpolate.comp.glsl blob
35cc399f28bf9e80f27933b17eccd3149c9af2f9, no matching Media3 renderer/controller
or JNI consumer in targeted path scan. Native filter source is not a
replacement for the Java/JNI consumer. No new corresponding Libass or
ISO/UDF implementation identified; prior bdj-runtime boundary remains.
No additional dependency imported. Search is not exhaustive.
