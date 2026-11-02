#!/usr/bin/env python3
"""Fail-closed Xray overlays for FongMi/TV 5.8.7 Exo source APIs.

Always start with public upstream files, preserve ISO, CMG, DRM, decode,
subtitle and preload architecture. Add only per-session Xray transport hooks.
"""

def one(code, original, replacement, reason):
    count=code.count(original)
    if count!=1:
        raise ValueError(f"Exo upstream changed ({reason}): expected 1 anchor, saw {count}")
    return code.replace(original,replacement,1)

def counted(code, original, replacement, count, reason):
    occurrences=code.count(original)
    if occurrences!=count:
        raise ValueError(f"Exo upstream changed ({reason}): expected {count}, saw {occurrences}")
    return code.replace(original,replacement)

def media_factory(code):
    code=one(code,"import androidx.media3.exoplayer.drm.DrmSessionManagerProvider;",
        "import androidx.media3.exoplayer.drm.DrmSessionManagerProvider;\n"
        "import androidx.media3.exoplayer.drm.DefaultDrmSessionManagerProvider;\n"
        "import androidx.media3.exoplayer.rtsp.RtspMediaSource;","media imports")
    code=one(code,"import com.fongmi.android.tv.App;",
        "import com.fongmi.android.tv.App;\n"
        "import com.fingmi.integration.xray.XrayPlaybackDataSourceFactory;\n"
        "import com.fingmi.xray.network.XrayHttpClient;","media session network import")
    code=one(code,"import java.io.File;",
        "import android.net.Uri;\nimport java.io.File;","RTSP URI import")
    code=one(code,"    private final SubtitleTranscriptSession subtitleTranscriptSession;",
        "    private final SubtitleTranscriptSession subtitleTranscriptSession;\n"
        "    private final XrayHttpClient proxy;","media session bound proxy")
    code=one(code,
        "    private ExoMediaSourceFactory(LibassPlaybackSession libassPlaybackSession, SubtitleTranscriptSession subtitleTranscriptSession) {",
        "    private ExoMediaSourceFactory(LibassPlaybackSession libassPlaybackSession, SubtitleTranscriptSession subtitleTranscriptSession, XrayHttpClient proxy) {\n"
        "        this.proxy = proxy;","media factory constructor")
    code=one(code,
        "    static MediaSourceFactorySupplier supplier(LibassPlaybackSession libassPlaybackSession, SubtitleTranscriptSession subtitleTranscriptSession) {",
        "    static MediaSourceFactorySupplier supplier(LibassPlaybackSession libassPlaybackSession, SubtitleTranscriptSession subtitleTranscriptSession, XrayHttpClient proxy) {",
        "media factory supplier")
    code=one(code,
        "return new ExoMediaSourceFactory(libassPlaybackSession, subtitleTranscriptSession);",
        "return new ExoMediaSourceFactory(libassPlaybackSession, subtitleTranscriptSession, proxy);",
        "media supplier session ownership")
    code=one(code,
        "        for (ConcatenatingUrl.Segment segment : segments) builder.add(factory.createMediaSource(mediaItem.buildUpon().setUri(UriUtil.uri(segment.url())).build()), segment.durationMs());",
        """        for (ConcatenatingUrl.Segment segment : segments) {
            MediaItem segmentItem = mediaItem.buildUpon().setUri(UriUtil.uri(segment.url())).build();
            // Resolve each part independently. A concatenation can mix
            // HTTP and RTSP; never let RTSP bypass the Xray socket factory.
            MediaSource.Factory segmentFactory = proxy == null ? factory : createMediaSourceFactory(segmentItem);
            builder.add(segmentFactory.createMediaSource(segmentItem), segment.durationMs());
        }""","Xray per-segment transport isolation")
    code=one(code,
        "    private MediaSource.Factory createMediaSourceFactory(MediaItem mediaItem) {\n"
        "        SubtitleTranscript transcript = subtitleTranscriptSession.forMediaItem(mediaItem);",
        """    private MediaSource.Factory createMediaSourceFactory(MediaItem mediaItem) {
        // RTSP and RTSPT must use the dedicated Xray socket transport.
        if (proxy != null && mediaItem.localConfiguration != null) {
            Uri uri = mediaItem.localConfiguration.uri;
            String scheme = uri.getScheme();
            if ("rtsp".equalsIgnoreCase(scheme) || "rtspt".equalsIgnoreCase(scheme)) {
                RtspMediaSource.Factory rtsp = new RtspMediaSource.Factory()
                        .setForceUseRtpTcp(true).setSocketFactory(proxy.rtspSocketFactory());
                String userAgent = ExoUtil.extractHeaders(mediaItem).get("User-Agent");
                if (userAgent != null && userAgent.codePoints().anyMatch(cp -> !Character.isWhitespace(cp))) rtsp.setUserAgent(userAgent);
                return rtsp;
            }
        }
        SubtitleTranscript transcript = subtitleTranscriptSession.forMediaItem(mediaItem);""",
        "Xray RTSP factory")
    code=one(code,
        "        DataSource.Factory dataSourceFactory = createDataSourceFactory(ExoUtil.extractHeaders(mediaItem), ExoUtil.extractAuth(mediaItem));",
        """        DataSource.Factory dataSourceFactory = proxy == null
                ? createDataSourceFactory(ExoUtil.extractHeaders(mediaItem), ExoUtil.extractAuth(mediaItem))
                : XrayPlaybackDataSourceFactory.create(ExoUtil.extractHeaders(mediaItem), ExoUtil.extractAuth(mediaItem), proxy);""",
        "Xray-only data source handoff")
    code=one(code,
        "        MediaSource.Factory factory = new DefaultMediaSourceFactory(dataSourceFactory, extractorsFactory).setSubtitleParserFactory(subtitleParserFactory);",
        """        MediaSource.Factory factory = new DefaultMediaSourceFactory(dataSourceFactory, extractorsFactory).setSubtitleParserFactory(subtitleParserFactory);
        if (proxy != null) {
            // DRM licenses must use the session's proxy, not the direct client.
            DefaultDrmSessionManagerProvider drm = new DefaultDrmSessionManagerProvider();
            drm.setDrmHttpDataSourceFactory(dataSourceFactory);
            factory.setDrmSessionManagerProvider(drm);
        }""",
        "Xray DRM network identity")
    for item in ("ConcatenatingMediaSource2.Builder","ContentTypeResolvingMediaSource.Factory",
                 "LocalClearKeyLicense.parse","SubtitleTranscriptParserFactory(transcript)",
                 "ProgressiveIsoCache.withDiskCache","XrayPlaybackDataSourceFactory.create",
                 "proxy.rtspSocketFactory()","drm.setDrmHttpDataSourceFactory(dataSourceFactory)"):
        if item not in code: raise ValueError("Exo media feature dropped: "+item)
    return code

