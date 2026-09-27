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

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: build hygiene guards are clean")
