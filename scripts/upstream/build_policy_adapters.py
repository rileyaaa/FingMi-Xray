#!/usr/bin/env python3
"""Version 5.8.7 official build/manifest + minimal fork safety policy overlays."""
from xml.etree import ElementTree
from exo_adapters import one

FORK_IGNORE=(
    "/recovery/work/",
    "/recovery/evidence/",
    "/libxray/libs/libXray.aar",
    "/app/libs/media3-container-1.11.0.aar",
    "__pycache__/",
    "*.py[cod]",
)

def gitignore(s):
    if not s or not s.endswith("\n"): raise ValueError("Unknown official .gitignore shape")
    additions=[p for p in FORK_IGNORE if p not in s.splitlines()]
    return s+("\n# Local Xray / TV recovery generated outputs\n"+"\n".join(additions)+"\n" if additions else "")


def proguard(s):
    if "-dontwarn" not in s or "-keep" not in s:
        raise ValueError("Official ProGuard config shape changed")
    if "-keep class libXray.**" in s or "-keep class go.**" in s:
        raise ValueError("Official R8 already owns Xray JNI keep policy; review deduplication")
    return s.rstrip()+"""

# Xray gomobile JNI bindings are invoked by native code; do not obfuscate.
-keep class libXray.** { *; }
-keep class go.** { *; }
"""


def leanback_manifest(s):
    row='''        <activity
            android:name=".ui.activity.SettingActivity"
            android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation"
            android:screenOrientation="sensorLandscape" />'''
    new='''

        <activity
            android:name=".ui.activity.SettingXrayActivity"
            android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation"
            android:screenOrientation="sensorLandscape" />'''
    s=one(s,row,row+new,"Leanback Xray settings Activity")
    root=ElementTree.fromstring(s)
    android="{http://schemas.android.com/apk/res/android}"
    activities=[x.get(android+"name") for x in root.findall("./application/activity")]
    if activities.count(".ui.activity.SettingXrayActivity")!=1:
        raise ValueError("Missing unique Xray settings Activity declaration")
    if ".ui.activity.PushActivity" in activities:
        raise ValueError("Obsolete upstream PushActivity must not be retained")
    return s


def main_manifest(s):
    # The released Xray fork intentionally cannot self-install an upstream
    # unsigned/foreign APK. Preserve all other new upstream permissions.
    s=one(s,
        '    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />\n',
        "", "disable upstream APK installation permission")
    root=ElementTree.fromstring(s)
    names=[x.get("{http://schemas.android.com/apk/res/android}name")
           for x in root.findall("./uses-permission")]
    if "android.permission.REQUEST_INSTALL_PACKAGES" in names:
        raise ValueError("Fork must not request upstream install-APK privilege")
    if "android.permission.INTERNET" not in names:
        raise ValueError("Official Android networking permission missing")
    return s
