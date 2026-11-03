#!/usr/bin/env python3
"""SDK/AC-free check that dedicated upstream tests and manual entrypoints stay together."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
UP = ROOT / "scripts/upstream"
TESTS = UP / "tests"

MIGRATED = [
    'test-upstream-activity-adapters.py',
    'test-upstream-build-only-workflow.py',
    'test-upstream-build-policy.py',
    'test-upstream-clean-checkout.py',
    'test-upstream-exo-adapters.py',
    'test-upstream-full-source-guards.py',
    'test-upstream-live-metadata.py',
    'test-upstream-media3-source-contract.py',
    'test-upstream-mode-runtime.py',
    'test-upstream-phone-import.py',
    'test-upstream-playback-contract.py',
    'test-upstream-playback-ownership.py',
    'test-upstream-prepare.py',
    'test-upstream-real-hooks-mock.py',
    'test-upstream-real-hooks.py',
    'test-upstream-recovery-adapters.py',
    'test-upstream-sha-input.py',
    'test-upstream-side-gate.py',
    'test-upstream-side-request-integration.py',
    'test-upstream-side-request-lifecycle.py',
    'test-upstream-side-requests.py',
    'test-upstream-sync.py',
    'test-upstream-vendor-whitespace.py',
    'test-upstream-workflow-shell.py',
    'test-upstream-xray-adapters.py',
    'test-upstream-xray-auth.py',
    'test-upstream-xray-resources.py',
    'test-xray-artwork-loader.py',
    'test-xray-guarded-data-source.py',
    'test-xray-playback-routing.py'
]
for name in MIGRATED:
    assert (TESTS / name).is_file(), "Moved upgrade test is missing: " + name
    assert not (ROOT / "tests" / name).exists(), "Upgrade-only test returned to shared tests/: " + name

assert (ROOT / "tests/test-upstream-update-disabled.py").is_file()
assert (ROOT / "tests/test-resolve-release-tag.py").is_file()
assert (ROOT / "scripts/build/resolve-release-tag.py").is_file()
assert (UP / "baseline.json").is_file()
assert (UP / "fork_scope.json").is_file()
assert (UP / "README.md").is_file()

workflows = (
    "current-main-build.yml",
    "publish-current-main-test-release.yml",
    "resume-verified-release.yml",
    "manual-upstream-sync.yml",
)
for name in workflows:
    s = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
    match = re.search(r"(?m)^on:\n((?:[ \t]+[^\n]*\n|\n)*)", s)
    assert match is not None
    assert re.findall(r"(?m)^  (\w+):", match.group(1)) == ["workflow_dispatch"], name
manual = (ROOT / ".github/workflows/manual-upstream-sync.yml").read_text(encoding="utf-8")
assert "python3 scripts/upstream/tests/test-upstream-layout.py" in manual
assert "python3 tests/test-upstream-" not in manual.replace(
    "python3 tests/test-upstream-update-disabled.py", "")
for rel in set(re.findall(r"(?m)\bpython3 (scripts/upstream/(?:tests/)?[\w.-]+\.py)", manual)):
    assert (ROOT / rel).is_file(), "One-click YAML references missing file: " + rel
for name in MIGRATED:
    assert name != "test-upstream-update-disabled.py"
print(f"PASS: {len(MIGRATED)} upgrade-only tests consolidated; all four Actions manual-only")
