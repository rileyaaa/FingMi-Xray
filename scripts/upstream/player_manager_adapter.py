#!/usr/bin/env python3
"""Upstream-first Xray binding in the public FongMi/TV 5.8.7 PlayerManager.

Never copy the old fork manager. Retain the public timeshift, ISO, decoder,
playback attempt, snapshot, preload and fallback architecture. Fail closed if
the selected upstream changes any hook's expected shape.
"""
from exo_adapters import one


def player_manager(code):
    code=one(code,"import com.fongmi.android.tv.player.exo.ExoPlayerEngine;",
        "import com.fongmi.android.tv.player.exo.ExoPlayerEngine;\n"
        "import com.fingmi.integration.xray.XrayPlaybackRouting;\n"
        "import com.fingmi.xray.network.XrayHttpClient;\n"
        "import okhttp3.OkHttpClient;","manager transport imports")
    code=one(code,"import java.util.UUID;",
        "import java.util.UUID;\nimport java.util.function.Function;","manager client callback type")
    code=one(code,"    private PlaySpec spec;",
        "    private PlaySpec spec;\n"
        "    private XrayHttpClient playbackProxy;\n"
        "    private XrayRestore xrayRestore;","Xray session fields")
    code=one(code,
        "    public boolean canPreloadNext() {\n        return PreloadSetting.isEnabled()",
        "    public boolean canPreloadNext() {\n        return !hasXraySession() && PreloadSetting.isEnabled()",
        "Xray cannot reuse direct next-item preload")
    code=one(code,
        "        if (isEmpty() || PlayerEngineFactory.matches(engine, spec)) return;",
        "        if (isEmpty() || PlayerEngineFactory.matches(engine, spec, playbackProxy)) return;",
        "engine selection with active Xray")
    code=one(code,"    public void clear() {\n        spec = null;\n    }",
        "    public void clear() {\n        xrayRestore = null;\n        spec = null;\n    }",
        "new media removes saved Xray identity")
    code=one(code,
        "    public boolean preload(PlaySpec spec, long startPositionMs, Object tag) {\n"
        "        if (!canPreloadNext()",
        "    public boolean preload(PlaySpec spec, long startPositionMs, Object tag) {\n"
        "        if (hasXraySession() || !canPreloadNext()",
        "active Xray preloading")
    code=one(code,
        "    private void ensureEngine(PlaySpec spec) {\n        if (mpvDrmExoFallback) {",
        """    private void ensureEngine(PlaySpec spec) {
        // Preserve the upstream MPV/DRM fallback unless a bound Xray engine
        // must be detached or a new Xray proxy requests its own Exo engine.
        if (mpvDrmExoFallback && playbackProxy == null &&
                !(engine instanceof ExoPlayerEngine exo && exo.proxy() != null)) {""",
        "DRM fallback must release old Xray engine")
    code=one(code,
        "        if (PlayerEngineFactory.matches(engine, spec)) return;\n"
        "        replaceEngine(PlayerEngineFactory.create(spec, listener));",
        "        if (PlayerEngineFactory.matches(engine, spec, playbackProxy)) return;\n"
        "        replaceEngine(PlayerEngineFactory.create(spec, playbackProxy, listener));",
        "engine recreation tied to session identity")
    code=one(code,
        "    public void start(PlaySpec spec, long timeout, long startPositionMs) {\n"
        "        this.spec = spec;",
        "    public void start(PlaySpec spec, long timeout, long startPositionMs) {\n"
        "        xrayRestore = null;\n        this.spec = spec;",
        "new source clears old Xray snapshot")
    code=one(code,
        "    public void parse(String key, Result result, boolean useParse, MediaMetadata metadata, long startPositionMs, long endingMs) {\n"
        "        stopParse();",
        "    public void parse(String key, Result result, boolean useParse, MediaMetadata metadata, long startPositionMs, long endingMs) {\n"
        "        xrayRestore = null;\n        stopParse();",
        "parsed source clears old Xray snapshot")
    code=one(code,"    public interface Callback {",
        """    public interface Callback {
        default void onXrayTransitionStarted() {}""",
        "media-side network cancellation callback")
    code=one(code,"    private record PlaybackSnapshot(",
        """    private record XrayRestore(PlaySpec spec, PlaybackSnapshot snapshot) {}

    private record PlaybackSnapshot(""",
        "pending Xray playback snapshot")
    code=one(code,"    private void replaceEngine(PlayerEngine replacement) {",
        """    /** Each Xray playback generation owns its own Exo HTTP/RTSP client. */
    public synchronized void setPlaybackProxy(XrayHttpClient next, boolean preservePlayback) {
        if (playbackProxy == next) return;
        PlaybackSnapshot snapshot = null;
        if (preservePlayback && spec != null && player != null) {
            XrayRestore saved = xrayRestore;
            snapshot = next != null && saved != null && saved.spec() == spec
                    ? saved.snapshot() : PlaybackSnapshot.capture(this);
        }
        xrayRestore = null;
        playbackProxy = next;
        if (next != null) callback.onXrayTransitionStarted();
        clearPreload();
        if (next == null && !preservePlayback) {
            if (spec != null) ensureEngine(spec.checkUa());
            else if (engine instanceof ExoPlayerEngine exo && exo.proxy() != null)
                replaceEngine(PlayerEngineFactory.create(listener));
            return;
        }
        if (spec == null) return;
        if (snapshot != null) {
            spec.setIsoEditionIndex(snapshot.selectedIsoEditionIndex());
            startCurrent(snapshot.positionMs());
            snapshot.restorePlayerState(this);
        } else if (next != null) {
            ensureEngine(spec.checkUa());
        }
    }

    /** ERROR: unbind the proxy immediately without resuming direct media. */
    public synchronized void clearPlaybackProxyPreservingState() {
        XrayHttpClient bound = engine instanceof ExoPlayerEngine exo ? exo.proxy() : null;
        if (!XrayPlaybackRouting.hasSession(playbackProxy, bound)) return;
        xrayRestore = spec == null || player == null
                ? null : new XrayRestore(spec, PlaybackSnapshot.capture(this));
        playbackProxy = null;
        clearPreload();
        if (spec != null) ensureEngine(spec.checkUa());
        else if (bound != null) replaceEngine(PlayerEngineFactory.create(listener));
    }

    public synchronized boolean hasXraySession() {
        XrayHttpClient bound = engine instanceof ExoPlayerEngine exo ? exo.proxy() : null;
        return XrayPlaybackRouting.hasSession(playbackProxy, bound);
    }

    public synchronized OkHttpClient getPlaybackHttpClient(OkHttpClient fallback) {
        XrayHttpClient bound = engine instanceof ExoPlayerEngine exo ? exo.proxy() : null;
        XrayHttpClient active = XrayPlaybackRouting.activeProxy(playbackProxy, bound);
        return active == null ? fallback : active.client();
    }

    public synchronized <T> T withHttpClient(OkHttpClient fallback, Function<OkHttpClient, T> action) {
        return action.apply(getPlaybackHttpClient(fallback));
    }

    private void replaceEngine(PlayerEngine replacement) {""",
        "Xray session lifecycle and transport handoff")
    for required in ("IsoDiscPreparation.isIso","PendingPreload queuedPreload",
                     "timeshift.isReplaying()","PlaybackSnapshot.capture(this)",
                     "snapshot.restorePlayerState(this)",
                     "XrayPlaybackRouting.activeProxy(playbackProxy, bound)",
                     "if (next != null) callback.onXrayTransitionStarted();",
                     "else if (bound != null) replaceEngine(PlayerEngineFactory.create(listener));"):
        if required not in code:
            raise ValueError("New PlayerManager lost essential upstream/Xray behavior: "+required)
    return code
