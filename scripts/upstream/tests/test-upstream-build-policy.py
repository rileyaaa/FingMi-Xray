#!/usr/bin/env python3
"""Official 5.8.7 manifest + Xray JNI/installer policy overlay regression."""
import argparse
from pathlib import Path
import sys
from xml.etree import ElementTree
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"scripts/upstream"))
from build_policy_adapters import gitignore,proguard,leanback_manifest,main_manifest


def rejects(fn,source):
    try: fn(source)
    except ValueError: return
    raise AssertionError("Unknown upstream "+fn.__name__+" accepted")

ignore=".idea/\n.gradle/\n"
new=gitignore(ignore)
for required in ("/recovery/work/","/recovery/evidence/",
                 "/libxray/libs/libXray.aar","/app/libs/media3-container-1.11.0.aar",
                 "__pycache__/","*.py[cod]"):
    assert required in new
assert gitignore(new)==new

r8="-dontwarn some.module.Class\n-keep class upstream.Class { *; }\n"
new=proguard(r8)
assert "-keep class libXray.** { *; }" in new
assert "-keep class go.** { *; }" in new
rejects(proguard,new)

leanback='''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application>
        <activity
            android:name=".ui.activity.SettingActivity"
            android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation"
            android:screenOrientation="sensorLandscape" />
        <activity android:name=".ui.activity.ModuleActivity" />
    </application>
</manifest>'''
new=leanback_manifest(leanback)
names=[a.attrib.get("{http://schemas.android.com/apk/res/android}name")
       for a in ElementTree.fromstring(new).findall("./application/activity")]
assert names.count(".ui.activity.SettingXrayActivity")==1
assert ".ui.activity.ModuleActivity" in names
rejects(leanback_manifest,leanback.replace(".ui.activity.SettingActivity", ".ui.activity.OtherSettings"))

# The real public 5.8.7 TV flavor adds a boot receiver and boot permission.
# They must both be removed without losing other upstream TV declarations.
boot_permission='    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\n'
boot_receiver="""        <receiver
            android:name=".receiver.BootReceiver"
            android:exported="true"
            android:priority="999">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.QUICKBOOT_POWERON" />
            </intent-filter>
        </receiver>

"""
booted=leanback.replace("    <application>",boot_permission+"    <application>")
booted=booted.replace("    </application>",boot_receiver+"    </application>")
clean=leanback_manifest(booted)
ElementTree.fromstring(clean)
for forbidden in ("android.permission.RECEIVE_BOOT_COMPLETED",".receiver.BootReceiver",
                  "android.intent.action.BOOT_COMPLETED","android.intent.action.QUICKBOOT_POWERON"):
    assert forbidden not in clean,forbidden
assert 'android:name=".ui.activity.ModuleActivity"' in clean
assert 'android:name=".ui.activity.SettingXrayActivity"' in clean
rejects(leanback_manifest,booted.replace(boot_receiver,""))
rejects(leanback_manifest,booted.replace('android:priority="999"','android:priority="500"'))


main='''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
    <uses-permission android:name="android.permission.REQUEST_DELETE_PACKAGES" />
    <application />
</manifest>'''
new=main_manifest(main)
assert "REQUEST_INSTALL_PACKAGES" not in new
assert "REQUEST_DELETE_PACKAGES" in new
assert "android.permission.INTERNET" in new
rejects(main_manifest,main.replace("REQUEST_INSTALL_PACKAGES","ANOTHER_PERMISSION"))

# Guard the version-aware TV recovery SHA baseline before generating the
# candidate: official 5.8.7 legitimately changes seven 5.6.3 source blobs.
# Parse only two literal tables from the guard; do not import the guard's
# top-level Java/SKD test harness during this cheap upstream preflight.
import ast
scope_script=(Path(__file__).resolve().parents[3] / "tests/test-tv-network-recovery.py").read_text(encoding="utf-8")
scope_ast=ast.parse(scope_script)
pins={}
for node in scope_ast.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        if node.targets[0].id in ("UPSTREAM_EXACT_BLOBS","UPSTREAM_EXACT_BLOBS_587"):
            pins[node.targets[0].id]=node.value
old_blobs=ast.literal_eval(pins["UPSTREAM_EXACT_BLOBS"])
new_blobs=dict(old_blobs)
new_table=pins["UPSTREAM_EXACT_BLOBS_587"]
for key,value in zip(new_table.keys,new_table.values):
    if key is not None:
        new_blobs[ast.literal_eval(key)]=ast.literal_eval(value)
assert len(old_blobs)==len(new_blobs)==9
assert sum(old_blobs[path]!=new_blobs[path] for path in old_blobs)==7
assert "elif upstream_version == \"5.8.7\":" in scope_script
assert "pinned_source_blobs = UPSTREAM_EXACT_BLOBS_587" in scope_script

parser=argparse.ArgumentParser()
parser.add_argument("--upstream",type=Path)
parser.add_argument("--target")
args=parser.parse_args()
if bool(args.upstream)!=bool(args.target):
    parser.error("both official Git Tree arguments required")
if args.upstream:
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    for path, expected in new_blobs.items():
        assert path in tree, "Official TV recovery scope missing: "+path
        assert tree[path][1]==expected, ("Official 5.8.7 business source diverged: "
                                       +path+" expected="+expected+" actual="+tree[path][1])
    for name,fn in (
        (".gitignore",gitignore),
        ("app/proguard-rules.pro",proguard),
        ("app/src/leanback/AndroidManifest.xml",leanback_manifest),
        ("app/src/main/AndroidManifest.xml",main_manifest),
    ):
        if name not in tree: raise AssertionError("Official build policy file missing "+name)
        raw=blob(args.upstream,tree[name]).decode("utf-8")
        transformed=fn(raw)
        assert transformed and len(transformed)>10,name
        if name=="app/src/leanback/AndroidManifest.xml":
            for forbidden in ("android.permission.RECEIVE_BOOT_COMPLETED", ".receiver.BootReceiver",
                              "android.intent.action.BOOT_COMPLETED", "android.intent.action.QUICKBOOT_POWERON"):
                assert forbidden not in transformed,forbidden
    print("PASS all 4 public build policy adapters "+args.target)
print("PASS Xray JNI, local generated outputs, TV settings and installer permissions")
