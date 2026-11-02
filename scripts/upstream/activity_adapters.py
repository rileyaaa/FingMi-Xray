#!/usr/bin/env python3
"""Minimal per-Activity Xray overlays on pristine FongMi 5.8.7 Leanback UI.

No old business/view/controller files are copied: keep official ISO, CMG,
dialog, channel, VOD, focus, remote-controller, browse and web playback code.
PlaybackService remains authoritative for the network identity.
"""
from exo_adapters import one

XRAY_IMPORTS = """import com.fingmi.xray.network.XrayHttpClient;
import com.fingmi.xray.session.XrayPlaybackSession;
import com.fingmi.xray.session.XraySessionListener;
import com.github.catvod.net.OkHttp;"""


def live_activity(s):
    s=one(s,"import com.fongmi.android.tv.R;",
        "import com.fongmi.android.tv.R;\n"+XRAY_IMPORTS,
        "Live Xray imports")
    s=one(s,"import java.util.List;",
        "import java.util.List;\nimport java.util.Objects;",
        "Live line identity comparison")
    s=one(s,"    private String mPlaybackKey;",
        """    private String mPlaybackKey;
    private XrayPlaybackSession mXray;
    private long mXrayEpoch;
    private Channel mXrayChannel;
    private String mXrayLine;
    private boolean mXrayPendingStart;""",
        "Live Xray activity identity")
    s=one(s,"    protected void initView(Bundle savedInstanceState) {\n        super.initView(savedInstanceState);",
        """    protected void initView(Bundle savedInstanceState) {
        super.initView(savedInstanceState);
        initXrayPlayback();""",
        "Live new upstream view initialization")
    s=one(s,"        mBinding.control.action.player.setOnClickListener(view -> onPlayer());",
        "        mBinding.control.action.player.setOnClickListener(view -> onPlayer());\n"
        "        mBinding.control.action.xray.setOnClickListener(view -> onXray());",
        "Live on-screen button")
    s=one(s,"    private void onPlayer() {\n        PlayerEngineDialog.show(this);",
        """    @Override
    public void onXrayEngineChanged() {
        mXrayPendingStart = false;
        if (mXray != null) mXray.begin("live:" + ++mXrayEpoch);
    }

    private void initXrayPlayback() {
        mXray = new XrayPlaybackSession(this, OkHttp.player(), new XrayPlaybackSession.Listener() {
            @Override
            public void onProxyChanged(XrayHttpClient resources, boolean preservePlayback) {
                if (mViewModel != null) mViewModel.cancelXrayMetadataRequests();
                if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive()) {
                    clearXrayDanmakuSource();
                    player().setPlaybackProxy(resources, preservePlayback);
                } else if (resources != null) {
                    // Never attach the old screen's client to another owner.
                    mXray.stop(false);
                    return;
                }
                if (mChannelAdapter != null) mChannelAdapter.setXrayLogoSuppressed(resources != null);
                if (mViewModel != null && mChannel != null && !isFinishing() && !isDestroyed())
                    mViewModel.getEpg(mChannel);
            }

            @Override
            public void onProxyError() {
                mXrayPendingStart = false;
                if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive()) {
                    clearXrayDanmakuSource();
                    player().clearPlaybackProxyPreservingState();
                }
                if (mChannelAdapter != null) mChannelAdapter.setXrayLogoSuppressed(false);
                if (mViewModel != null) mViewModel.cancelXrayMetadataRequests();
            }

            @Override
            public void onStateChanged(int state, String message) {
                if (isFinishing() || isDestroyed()) return;
                mBinding.control.action.xray.setSelected(state == XraySessionListener.RUNNING);
                mBinding.control.action.xray.setText(
                        state == XraySessionListener.RUNNING ? R.string.xray_on :
                        state == XraySessionListener.STARTING ? R.string.xray_starting :
                        state == XraySessionListener.ERROR ? R.string.xray_error :
                        R.string.xray_off);
                if (state == XraySessionListener.RUNNING && mXrayPendingStart) {
                    mXrayPendingStart = false;
                    if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive() && mLive != null)
                        mLive.refresh();
                } else if (state == XraySessionListener.ERROR || state == XraySessionListener.IDLE) {
                    mXrayPendingStart = false;
                    if (message != null && !message.isEmpty()) Notify.show(message);
                }
            }
        });
        mXray.begin("live:" + ++mXrayEpoch);
    }

    private void onXray() {
        if (mXray == null || service() == null || !isPlaybackCurrent() || isWebPlaybackActive()) return;
        int state = mXray.state();
        if (state == XraySessionListener.RUNNING || state == XraySessionListener.STARTING) {
            mXrayPendingStart = false;
            mXray.stop(true);
            return;
        }
        if (hasPlaybackSession() && player().hasPlaySpec()) {
            mXray.mediaUrlChanged(player().getUrl());
            if (!mXray.enable()) Notify.show(R.string.xray_public_http_required);
        } else if (mChannel != null &&
                XrayPlaybackSession.supportsDirectLiveSource(mChannel.getCurrent())) {
            mXrayPendingStart = mXray.enableForPending(mChannel.getCurrent());
            if (!mXrayPendingStart) Notify.show(R.string.xray_public_http_required);
        } else Notify.show(R.string.xray_live_required);
    }

    @Override
    protected void onXrayBindingReplaced() {
        mXrayPendingStart = false;
        if (mXray != null) mXray.begin("live:" + ++mXrayEpoch);
    }

    private void onPlayer() {
        PlayerEngineDialog.show(this);""",
        "Live Xray UI callbacks")
    s=one(s,
        "    public void preparePlaybackForRefresh() {\n        mInput.cancelSeek();",
        """    public void preparePlaybackForRefresh() {
        // A different source line starts a direct session. A same-channel
        // parser/CDN URL refresh preserves the existing Xray identity.
        String line = mChannel == null ? null : mChannel.getCurrent();
        if (mXray != null && !Objects.equals(line, mXrayLine)) {
            mXrayLine = line;
            mXrayPendingStart = false;
            mXray.begin("live:" + ++mXrayEpoch);
        }
        mInput.cancelSeek();""",
        "Live line switching")
    s=one(s,"    public void renderChannelSelection(Channel channel) {\n        App.post(mR0, 100);",
        """    public void renderChannelSelection(Channel channel) {
        if (mXray != null && mXrayChannel != channel) {
            mXrayChannel = channel;
            mXrayLine = channel == null ? null : channel.getCurrent();
            mXrayPendingStart = false;
            mXray.begin("live:" + ++mXrayEpoch);
        }
        App.post(mR0, 100);""",
        "Live channel identity switching")
    s=one(s,"    public void startPlayback(Result result, long position, MediaMetadata metadata) {\n        mInput.cancelSeek();",
        """    public void startPlayback(Result result, long position, MediaMetadata metadata) {
        if (mXray != null) mXray.mediaUrlChanged(result.getRealUrl());
        mInput.cancelSeek();""",
        "Live resolved URL update")
    s=one(s,"    protected void onDestroy() {\n        mInput.cancelSeek();",
        """    protected void onDestroy() {
        if (mXray != null) mXray.close();
        mInput.cancelSeek();""",
        "Live destruction")
    for required in ("mLive.onPlaybackServiceReady();",
                     "mViewModel.cancelXrayMetadataRequests();",
                     "clearXrayDanmakuSource();",
                     "isWebPlaybackActive()",
                     "onXrayEngineChanged()",
                     "mChannelAdapter.setXrayLogoSuppressed(resources != null);",
                     "mBinding.control.action.xray.setOnClickListener(view -> onXray());",
                     "startPlayer(mPlaybackKey, result, false, getHome().getTimeout(), position, metadata);",
                     "new XrayPlaybackSession(this, OkHttp.player()",
                     "if (mXray != null) mXray.close();"):
        if required not in s: raise ValueError("Live Activity lost official/Xray feature: "+required)
    return s