def exo_session(code):
    code=one(code,"import com.fongmi.android.tv.App;",
        "import com.fongmi.android.tv.App;\nimport com.fingmi.xray.network.XrayHttpClient;","Exo session Xray type")
    code=one(code,"    private final ExoPlayer player;",
        "    private final ExoPlayer player;\n    private final XrayHttpClient proxy;","session-bound proxy field")
    code=one(code,"    ExoPlayerSession(AudioProcessor audioProcessor) {",
        """    ExoPlayerSession(AudioProcessor audioProcessor, XrayHttpClient proxy) {
        this.proxy = proxy;""","Exo session constructor")
    code=counted(code,
        "ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession)",
        "ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession, proxy)",
        2,"playback and preload source factories")
    for item in ("DecoderManager decoderManager","SubtitleTranscriptSession subtitleTranscriptSession",
                 "decoderManager.attach(player)","subtitleTranscriptSession.close()",
                 "LibassSubtitleController(player"):
        if item not in code: raise ValueError("Exo session feature dropped: "+item)
    return code

def exo_engine(code):
    code=one(code,"import com.fongmi.android.tv.App;",
        "import com.fongmi.android.tv.App;\n"
        "import com.fingmi.integration.xray.XrayPlaybackDataSourceFactory;\n"
        "import com.fingmi.xray.network.XrayHttpClient;","Exo engine imports")
    code=one(code,"    private final ExoPlayer player;",
        "    private final ExoPlayer player;\n    private final XrayHttpClient proxy;","engine bound transport")
    code=one(code,"    public ExoPlayerEngine(Player.Listener listener) {",
        """    public ExoPlayerEngine(Player.Listener listener) {
        this(listener, null);
    }

    public ExoPlayerEngine(Player.Listener listener, XrayHttpClient proxy) {
        this.proxy = proxy;""","engine constructor")
    code=one(code,"this.session = new ExoPlayerSession(effect.getAudioProcessor());",
        "this.session = new ExoPlayerSession(effect.getAudioProcessor(), proxy);",
        "engine -> Exo session proxy")
    code=one(code,"    private void updateEventLogger() {",
        """    public XrayHttpClient proxy() {
        return proxy;
    }

    private void updateEventLogger() {""","bound client inspection")
    code=one(code,
        "session.createMediaSource(item), ExoMediaSourceFactory.createDataSourceFactory(this.spec.getHeaders(), this.spec.getAuth()));",
        """session.createMediaSource(item), proxy == null
                        ? ExoMediaSourceFactory.createDataSourceFactory(this.spec.getHeaders(), this.spec.getAuth())
                        : XrayPlaybackDataSourceFactory.create(this.spec.getHeaders(), this.spec.getAuth(), proxy));""",
        "ISO navigation uses session proxy")
    code=counted(code,"        preload.start(player, item);",
        "        if (proxy == null) preload.start(player, item);",
        2,"direct disk preload cannot leak Xray network")
    code=one(code,"    public boolean preload(PlaySpec spec, long startPositionMs, Runnable onError) {",
        """    public boolean preload(PlaySpec spec, long startPositionMs, Runnable onError) {
        if (proxy != null) return false;""","cross-session preload")
    for item in ("IsoNavigationPlayerController(player)","new ExoPlaybackLog()",
                 "new EndTrimMediaSource(source","navigation.prepareMediaSource(",
                 "LogSession.get().addListener(logListener)","XrayPlaybackDataSourceFactory.create"):
        if item not in code: raise ValueError("Exo engine feature dropped: "+item)
    return code

