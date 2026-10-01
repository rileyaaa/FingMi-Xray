#!/usr/bin/env python3
"""Guard build hygiene rules that previously produced noisy CI warnings."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
errors = []

player_builder = (ROOT / "scripts/build/build-player-aar-candidate.sh").read_text(encoding="utf-8")
player_verifier = (ROOT / "scripts/build/player_candidate.py").read_text(encoding="utf-8")
libass_builder = (ROOT / "scripts/build/build-libass-candidate.py").read_text(encoding="utf-8")
libass_extractor = (ROOT / "scripts/build/build-libass-extractor.py").read_text(encoding="utf-8")
player_importer = (ROOT / "scripts/build/import-player-aar-candidate.py").read_text(encoding="utf-8")
libass_contract = (ROOT / "scripts/build/check-libass-contract.py").read_text(encoding="utf-8")
libass_native_contract = (ROOT / "compat/media3-libass/tests/published-568-native-contract.json").read_text(encoding="utf-8")
for required in (
    'SOURCE_COMMIT="3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"',
    "https://github.com/FongMi/media.git",
    ":lib-decoder-ffmpeg:assembleRelease",
    ":lib-decoder-mpegh:assembleRelease",
    ":lib-mpvplayer:assembleRelease",
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
    "candidate manifest points at an unexpected FongMi/media commit",
):
    if required not in player_verifier:
        errors.append(f"player candidate verifier lost pinned-source contract: {required}")

for required in (
    "published-568-native-contract.json",
):
    if required not in libass_contract:
        errors.append(f"Libass contract checker lost current native contract: {required}")

for required in (
    "SOURCE_COMMIT='9dae39e9689ee305c83f94bd11cf3bcecb9d6171'",
    "historical_matroska_source_commit",
    "exact public FongMi/media@",
):
    if required not in libass_extractor:
        errors.append(f"Libass extractor lost public historical Matroska provenance: {required}")
if (ROOT / "compat/media3-libass/patches/matroska-libass-hooks.patch").exists():
    errors.append("Libass extractor must use the public historical Matroska source directly, not rebuild hooks with matroska-libass-hooks.patch")
for forbidden in ("--restored-decoder", "PUBLISHED_JNI", "verified_decoder_replacement"):
    if forbidden in player_importer:
        errors.append(f"active player importer must not restore historical decoder JNI: {forbidden}")
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
for required in ("PT_LOAD", "section_metadata", "--self-test"):
    if required not in elf_runtime_guard:
        errors.append(f"ELF runtime guard lost strip-aware contract: {required}")
for required in (
    "libXray.aar",
    "lib-decoder-ffmpeg-release.aar",
    "lib-decoder-mpegh-release.aar",
    "lib-exoplayer-libass-reconstructed.aar",
    'rglob(f"app-leanback-{abi}-debug.apk")',
    "recursive APK discovery failed",
    "armeabi-v7a",
    "arm64-v8a",
):
    if required not in final_native_guard:
        errors.append(f"final native APK guard lost required provenance input: {required}")
for required in (
    "android.permission.RECEIVE_BOOT_COMPLETED",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.BIND_VPN_SERVICE",
    "com.fingmi.xray.service.XrayService",
    'xray.get(A + "exported") != "false"',
    'xray.get(A + "process") != ":xray"',
):
    if required not in final_manifest_guard:
        errors.append(f"final APK manifest guard lost security contract: {required}")

audio_setting = (ROOT / "app/src/main/java/com/fongmi/android/tv/setting/AudioSetting.java").read_text(encoding="utf-8")
for required in (
    "public static final int MAX_BOOST = 1200;",
    'Math.clamp(Prefers.getInt("audio_boost"), MIN_BOOST, MAX_BOOST)',
):
    if required not in audio_setting:
        errors.append(f"AudioSetting must follow the pinned FongMi/TV upstream contract: {required}")
if "public static final int MAX_BOOST = 2000;" in audio_setting:
    errors.append("AudioSetting must not carry the Release-only 5.6.8 20 dB boost override")

release_only_paths = (
    "compat/media3-dolby568",
    "scripts/build/apply-media3-dolby568-overlay.py",
    "scripts/build/apply-media3-mpv568-overlay.py",
    "scripts/build/apply-media3-iso568-overlay.py",
    "scripts/recovery/restore-published-568-ffmpeg.py",
    "scripts/recovery/restore-published-568-mpv.py",
    "scripts/recovery/restore-published-568-iso.py",
    "scripts/recovery/check-published-568-ffmpeg.py",
    "scripts/recovery/check-published-568-mpv.py",
    "scripts/recovery/check-published-568-iso.py",
    "scripts/recovery/published_568_ffmpeg_contract.py",
    "scripts/recovery/published_568_mpv_contract.py",
    "scripts/recovery/published_568_iso_contract.py",
)
for relative in release_only_paths:
    if (ROOT / relative).exists():
        errors.append(f"current-main must not restore Release-only FongMi media behavior: {relative}")

platform = (ROOT / "chaquo/src/main/java/com/fongmi/chaquo/Platform.java").read_text(encoding="utf-8")
for required in (
    "import com.chaquo.python.android.AndroidPlatform;",
    "Collections.addAll(supportedAbis, Build.SUPPORTED_ABIS);",
    "Collections.addAll(supportedAbis, Build.CPU_ABI, Build.CPU_ABI2);",
    "AndroidPlatform.ABI = ABI;",
):
    if required not in platform:
        errors.append(f"Platform.java must follow the pinned FongMi/TV upstream ABI selection: {required}")
for forbidden in (
    "android.os.Process.is64Bit()",
    "Build.SUPPORTED_64_BIT_ABIS",
    "Build.SUPPORTED_32_BIT_ABIS",
    "Collections.addAll(supportedAbis, processAbis);",
):
    if forbidden in platform:
        errors.append(f"Platform.java must not carry fork-only Chaquopy ABI selection: {forbidden}")

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
        "'platforms;android-36'",
        ":app:compileLeanbackDebugJavaWithJavac",
        ":app:assembleLeanbackDebug",
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
        "scripts/build/apply-media3-dolby568-overlay.py",
        "scripts/build/apply-media3-mpv568-overlay.py",
        "scripts/build/apply-media3-iso568-overlay.py",
        "scripts/recovery/restore-published-568-ffmpeg.py",
        "scripts/recovery/restore-published-568-mpv.py",
        "scripts/recovery/restore-published-568-iso.py",
        "scripts/recovery/check-published-568-ffmpeg.py",
        "scripts/recovery/check-published-568-mpv.py",
        "scripts/recovery/check-published-568-iso.py",
        "scripts/recovery/restore-published-ffmpegjni.py",
        "scripts/recovery/check-player-ffmpegjni-against-published.py",
        "--restored-decoder",
    ):
        if forbidden in text:
            errors.append(f"{name} must follow public FongMi media instead of Release-only recovery: {forbidden}")

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

if 'PREVIOUS_RELEASE_TAG: "v5.6.3-xray.test.5"' not in publish_workflow:
    errors.append("publish workflow must retire the current test.5 release only after replacement verification")
if 'RELEASE_TAG: "v5.6.3-xray.test.6"' not in publish_workflow:
    errors.append("publish workflow must target the next v5.6.3-xray.test.6 pre-release")
for required in (
    'for stale_tag in "$PREVIOUS_RELEASE_TAG" "build-inputs-5.6.3"; do',
    "'v5.6.0-xray.5'",
    'select(startswith("source-backup-") | not)',
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
