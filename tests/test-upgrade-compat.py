#!/usr/bin/env python3
"""Guard compatibility with persisted state from v5.6.0-xray.5."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subtitle = (ROOT / "app/src/main/java/com/fongmi/android/tv/setting/SubtitleSetting.java").read_text(
    encoding="utf-8"
)

required = (
    'int legacy = Prefers.getBoolean("caption") ? STYLE_SYSTEM : STYLE_ORIGINAL;',
    'int migrated = Prefers.getInt("subtitle_style_source", legacy);',
    'Prefers.getInt("subtitle_style", migrated)',
)
for needle in required:
    if needle not in subtitle:
        raise SystemExit(f"legacy subtitle style preference migration is missing: {needle}")

print("PASS: persisted-state upgrade compatibility guards are clean")
