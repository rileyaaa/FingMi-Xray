#!/usr/bin/env python3
"""Guard build hygiene rules that previously produced noisy CI warnings."""

from pathlib import Path
import re
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
errors = []

player_builder = (ROOT / "scripts/build/build-player-aar-candidate.sh").read_text(encoding="utf-8")
player_verifier = (ROOT / "scripts/build/player_candidate.py").read_text(encoding="utf-8")
libass_builder = (ROOT / "scripts/build/build-libass-candidate.py").read_text(encoding="utf-8")
libass_input = (ROOT / "scripts/build/libass_native_input.py").read_text(encoding="utf-8")
libass_extractor = (ROOT / "scripts/build/build-libass-extractor.py").read_text(encoding="utf-8")
player_importer = (ROOT / "scripts/build/import-player-aar-candidate.py").read_text(encoding="utf-8")
libass_contract = (ROOT / "scripts/build/check-libass-contract.py").read_text(encoding="utf-8")
libass_native_contract = (ROOT / "compat/media3-libass/tests/published-568-native-contract.json").read_text(encoding="utf-8")
for required in (
    'SOURCE_COMMIT="3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"',
    "https://github.com/FongMi/media.git",
    ":lib-decoder:assembleRelease",
    ":lib-decoder-ffmpeg:assembleRelease",
    ":lib-decoder-mpegh:assembleRelease",
    ":lib-mpvplayer:assembleRelease",
    'rm -rf "$SOURCE_DIR" "$STAGE"',
):
    if required not in player_builder:
        errors.append(f"player candidate builder lost pinned-source contract: {required}")
for required in (
    'SOURCE_COMMIT = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"',
    '"lib-decoder-release.aar"',
    '"lib-decoder-ffmpeg-release.aar"',
    '"lib-decoder-mpegh-release.aar"',
    '"lib-mpvplayer-release.aar"',
    'EXPECTED_AAR_COUNT = 18',
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
    if required not in libass_input:
        errors.append(f"Libass native reader lost pinned APK/SO provenance: {required}")
if "read_native_inputs(a.v7_apk,a.v8_apk,a.native_source)" not in libass_builder:
    errors.append("Libass builder must verify exact native bytes for either APK container mode")

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
    'rglob(name)',
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
    "python3 scripts/build/publish-current-release.py",
    "python3 tests/test-release-publication.py",
):
    if required not in publish_workflow:
        errors.append(f"publish workflow is missing stable source targeting guard: {required}")


