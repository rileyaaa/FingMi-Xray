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
        modified[path] = sources[path].replace(needle, "", 1)
        errors = policy.audit(modified)
        assert any(path in e and needle in e for e in errors), f"Lost Xray hook accepted: {path}: {needle}"

print(f"PASS Xray integration contract guard: {len(policy.REQUIRED)} real source files and missing-hook cases")
