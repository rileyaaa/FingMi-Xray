#!/usr/bin/env python3
"""Guard build hygiene rules that previously produced noisy CI warnings."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
errors = []

wrong_xliff = 'xmlns:xliff="http://schemas.android.com/apk/res-auto"'
for path in sorted((ROOT / "app/src").rglob("strings.xml")):
    text = path.read_text(encoding="utf-8")
    if wrong_xliff in text:
        errors.append(f"{path.relative_to(ROOT)} uses the Android res-auto namespace for xliff")
    if 'name="detail_title"' in text:
        line = next((line for line in text.splitlines() if 'name="detail_title"' in line), "")
        if "%1$s" not in line or "%2$s" not in line:
            errors.append(f"{path.relative_to(ROOT)} detail_title must use positional substitutions")

player_builder = (ROOT / "scripts/build/build-player-aar-candidate.sh").read_text(encoding="utf-8")
player_verifier = (ROOT / "scripts/build/player_candidate.py").read_text(encoding="utf-8")
dolby_overlay = (ROOT / "scripts/build/apply-media3-dolby568-overlay.py").read_text(encoding="utf-8")
mpv_overlay = (ROOT / "scripts/build/apply-media3-mpv568-overlay.py").read_text(encoding="utf-8")
iso_overlay = (ROOT / "scripts/build/apply-media3-iso568-overlay.py").read_text(encoding="utf-8")
player_importer = (ROOT / "scripts/build/import-player-aar-candidate.py").read_text(encoding="utf-8")
mpv_contract = (ROOT / "scripts/recovery/published_568_mpv_contract.py").read_text(encoding="utf-8")
mpv_restorer = (ROOT / "scripts/recovery/restore-published-568-mpv.py").read_text(encoding="utf-8")
iso_contract = (ROOT / "scripts/recovery/published_568_iso_contract.py").read_text(encoding="utf-8")
iso_restorer = (ROOT / "scripts/recovery/restore-published-568-iso.py").read_text(encoding="utf-8")
libass_importer = (ROOT / "scripts/build/import-libass-candidate.py").read_text(encoding="utf-8")
libass_builder = (ROOT / "scripts/build/build-libass-candidate.py").read_text(encoding="utf-8")
libass_extractor_builder = (ROOT / "scripts/build/build-libass-extractor.py").read_text(encoding="utf-8")
libass_build_contract = (ROOT / "scripts/build/libass_build_contract.py").read_text(encoding="utf-8")
libass_contract = (ROOT / "scripts/build/check-libass-contract.py").read_text(encoding="utf-8")
libass_native_contract = (ROOT / "compat/media3-libass/tests/published-568-native-contract.json").read_text(encoding="utf-8")
for required in (
    'SOURCE_COMMIT="3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"',
    "https://github.com/FongMi/media.git",
    ":lib-decoder-ffmpeg:assembleRelease",
    ":lib-decoder-mpegh:assembleRelease",
    ":lib-mpvplayer:assembleRelease",
    "scripts/build/apply-media3-dolby568-overlay.py",
    "scripts/build/apply-media3-mpv568-overlay.py",
    "scripts/build/apply-media3-iso568-overlay.py",
    'DOLBY_OVERLAY_ID="fongmi-tv-5.6.8-dolby-release-overlay-v1"',
    'MPV_OVERLAY_ID="fongmi-tv-5.6.8-mpv-bridge-v2"',
    'ISO_OVERLAY_ID="fongmi-tv-5.6.8-iso-navigation-stream-overlay-v4"',
    ":lib-mpvplayer:testDebugUnitTest",
    '"androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5Renderer.class"',
    '"androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP7Converter.class"',
    '"androidx/media3/extractor/iso/udf/NativeUdfFileSystem.class"',
    '"androidx/media3/exoplayer/iso/IsoNavigationSession.class"',
    '"androidx/media3/exoplayer/source/iso/IsoNavigationDataSource.class"',
    '"androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource.class"',
    '"androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource$NavigationTimeline.class"',
    '"androidx/media3/exoplayer/iso/IsoNavigationSession$DvdMenuHighlight.class"',
    '"androidx/media3/exoplayer/iso/IsoNavigationSession$HdmvMenuOverlay.class"',
    "lib-extractor-release.aar lost packet-level ISO navigation timestamp hook",
    "lib-exoplayer-release.aar lost IsoNavigationSession consumer keep rule",
    'rm -rf "$SOURCE_DIR" "$STAGE"',
):
    if required not in player_builder:
        errors.append(f"player candidate builder lost pinned-source contract: {required}")
for required in (
    'SOURCE_COMMIT = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"',
    '"lib-decoder-ffmpeg-release.aar"',
    '"lib-decoder-mpegh-release.aar"',
    '"lib-mpvplayer-release.aar"',
    'EXPECTED_AAR_COUNT = 17',
    '"androidx/media3/decoder/mpegh/MpeghAudioRenderer.class"',
    'DOLBY_OVERLAY_ID = "fongmi-tv-5.6.8-dolby-release-overlay-v1"',
    'MPV_OVERLAY_ID = "fongmi-tv-5.6.8-mpv-bridge-v2"',
    'ISO_OVERLAY_ID = "fongmi-tv-5.6.8-iso-navigation-stream-overlay-v4"',
    '"is/xyz/mpv/MPVLib$Stream.class"',
    '"androidx/media3/mpvplayer/nativebridge/MpvClient$LongResultCallback.class"',
    '"androidx/media3/mpvplayer/media/MpvIsoStream.class"',
    '"androidx/media3/mpvplayer/media/MpvIsoStreamManager.class"',
    '"androidx/media3/extractor/iso/udf/NativeUdfFileSystem.class"',
    '"androidx/media3/exoplayer/iso/IsoNavigationSession.class"',
    '"androidx/media3/exoplayer/source/iso/IsoNavigationDataSource.class"',
    '"androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource.class"',
    '"androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource$NavigationTimeline.class"',
    '"androidx/media3/exoplayer/iso/IsoNavigationSession$DvdMenuHighlight.class"',
    '"androidx/media3/exoplayer/iso/IsoNavigationSession$HdmvMenuOverlay.class"',
    "candidate extractor AAR lost packet-level ISO navigation timestamp hook",
    "candidate exoplayer AAR lost IsoNavigationSession JNI keep rule",
    "candidate manifest is missing the pinned MPV release overlay",
    "candidate manifest is missing the pinned native ISO overlay",
    '"androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5Renderer.class"',
    '"androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP7Converter$Factory.class"',
    "candidate manifest points at an unexpected FongMi/media commit",
    "candidate manifest is missing the pinned Dolby release overlay",
):
    if required not in player_verifier:
        errors.append(f"player candidate verifier lost pinned-source contract: {required}")

for required in (
    "FfmpegDolbyVisionP5Renderer",
    "Loaded FfmpegDolbyVisionP5Renderer.",
    "Error instantiating Dolby Vision profile 5 renderer",
    "patch_decode_track_selector",
    "DOLBY_VISION_P5_RENDERER_NAME",
    "setDolbyVisionP7ConverterFactory",
    "FfmpegDolbyVisionP7Converter$Factory",
):
    if required not in dolby_overlay:
        errors.append(f"Dolby 5.6.8 overlay lost release contract: {required}")
for required in (
    'LIBASS_EXTRACTOR_AAR_SHA256 = "f4667540c598416895cae5c4201fbe1c0e30c88d2673395a23db91b1b107278b"',
    'LIBASS_CANDIDATE_AAR_SHA256 = "f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861"',
):
    if required not in libass_build_contract:
        errors.append(f"Libass shared build contract lost immutable pin: {required}")

for required in (
    "from libass_build_contract import LIBASS_EXTRACTOR_AAR_SHA256",
    "observed_output==LIBASS_EXTRACTOR_AAR_SHA256",
):
    if required not in libass_extractor_builder:
        errors.append(f"Libass extractor builder lost self-verifying output contract: {required}")

for required in (
    "LIBASS_CANDIDATE_AAR_SHA256",
    "LIBASS_EXTRACTOR_AAR_SHA256",
    "EXTRACTOR=LIBASS_EXTRACTOR_AAR_SHA256",
    "observed_output==LIBASS_CANDIDATE_AAR_SHA256",
):
    if required not in libass_builder:
        errors.append(f"Libass builder lost shared reconstruction contract: {required}")

for required in (
    "from libass_build_contract import LIBASS_CANDIDATE_AAR_SHA256",
    "AAR_SHA256 = LIBASS_CANDIDATE_AAR_SHA256",
    "from published_568_iso_contract import NATIVE_SHA256 as ISO_NATIVE_SHA256",
    "merge_pinned_iso_native",
    "check_combined_iso_contract",
    "Current extractor lacks pinned ISO native entries",
    "check-published-568-iso.py",
):
    if required not in libass_importer:
        errors.append(f"Libass importer lost shared candidate/native-ISO contract: {required}")
if "2318eb904a016d0160aed2a4b7de8501578cd0f223c65e5c61086f7a9a80f573" in libass_importer:
    errors.append("Libass importer still contains superseded candidate SHA")

for required in (
    'OVERLAY_ID = "fongmi-tv-5.6.8-iso-navigation-stream-overlay-v4"',
    "NativeUdfFileSystem",
    'System.loadLibrary("isoJNI")',
    "nativeOpen(CacheDataReader reader)",
    "nativeFindFile(long handle, String path)",
    "nativeListFiles(long handle, String path)",
    "disableNativeAndOpenJava",
    "openJavaFallback",
    "udf.close()",
    "package androidx.media3.exoplayer.iso;",
    "public final class IsoNavigationSession implements Closeable",
    "CacheDataReader reader, IsoNavigationSession session, int navigationFlags",
    "private volatile int discontinuityId;",
    "private long finiteStillDurationMs;",
    "private long finiteStillId;",
    "private volatile boolean infiniteStill;",
    "private volatile boolean menuActive;",
    "private volatile int menuDomain;",
    "private volatile long stateVersion;",
    "private volatile boolean titleEnded;",
    "private volatile boolean waitingForDrain;",
    "private long pollAction()",
    "ACTION_UP = 1",
    "ACTION_DOWN = 2",
    "ACTION_LEFT = 3",
    "ACTION_RIGHT = 4",
    "ACTION_SELECT = 5",
    "ACTION_MENU = 6",
    "ACTION_POPUP_MENU = 7",
    "ACTION_PREVIOUS = 8",
    "ACTION_TITLE_MENU = 11",
    "nativeClose(long handle)",
    "nativeCopyHdmvMenuOverlay(",
    "nativeDisableSubtitles(long handle)",
    "nativeGetChapterTimesUs(long handle, int titleIndex)",
    "nativeGetClipInfo(long handle, int clipIndex)",
    "nativeGetClipNames(long handle, int titleIndex)",
    "nativeGetClipTimesUs(long handle, int titleIndex)",
    "nativeGetCurrentClipIndex(long handle)",
    "nativeGetCurrentTitleIndex(long handle)",
    "nativeGetDiscType(long handle)",
    "nativeGetDvdMenuHighlight(long handle)",
    "nativeGetHdmvMenuOverlayInfo(long handle, int lastOverlayId)",
    "nativeGetReadPlayItemIndex(long handle)",
    "nativeGetReadPlayItemStartTimeUs(long handle)",
    "nativeGetSegmentStartTimeUs(long handle)",
    "nativeGetSelectedTrackIndex(long handle, boolean subtitle)",
    "nativeGetTitleCount(long handle)",
    "nativeGetTitleInfo(long handle, int titleIndex)",
    "nativeGetTrackInfo(",
    "nativeGetWaitTimeoutMs(long handle)",
    "nativeHasMenu(long handle)",
    "nativeIsBdj(long handle)",
    "nativePump(long handle)",
    "nativeRead(",
    "nativeResumeBlurayPlaylist(",
    "nativeResumeDvdWait(long handle, int discontinuityId)",
    "nativeSeekToChapter(long handle, int chapterIndex)",
    "nativeSeekToTimeUs(long handle, long timeUs)",
    "nativeSelectTitle(long handle, int titleIndex)",
    "nativeSelectTrack(",
    "nativeSkipFiniteStill(",
    "-keep class androidx.media3.exoplayer.iso.IsoNavigationSession { *; }",
    "public final class IsoNavigationDataSource extends BaseDataSource",
    "RESULT_WAIT_FOR_STATE = -2",
    "RESULT_SEGMENT_REPLACED = -4",
    "RESULT_SEGMENT_END = -5",
    "expectedDiscontinuityId",
    "active.read(buffer, offset, requested, expectedDiscontinuityId)",
    "signalStateChangeLocked()",
    "result = pumpNativeLocked();",
    "MAX_MENU_REPLAY_BYTES = 64 * 1024 * 1024",
    "public final class IsoNavigationMediaSource extends CompositeMediaSource<Void>",
    "new BdmvTsExtractor(",
    "TimestampDiscontinuityProvider",
    "pollTimestampOffsetUs(long packetPosition)",
    "setTimestampDiscontinuityProvider(",
    "input.getPosition() - tsPacketBuffer.bytesLeft()",
    "timestampAdjusters.get(i).reset(timestampOffsetUs)",
    "createReplayDataSourceFactory",
    "getReplayForCurrentSegment",
    "awaitReplacementAndThrow",
    "recordPlayItemTransition",
    "NavigationTimeline extends ForwardingTimeline",
    "window.positionInFirstPeriodUs = -segmentStartUs",
    "period.positionInWindowUs += segmentStartUs",
    "getDvdMenuHighlightSnapshot",
    "getHdmvMenuOverlay(int lastVersion)",
    "DvdPrivateStreamReader",
    "buildDvdPrivateStreamReader",
    "fillDvdTrackLanguages",
    "buildCurrentBdmvClipInfo",
    "new StreamInfo(",
    "new EpMapEntry(",
    "decodeIso639",
    "import androidx.annotation.Nullable;",
    "import androidx.media3.common.C;",
    "new PsExtractor()",
):
    if required not in iso_overlay:
        errors.append(f"ISO 5.6.8 native navigation overlay lost release ABI contract: {required}")

for required in (
    "enqueueCommandLongResult",
    "eventCommandReply(long requestId, int error, long result)",
    "public interface Stream",
    "openStream",
    "commandLongResult",
    "loadScript(String path, MpvClient.LongResultCallback callback)",
    "load-script",
    "unloadScript(long clientId)",
    "unload-script",
    "secondary-sub-scale",
    "MPVLib$Stream",
    'STREAM_SCHEME = "media3iso"',
    '"/disc.iso"',
    "registerStream",
    "unregisterStream",
    "MpvIsoStreamManager",
    "setDataSourceFactory",
):
    if required not in mpv_overlay:
        errors.append(f"MPV 5.6.8 overlay lost release bridge contract: {required}")
for required in (
    "f62a39a5e1069d99e6072bb74961ab57b55100b4a1fa66cab08a79d2e2b3c89f",
    "3f22f95799b8f7865c0a7545165bde6788d0b7a21331ba081fb346b4f1a0c250",
    "a139aca2bf031d1147ef0ef953ecf8b3ed1d5f007b6280ab817f91c944282229",
    "3d1ca344d913b8758643df52f2763dead2ece06460e365e859d84cd54c4adc88",
):
    if required not in mpv_contract:
        errors.append(f"MPV 5.6.8 native contract lost pinned provenance: {required}")
for required in (
    "lib-mpvplayer-release.aar",
    "read_published_native",
    "candidate MPV AAR lacks native bridge entries",
):
    if required not in mpv_restorer:
        errors.append(f"MPV 5.6.8 restorer lost immutable mutation contract: {required}")

for required in (
    "e7fb4d37797b761414194a5d76b89ea4c53fe8c3a628bf8e824a54e501c15dfc",
    "8ea04aeaf831a254f4fe73face64f0c2c7dd560e604503b6e3ed4375ba267267",
    "libisoJNI.so",
):
    if required not in iso_contract:
        errors.append(f"ISO 5.6.8 native contract lost pinned provenance: {required}")
for required in (
    "lib-extractor-release.aar",
    "read_published_native",
    "candidate extractor AAR unexpectedly already contains libisoJNI.so",
):
    if required not in iso_restorer:
        errors.append(f"ISO 5.6.8 restorer lost immutable mutation contract: {required}")

for required in (
    "published_568_ffmpeg_contract",
    "NATIVE_SHA256",
    "PUBLISHED_CLOSURE",
    "libffmpegDoviJNI.so",
    "published_568_iso_contract",
    "PUBLISHED_ISO",
    "--restored-iso",
):
    if required not in player_importer:
        errors.append(f"player importer lost 5.6.8 FFmpeg closure contract: {required}")

for required in (
    "published-568-native-contract.json",
):
    if required not in libass_contract:
        errors.append(f"Libass contract checker lost current native contract: {required}")
for required in (
    '"version": "5.6.8"',
    "58bc83730285c9a4ba40bf71d4deeea8be7e69dfb7d1a053f6a77aea006ad6ee",
    "7e160faba4f64abb7551b48d07ae886af73464d3079978dcd55352e7b22bd6b3",
    '"LibassFrame": "(I[Landroidx/media3/exoplayer/libass/LibassImage;)V"',
    '"LibassImage": "(IIIII[BI)V"',
):
    if required not in libass_native_contract:
        errors.append(f"Libass 5.6.8 native contract lost pinned ABI evidence: {required}")

for required in (
    "2859ebef12bf0fa0dfec023d410df478ac5e5a82a72ef2be48f6e4fa09a24761",
    "948df594843e304c332476a380163dc1cc74f964be5ea1539ff0465a9dd936eb",
    "58bc83730285c9a4ba40bf71d4deeea8be7e69dfb7d1a053f6a77aea006ad6ee",
    "7e160faba4f64abb7551b48d07ae886af73464d3079978dcd55352e7b22bd6b3",
):
    if required not in libass_builder:
        errors.append(f"Libass builder lost pinned APK/SO provenance: {required}")

elf_runtime_guard = (ROOT / "scripts/build/check-elf-runtime.py").read_text(encoding="utf-8")
final_native_guard = (ROOT / "scripts/build/check-final-apk-native.py").read_text(encoding="utf-8")
final_manifest_guard = (ROOT / "scripts/build/check-final-apk-manifest.py").read_text(encoding="utf-8")
app_manifest = (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
for required in ("PT_LOAD", "section_metadata", "--self-test"):
    if required not in elf_runtime_guard:
        errors.append(f"ELF runtime guard lost strip-aware contract: {required}")
for required in (
    "libXray.aar",
    "lib-decoder-ffmpeg-release.aar",
    "lib-mpvplayer-release.aar",
    "lib-decoder-mpegh-release.aar",
    "lib-exoplayer-libass-reconstructed.aar",
    "published_568_ffmpeg_contract.py",
    "published_568_mpv_contract.py",
    "published_568_iso_contract.py",
    "FFMPEG_SONAMES",
    "MPV_SONAMES",
    "ISO_SONAMES",
    "libplayer.so",
    "libmpv.so",
    "libisoJNI.so",
    "lib-extractor-release.aar",
    "libffmpegDoviJNI.so",
    'rglob(f"app-leanback-{abi}-debug.apk")',
    "recursive APK discovery failed",
    "armeabi-v7a",
    "arm64-v8a",
):
    if required not in final_native_guard:
        errors.append(f"final native APK guard lost required provenance input: {required}")
for required in (
    "android.permission.READ_PHONE_STATE",
    "android.permission.RECEIVE_BOOT_COMPLETED",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.BIND_VPN_SERVICE",
    "com.fingmi.xray.service.XrayService",
    'xray.get(A + "exported") != "false"',
    'xray.get(A + "process") != ":xray"',
):
    if required not in final_manifest_guard:
        errors.append(f"final APK manifest guard lost security contract: {required}")

if '<uses-permission android:name="android.permission.READ_PHONE_STATE" tools:node="remove" />' not in app_manifest:
    errors.append("app manifest must explicitly remove transitive READ_PHONE_STATE from final APK")

mpv_util = (ROOT / "app/src/main/java/com/fongmi/android/tv/player/mpv/MpvUtil.java").read_text(encoding="utf-8")
if 'List.of("sub-scale", "sub-scale-signs", "secondary-sub-scale")' not in mpv_util:
    errors.append("MpvUtil lost 5.6.8 secondary subtitle scale ownership")

audio_setting = (ROOT / "app/src/main/java/com/fongmi/android/tv/setting/AudioSetting.java").read_text(encoding="utf-8")
for required in (
    "public static final int MAX_BOOST = 2000;",
    'Math.clamp(Prefers.getInt("audio_boost"), MIN_BOOST, MAX_BOOST)',
):
    if required not in audio_setting:
        errors.append(f"AudioSetting lost FongMi 5.6.8 20 dB boost contract: {required}")

platform = (ROOT / "chaquo/src/main/java/com/fongmi/chaquo/Platform.java").read_text(encoding="utf-8")
for required in (
    "import com.chaquo.python.android.AndroidPlatform;",
    "android.os.Process.is64Bit()",
    "Build.SUPPORTED_64_BIT_ABIS",
    "Build.SUPPORTED_32_BIT_ABIS",
    "Collections.addAll(supportedAbis, processAbis);",
    "AndroidPlatform.ABI = ABI;",
):
    if required not in platform:
        errors.append(f"Platform.java is missing Chaquopy 17 process-ABI runtime handoff: {required}")
if "Collections.addAll(supportedAbis, Build.SUPPORTED_ABIS);" in platform:
    errors.append("Platform.java must not choose Chaquopy assets from cross-bitness device ABI order")

required_action_majors = {
    "actions/checkout": 7,
    "actions/setup-java": 6,
    "actions/setup-python": 7,
    "actions/upload-artifact": 7,
}
for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
    text = path.read_text(encoding="utf-8")

    upload_count = text.count("actions/upload-artifact@")
    retention_values = [int(value) for value in re.findall(r"retention-days:\s*(\d+)", text)]
    if upload_count != len(retention_values):
        errors.append(
            f"{path.relative_to(ROOT)} must set an explicit retention-days value for every upload-artifact step"
        )
    for days in retention_values:
        if days > 3:
            errors.append(
                f"{path.relative_to(ROOT)} retains an Actions artifact for {days} days; maximum is 3"
            )

    for action, minimum in required_action_majors.items():
        for match in re.finditer(re.escape(action) + r"@v(\d+)", text):
            major = int(match.group(1))
            if major < minimum:
                errors.append(
                    f"{path.relative_to(ROOT)} uses {action}@v{major}; require v{minimum}+ for Node 24 runners"
                )

current_workflow = (ROOT / ".github/workflows/current-main-build.yml").read_text(encoding="utf-8")
publish_workflow = (ROOT / ".github/workflows/publish-current-main-test-release.yml").read_text(encoding="utf-8")
recovery_player_workflow = (ROOT / ".github/workflows/recovery-player-aars.yml").read_text(encoding="utf-8")
recovery_native_workflow = (ROOT / ".github/workflows/recovery-restore-ffmpegjni.yml").read_text(encoding="utf-8")
recovery_faithful_workflow = (ROOT / ".github/workflows/recovery-build.yml").read_text(encoding="utf-8")

current_marker_exists = (ROOT / ".github/.trigger-current-main-build").exists()
publish_marker_exists = (ROOT / ".github/.trigger-publish-current-main-test").exists()
for name, text in (
    ("current-main-build.yml", current_workflow),
    ("publish-current-main-test-release.yml", publish_workflow),
):
    if "on:\n  workflow_dispatch:" not in text:
        errors.append(f"{name} must retain workflow_dispatch")
    for trigger in ("pull_request:", "schedule:", "workflow_call:"):
        if f"\n  {trigger}" in text:
            errors.append(f"{name} must not enable automatic trigger {trigger}")
    has_push = "\n  push:" in text
    marker_push_allowed = (
        (name == "current-main-build.yml" and current_marker_exists)
        or (name == "publish-current-main-test-release.yml" and publish_marker_exists)
    )
    if has_push and not marker_push_allowed:
        errors.append(f"{name} must remain manual-only outside the marker trigger commit")
    if name == "current-main-build.yml" and current_marker_exists and not has_push:
        errors.append("current-main marker exists but current-main workflow is not armed with temporary push")
    if name == "publish-current-main-test-release.yml" and publish_marker_exists and not has_push:
        errors.append("publish marker exists but publish workflow is not armed with temporary push")

for required in (
    "BUILD_SOURCE_SHA: ${{ github.sha }}",
    "Verify temporary push trigger source",
    "ref: ${{ env.BUILD_SOURCE_SHA }}",
    'test "$changed" = ".github/.trigger-current-main-build"',
):
    if required not in current_workflow:
        errors.append(f"current-main workflow is missing stable source targeting guard: {required}")


if "permissions:\n  contents: write\n  actions: read" not in publish_workflow:
    errors.append(
        "publish workflow must retain the least-privilege release-capable GITHUB_TOKEN pair "
        "(contents: write + actions: read)"
    )

for required in (
    "BUILD_SOURCE_SHA: ${{ github.sha }}",
    "Verify temporary push trigger source",
    "ref: ${{ env.BUILD_SOURCE_SHA }}",
    'test "$changed" = ".github/.trigger-publish-current-main-test"',
    '--target "$BUILD_SOURCE_SHA"',
    ".object.sha == $sha",
):
    if required not in publish_workflow:
        errors.append(f"publish workflow is missing stable source targeting guard: {required}")


for name, text in (
    ("current-main-build.yml", current_workflow),
    ("publish-current-main-test-release.yml", publish_workflow),
):
    for forbidden in (
        ":app:compileMobile",
        ":app:assembleMobile",
        "MobileDebug",
        "PLAYER_ARTIFACT_ID",
        "PLAYER_RELEASE_TAG",
        "PLAYER_RELEASE_ASSET",
        "PLAYER_ZIP_SHA256",
    ):
        if forbidden in text:
            errors.append(f"{name} must stay TV-only and rebuild player inputs from source; found {forbidden}")

    for required in (
        "bash scripts/build/build-player-aar-candidate.sh",
        "scripts/recovery/restore-published-568-ffmpeg.py",
        "scripts/recovery/restore-published-568-mpv.py",
        "scripts/recovery/restore-published-568-iso.py",
        "--v7-apk build/work/current-main/input/published-v568-v7.apk",
        "--v8-apk build/work/current-main/input/published-v568-v8.apk",
        "--restored-mpv build/work/current-main/restored/lib-mpvplayer-release.aar",
        "--restored-iso build/work/current-main/restored/lib-extractor-release.aar",
        "scripts/recovery/check-published-568-ffmpeg.py --aar app/libs/lib-decoder-ffmpeg-release.aar",
        "scripts/recovery/check-published-568-mpv.py --aar app/libs/lib-mpvplayer-release.aar",
        "scripts/recovery/check-published-568-iso.py --aar app/libs/lib-extractor-release.aar",
        "'platforms;android-36'",
        ":app:compileLeanbackDebugJavaWithJavac",
        ":app:assembleLeanbackDebug",
        "python3 tests/test-upgrade-compat.py",
        "python3 scripts/build/check-elf-runtime.py --self-test",
        "python3 scripts/build/check-final-apk-native.py --self-test",
        "python3 scripts/build/check-final-apk-manifest.py --self-test",
        "Verify MPEG-H survives final TV APK packaging",
        'entry="lib/${abi}/libmpeghJNI.so"',
        "Landroidx/media3/decoder/mpegh/MpeghAudioRenderer;",
        "Verify pinned native runtime survives final TV APK packaging",
        "python3 scripts/build/check-final-apk-native.py",
        "--apk-dir app/build/outputs/apk/leanback",
        "Verify final Leanback manifest security contract",
        "python3 scripts/build/check-final-apk-manifest.py",
        'apkanalyzer="$sdk_root/cmdline-tools/latest/bin/apkanalyzer"',
        "find app/build/outputs/apk/leanback -type f -name 'app-leanback-*-debug.apk'",
        'test "${#apks[@]}" -eq 2',
        'for apk in "${apks[@]}"; do',
    ):
        if required not in text:
            errors.append(f"{name} is missing pinned TV build contract: {required}")

    for forbidden in (
        "scripts/recovery/restore-published-ffmpegjni.py",
        "scripts/recovery/check-player-ffmpegjni-against-published.py",
    ):
        if forbidden in text:
            errors.append(f"{name} must use the complete 5.6.8 FFmpeg closure; found {forbidden}")

    for retired in ("5.6.5", "5.6.6"):
        if f"releases/download/{retired}/" in text:
            errors.append(f"{name} still references deleted FongMi {retired} Release assets")
    for required in (
        "releases/download/5.6.8/",
        "2859ebef12bf0fa0dfec023d410df478ac5e5a82a72ef2be48f6e4fa09a24761",
        "948df594843e304c332476a380163dc1cc74f964be5ea1539ff0465a9dd936eb",
    ):
        if required not in text:
            errors.append(f"{name} is missing pinned FongMi 5.6.8 Libass container provenance: {required}")

    for required in (
        "Reclaim transient provenance/native harness space before",
        '"$work/input"',
        '"$work/tools"',
        '"$work/restored"',
        '"$work/libxray-bindings"',
        '"$work/xray-native-chain"',
        '"$work/extractor"',
    ):
        if required not in text:
            errors.append(f"{name} must reclaim verified build scratch before Gradle compile/assemble: {required}")

for name, text in (
    ("recovery-player-aars.yml", recovery_player_workflow),
    ("recovery-restore-ffmpegjni.yml", recovery_native_workflow),
    ("recovery-build.yml", recovery_faithful_workflow),
):
    if "bash scripts/build/build-player-aar-candidate.sh" not in text:
        errors.append(f"{name} must rebuild the pinned player candidate from source")
    for forbidden in (
        "10859533459",
        "0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee",
    ):
        if forbidden in text:
            errors.append(f"{name} still depends on retired player artifact storage: {forbidden}")

if "fingmi-xray-5.6.3-current-main-debug" not in current_workflow:
    errors.append("current-main-build.yml must retain the short-lived TV debug artifact")
if "retention-days: 2" not in current_workflow:
    errors.append("current-main-build.yml debug artifact must remain short-lived (2 days)")
for required in (
    "actions: write",
    "Remove superseded current-main debug artifacts",
    'select(.name == "fingmi-xray-5.6.3-current-main-debug")',
    'gh api --method DELETE "repos/${GITHUB_REPOSITORY}/actions/artifacts/$id"',
):
    if required not in current_workflow:
        errors.append(f"current-main-build.yml must auto-prune superseded debug artifacts: {required}")
if "fingmi-xray-5.6.3-current-main-debug" in publish_workflow:
    errors.append("publish workflow must not duplicate successful APKs into Actions artifacts")

if 'PREVIOUS_RELEASE_TAG: "v5.6.3-xray.test.4"' not in publish_workflow:
    errors.append("publish workflow must retire the current test.4 release only after replacement verification")
if 'RELEASE_TAG: "v5.6.3-xray.test.5"' not in publish_workflow:
    errors.append("publish workflow must target the next v5.6.3-xray.test.5 pre-release")
for required in (
    'for stale_tag in "$PREVIOUS_RELEASE_TAG" "build-inputs-5.6.3"; do',
    "'v5.6.0-xray.5'",
    'test "$remaining" = "$expected"',
):
    if required not in publish_workflow:
        errors.append(f"publish workflow must leave only golden + current test releases: {required}")

for name, text in (
    ("current-main-build.yml", current_workflow),
    ("publish-current-main-test-release.yml", publish_workflow),
):
    if "fingmi-xray-5.6.3-build-failure-reports" not in text or "retention-days: 1" not in text:
        errors.append(f"{name} failure reports must remain short-lived (1 day)")

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: build hygiene guards are clean")