for name, text in (
    ("current-main-build.yml", current_workflow),
    ("publish-current-main-test-release.yml", publish_workflow),
):
    # The upstream daemon criteria select JetBrains, not any Java 21 vendor.
    # Preflight must start a real daemon before expensive native reconstruction.
    if not re.search(r"distribution: jetbrains\s+java-version: [\"']21[\"']", text):
        errors.append(f"{name} must install JetBrains JDK 21 for the upstream daemon criteria")
    preflight = text.find("Verify upstream Gradle daemon toolchain")
    native_build = text.find("Rebuild and verify pinned player/native inputs")
    if preflight < 0 or native_build < preflight:
        errors.append(f"{name} must preflight the daemon before rebuilding native inputs")
    if "-Porg.gradle.java.installations.auto-download=false" not in text or "help --stacktrace --warning-mode all" not in text:
        errors.append(f"{name} must start the daemon without fallback toolchain downloads")
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
        ":xray:testDebugUnitTest",
        ":tv-recovery:testDebugUnitTest",
        ":app:compileLeanbackReleaseJavaWithJavac",
        ":app:assembleLeanbackRelease",
        "python3 scripts/build/check-elf-runtime.py --self-test",
        "python3 scripts/build/check-final-apk-native.py --self-test",
        "python3 scripts/build/check-final-apk-manifest.py --self-test",
        "python3 tests/test-release-publication.py",
        "Verify MPEG-H survives final TV APK packaging",
        'entry="lib/${abi}/libmpeghJNI.so"',
        "Landroidx/media3/decoder/mpegh/MpeghAudioRenderer;",
        "Verify pinned native runtime survives final TV APK packaging",
        "python3 scripts/build/check-final-apk-native.py",
        "--apk-dir app/build/outputs/apk/leanback",
        "Verify imported player startup",
        "python3 tests/test-player-startup.py",
        "Verify final Media3 DEX linkage",
        "python3 scripts/build/check-final-apk-media3.py",
        "python3 tests/test-media3-dex-linkage.py",
        "python3 tests/test-player-candidate-linkage.py",
        "Verify final Leanback manifest security contract",
        "python3 scripts/build/check-final-apk-manifest.py",
        'apkanalyzer="$sdk_root/cmdline-tools/latest/bin/apkanalyzer"',
        "find app/build/outputs/apk/leanback -type f -name 'leanback-*.apk'",
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

    if "github.com/FongMi/Release/releases/download/" in text:
        errors.append(f"{name} must not depend on deleted upstream APK containers")
    for required in (
        "python3 scripts/build/libass_native_input.py",
        '--fetch-retained "$GITHUB_REPOSITORY"',
        "--output-dir build/work/current-main/input",
        "--report build/work/current-main/libass-native-input.json",
        "--native-source retained-release",
        'libass-source-v7.apk',
        'libass-source-v8.apk',
        "python3 tests/test-libass-native-input.py",
    ):
        if required not in text:
            errors.append(f"{name} is missing retained Libass native provenance: {required}")
    if text.index("python3 scripts/build/libass_native_input.py") > text.index("bash scripts/build/build-player-aar-candidate.sh"):
        errors.append(f"{name} must verify available Libass inputs before rebuilding player")

    for required in (
        "Reclaim remaining verified Libass scratch before Gradle compile/assemble",
        '"$work/input"',
        '"$work/tools"',
        '"$work/restored"',
        '"$work/libxray-bindings"',
        '"$work/xray-native-chain"',
        '"$work/extractor"',
    ):
        if required not in text:
            errors.append(f"{name} must reclaim verified build scratch before Gradle compile/assemble: {required}")

    # Exercise the actual cleanup step in an isolated fake build tree. The
    # verified Xray inputs must go before Maven starts, but Libass inputs and
    # the AARs consumed by later Gradle tasks must survive byte-for-byte.
    cleanup_marker = "      - name: Reclaim verified Xray scratch before Libass\n"
    libass_marker = "      - name: Build and import reconstructed Libass candidate\n"
    if cleanup_marker not in text or text.index(cleanup_marker) > text.index(libass_marker):
        errors.append(f"{name} must retire Xray scratch before Libass starts")
        continue
    native_start = text.index("      - name: Verify current Xray chain")
    native = text[native_start:text.index(cleanup_marker)]
    v7_end = native.index('--android-root "$work/v7-harness/android/root"')
    arm64_start = native.index('python3 scripts/recovery/prepare-native-converter-harness.py', v7_end)
    v7_cleanup = 'rm -rf "$work/v7-harness"'
    v8_cleanup = 'rm -rf "$work/arm64-harness"'
    if v7_cleanup not in native[v7_end:arm64_start]:
        errors.append(f"{name} must retire verified v7 runtime before preparing arm64")
    if v8_cleanup not in native[native.index('--android-root "$work/arm64-harness/android/root"'):]:
        errors.append(f"{name} must retire verified arm64 runtime after its test")
    cleanup = text.split(cleanup_marker, 1)[1].split(libass_marker, 1)[0]
    cleanup = textwrap.dedent(cleanup.split("        run: |\n", 1)[1])
    with tempfile.TemporaryDirectory(prefix="fingmi-scratch-check-") as directory:
        root = Path(directory)
        work = root / "build/work/current-main"
        retired = [work / path for path in (
            "tools/jadx/tool", "restored/libXray.aar", "libxray-bindings/classes.jar",
            "xray-native-chain/test/input.jar", "input/published-v560-v7.apk",
            "input/published-v560-v8.apk", "input/jadx.zip",
        )]
        retained = [work / "input" / path for path in (
            "player-candidate.zip", "media3-container-1.11.0.aar",
            "libass-source-v7.apk", "libass-source-v8.apk",
        )] + [root / path for path in (
            "app/libs/player.aar", "libxray/libs/libXray.aar", "unrelated-keep",
        )]
        for path in retired + retained:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"verified-input")
        subprocess.run(["bash", "-euo", "pipefail", "-c", cleanup], cwd=root,
                       check=True, stdout=subprocess.DEVNULL)
        if any(path.exists() for path in retired):
            errors.append(f"{name} cleanup retains consumed Xray scratch")
        if any(not path.is_file() or path.read_bytes() != b"verified-input" for path in retained):
            errors.append(f"{name} cleanup damaged a later build input")

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

