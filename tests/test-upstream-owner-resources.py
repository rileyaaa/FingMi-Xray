#!/usr/bin/env python3
"""Verify 5.9 shared playback owner, VOD cancellation, phone input and TV resources.

Exact generated sources; deterministic JVM stubs, XML structure, not full Android linkage.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/upstream-adaptation"))
from prepare_candidate import LOCK, blob, guard_fork, overlay, verified_checkout
from verify_recovery_batch import method

BASE = "app/src/main/java/com/fongmi/android/tv/"
LEAN = "app/src/leanback/"
NS = "{http://schemas.android.com/apk/res/android}"
FIXTURE = r'''
import java.util.*;
@interface Nullable {}
class Client {}
class OkHttp {
    static final Client ordinary = new Client();
    static Client player() { return ordinary; }
}
class Uri {
    final boolean live;
    Uri(boolean live) { this.live = live; }
}
class LiveDanmaku {
    Uri source;
    static boolean isLive(Uri uri) { return uri != null && uri.live; }
    void setDataSource(Uri uri) { source = uri; }
}
class DanmakuController {
    Client client;
    Uri source;
    void setOkHttpClient(Client c) { client = c; }
    void setDataSource(Uri uri) { source = uri; }
}
class View {
    boolean attached = true;
    Object getPlayer() { return attached ? this : null; }
    void setPlayer(Object value) { attached = value != null; }
}
class State { void setValue(Object value) {} }
class PlayerManager {
    Client proxy;
    boolean suspended;
    boolean isXrayPlaybackSuspended() { return suspended; }
    Client getPlaybackHttpClient(Client fallback) { return proxy == null ? fallback : proxy; }
}
class PlaybackHost {
    Object mService;
    boolean playbackReplaced, web, pip, finished;
    Object pendingResume = new Object();
    final State playbackPlayerState = new State();
    final View view = new View(), seek = new View();
    final PlayerManager manager = new PlayerManager();
    final DanmakuController danmakuController = new DanmakuController();
    final LiveDanmaku liveDanmaku = new LiveDanmaku();
    int order, retiredOrder, detachedOrder;
    PlayerManager player() { return manager; }
    View getPlayerView() { return view; }
    View getSeekView() { return seek; }
    boolean isWebPlaybackActive() { return web; }
    void pauseWebPlaybackForResume() { web = false; }
    void detachPlayerView() { detachedOrder = ++order; view.setPlayer(null); liveDanmaku.setDataSource(null); }
    boolean isInPictureInPictureMode() { return pip; }
    void finish() { finished = true; }
    protected void onXrayBindingReplaced() { retiredOrder = ++order; }
    __PLAYBACK__
}
enum TaskType { DETAIL, PLAYBACK, PRELOAD, OTHER }
class Tasks {
    final List<TaskType> cancelled = new ArrayList<>();
    void cancel(TaskType type) { cancelled.add(type); }
}
class VideoHost {
    final Tasks requestTasks = new Tasks();
    __VIDEO__
}
class TextUtils { static boolean isEmpty(String s) { return s == null || s.isEmpty(); } }
class XrayLiveAutoRules { static final int MAX_LENGTH = 4096; }
class XrayImportEvent {
    static String link;
    static void post(String value) { link = value; }
}
class XrayLiveRulesEvent {
    static boolean applied;
    static int calls;
    static String groups, channels;
    static boolean post(String g, String c) { calls++; groups = g; channels = c; return applied; }
}
class Response {
    enum Status { BAD_REQUEST }
    final boolean ok;
    Response(boolean ok) { this.ok = ok; }
}
class Nano {
    static Response ok() { return new Response(true); }
    static Response error(Response.Status status, String message) { return new Response(false); }
}
class PhoneHost {
    __ACTION__
    void send(Map<String,String> params) { onXray(params); }
    Response rules(Map<String,String> params) { return onXrayLiveRules(params); }
}
public class OwnerHarness {
    static int count;
    static void check(boolean value, String message) {
        count++;
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        PlaybackHost host = new PlaybackHost();
        Uri file = new Uri(false), live = new Uri(true);
        host.updatePlaybackDanmakuClient();
        check(host.danmakuController.client == OkHttp.ordinary, "unbound normal client");
        host.mService = new Object();
        host.updatePlaybackDanmakuClient();
        check(host.danmakuController.client == OkHttp.ordinary, "bound normal client");
        host.setSource(file);
        check(host.danmakuController.source == file && host.liveDanmaku.source == null, "ordinary static source");
        host.setSource(live);
        check(host.danmakuController.source == null && host.liveDanmaku.source == live, "upstream live source");
        host.clearPlaybackDanmakuSource();
        check(host.danmakuController.source == null && host.liveDanmaku.source == null, "clear both source kinds");
        host.manager.proxy = new Client();
        host.updatePlaybackDanmakuClient();
        check(host.danmakuController.client == host.manager.proxy, "explicit playback client");
        host.setSource(file);
        host.manager.suspended = true; host.manager.proxy = null;
        host.updatePlaybackDanmakuClient();
        check(host.danmakuController.source == null, "suspension clears retained file");
        host.setSource(file);
        check(host.danmakuController.source == null && host.liveDanmaku.source == null, "suspended cannot fetch file");
        host.setSource(live);
        check(host.liveDanmaku.source == null, "suspended cannot subscribe");
        host.manager.suspended = false;
        host.web = true; host.pip = true;
        host.replace();
        check(host.playbackReplaced && host.retiredOrder > 0 && host.retiredOrder < host.detachedOrder, "old owner retired before detach");
        check(host.pendingResume == null && !host.web && !host.seek.attached && host.finished, "upstream replacement cleanup");
        VideoHost video = new VideoHost();
        video.cancelXrayTransitionRequests();
        check(video.requestTasks.cancelled.equals(List.of(TaskType.DETAIL, TaskType.PLAYBACK, TaskType.PRELOAD)), "exact VOD cancellation lanes");
        PhoneHost phone = new PhoneHost();
        phone.send(Map.of());
        check(XrayImportEvent.link == null, "no empty import");
        phone.send(Map.of("link", "  vmess://synthetic  "));
        check("vmess://synthetic".equals(XrayImportEvent.link), "existing share input");
        check(!phone.rules(Map.of("groups", "")).ok && XrayLiveRulesEvent.calls == 0, "both lists required");
        check(!phone.rules(Map.of("groups", "a".repeat(4097), "channels", "")).ok && XrayLiveRulesEvent.calls == 0, "oversize rejected");
        check(!phone.rules(Map.of("groups", "", "channels", "")).ok && XrayLiveRulesEvent.calls == 1, "closed settings not acknowledged");
        XrayLiveRulesEvent.applied = true;
        check(phone.rules(Map.of("groups", "", "channels", "")).ok && XrayLiveRulesEvent.groups.isEmpty() && XrayLiveRulesEvent.channels.isEmpty(), "explicit empty lists clear form");
        System.out.println("PASS actual 5.9 base playback/VOD/phone methods: " + count + " assertions");
    }
}
'''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-tv", type=Path, required=True)
    p.add_argument("--tv", type=Path, required=True)
    a = p.parse_args()
    old, tv = a.old_tv.resolve(), a.tv.resolve()
    guard_fork()
    verified_checkout(old, "old_tv")
    verified_checkout(tv, "tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-owner-resource-") as d:
        work = Path(d)
        candidate = work / "candidate"
        conflicts, manual = overlay(old, tv, candidate)
        files = [BASE+"ui/activity/PlaybackActivity.java", BASE+"model/VideoViewModel.java",
                 BASE+"server/process/Action.java", LEAN+"AndroidManifest.xml",
                 LEAN+"res/layout/view_control_live_action.xml"] + [
                 LEAN+"res/"+lang+"/strings.xml" for lang in ("values", "values-zh-rCN", "values-zh-rTW")]
        for path in files:
            row = next(x for x in LOCK["fork_scope"] if x["path"] == path)
            assert path not in conflicts+manual and blob(candidate/path) == row["resolved"], path
        activity, video, action = [(candidate/p).read_text() for p in files[:3]]
        def same(p, source, sig):
            assert method(source, sig) == method((tv/p).read_text(), sig), sig
        for sig in ("private void claimBinding()", "private static void bindPlayerOutput(", "private void hidePlayerViewForWebPlayback()"):
            same(files[0], activity, sig)
        sync = method(activity, "private void syncPlayerView(Player player)")
        assert sync.index("updatePlaybackDanmakuClient();") < sync.index("syncDanmakuSource();")
        assert "if (isNativePlaybackOwner()) PlaybackActivity.this.onPlaybackUrlChanged(url);" in activity
        for sig in ("public void cancelContent()", "public void resolveContent(", "private PlaybackResult<VodPlayRequest> getPlaybackResult("):
            same(files[1], video, sig)
        for sig in ("private Response onSync(", "private Response onRefresh(", "private void onFile("):
            same(files[2], action, sig)
        assert 'if ("xrayLiveRules".equals(param)) return onXrayLiveRules(params);' in action
        assert 'case "xray" -> onXray(params);' in action
        for path in files[5:]:
            def strings(root):
                nodes = ET.parse(root/path).getroot()
                items = [x for x in nodes if x.tag == "string"]
                assert len(items) == len({x.attrib["name"] for x in items})
                for x in items:
                    x.tail = None
                return {x.attrib["name"]: ET.tostring(x) for x in items}
            before, after, fork = strings(tv), strings(candidate), strings(ROOT)
            assert all(after[k] == v for k,v in before.items()), path
            added = {k:v for k,v in fork.items() if k.startswith("xray_") or k == "app_name"}
            assert {k:v for k,v in after.items() if k not in before} == added, path
        path = files[4]
        def tree(root): return ET.parse(root/path).getroot()
        before, after = tree(tv), tree(candidate)
        controls = [x for x in after.iter() if x.get(NS+"id") == "@+id/xray"]
        assert len(controls) == 1 and controls[0].get(NS+"text") == "@string/xray_off"
        for parent in after.iter():
            if controls[0] in list(parent):
                parent.remove(controls[0])
                break
        def shape(x):
            return (x.tag, x.attrib, (x.text or "").strip(), [shape(v) for v in x])
        assert shape(before) == shape(after), "upstream Live control drift"
        path = files[3]
        before, after = tree(tv), tree(candidate)
        boot = "android.permission.RECEIVE_BOOT_COMPLETED"
        for node in list(before):
            if node.tag == "uses-permission" and node.get(NS+"name") == boot:
                before.remove(node)
        app = before.find("application")
        for node in list(app):
            if node.tag == "receiver" and node.get(NS+"name") == ".receiver.BootReceiver":
                app.remove(node)
        app = after.find("application")
        matches = [x for x in app if x.get(NS+"name") == ".ui.activity.SettingXrayActivity"]
        assert len(matches) == 1 and matches[0].tag == "activity" and matches[0].get(NS+"exported") != "true"
        app.remove(matches[0])
        assert shape(before) == shape(after), "unexpected 5.9 manifest change"
        methods = "\n".join(method(activity, sig) for sig in (
            "private void onPlaybackReplaced()", "protected final void clearPlaybackDanmakuSource()",
            "protected final void updatePlaybackDanmakuClient()", "private void setDanmakuSource("))
        methods += "\nvoid replace() { onPlaybackReplaced(); }\nvoid setSource(Uri uri) { setDanmakuSource(uri); }\n"
        java = FIXTURE.replace("__PLAYBACK__", methods).replace("__VIDEO__", method(video, "public void cancelXrayTransitionRequests()"))
        java = java.replace("__ACTION__", "\n".join(method(action,sig) for sig in ("private void onXray(", "private Response onXrayLiveRules(")))
        src = work/"OwnerHarness.java"
        def run(source, fail=None):
            src.write_text(source)
            subprocess.run(["javac", "--release", "17", str(src)], check=True)
            cmd = ["java", "-cp", str(work), "OwnerHarness"]
            if fail:
                out = subprocess.run(cmd, text=True, capture_output=True)
                assert out.returncode != 0 and "AssertionError: "+fail in out.stderr, out.stderr
            else:
                subprocess.run(cmd, check=True)
        run(java)
        for needle, replacement, failure in (
            ("        onXrayBindingReplaced();", "", "old owner retired before detach"),
            ("if (mService != null && player().isXrayPlaybackSuspended()) uri = null;", "", "suspended cannot fetch file"),
            ("        requestTasks.cancel(TaskType.PRELOAD);", "", "exact VOD cancellation lanes"),
            ("if (!XrayLiveRulesEvent.post(groups, channels))", "if (false)", "closed settings not acknowledged"),
        ):
            assert java.count(needle) == 1, needle
            run(java.replace(needle,replacement), failure)
        print("PASS four negative controls; XML preservation and exact host method checks; no full Android linkage", flush=True)
        print("REMAINING_SCOPE", len(conflicts), "unresolved", len(manual), "old-media-review", flush=True)

if __name__ == "__main__":
    main()
