#!/usr/bin/env python3
"""Fail-closed 5.8.7 playback owner and Xray Live/VOD Activity adapter tests."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/upstream"))
from playback_activity_adapter import playback_activity,video_view_model
from activity_adapters import live_activity,video_activity


def refuse(fn,code):
    try: fn(code)
    except ValueError: return
    raise AssertionError(fn.__name__+" accepted unknown upstream code shape")


BASE='''class PlaybackActivity {
    protected void onReclaim() {
    }
    private void setDanmakuSource(@Nullable Uri uri) {}
    private void onPlaybackReplaced() {
        playbackReplaced = true;
    }
    void navigate() {mService.claimBinding(getNavigationCallback(), this::onPlaybackReplaced);}
    void cleanup() {
        playbackPlayerState.setValue(null);
        getSeekView().setPlayer(null);
        releasePlaybackService();
    }
}'''
z=playback_activity(BASE)
assert z.count("onXrayBindingReplaced();")==1
assert "protected void onXrayBindingReplaced()" in z
assert "protected final void clearXrayDanmakuSource()" in z
assert "public void onXrayEngineChanged()" in z
assert "mService.claimBinding(getNavigationCallback(), this::onPlaybackReplaced);" in z
refuse(playback_activity, BASE.replace("playbackReplaced = true;",
                                       "playbackReplaced = false;"))

VIDEO_VM='''class VideoViewModel {
    private void execute() {
        requestTasks.execute(type, timeout, load, result, error);
        playbackState.reset();
        stopSearch();
    }
    @Override
    public void cancelContent() {
        requestTasks.cancel(TaskType.PRELOAD);
    }
}'''
z=video_view_model(VIDEO_VM)
for needle in ("cancelXrayTransitionRequests()","requestTasks.cancel(TaskType.DETAIL)",
               "requestTasks.cancel(TaskType.PLAYBACK)",
               "requestTasks.cancel(TaskType.PRELOAD)","stopSearch();"):
    assert needle in z,needle
refuse(video_view_model, VIDEO_VM.replace("public void cancelContent()",
                                          "public void releaseContent()"))

LIVE='''import com.fongmi.android.tv.R;
import java.util.List;
class LiveActivity {
    private String mPlaybackKey;
    protected void initView(Bundle savedInstanceState) {
        super.initView(savedInstanceState);
        mClock = Clock.create(mBinding.widget.clock);
    }
    void onConnected() {mLive.onPlaybackServiceReady();}
    void initEvent() {
        mBinding.control.action.player.setOnClickListener(view -> onPlayer());
    }
    private void onPlayer() {
        PlayerEngineDialog.show(this);
    }
    public void preparePlaybackForRefresh() {
        mInput.cancelSeek();
    }
    public void renderChannelSelection(Channel channel) {
        App.post(mR0, 100);
    }
    public void startPlayback(Result result, long position, MediaMetadata metadata) {
        mInput.cancelSeek();
        startPlayer(mPlaybackKey, result, false, getHome().getTimeout(), position, metadata);
    }
    protected void onDestroy() {
        mInput.cancelSeek();
    }
}'''
z=live_activity(LIVE)
for needle in ('new XrayPlaybackSession(this, OkHttp.player()', 'mXray.enableForPending(',
               'mViewModel.cancelXrayMetadataRequests();','mLive.refresh();',
               'mXray.begin("live:" + ++mXrayEpoch);','setXrayLogoSuppressed(resources != null)',
               'protected void onXrayBindingReplaced()', 'mXray.mediaUrlChanged(result.getRealUrl())',
               'mBinding.control.action.xray.setOnClickListener(view -> onXray());',
               'mXray.close();','clearXrayDanmakuSource();'):
    assert needle in z,needle
assert "startPlayer(mPlaybackKey, result, false, getHome().getTimeout(), position, metadata);" in z
assert "isWebPlaybackActive()" in z
assert "public void onXrayEngineChanged()" in z
refuse(live_activity,LIVE.replace("renderChannelSelection(Channel channel)",
                                  "renderOtherSelection(Channel channel)"))

VOD='''import com.fongmi.android.tv.R;
class VideoActivity {
    private VideoViewModel mViewModel;
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        saveHistory(true);
        mVod.reset();
        externalPlaybackCompleted = false;
    }
    protected void initView(Bundle savedInstanceState) {
        super.initView(savedInstanceState);
        mFrameParams = mBinding.video.getLayoutParams();
    }
    void initEvent() {
        mBinding.control.action.player.setOnClickListener(view -> onPlayer());
    }
    private void onPlayer() {
        PlayerEngineDialog.show(this);
    }
    public void prepareSource(Vod item) {
        mInput.cancelSeek();
    }
    public void stopPlaybackForRefresh() {
        mInput.cancelSeek();
        stopWebPlayback();
    }
    public void startPlayback(Result result, boolean useParse, long startPositionMs, MediaMetadata metadata) {
        mInput.cancelSeek();
    }
    protected void onDestroy() {
        mInput.cancelSeek();
    }
}'''
z=video_activity(VOD)
for needle in ("new XrayPlaybackSession(this, OkHttp.player()",
               "mViewModel.cancelXrayTransitionRequests();","resetXrayForPlaybackChange()",
               "mXray.mediaUrlChanged(result.getRealUrl());","mXray.enable()",
               'mXray.begin("vod:" + ++mXrayEpoch);',"mXray.close();","clearXrayDanmakuSource();",
               "mBinding.control.action.xray.setOnClickListener(view -> onXray());"):
    assert needle in z,needle
assert "stopWebPlayback();" in z
assert "isWebPlaybackActive()" in z
assert "public void onXrayEngineChanged()" in z
assert "getPlayerView().setDanmakuSource(null)" not in z
refuse(video_activity,VOD.replace("stopPlaybackForRefresh()","stopSourceForRefresh()"))

parser=argparse.ArgumentParser()
parser.add_argument("--upstream",type=Path)
parser.add_argument("--target")
args=parser.parse_args()
if bool(args.upstream)!=bool(args.target): parser.error("both public git tree arguments required")
if args.upstream:
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    for name,fn in (
        ("app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java",playback_activity),
        ("app/src/main/java/com/fongmi/android/tv/model/VideoViewModel.java",video_view_model),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",live_activity),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java",video_activity),
    ):
        if name not in tree: raise AssertionError("No official UI source: "+name)
        public=blob(args.upstream,tree[name]).decode("utf-8")
        candidate=fn(public)
        assert candidate!=public and len(candidate)>len(public),name
        if name.endswith("Activity.java"):
            assert "onXrayBindingReplaced()" in candidate
    print("PASS four official 5.8.7 UI/owner adapter sources at "+args.target)

print("PASS Xray Live/VOD direct reset, pending Live, owner transfer, stale VOD request guards")