if "fingmi-xray-5.6.3-current-main-release" not in current_workflow:
    errors.append("current-main-build.yml must retain the short-lived TV debug artifact")
if "retention-days: 2" not in current_workflow:
    errors.append("current-main-build.yml debug artifact must remain short-lived (2 days)")
for required in (
    "actions: write",
    "Remove superseded current-main release artifacts",
    'select(.name == "fingmi-xray-5.6.3-current-main-release")',
    'gh api --method DELETE "repos/${GITHUB_REPOSITORY}/actions/artifacts/$id"',
):
    if required not in current_workflow:
        errors.append(f"current-main-build.yml must auto-prune superseded debug artifacts: {required}")
if "fingmi-xray-5.6.3-current-main-release" in publish_workflow:
    errors.append("publish workflow must not duplicate successful APKs into Actions artifacts")

if not re.search(r'PREVIOUS_BACKUP_TAG: "source-backup-[^\"]+"', publish_workflow):
    errors.append("publish workflow must explicitly select the previous source backup")
if 'RELEASE_TAG: "v5.6.3-xray.2"' not in publish_workflow:
    errors.append("publish workflow must target the v5.6.3-xray.2 formal release")
for required in (
    "      replace_existing:",
    "        type: boolean",
    "        default: false",
    "  group: fingmi-formal-release",
    "  cancel-in-progress: false",
    "      ALLOW_EXISTING_RELEASE:",
    "      ROLLBACK_TAG:",
    "Publish verified APKs and matching complete source backup",
):
    if required not in publish_workflow:
        errors.append(f"publish workflow lost staged replacement/source backup contract: {required}")

for name, text in (
    ("current-main-build.yml", current_workflow),
    ("publish-current-main-test-release.yml", publish_workflow),
):
    if "fingmi-xray-5.6.3-build-failure-reports" not in text or "retention-days: 1" not in text:
        errors.append(f"{name} failure reports must remain short-lived (1 day)")

app_build = (ROOT / "app/build.gradle").read_text(encoding="utf-8")
version_name = re.search(r'versionName "([^"]+)"', app_build).group(1)
version_code = int(re.search(r'versionCode (\d+)', app_build).group(1))
if version_name != "v5.6.3-xray.2" or version_code != 563002:
    errors.append("fork release version must match v5.6.3-xray.2 / 563002")
if f'RELEASE_TAG: "{version_name}"' not in publish_workflow:
    errors.append("publish tag must equal the versionName embedded in the APK")
for name, text in (("current-main", current_workflow), ("publish", publish_workflow)):
    if "keytool -genkeypair" in text or "current-main-debug.jks" in text:
        errors.append(f"{name} must never generate a replacement release key")
    for required in ("python3 scripts/build/check-release-signing.py", "--build-type release"):
        if required not in text:
            errors.append(f"{name} lost persistent signing/release verification: {required}")
# APK formal status and backup-only prerelease status are asserted by the
# publication transaction tests; a whole-workflow '--prerelease' text ban
# cannot distinguish the two intentionally different release types.
if "signing/release-signing.properties" not in app_build or "signingConfigs.release" not in app_build:
    errors.append("app must use the persistent private-project release signing configuration")

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: build hygiene guards are clean")