def engine_factory(code):
    code=one(code,"import com.fongmi.android.tv.player.exo.ExoPlayerEngine;",
        "import com.fongmi.android.tv.player.exo.ExoPlayerEngine;\n"
        "import com.fingmi.integration.xray.XrayPlaybackRouting;\n"
        "import com.fingmi.xray.network.XrayHttpClient;","engine factory imports")
    code=one(code,"    public static PlayerEngine create(PlayerEngine.Type type, Player.Listener listener) {",
        """    /** Active Xray playback owns a dedicated Exo engine. */
    public static PlayerEngine create(PlaySpec spec, XrayHttpClient proxy, Player.Listener listener) {
        return proxy == null ? create(spec, listener) : new ExoPlayerEngine(listener, proxy);
    }

    public static PlayerEngine create(PlayerEngine.Type type, Player.Listener listener) {""",
        "engine creation with Xray proxy")
    code=one(code,"    public static boolean canPreload(PlaySpec spec) {",
        """    public static boolean matches(PlayerEngine engine, PlaySpec spec, XrayHttpClient proxy) {
        if (engine == null) return false;
        return XrayPlaybackRouting.canReuseEngine(proxy,
                engine instanceof ExoPlayerEngine exo ? exo.proxy() : null,
                engine instanceof ExoPlayerEngine,
                () -> engine.getType() == resolve(spec),
                engine::needsRebuild);
    }

    public static boolean canPreload(PlaySpec spec) {""",
        "engine instance identity matching")
    for item in ("CmgConfiguration.fromMediaUri","MpvDrmSupport.supports",
                 "UriUtil.scheme(spec.getUrl())","canPreload(PlaySpec spec)",
                 "PlayerEngineFactory","XrayPlaybackRouting.canReuseEngine"):
        if item not in code: raise ValueError("Upstream engine factory feature dropped: "+item)
    return code
