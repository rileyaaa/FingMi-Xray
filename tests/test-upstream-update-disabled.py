#!/usr/bin/env python3
"""Verify the Xray fork cannot silently self-update from upstream FongMi releases."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
UPDATER = APP / "src/main/java/com/fongmi/android/tv/Updater.java"
MANIFEST = APP / "src/main/AndroidManifest.xml"

updater = UPDATER.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")

errors = []

if "android.permission.REQUEST_INSTALL_PACKAGES" in manifest:
    errors.append("app manifest still requests REQUEST_INSTALL_PACKAGES")

for forbidden in ("Github.", "Download.", "FileUtil.openFile", "OkHttp", "update.apk"):
    if forbidden in updater:
        errors.append(f"Updater.java still contains active upstream update code: {forbidden}")

if "Intentionally disabled" not in updater:
    errors.append("Updater.java is not the fork-safe no-op implementation")

for source_root in (APP / "src/main", APP / "src/leanback"):
    for path in sorted(source_root.rglob("*.java")):
        if path == UPDATER:
            continue
        text = path.read_text(encoding="utf-8")
        if "Updater.create()" in text:
            errors.append(f"{path.relative_to(ROOT)} still invokes Updater.create()")
        if path.name != "Github.java" and ("Github.getJson(" in text or "Github.getApk(" in text):
            errors.append(f"{path.relative_to(ROOT)} still calls the upstream release endpoint")

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: upstream self-update is disabled and package-install permission is absent")
