#!/usr/bin/env python3
"""Test upstream-first 5.8.7 Xray side-request adapters and public Git Tree.

Use --upstream and --target in Actions to verify the selected, actual FongMi
commit, not merely the fixture. Fail if upstream callback or network APIs move.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"scripts/upstream"))
from side_request_adapters import playback_service,danmaku_api,subtitle_api,download


def reject(transform,source):
    try:
        transform(source)
    except ValueError:
        return
    raise AssertionError("Must reject unrecognized upstream "+transform.__name__)


DANMAKU='''import com.fongmi.android.tv.R;
class DanmakuApi {
    private static final AtomicInteger REQUEST_ID = new AtomicInteger();
    public static void cancel() {
        REQUEST_ID.incrementAndGet();
        OkHttp.cancel(TAG);
    }

    public static void search(String name, Consumer<Danmaku> success) {}
    void execute() {
        new ApiCallback<>(requestId, REQUEST_ID, parser, success, error);
        return OkHttp.newCall(url.replace("{name}", Uri.encode(name)).replace("{episode}", Uri.encode(episode)), TAG);
        return OkHttp.newCall(url, OkHttp.toBody(params), TAG);
    }
}'''
d=danmaku_api(DANMAKU)
assert d.count("XraySideRequestGate.newCall(")==2
assert "XraySideRequestGate.cancel(TAG);" in d
assert "REQUEST_ID.incrementAndGet()" in d
reject(danmaku_api,DANMAKU.replace("OkHttp.toBody(params)","newBody(params)"))

SUBTITLE='''import com.fongmi.android.tv.R;
class SubtitleApi {
    private static final AtomicInteger REQUEST_ID = new AtomicInteger();
    public static void cancel() {
        REQUEST_ID.incrementAndGet();
        OkHttp.cancel(TAG);
        cancelDownload();
    }
    void run() {
        Download task = SubtitleArchive.createDownload(item.getName(), item.getUrl()).tag(TAG);
        return OkHttp.newCall(builder.build().toString(), TAG);
        return OkHttp.newCall(builder.build().toString(), TAG);
        ApiCallback.post(requestId, REQUEST_ID, () -> success.accept(items));
        if (download != task) return;
    }
}'''
s=subtitle_api(SUBTITLE)
assert s.count("XraySideRequestGate.newCall(")==2
assert "XraySideRequestGate.usePlaybackTransport(" in s
assert "ApiCallback.post(requestId, REQUEST_ID" in s
assert "XraySideRequestGate.cancel(TAG);" in s
reject(subtitle_api,SUBTITLE.replace("download != task","download == task"))
# Only the two official call sites are permitted, so future drift fails closed.
reject(subtitle_api,SUBTITLE.replace(
    "return OkHttp.newCall(builder.build().toString(), TAG);", "return Other.newCall();", 1))

DOWNLOAD='''public final class Download {
    private Call.Factory factory;
    public Download tag(String tag) { return this; }
    void doWork() {
            Call.Factory client = OkHttp.client();
            this.factory = factory;
            factory.newCall(request);
    }
}'''
dl=download(DOWNLOAD)
assert "public Download transport(Call.Factory client)" in dl
assert "Call.Factory client = playbackTransport == null ? OkHttp.client() : playbackTransport;" in dl
assert "factory.newCall(request)" in dl
assert "this.factory = factory;" in dl
reject(download,DOWNLOAD.replace("Call.Factory client = OkHttp.client();","Call.Factory client = Other.client();"))

SERVICE='''import com.fongmi.android.tv.bean.History;
class PlaybackService {
    void claimBinding() {
        if (binding != null) binding.onReplaced().run();
        binding = new ActivityBinding(owner, onReplaced);
    }
    private boolean setBrowseItem(MediaItem item, long startPositionMs) {
            if (!player.browse(result, item.mediaId, item.mediaMetadata, startPositionMs)) return false;
            if (binding != null) binding.onReplaced().run();
            binding = null;
        return true;
    }
    private PlayerManager player;
    public void onCreate() {
        player = new PlayerManager(this);
        sessionPlayer = new SessionPlayer(player.getPlayer());
        session = new MediaLibrarySession.Builder(this, sessionPlayer, this).setBitmapLoader(new ArtworkBitmapLoader(this)).build();
        liveMetadata = new LiveMetadata(player, library);
    }
    public void onDestroy() {
        running = false;
    }
    @Override
    public void onPlayerRebuild(Player newPlayer) { }
}'''
sr=playback_service(SERVICE)
assert "XraySideRequestGate.bind(player);" in sr
assert "XraySideRequestGate.unbind(player);" in sr
assert sr.count("DanmakuApi.cancel();")==2
assert sr.count("SubtitleApi.cancel();")==2
assert "XrayArtworkBitmapLoader(player, new ArtworkBitmapLoader(this))" in sr
assert "@Override\n    @Override" not in sr
assert "onXrayTransitionStarted()" in sr
assert sr.count("player.clearPlaybackProxyPreservingState();") == 2
# A media-library browse takeover starts playback synchronously. Never
# allow new media to inherit the old activity's Xray transport.
browse_section = sr.split("private boolean setBrowseItem(", 1)[1]
assert browse_section.index("player.clearPlaybackProxyPreservingState();") < browse_section.index(
    "if (!player.browse(")
assert "if (!hadXray && binding != null) binding.onReplaced().run();" in browse_section
assert "XraySideRequestGate.cancelRemoteDownloads();" in sr
assert "OkHttp.cancel(LiveApi.METADATA_TAG);" in sr
assert "XraySideRequestGate.cancelRemoteDownloads();" in sr
assert "liveMetadata = new LiveMetadata(player, library)" in sr
reject(playback_service,SERVICE.replace("setBitmapLoader(new ArtworkBitmapLoader(this))",
                                      "setBitmapLoader(new OtherBitmapLoader(this))"))
reject(playback_service,SERVICE.replace(
    "if (!player.browse(result, item.mediaId, item.mediaMetadata, startPositionMs)) return false;",
    "if (player.browse(result, item.mediaId, item.mediaMetadata, startPositionMs)) return true;"))

parser=argparse.ArgumentParser()
parser.add_argument("--upstream",type=Path)
parser.add_argument("--target")
args=parser.parse_args()
if bool(args.upstream)!=bool(args.target):
    parser.error("--upstream and --target must both be specified")
if args.upstream:
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    for name,fn in (
        ("app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java",playback_service),
        ("app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java",danmaku_api),
        ("app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java",subtitle_api),
        ("catvod/src/main/java/com/github/catvod/net/Download.java",download),
    ):
        if name not in tree: raise AssertionError("New upstream side API missing: "+name)
        raw=blob(args.upstream,tree[name]).decode("utf-8")
        transformed=fn(raw)
        assert len(transformed)>len(raw),name
        if name.endswith("PlaybackService.java"):
            assert "@Override\n    @Override" not in transformed
        if name.endswith("Download.java"):
            assert "factory.newCall(request)" in transformed
    print("PASS all four real public side-request API transformations at "+args.target)

print("PASS side-request adapters: request generation, subtitle download parts, service Xray cancellation")
