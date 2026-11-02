#!/usr/bin/env python3
"""Test actual upgraded Xray transport guard and its failure detection."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/upstream/verify_playback.py"
spec = importlib.util.spec_from_file_location("fingmi_playback_contract", MODULE)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

gradle = (ROOT / "app/build.gradle").read_text(encoding="utf-8")
required = policy.required_for_version(gradle)
sources = {name: (ROOT / name).read_text(encoding="utf-8") if (ROOT / name).is_file() else None
           for name in required}
assert policy.audit(sources, required) == [], "Current upstream source has lost Xray wiring"

for path, anchors in required.items():
    # A missing file must be blocked before any native rebuild.
    missing = dict(sources)
    del missing[path]
    assert any(path in e for e in policy.audit(missing, required)), f"Lost file accepted: {path}"
    # Every individual required call site must be fail-closed, not just the
    # combined presence of a media factory or Xray control.
    for needle in anchors:
        modified = dict(sources)
        modified[path] = sources[path].replace(needle, "")
        errors = policy.audit(modified, required)
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
service_path = "app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java"
subtitle_path = "app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java"
browse_order = """private boolean setBrowseItem() {
    player.clearPlaybackProxyPreservingState();
    if (!player.browse(result)) return false;
    if (!hadXray && binding != null) binding.onReplaced().run();
}
private void redirectPush() {}
"""
candidate[service_path] += "\n" + browse_order
subtitle_call = "return XraySideRequestGate.newCall(builder.build().toString(), TAG);"
candidate[subtitle_path] += "\n" + (subtitle_call + "\n") * 2
assert policy.audit(candidate, policy.REQUIRED_587) == []

# Altering the takeover order is a network-identity leak even when all
# required method names still appear elsewhere in the source.
bad_order = dict(candidate)
bad_order[service_path] = bad_order[service_path].replace(
    "    player.clearPlaybackProxyPreservingState();\n    if (!player.browse(result))",
    "    if (!player.browse(result)) return false;\n    player.clearPlaybackProxyPreservingState();\n    if (false)")
assert any("BEFORE browse" in reason
           for reason in policy.audit(bad_order, policy.REQUIRED_587))
one_subtitle = dict(candidate)
one_subtitle[subtitle_path] = one_subtitle[subtitle_path].replace(subtitle_call, "", 1)
assert any("both subtitle" in reason
           for reason in policy.audit(one_subtitle, policy.REQUIRED_587))
for path, anchors in policy.REQUIRED_587.items():
    for needle in anchors:
        broken = dict(candidate)
        broken[path] = broken[path].replace(needle, "")
        assert any(path in reason and needle in reason
                   for reason in policy.audit(broken, policy.REQUIRED_587)), (path, needle)
# A production source tree must never pass the other version's contract by
# accident: the guard always selects from the actual app version.
other = policy.REQUIRED_587 if required is policy.REQUIRED else policy.REQUIRED
other_sources = {name: (ROOT / name).read_text(encoding="utf-8") if (ROOT / name).is_file() else None
                 for name in other}
assert policy.audit(other_sources, other), "Different-version playback contract unexpectedly passed"

print(f"PASS Xray integration contract guard: {len(required)} real source files and missing-hook cases")
