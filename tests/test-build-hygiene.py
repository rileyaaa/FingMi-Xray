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

platform = (ROOT / "chaquo/src/main/java/com/fongmi/chaquo/Platform.java").read_text(encoding="utf-8")
for deprecated in ("Build.CPU_ABI", "Build.CPU_ABI2"):
    if deprecated in platform:
        errors.append(f"Platform.java still uses deprecated {deprecated}")

required_action_majors = {
    "actions/checkout": 7,
    "actions/setup-java": 6,
    "actions/setup-python": 7,
    "actions/upload-artifact": 7,
}
for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
    text = path.read_text(encoding="utf-8")
    for action, minimum in required_action_majors.items():
        for match in re.finditer(re.escape(action) + r"@v(\d+)", text):
            major = int(match.group(1))
            if major < minimum:
                errors.append(
                    f"{path.relative_to(ROOT)} uses {action}@v{major}; require v{minimum}+ for Node 24 runners"
                )

current_workflow = (ROOT / ".github/workflows/current-main-build.yml").read_text(encoding="utf-8")
publish_workflow = (ROOT / ".github/workflows/publish-current-main-test-release.yml").read_text(encoding="utf-8")

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
    ):
        if forbidden in text:
            errors.append(f"{name} must stay TV-only / Release-input based; found {forbidden}")

    for required in (
        'PLAYER_RELEASE_TAG: "build-inputs-5.6.3"',
        'PLAYER_RELEASE_ASSET: "fongmi-media3-aar-candidate-1.11.0.zip"',
        ":app:compileLeanbackDebugJavaWithJavac",
        ":app:assembleLeanbackDebug",
    ):
        if required not in text:
            errors.append(f"{name} is missing pinned TV build contract: {required}")

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

for name, text in (
    ("current-main-build.yml", current_workflow),
    ("publish-current-main-test-release.yml", publish_workflow),
):
    if "fingmi-xray-5.6.3-build-failure-reports" not in text or "retention-days: 1" not in text:
        errors.append(f"{name} failure reports must remain short-lived (1 day)")

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: build hygiene guards are clean")
