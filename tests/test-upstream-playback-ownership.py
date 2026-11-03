#!/usr/bin/env python3
"""Execute selected 5.8.7 playback owner and danmaku methods on JVM stubs.

Only real generated source methods are extracted; Android framework / network
objects are replaced. Tests that an outgoing Xray identity is detached while
its Activity still owns the binding, before the next owner can claim it.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java"
SERVICE = ROOT / "app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java"
LIVE = ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java"
VIDEO = ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java"


def method(path: Path, signature: str) -> str:
    source = path.read_text(encoding="utf-8")
    if source.count(signature) != 1:
        raise AssertionError(f"{path.name}: unique method not found: {signature}")
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for end in range(opening, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise AssertionError(f"Unclosed method in {path.name}: {signature}")


def verify() -> None:
    gradle = (ROOT / "app/build.gradle").read_text(encoding="utf-8")
    if re.search(r'versionName\s+"v5\.6\.3-xray\.\d+"', gradle):
        print("SKIP: v5.6.3 uses historical Xray binding/danmaku JVM tests")
        return
    if not re.search(r'versionName\s+"v5\.8\.7-xray\.\d+"', gradle):
        raise SystemExit("Unreviewed PlaybackActivity version for owner handoff JVM test")

    base_methods = "\n".join(method(BASE, sig) for sig in (
        "protected boolean isOwner()",
        "protected boolean isBindingOwner()",
        "protected boolean isPlaybackCurrent()",
        "protected void onXrayBindingReplaced()",
        "private void onPlaybackReplaced()",
    ))
    handoff = method(BASE, "private void onPlaybackReplaced()")
    if (handoff.index("onXrayBindingReplaced();") > handoff.index("playbackReplaced = true;")):
        raise SystemExit("Xray owner detached after playbackReplaced invalidated its client callback")
    service_methods = "\n".join(method(SERVICE, sig) for sig in (
        "public void claimBinding(", "public boolean ownsBinding(",
    ))
    service_claim = method(SERVICE, "public void claimBinding(")
    if service_claim.index("binding.onReplaced().run();") > service_claim.index("binding = new ActivityBinding("):
        raise SystemExit("Upstream PlaybackService moves binding before releasing previous owner")
    live_hook = method(LIVE, "protected void onXrayBindingReplaced()")
    video_hook = method(VIDEO, "protected void onXrayBindingReplaced()")
    video_reset = method(VIDEO, "private void resetXrayForPlaybackChange()")
    for path in (LIVE, VIDEO):
        activity = path.read_text(encoding="utf-8")
        if ("if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive()) {" not in activity
                or "player().setPlaybackProxy(resources, preservePlayback);" not in activity):
            raise SystemExit(f"{path.name} lost current-owner-only Xray proxy binding")

    owner_harness = r'''
class XrayHttpClient { boolean closed; }
class PlayerManager {
    String key;
    XrayHttpClient proxy;
    String getKey() { return key; }
    boolean hasXraySession() { return proxy != null; }
    void clearPlaybackProxyPreservingState() { proxy = null; }
    void setPlaybackProxy(XrayHttpClient next, boolean preserve) { proxy = next; }
}
class PlaybackService {
    interface NavigationCallback {}
    record ActivityBinding(NavigationCallback owner, Runnable onReplaced) {}
    static class LiveMetadata { void cancel() {} }
    final LiveMetadata liveMetadata = new LiveMetadata();
    final PlayerManager manager = new PlayerManager();
    final PlayerManager player = manager;
    ActivityBinding binding;
    void saveProgress() {}
    void cancelNavigation() {}
    __SERVICE_METHODS__
}
class PlaybackActivity {
    PlaybackService mService;
    String key;
    boolean playbackReplaced, pip, finished, detached;
    Object pendingResume;
    final PlaybackService.NavigationCallback navigation = new PlaybackService.NavigationCallback() {};
    static class State { void setValue(Object value) {} }
    static class SeekView { void setPlayer(Object value) {} }
    final State playbackPlayerState = new State();
    final SeekView seek = new SeekView();
    PlaybackActivity(PlaybackService service, String key) { mService=service; this.key=key; }
    PlaybackService service() { return mService; }
    PlayerManager player() { return mService.manager; }
    String getPlaybackKey() { return key; }
    PlaybackService.NavigationCallback getNavigationCallback() { return navigation; }
    void detachPlayerView() { detached=true; }
    SeekView getSeekView() { return seek; }
    boolean isInPictureInPictureMode() { return pip; }
    boolean isWebPlaybackActive() { return false; }
    void finish() { finished=true; }
    void claim() { mService.claimBinding(getNavigationCallback(), this::onPlaybackReplaced); }
    __BASE_METHODS__
}
interface ProxyListener { void onChanged(XrayHttpClient next, boolean preserve); }
class Session {
    XrayHttpClient resources;
    final ProxyListener listener;
    int closed;
    Session(ProxyListener listener) { this.listener=listener; }
    void enable() {
        resources=new XrayHttpClient();
        listener.onChanged(resources, false);
    }
    void begin(String identity) {
        if (resources == null) return;
        XrayHttpClient previous=resources;
        resources=null;
        try { listener.onChanged(null, false); }
        finally { previous.closed=true; closed++; }
    }
}
class LiveActivity extends PlaybackActivity {
    Session mXray;
    long mXrayEpoch;
    boolean mXrayPendingStart;
    LiveActivity(PlaybackService service, String key) {
        super(service, key);
        mXray = new Session((resources, preservePlayback) -> {
            if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive())
                player().setPlaybackProxy(resources, preservePlayback);
        });
    }
    __LIVE_HOOK__
}
class VideoActivity extends PlaybackActivity {
    Session mXray;
    long mXrayEpoch;
    boolean mXrayProxyFailed;
    VideoActivity(PlaybackService service, String key) {
        super(service, key);
        mXray = new Session((resources, preservePlayback) -> {
            if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive())
                player().setPlaybackProxy(resources, preservePlayback);
        });
    }
    __VIDEO_HOOK__
    __VIDEO_RESET__
}
public final class XrayOwnerHandoff587Test {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    private static void handoff(boolean oldLive) {
        PlaybackService service = new PlaybackService();
        service.manager.key="A";
        PlaybackActivity outgoing = oldLive ? new LiveActivity(service, "A") : new VideoActivity(service, "A");
        Session session = oldLive ? ((LiveActivity) outgoing).mXray : ((VideoActivity) outgoing).mXray;
        outgoing.claim();
        session.enable();
        XrayHttpClient previous = session.resources;
        check(previous != null && service.manager.proxy == previous, "old owner proxy install");
        PlaybackActivity incoming = oldLive ? new VideoActivity(service, "B") : new LiveActivity(service, "B");
        incoming.claim();
        check(previous.closed && session.closed == 1, "old owner proxy was not closed");
        check(service.manager.proxy == null, "closed Xray transport leaked into new owner");
        check(outgoing.playbackReplaced && outgoing.detached && !outgoing.isPlaybackCurrent(), "old owner not revoked");
        service.manager.key="B";
        Session next = oldLive ? ((VideoActivity) incoming).mXray : ((LiveActivity) incoming).mXray;
        next.enable();
        XrayHttpClient current = next.resources;
        check(current != null && service.manager.proxy == current, "new owner proxy install");
        outgoing.onXrayBindingReplaced();
        check(service.manager.proxy == current && !current.closed, "late old callback stole new proxy");
        incoming.claim();
        check(service.manager.proxy == current, "repeated owner claim dropped current proxy");
    }
    private static void mobile(boolean pip) {
        PlaybackService service = new PlaybackService();
        PlaybackActivity first = new PlaybackActivity(service, null);
        first.pip=pip;
        first.claim();
        new PlaybackActivity(service, null).claim();
        check(first.detached && first.playbackReplaced, "base playback handoff lost cleanup");
        check(first.finished == pip, "base mobile PiP completion changed");
    }
    public static void main(String[] args) {
        handoff(true); handoff(false); mobile(false); mobile(true);
        System.out.println("PASS 5.8.7 actual owner/Service hook sequence: Live/VOD handoff, closed-client detachment, late old callback, mobile PiP");
    }
}
'''
    owner_harness = (owner_harness
        .replace("__SERVICE_METHODS__", service_methods)
        .replace("__BASE_METHODS__", base_methods)
        .replace("__LIVE_HOOK__", live_hook)
        .replace("__VIDEO_HOOK__", video_hook)
        .replace("__VIDEO_RESET__", video_reset))

    clear = method(BASE, "protected final void clearXrayDanmakuSource()")
    select = method(BASE, "private void setDanmakuSource(@Nullable Uri uri)")
    danmaku_harness = r'''
@interface Nullable {}
class Uri { final boolean live; Uri(boolean live) { this.live=live; } }
class LiveDanmaku {
    Uri source;
    static boolean isLive(Uri uri) { return uri != null && uri.live; }
    void setDataSource(Uri uri) { source=uri; }
}
class DanmakuPlayerViewController {
    Uri source;
    void setDataSource(Uri uri) { source=uri; }
}
class PlayerView { Object getPlayer() { return new Object(); } }
public final class XrayDanmaku587Test {
    final LiveDanmaku liveDanmaku=new LiveDanmaku();
    final DanmakuPlayerViewController danmakuController=new DanmakuPlayerViewController();
    final PlayerView view=new PlayerView();
    PlayerView getPlayerView() { return view; }
    __CLEAR__
    __SELECT__
    static void check(boolean value) { if (!value) throw new AssertionError("stale Live or VOD danmaku source"); }
    public static void main(String[] args) {
        XrayDanmaku587Test a=new XrayDanmaku587Test();
        Uri live=new Uri(true), vod=new Uri(false);
        a.setDanmakuSource(live);
        check(a.liveDanmaku.source == live && a.danmakuController.source == null);
        a.clearXrayDanmakuSource();
        check(a.liveDanmaku.source == null && a.danmakuController.source == null);
        a.setDanmakuSource(vod);
        check(a.liveDanmaku.source == null && a.danmakuController.source == vod);
        a.clearXrayDanmakuSource();
        check(a.liveDanmaku.source == null && a.danmakuController.source == null);
        System.out.println("PASS 5.8.7 actual Live/VOD danmaku source clearing on proxy handoff");
    }
}
'''.replace("__CLEAR__", clear).replace("__SELECT__", select)

    with tempfile.TemporaryDirectory(prefix="fongmi-587-playback-ownership-") as folder:
        root = Path(folder)
        for filename, content in (("XrayOwnerHandoff587Test.java", owner_harness),
                                  ("XrayDanmaku587Test.java", danmaku_harness)):
            (root / filename).write_text(content, encoding="utf-8")
        subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-d", str(root),
                        str(root / "XrayOwnerHandoff587Test.java"),
                        str(root / "XrayDanmaku587Test.java")], check=True)
        for classname in ("XrayOwnerHandoff587Test", "XrayDanmaku587Test"):
            subprocess.run(["java", "-cp", str(root), classname], check=True)


if __name__ == "__main__":
    verify()
