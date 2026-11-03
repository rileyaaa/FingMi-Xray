#!/usr/bin/env python3
"""Verify upstream-first TV action buttons and three Xray-only translations."""
import argparse
from pathlib import Path
import sys
from xml.etree import ElementTree
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"scripts/upstream"))
from xray_resources import xray_strings,xray_control_layout

ROOT=Path(__file__).resolve().parents[3]
LOCALES=(
    "app/src/leanback/res/values/strings.xml",
    "app/src/leanback/res/values-zh-rCN/strings.xml",
    "app/src/leanback/res/values-zh-rTW/strings.xml",
)
LAYOUTS=(
    "app/src/leanback/res/layout/view_control_live_action.xml",
    "app/src/leanback/res/layout/view_control_vod_action.xml",
)
for rel in LOCALES:
    old=(ROOT/rel).read_text(encoding="utf-8")
    official='<resources>\n    <string name="new_upstream_setting">New</string>\n</resources>\n'
    merged=xray_strings(official,old)
    root=ElementTree.fromstring(merged)
    names=[node.attrib.get("name") for node in root]
    assert "new_upstream_setting" in names
    assert "xray_on" in names and "xray_off" in names and "xray_setting" in names
    assert names.count("xray_on")==1
    assert len([x for x in names if x.startswith("xray_")])>=20
    conflict=official.replace("new_upstream_setting","xray_on")
    try: xray_strings(conflict,old)
    except ValueError: pass
    else: raise AssertionError("Overlapping official Xray strings must stop: "+rel)

synthetic='''<HorizontalScrollView xmlns:android="http://schemas.android.com/apk/res/android"
xmlns:tools="http://schemas.android.com/tools">
<androidx.appcompat.widget.LinearLayoutCompat>
        <com.google.android.material.textview.MaterialTextView
            android:id="@+id/player"
            style="@style/Control"
            android:layout_marginEnd="8dp"
            android:text="@string/play_exo" />
        <com.google.android.material.textview.MaterialTextView
            android:id="@+id/decoder"
            style="@style/Control" />
</androidx.appcompat.widget.LinearLayoutCompat>
</HorizontalScrollView>'''
out=xray_control_layout(synthetic)
ids=[e.get("{http://schemas.android.com/apk/res/android}id") for e in ElementTree.fromstring(out).iter()]
assert ids.count("@+id/xray")==1 and ids.count("@+id/player")==1
assert ids.count("@+id/decoder")==1
assert 'android:text="@string/xray_off"' in out
try: xray_control_layout(synthetic.replace("play_exo","play_other"))
except ValueError: pass
else: raise AssertionError("Unknown source UI control accepted")

p=argparse.ArgumentParser()
p.add_argument("--upstream",type=Path)
p.add_argument("--target")
args=p.parse_args()
if bool(args.upstream)!=bool(args.target):p.error("--upstream/--target required together")
if args.upstream:
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    for name in LOCALES:
        assert name in tree
        content=blob(args.upstream,tree[name]).decode("utf-8")
        translated=xray_strings(content,(ROOT/name).read_text(encoding="utf-8"))
        ElementTree.fromstring(translated)
    for name in LAYOUTS:
        assert name in tree
        original=blob(args.upstream,tree[name]).decode("utf-8")
        generated=xray_control_layout(original)
        assert generated!=original
    print("PASS official Leanback actions and Xray translations at "+args.target)
print("PASS 3 Xray locales, 2 upstream action rows, XML parsing, and collision guards")
