#!/usr/bin/env python3
"""Generate Leanback Xray controls and resources from official FongMi XML.

No old player controls or upstream strings are copied from the fork. Only
previously audited xray_* resources are brought across. Unknown upstream XML
structure or an upstream-owned name collision must stop the upgrade.
"""
import re
from xml.etree import ElementTree
from exo_adapters import one


def xray_strings(upstream, current_fork):
    if upstream.count("</resources>") != 1:
        raise ValueError("Official Leanback strings lost unique resources root")
    old=ElementTree.fromstring(current_fork)
    new=ElementTree.fromstring(upstream)
    if old.tag != "resources" or new.tag != "resources":
        raise ValueError("Unrecognized Leanback resource XML")
    old_items=[node for node in old if node.tag=="string" and node.get("name","").startswith("xray_")]
    old_names=[node.get("name") for node in old_items]
    if len(old_items)<20 or len(set(old_names)) != len(old_names):
        raise ValueError("Xray resource inventory is unexpectedly incomplete or duplicated")
    required={"xray_on","xray_off","xray_error","xray_starting",
              "xray_setting","xray_not_configured","xray_vod_required","xray_live_required"}
    if not required.issubset(set(old_names)):
        raise ValueError("Xray playback labels changed unexpectedly")
    upstream_names={node.get("name") for node in new}
    collision=set(old_names)&upstream_names
    if collision:
        raise ValueError("Upstream resource names now conflict with fork Xray labels: "+str(sorted(collision)))
    lines=[]
    for node in old_items:
        # Preserve the Android formatting syntax (%1$d, escaped newlines)
        # rather than serializing with ElementTree and altering backslashes.
        name=re.escape(node.get("name"))
        matches=re.findall(r'(?m)^[ \t]*<string[ \t]+name="'+name+r'"[^>]*>.*</string>[ \t]*$',current_fork)
        if len(matches)!=1:
            raise ValueError("Unsupported XML formatting for Xray label: "+node.get("name"))
        lines.append(matches[0].rstrip())
    result=upstream.replace("</resources>","\n"+("\n".join(lines))+"\n</resources>")
    ElementTree.fromstring(result)
    return result


def xray_control_layout(upstream):
    row='''        <com.google.android.material.textview.MaterialTextView
            android:id="@+id/player"
            style="@style/Control"
            android:layout_marginEnd="8dp"
            android:text="@string/play_exo" />'''
    xray='''

        <com.google.android.material.textview.MaterialTextView
            android:id="@+id/xray"
            style="@style/Control"
            android:layout_marginEnd="8dp"
            android:text="@string/xray_off" />'''
    result=one(upstream,row,row+xray,"official playback engine button")
    root=ElementTree.fromstring(result)
    ids=[node.get("{http://schemas.android.com/apk/res/android}id") for node in root.iter()]
    if ids.count("@+id/xray")!=1 or ids.count("@+id/player")!=1:
        raise ValueError("Duplicate Xray/player controls in Leanback UI")
    if "@+id/decoder" not in ids:
        raise ValueError("New upstream decoder/player action row unexpectedly removed")
    return result
