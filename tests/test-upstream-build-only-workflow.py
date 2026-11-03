#!/usr/bin/env python3
"""No publish, tag mutation, or main push is allowed in build-only mode."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / ".github/workflows/manual-upstream-sync.yml").read_text(encoding="utf-8")
parts = text.split("      - name: ")


def section(name):
    item = next((p for p in parts if p.startswith(name + "\n")), None)
    assert item is not None, "Missing workflow step: " + name
    return item


assert re.search(r"(?m)^      build_without_publish:\n"
                 r"        description: [^\n]+\n"
                 r"        type: boolean\n"
                 r"        default: false$", text)
assert 'if [[ "$APPLY_TO_MAIN" == "true" && "$BUILD_WITHOUT_PUBLISH" == "true" ]]' in section(
    "Verify reusable upgrade engine locally")
assert 'BUILD_CANDIDATE: ${{ inputs.apply_to_main || inputs.build_without_publish }}' in section(
    "Three-way merge and regenerate approved fork adapters")
assert 'if [[ "$BUILD_CANDIDATE" != "true" ]]' in section(
    "Three-way merge and regenerate approved fork adapters")
build_gate = 'if: ${{ inputs.apply_to_main || inputs.build_without_publish }}'
for name in (
    "Run fork source guards",
    "Prepare Android SDK 36 and 37",
    "Verify upstream Gradle daemon toolchain",
    "Verify persistent private-project release signing",
    "Rebuild and verify pinned player/native inputs",
    "Prepare public player and Xray native dependencies",
    "Verify current Xray chain against published v7 and arm64 native",
    "Reclaim verified Xray scratch before Libass",
    "Build and import reconstructed Libass candidate",
    "Verify imported player startup",
    "Verify Xray artwork lifecycle",
    "Verify proxy policy host regression",
    "Compile upgraded Leanback source",
    "Assemble Android TV release APKs",
    "Verify MPEG-H survives final TV APK packaging",
    "Verify pinned native runtime survives final TV APK packaging",
    "Verify final Media3 DEX linkage",
    "Verify final Leanback manifest security contract",
):
    assert build_gate in section(name), "Build-only skips a required check: " + name

shared = 'if: ${{ (inputs.apply_to_main || inputs.build_without_publish) && success() }}'
for name in ("Record build inputs and outputs", "Stage Android TV release APKs"):
    assert shared in section(name), "Build-only doesn't package verified outputs: " + name
asset = section("Upload fully verified APKs for private build-only test")
assert 'if: ${{ inputs.build_without_publish && !inputs.apply_to_main && success() }}' in asset
assert "release/*.apk" in asset and "BUILD_RESULT.txt" in asset
assert "if-no-files-found: error" in asset and "retention-days: 2" in asset
assert 'if: ${{ (inputs.apply_to_main || inputs.build_without_publish) && failure() }}' in section(
    "Upload build reports on failure")
assert 'if: ${{ inputs.apply_to_main && !inputs.build_without_publish }}' in section(
    "Push fully verified candidate source to main")
assert 'if: ${{ inputs.apply_to_main && !inputs.build_without_publish && success() }}' in section(
    "Publish verified APKs")
assert text.count("git push origin HEAD:refs/heads/main") == 1
assert text.count("python3 scripts/build/publish-current-release.py") == 1
assert text.index("Stage Android TV release APKs") < text.index("Upload fully verified APKs") < text.index(
    "Push fully verified candidate source to main")
assert 'APPLY_TO_MAIN: ${{ inputs.apply_to_main }}' in text
print("PASS: build-only validates full APK pipeline and uploads private artifacts without main push or Release")
