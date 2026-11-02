#!/usr/bin/env python3
"""Check 5.8.7 Xray-only phone import, Nano assets, QR and removed PushActivity."""
import argparse
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"scripts/upstream/templates/xray.html.in"
DIALOG=ROOT/"scripts/upstream/templates/XrayPhoneImportDialog.java.in"
SETTING=ROOT/"app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingXrayActivity.java"

class Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[]
        self.actions=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if "id" in attrs: self.ids.append(attrs["id"])
        if tag=="form": self.actions.append(attrs)

page=HTML.read_text(encoding="utf-8")
dialog=DIALOG.read_text(encoding="utf-8")
setting=SETTING.read_text(encoding="utf-8")
parser=Markup()
parser.feed(page)
assert parser.ids.count("xray_link")==1
assert parser.ids.count("action_xray")==1
assert parser.ids.count("status")==1
assert len(parser.actions)==1
assert 'new URLSearchParams({do:"xray",link:value})' in page
assert 'fetch("/action"' in page
assert 'if(!response.ok)' in page
assert "link.value=\"\";" in page
assert "localStorage" not in page and "sessionStorage" not in page
assert not any(s in page for s in ("http://cdn","https://cdn", "https://fonts"))
assert 'String url = Server.get().getAddress() + "/xray.html";' in dialog
assert "QRCode.getBitmap(url, 240, 1)" in dialog
assert "address.setTextIsSelectable(true)" in dialog
assert "if (bitmap != null)" in dialog
assert "PushActivity" not in dialog
assert setting.count("PushActivity.start(this, 6);")==1
assert "XrayImportEvent" in setting

parser=argparse.ArgumentParser()
parser.add_argument("--upstream",type=Path)
parser.add_argument("--target")
args=parser.parse_args()
if bool(args.upstream)!=bool(args.target):
    parser.error("--upstream and --target must both be specified")
if args.upstream:
    import sys
    sys.path.insert(0,str(ROOT/"scripts/upstream"))
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    name="app/src/main/java/com/fongmi/android/tv/server/Nano.java"
    nano=blob(args.upstream,tree[name]).decode("utf-8")
    assert "return getAssets(url.substring(1));" in nano
    assert "InputStream is = Asset.open(path);" in nano
    name="app/src/main/java/com/fongmi/android/tv/server/process/Action.java"
    assert 'case "danmaku" -> onDanmaku(params);' in blob(args.upstream,tree[name]).decode()
    print("PASS public Nano serves new Xray-only page, existing Action route is adaptable")
print("PASS isolated Xray phone page and selectable QR fallback, no old PushActivity dependency")
