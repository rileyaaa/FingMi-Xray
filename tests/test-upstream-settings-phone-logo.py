#!/usr/bin/env python3
"""Check real staged 5.9 settings, phone input and channel-logo contracts.

No Android/Media3 build claim: run candidate Java adapter against deterministic
view/Glide boundaries, actual JavaScript functions against a mock HTTP transport,
and compare upstream XML/resource/navigation structures.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/upstream-adaptation"))
from prepare_candidate import LOCK, blob, guard_fork, overlay, verified_checkout
from verify_recovery_batch import method

LEAN = "app/src/leanback/"
ACT = LEAN+"java/com/fongmi/android/tv/ui/activity/"
CHANNEL = LEAN+"java/com/fongmi/android/tv/ui/adapter/ChannelAdapter.java"
ASSET = "app/src/main/assets/"
NS = "{http://schemas.android.com/apk/res/android}"

JAVA = r'''
import java.util.*;
import java.util.function.*;
@interface NonNull {}
class LayoutInflater {
    static LayoutInflater from(Object ignored) { return new LayoutInflater(); }
}
class ViewGroup { Object getContext() { return this; } }
class Logo { int clears; Object image; void setImageDrawable(Object value) { image = value; } }
class Label { void setText(String ignored) {} }
class View {
    boolean selected;
    void setSelected(boolean value) { selected = value; }
    void setRightListener(Runnable r) {}
    void setOnClickListener(Consumer<View> c) {}
    void setOnLongClickListener(Predicate<View> p) {}
}
class AdapterChannelBinding {
    final Logo logo = new Logo();
    final Label name = new Label(), number = new Label();
    final View root = new View();
    View getRoot() { return root; }
    static AdapterChannelBinding inflate(LayoutInflater l, ViewGroup g, boolean b) { return new AdapterChannelBinding(); }
}
class Channel {
    boolean selected;
    int loads;
    void loadLogo(Logo logo) { loads++; logo.image = this; }
    String getShow() { return "channel"; }
    String getNumber() { return "1"; }
    boolean isSelected() { return selected; }
    void setSelected(boolean value) { selected = value; }
}
class Glide {
    static Glide with(Logo logo) { return new Glide(); }
    void clear(Logo logo) { logo.clears++; logo.image = null; }
}
class RecyclerView {
    static class ViewHolder { final View view; ViewHolder(View v) { view = v; } }
    static abstract class Adapter<V extends ViewHolder> {
        int refreshes, selectionChanges;
        void notifyDataSetChanged() { refreshes++; }
        void notifyItemRemoved(int pos) {}
        void notifyItemChanged(int pos, Object payload) { selectionChanges++; }
        public abstract int getItemCount();
        public abstract V onCreateViewHolder(ViewGroup parent, int type);
        public abstract void onBindViewHolder(V holder, int position);
        public void onBindViewHolder(V holder, int position, List<Object> payloads) { onBindViewHolder(holder, position); }
        public void onAttachedToRecyclerView(RecyclerView view) {}
        public void onDetachedFromRecyclerView(RecyclerView view) {}
        public void onViewRecycled(V holder) {}
    }
    final List<ViewHolder> holders = new ArrayList<>();
    int getChildCount() { return holders.size(); }
    View getChildAt(int i) { return holders.get(i).view; }
    ViewHolder getChildViewHolder(View view) { return holders.stream().filter(h -> h.view == view).findFirst().orElseThrow(); }
}
__ACTUAL_ADAPTER__
class LogoHarness {
    static int count;
    static void check(boolean ok, String label) { count++; if (!ok) throw new AssertionError(label); }
    public static void main(String[] args) throws Exception {
        ChannelAdapter a = new ChannelAdapter(null);
        Channel first = new Channel(), second = new Channel();
        a.addAll(List.of(first, second));
        var one = a.onCreateViewHolder(new ViewGroup(), 0);
        var two = a.onCreateViewHolder(new ViewGroup(), 0);
        var field = one.getClass().getDeclaredField("binding");
        field.setAccessible(true);
        AdapterChannelBinding b1 = (AdapterChannelBinding)field.get(one), b2 = (AdapterChannelBinding)field.get(two);
        RecyclerView rv = new RecyclerView();
        rv.holders.add(one); a.onAttachedToRecyclerView(rv);
        a.onBindViewHolder(one, 0);
        check(first.loads == 1 && b1.logo.image == first, "normal load");
        a.setXrayLogoSuppressed(true);
        check(b1.logo.image == null && b1.logo.clears == 1, "clear already visible logo");
        a.onBindViewHolder(two, 1);
        check(second.loads == 0 && b2.logo.image == null, "suppress new logo");
        int before = a.refreshes;
        a.setXrayLogoSuppressed(true);
        check(a.refreshes == before, "idempotent suppression");
        a.setSelected(second);
        check(a.selectionChanges == 1 && second.selected, "upstream targeted selection");
        a.onBindViewHolder(two, 1, List.of(Boolean.TRUE));
        check(b2.root.selected && second.loads == 0, "selection payload never reloads logo");
        a.setXrayLogoSuppressed(false);
        a.onBindViewHolder(two, 1);
        check(second.loads == 1 && b2.logo.image == second, "normal load restored");
        a.onDetachedFromRecyclerView(rv);
        int clears = b1.logo.clears;
        a.setXrayLogoSuppressed(true);
        check(b1.logo.clears == clears, "detached recycler not touched");
        a.onViewRecycled(two);
        check(b2.logo.image == null, "upstream recycling clears logo");
        System.out.println("PASS actual channel adapter "+count+" assertions");
    }
}
'''

JS = r'''
const assert = require('node:assert/strict');
const nav = require(process.argv[2]), prior = require(process.argv[3]);
for (const route of ['', '?tab=search', '?tab=push', '?tab=play', '?tab=subtitles', '?tab=danmaku', '?tab=settings', '?tab=files&path=%2Fabc', '?tab=other']) {
    assert.deepEqual(nav.webRoute(route), prior.webRoute(route));
}
assert.deepEqual(nav.webRoute('?tab=xray'), {tab:'xray',panel:6,path:''});
assert.deepEqual(nav.webRoute('?tab=6'), {tab:'xray',panel:6,path:''});
assert.equal(nav.webPageUrl('xray'), '/?tab=xray');
assert.deepEqual(nav.remoteReturnRoute('?from=xray'), nav.webRoute('?tab=xray'));
const fields = { '#xray_link':'', '#xray_live_groups':'', '#xray_live_channels':'' };
const buttons = {action_xray:{disabled:false},action_xrayLiveRules:{disabled:false}};
const document = {getElementById:id=>buttons[id]};
let confirmations = true, requests = [], notices = [];
const confirm = () => confirmations;
const warnToast = value => notices.push(value);
const t = k => k;
const pendingActions = new Set();
function $(id) {
    return {val(value) { if (arguments.length) { fields[id] = value; return this; } return fields[id]; }};
}
$.ajax = options => {
    const state = {options};
    requests.push(state);
    return {done(fn){state.done=fn;return this;}, fail(fn){state.fail=fn;return this;}, always(fn){state.always=fn;return this;}};
};
function complete(success) { const r=requests.at(-1); (success?r.done:r.fail)(); r.always(); }
__ACTUAL_FUNCTIONS__
sendXray(); assert.equal(requests.length,0);
fields['#xray_link']='  vmess://synthetic  ';
sendXray(); assert.equal(requests.length,1);
assert.deepEqual(requests[0].options.data,{link:'vmess://synthetic',do:'xray'});
assert.equal(requests[0].options.url,'/action');
assert.equal(requests[0].options.type,'POST');
assert.equal(buttons.action_xray.disabled,true);
sendXray(); assert.equal(requests.length,1);
complete(false); assert.equal(fields['#xray_link'],'  vmess://synthetic  ');
assert.equal(buttons.action_xray.disabled,false);
sendXray(); fields['#xray_link']='trojan://new'; complete(true);
assert.equal(fields['#xray_link'],'trojan://new');
sendXray(); complete(true); assert.equal(fields['#xray_link'],'');
fields['#xray_live_groups']='  ';
fields['#xray_live_channels']=' ';
confirmations=false; let count=requests.length; sendXrayLiveRules(); assert.equal(requests.length,count);
confirmations=true; sendXrayLiveRules();
assert.deepEqual(requests.at(-1).options.data,{groups:'',channels:'',do:'xrayLiveRules'});
complete(false); assert.equal(notices.at(-1),'actionFailed');
fields['#xray_live_groups']=' 海外 ';
fields['#xray_live_channels']=' 東森* ';
sendXrayLiveRules();
assert.deepEqual(requests.at(-1).options.data,{groups:'海外',channels:'東森*',do:'xrayLiveRules'});
complete(true); assert.match(notices.at(-1),/确认并保存/);
assert.equal(fields['#xray_live_channels'],' 東森* ');
console.log('PASS actual phone routes, send success/failure, edit ownership, explicit blank rules, ordinary routes');
'''

def shape(node):
    return node.tag, node.attrib, (node.text or "").strip(), [shape(x) for x in node]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-tv", type=Path, required=True)
    p.add_argument("--tv", type=Path, required=True)
    a=p.parse_args()
    old,tv=a.old_tv.resolve(),a.tv.resolve()
    guard_fork()
    verified_checkout(old,"old_tv")
    verified_checkout(tv,"tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-settings-phone-logo-") as tmp:
        work=Path(tmp)
        candidate=work/"candidate"
        conflicts,manual=overlay(old,tv,candidate)
        paths=[CHANNEL,ACT+"SettingActivity.java",ACT+"SettingXrayActivity.java",LEAN+"res/layout/activity_setting.xml",
               ASSET+"index.html",ASSET+"js/script.js",ASSET+"js/navigation.js",ASSET+"js/i18n.js",ASSET+"css/ui.css"]
        for path in paths:
            row=next(x for x in LOCK["fork_scope"] if x["path"]==path)
            assert path not in conflicts+manual and blob(candidate/path)==row["resolved"],path
        assert not (candidate/(ACT+"PushActivity.java")).exists()
        assert ACT+"PushActivity.java" not in conflicts
        setting=(candidate/paths[1]).read_text()
        source=(tv/paths[1]).read_text()
        fork=(ROOT/paths[1]).read_text()
        for sig in ("private void onXray(", "private void setXrayText()", "protected void onResume()"):
            assert method(setting,sig)==method(fork,sig),sig
        assert "mBinding.xray.setOnClickListener(this::onXray);" in setting
        assert "mBinding.module.setOnClickListener(view -> ModuleActivity.start(this));" in setting
        assert "Updater." not in setting and "mBinding.version.setOnClickListener" not in setting
        for sig in ("private void setOtherText()", "private void setCacheText()", "public void setConfig(", "private void onPlayer(", "private void onDanmaku("):
            assert method(setting,sig)==method(source,sig),sig
        phone=(candidate/paths[2]).read_text()
        oldphone=(ROOT/paths[2]).read_text()
        assert method(phone,"private void onPhone(")=='private void onPhone(View view) {\n        LocalConnectDialog.show(this, "xray");\n    }'
        for sig in ("public void onXrayImportEvent(", "public void onXrayLiveRulesEvent("):
            assert method(phone,sig)==method(oldphone,sig),sig
        connect=(candidate/"app/src/main/java/com/fongmi/android/tv/ui/dialog/LocalConnectDialog.java").read_text()
        assert "PermissionUtil.requestLocalNetwork" in connect and "Server.get().getPageAddress(tab)" in connect
        path=paths[3]
        before=ET.parse(tv/path).getroot()
        after=ET.parse(candidate/path).getroot()
        nodes={x.get(NS+"id"):x for x in after.iter() if x.get(NS+"id")}
        assert "@+id/xray" in nodes and "@+id/xrayText" in nodes
        for parent in after.iter():
            if nodes["@+id/xray"] in list(parent):
                parent.remove(nodes["@+id/xray"])
                break
        version=nodes["@+id/version"]
        for key in ("focusable","focusableInTouchMode"):
            assert version.get(NS+key)=="false"
            version.set(NS+key,"true")
        assert shape(before)==shape(after),"ordinary settings XML changed"
        adapter=(candidate/CHANNEL).read_text()
        original=(tv/CHANNEL).read_text()
        for sig in ("public void setSelected(", "private void updateSelection(", "public void onBindViewHolder(@NonNull ViewHolder holder, int position, @NonNull List<Object> payloads)", "public void onViewRecycled("):
            assert method(adapter,sig)==method(original,sig),sig
        adapter=re.sub(r"(?m)^(?:package|import) .+;\s*$","",adapter).replace("public class ChannelAdapter","class ChannelAdapter",1)
        java=JAVA.replace("__ACTUAL_ADAPTER__",adapter)
        jfile=work/"LogoHarness.java"
        def run_java(code, failure=None):
            jfile.write_text(code)
            subprocess.run(["javac","--release","17",str(jfile)],check=True)
            result=subprocess.run(["java","-cp",str(work),"LogoHarness"],text=True,capture_output=True)
            if failure:
                assert result.returncode!=0 and "AssertionError: "+failure in result.stderr,result.stderr
            else:
                assert result.returncode==0,result.stderr
                print(result.stdout.strip(),flush=True)
        run_java(java)
        run_java(java.replace("if (suppressed && mRecyclerView != null)","if (false)"),"clear already visible logo")
        run_java(java.replace("if (xrayLogoSuppressed) {","if (false) {"),"suppress new logo")
        html=(candidate/(ASSET+"index.html")).read_text()
        for ident in ("panel6","tab6","xray_link","xray_live_groups","xray_live_channels","action_xray","action_xrayLiveRules"):
            assert html.count('id="'+ident+'"')==1,ident
        assert 'aria-controls="panel6"' in html and 'maxlength="4096"' in html
        source=(candidate/(ASSET+"js/script.js")).read_text()
        assert "for (let i = 1; i <= 6; i++)" in source
        def function(name):
            pos=source.index("function "+name+"(")
            end=source.index("\nfunction ",pos+1)
            return source[pos:end]
        funcs="\n".join(function(name) for name in ("doAction","sendXray","sendXrayLiveRules"))
        js=JS.replace("__ACTUAL_FUNCTIONS__",funcs)
        jsfile=work/"phone.cjs"
        jsfile.write_text(js)
        subprocess.run(["node",str(jsfile),str(candidate/(ASSET+"js/navigation.js")),str(tv/(ASSET+"js/navigation.js"))],check=True)
        # A false-success implementation must not pass the actual regression.
        jsfile.write_text(js.replace("if ($('#xray_link').val().trim() === link) $('#xray_link').val('');","$('#xray_link').val('');"))
        bad=subprocess.run(["node",str(jsfile),str(candidate/(ASSET+"js/navigation.js")),str(tv/(ASSET+"js/navigation.js"))],text=True,capture_output=True)
        assert bad.returncode!=0 and "trojan://new" in bad.stderr,bad.stderr
        print("PASS settings structure, phone route ownership and three negative controls",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review",flush=True)

if __name__=="__main__":
    main()
