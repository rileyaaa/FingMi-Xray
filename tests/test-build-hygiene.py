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
libass_builder = (ROOT / "scripts/build/build-libass-candidate.py").read_text(encoding="utf-8")
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
    "74f578537e063e01423667b2acad4b152eb8e1fdae0f75c98ed9a1c9b05c5789",
    "0799e9942972a642149105ada63b483f5de0f4dddf546ce698b7a6ef2299a679",
    "052c81b548649a0a3d697f034640f8c4b00530b6572662b16cc6ca3f6efb1f26",
    "c625360ef9224a516a1092ea757130f4c6f11c63544c50a1b279b654cf4710f7",
):
    if required not in libass_builder:
        errors.append(f"Libass builder lost pinned APK/SO provenance: {required}")

platform = (ROOT / "chaquo/src/main/java/com/fongmi/chaquo/Platform.java").read_text(encoding="utf-8")
for required in (
    "import com.chaquo.python.android.AndroidPlatform;",
    "Collections.addAll(supportedAbis, Build.SUPPORTED_ABIS);",
    "AndroidPlatform.ABI = ABI;",
):
    if required not in platform:
        errors.append(f"Platform.java is missing Chaquopy 17 ABI runtime handoff: {required}")

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
    marker_push_allowed = name == "publish-current-main-test-release.yml" and publish_marker_exists
    if has_push and not marker_push_allowed:
        errors.append(f"{name} must remain manual-only outside the marker trigger commit")
    if marker_push_allowed and not has_push:
        errors.append("publish marker exists but publish workflow is not armed with temporary push")

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
        "Verify MPEG-H survives final TV APK packaging",
        'entry="lib/${abi}/libmpeghJNI.so"',
        "Landroidx/media3/decoder/mpegh/MpeghAudioRenderer;",
    ):
        if required not in text:
            errors.append(f"{name} is missing pinned TV build contract: {required}")

    if "releases/download/5.6.5/" in text:
        errors.append(f"{name} still references the deleted FongMi 5.6.5 Release assets")
    for required in (
        "releases/download/5.6.6/",
        "74f578537e063e01423667b2acad4b152eb8e1fdae0f75c98ed9a1c9b05c5789",
        "0799e9942972a642149105ada63b483f5de0f4dddf546ce698b7a6ef2299a679",
    ):
        if required not in text:
            errors.append(f"{name} is missing pinned FongMi 5.6.6 Libass provenance: {required}")

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
