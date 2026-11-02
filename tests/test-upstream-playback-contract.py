#!/usr/bin/env python3
"""Test actual upgraded Xray transport guard and its failure detection."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/upstream/verify_playback.py"
spec = importlib.util.spec_from_file_location("fingmi_playback_contract", MODULE)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

sources = {name: (ROOT / name).read_text(encoding="utf-8")
           for name in policy.REQUIRED}
assert policy.audit(sources) == [], "Current-main has already lost Xray wiring"

for path, anchors in policy.REQUIRED.items():
    # A missing file must be blocked before any native rebuild.
    missing = dict(sources)
    del missing[path]
    assert any(path in e for e in policy.audit(missing)), f"Lost file accepted: {path}"
    # Every individual required call site must be fail-closed, not just the
    # combined presence of a media factory or Xray control.
    for needle in anchors:
        modified = dict(sources)
        modified[path] = sources[path].replace(needle, "")
        errors = policy.audit(modified)
        assert any(path in e and needle in e for e in errors), f"Lost Xray hook accepted: {path}: {needle}"


# A new upstream version selects a genuinely different contract. It must
# never be allowed to pass just because the old 5.6.3 strings are still around.
assert policy.required_for_version('versionName "v5.6.3-xray.1"') is policy.REQUIRED
assert policy.required_for_version('versionName "v5.8.7-xray.1"') is policy.REQUIRED_587
assert policy.required_for_version('versionName "v5.9.0-xray.1"') is policy.REQUIRED_587
try:
    policy.required_for_version('versionName "latest"')
    raise AssertionError("unknown future version accepted")
except ValueError:
    pass
# Synthesize the *expected* post-upgrade source shapes. Fail if any individual
# Xray or side-request hook disappears, even in a newer upstream component.
candidate = {name: "\n".join(anchors)
             for name, anchors in policy.REQUIRED_587.items()}
assert policy.audit(candidate, policy.REQUIRED_587) == []
for path, anchors in policy.REQUIRED_587.items():
    for needle in anchors:
        broken = dict(candidate)
        broken[path] = broken[path].replace(needle, "")
        assert any(path in reason and needle in reason
                   for reason in policy.audit(broken, policy.REQUIRED_587)), (path, needle)
# The current local 5.6.3 source MUST fail the new upstream contract.
missing_new = {name: (ROOT / name).read_text(encoding="utf-8")
               if (ROOT / name).is_file() else None
               for name in policy.REQUIRED_587}
assert policy.audit(missing_new, policy.REQUIRED_587), "Never accept 5.6.3 as upgraded"

print(f"PASS Xray integration contract guard: {len(policy.REQUIRED)} real source files and missing-hook cases")