def video_activity(s):
    s=one(s,"import com.fongmi.android.tv.R;",
        "import com.fongmi.android.tv.R;\n"+XRAY_IMPORTS,
        "VOD Xray imports")
    s=one(s,"    private VideoViewModel mViewModel;",
        """    private VideoViewModel mViewModel;
    private XrayPlaybackSession mXray;
    private long mXrayEpoch;
    private boolean mXrayProxyFailed;""",
        "VOD Xray session fields")
    s=one(s,"    protected void initView(Bundle savedInstanceState) {\n        super.initView(savedInstanceState);",
        """    protected void initView(Bundle savedInstanceState) {
        super.initView(savedInstanceState);
        initXrayPlayback();""",
        "VOD app view lifecycle")
    s=one(s,
        "        saveHistory(true);\n        mVod.reset();",
        "        saveHistory(true);\n        resetXrayForPlaybackChange();\n        mVod.reset();",
        "VOD deep link changes")
    s=one(s,"        mBinding.control.action.player.setOnClickListener(view -> onPlayer());",
        "        mBinding.control.action.player.setOnClickListener(view -> onPlayer());\n"
        "        mBinding.control.action.xray.setOnClickListener(view -> onXray());",
        "VOD button")
    s=one(s,"    private void onPlayer() {\n        PlayerEngineDialog.show(this);",
        """    @Override
    public void onXrayEngineChanged() {
        resetXrayForPlaybackChange();
    }

    private void initXrayPlayback() {
        mXray = new XrayPlaybackSession(this, OkHttp.player(), new XrayPlaybackSession.Listener() {
            @Override
            public void onProxyChanged(XrayHttpClient resources, boolean preservePlayback) {
                if (resources != null && mViewModel != null)
                    mViewModel.cancelXrayTransitionRequests();
                if (service() != null && isPlaybackCurrent() && !isWebPlaybackActive()) {
                    clearXrayDanmakuSource();
                    player().setPlaybackProxy(resources, preservePlayback);
                } else if (resources != null) {
                    mXray.stop(false);
                }
            }

            @Override
            public void onProxyError() {
                if (service() == null || !isPlaybackCurrent() || isWebPlaybackActive()) return;
                mXrayProxyFailed = player().hasXraySession();
                if (!mXrayProxyFailed) return;
                clearXrayDanmakuSource();
                player().clearPlaybackProxyPreservingState();
            }

            @Override
            public void onStateChanged(int state, String message) {
                if (isFinishing() || isDestroyed()) return;
                mBinding.control.action.xray.setSelected(state == XraySessionListener.RUNNING);
                mBinding.control.action.xray.setText(
                        state == XraySessionListener.RUNNING ? R.string.xray_on :
                        state == XraySessionListener.STARTING ? R.string.xray_starting :
                        state == XraySessionListener.ERROR ? R.string.xray_error :
                        R.string.xray_off);
                if (state == XraySessionListener.ERROR) {
                    if (mXrayProxyFailed && message != null && !message.isEmpty()) showError(message);
                    mXrayProxyFailed = false;
                    if (message != null && !message.isEmpty()) Notify.show(message);
                } else if (state == XraySessionListener.IDLE && message != null && !message.isEmpty()) {
                    Notify.show(message);
                }
            }
        });
        mXray.begin("vod:" + ++mXrayEpoch);
    }

    private void resetXrayForPlaybackChange() {
        mXrayProxyFailed = false;
        if (mXray != null) mXray.begin("vod:" + ++mXrayEpoch);
    }

    private void onXray() {
        if (mXray == null || service() == null || !isPlaybackCurrent() || isWebPlaybackActive()) return;
        int state = mXray.state();
        if (state == XraySessionListener.RUNNING || state == XraySessionListener.STARTING) {
            mXray.stop(true);
            return;
        }
        if (!hasActivePlaybackSession() || !player().hasPlaySpec()) {
            Notify.show(R.string.xray_vod_required);
            return;
        }
        mXray.mediaUrlChanged(player().getUrl());
        if (!mXray.enable()) Notify.show(R.string.xray_vod_public_http_required);
        else player().clearPreload();
    }

    @Override
    protected void onXrayBindingReplaced() {
        resetXrayForPlaybackChange();
    }

    private void onPlayer() {
        PlayerEngineDialog.show(this);""",
        "VOD Xray lifecycle callbacks")
    s=one(s,
        "    public void prepareSource(Vod item) {\n        mInput.cancelSeek();",
        """    public void prepareSource(Vod item) {
        resetXrayForPlaybackChange();
        mInput.cancelSeek();""",
        "VOD source change")
    s=one(s,
        "    public void stopPlaybackForRefresh() {\n        mInput.cancelSeek();",
        """    public void stopPlaybackForRefresh() {
        // Episode, quality, parsing and source changes start direct by default.
        resetXrayForPlaybackChange();
        mInput.cancelSeek();""",
        "VOD episode or quality change")
    s=one(s,
        "    public void startPlayback(Result result, boolean useParse, long startPositionMs, MediaMetadata metadata) {\n        mInput.cancelSeek();",
        """    public void startPlayback(Result result, boolean useParse, long startPositionMs, MediaMetadata metadata) {
        if (mXray != null) mXray.mediaUrlChanged(result.getRealUrl());
        mInput.cancelSeek();""",
        "VOD source URL update")
    s=one(s,
        "    protected void onDestroy() {\n        mInput.cancelSeek();",
        """    protected void onDestroy() {
        if (mXray != null) mXray.close();
        mInput.cancelSeek();""",
        "VOD close Xray before service detach")
    for required in ("mVod.onPlaybackServiceReady();",
                     "stopWebPlayback();",
                     "externalPlaybackCompleted = false;",
                     "R.string.xray_on",
                     "mBinding.control.action.xray.setOnClickListener(view -> onXray());",
                     "mViewModel.cancelXrayTransitionRequests();",
                     "clearXrayDanmakuSource();",
                     "isWebPlaybackActive()",
                     "onXrayEngineChanged()",
                     "new XrayPlaybackSession(this, OkHttp.player()",
                     "if (mXray != null) mXray.close();"):
        if required not in s:
            raise ValueError("VOD Activity lost official/Xray feature: "+required)
    return s
