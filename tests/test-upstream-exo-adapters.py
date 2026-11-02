#!/usr/bin/env python3
"""Offline fixtures and optional real-upstream checks for 5.8.7 Exo overlays."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/upstream"))
from exo_adapters import media_factory,exo_session,exo_engine,engine_factory
from player_manager_adapter import player_manager

def rejects(fn,source):
    try: fn(source)
    except ValueError: return
    raise AssertionError(fn.__name__+" must fail closed when upstream API drifts")

media='''import androidx.media3.exoplayer.drm.DrmSessionManagerProvider;
import com.fongmi.android.tv.App;
import java.io.File;
public class ExoMediaSourceFactory {
 private final SubtitleTranscriptSession subtitleTranscriptSession;
    private ExoMediaSourceFactory(LibassPlaybackSession libassPlaybackSession, SubtitleTranscriptSession subtitleTranscriptSession) {
      this.subtitleTranscriptSession=subtitleTranscriptSession;
    }
    static MediaSourceFactorySupplier supplier(LibassPlaybackSession libassPlaybackSession, SubtitleTranscriptSession subtitleTranscriptSession) {
      return new ExoMediaSourceFactory(libassPlaybackSession, subtitleTranscriptSession);
    }
    private MediaSource.Factory createMediaSourceFactory(MediaItem mediaItem) {
        SubtitleTranscript transcript = subtitleTranscriptSession.forMediaItem(mediaItem);
        LocalClearKeyLicense.parse(mediaItem.localConfiguration.drmConfiguration);
        new SubtitleTranscriptParserFactory(transcript);
        DataSource.Factory dataSourceFactory = createDataSourceFactory(ExoUtil.extractHeaders(mediaItem), ExoUtil.extractAuth(mediaItem));
        MediaSource.Factory factory = new DefaultMediaSourceFactory(dataSourceFactory, extractorsFactory).setSubtitleParserFactory(subtitleParserFactory);
        return new ContentTypeResolvingMediaSource.Factory(factory, dataSourceFactory);
    }
    void preserve() {
        for (ConcatenatingUrl.Segment segment : segments) builder.add(factory.createMediaSource(mediaItem.buildUpon().setUri(UriUtil.uri(segment.url())).build()), segment.durationMs());
       new ConcatenatingMediaSource2.Builder();
       ProgressiveIsoCache.withDiskCache(factory, cache);
    }
}'''
m=media_factory(media)
assert "createMediaSourceFactory(segmentItem)" in m, "mixed-protocol media must use its own Xray factory"
for marker in ("XrayPlaybackDataSourceFactory.create(","proxy.rtspSocketFactory()",
               "drm.setDrmHttpDataSourceFactory(dataSourceFactory)",
               "ConcatenatingMediaSource2.Builder","ProgressiveIsoCache.withDiskCache",
               "SubtitleTranscriptParserFactory(transcript)","ContentTypeResolvingMediaSource.Factory"):
    assert marker in m,marker
rejects(media_factory,media.replace("ContentTypeResolvingMediaSource.Factory","AnotherFactory"))

session='''import com.fongmi.android.tv.App;
class ExoPlayerSession {
    private final ExoPlayer player;
    ExoPlayerSession(AudioProcessor audioProcessor) {
        new DecoderManager(); decoderManager.attach(player);
        new SubtitleTranscriptSession();
        new LibassSubtitleController(player, sub);
    }
    private MediaSource createMediaSource() {
        return ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession).get().createMediaSource(item);
    }
    private Builder createPreloadManagerBuilder() {
        return builder.setMediaSourceFactorySupplier(ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession));
    }
    void close() { subtitleTranscriptSession.close(); }
    private DecoderManager decoderManager;
    private SubtitleTranscriptSession subtitleTranscriptSession;
}'''
s=exo_session(session)
assert s.count("ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession, proxy)")==2
assert "decoderManager.attach(player)" in s
rejects(exo_session,session.replace("subtitleTranscriptSession.close()","subtitleTranscriptSession.shutdown()"))

engine='''import com.fongmi.android.tv.App;
public class ExoPlayerEngine {
    private final ExoPlayer player;
    public ExoPlayerEngine(Player.Listener listener) {
        this.session = new ExoPlayerSession(effect.getAudioProcessor());
        new IsoNavigationPlayerController(player);
        new ExoPlaybackLog();
        LogSession.get().addListener(logListener);
    }
    private void updateEventLogger() {}
    private void setMediaItem() {
        MediaSource source = navigation.prepareMediaSource(App.get(),
                session.createMediaSource(item), ExoMediaSourceFactory.createDataSourceFactory(this.spec.getHeaders(), this.spec.getAuth()));
        new EndTrimMediaSource(source, ending);
        preload.start(player, item);
    }
    public boolean preload(PlaySpec spec, long startPositionMs, Runnable onError) {
        preload.start(player, item);
        return true;
    }
}'''
e=exo_engine(engine)
assert e.count("if (proxy == null) preload.start(player, item);")==2
assert "if (proxy != null) return false;" in e
assert "XrayPlaybackDataSourceFactory.create(this.spec.getHeaders(), this.spec.getAuth(), proxy)" in e
rejects(exo_engine,engine.replace("navigation.prepareMediaSource(","navigation.prepare("))

factory='''import com.fongmi.android.tv.player.exo.ExoPlayerEngine;
public final class PlayerEngineFactory {
    public static PlayerEngine create(PlayerEngine.Type type, Player.Listener listener) {
        return new ExoPlayerEngine(listener);
    }
    public static boolean canPreload(PlaySpec spec) {
        return !isCmg(spec);
    }
    private static PlayerEngine.Type resolve(PlaySpec spec) {
        CmgConfiguration.fromMediaUri(spec.getUri());
        MpvDrmSupport.supports(item);
        UriUtil.scheme(spec.getUrl());
        return EXO;
    }
}'''
f=engine_factory(factory)
assert "XrayPlaybackRouting.canReuseEngine(" in f
assert "new ExoPlayerEngine(listener, proxy)" in f
rejects(engine_factory,factory.replace("MpvDrmSupport.supports","MpvDrmSupport.check"))

manager='''import com.fongmi.android.tv.player.exo.ExoPlayerEngine;
import java.util.UUID;
class PlayerManager {
    private PlaySpec spec;
    public boolean canPreloadNext() {
        return PreloadSetting.isEnabled() && engine.getType() == EXO;
    }
    void setEngine(int target) {
        if (isEmpty() || PlayerEngineFactory.matches(engine, spec)) return;
    }
    public void clear() {
        spec = null;
    }
    public boolean preload(PlaySpec spec, long startPositionMs, Object tag) {
        if (!canPreloadNext() || spec == null) return false;
        return true;
    }
    private void ensureEngine(PlaySpec spec) {
        if (mpvDrmExoFallback) {
            return;
        }
        if (PlayerEngineFactory.matches(engine, spec)) return;
        replaceEngine(PlayerEngineFactory.create(spec, listener));
    }
    public void start(PlaySpec spec, long timeout, long startPositionMs) {
        this.spec = spec;
    }
    public void parse(String key, Result result, boolean useParse, MediaMetadata metadata, long startPositionMs, long endingMs) {
        stopParse();
    }
    public interface Callback {}
    private record PlaybackSnapshot(long selectedIsoEditionIndex) {
        static PlaybackSnapshot capture(PlayerManager manager) {return null;}
        void restorePlayerState(PlayerManager manager) {}
    }
    private void replaceEngine(PlayerEngine replacement) {}
    void preserve() {
        IsoDiscPreparation.isIso(media);
        PendingPreload queuedPreload;
        timeshift.isReplaying();
        PlaybackSnapshot.capture(this);
        snapshot.restorePlayerState(this);
    }
}'''
m=player_manager(manager)
for marker in ("setPlaybackProxy(XrayHttpClient next, boolean preservePlayback)",
               "clearPlaybackProxyPreservingState()","XrayPlaybackRouting.activeProxy",
               "if (next != null) callback.onXrayTransitionStarted();",
               "!hasXraySession() && PreloadSetting.isEnabled()",
               "else if (bound != null) replaceEngine(PlayerEngineFactory.create(listener));"):
    assert marker in m,marker
rejects(player_manager,manager.replace("private void replaceEngine(PlayerEngine replacement)",
                                       "private void installEngine(PlayerEngine replacement)"))

p=argparse.ArgumentParser()
p.add_argument("--upstream",type=Path)
p.add_argument("--target")
args=p.parse_args()
if bool(args.upstream)!=bool(args.target):
    p.error("--upstream and --target are required together")
if args.upstream:
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    for name,transform in (
        ("app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java",media_factory),
        ("app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerSession.java",exo_session),
        ("app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java",exo_engine),
        ("app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java",engine_factory),
        ("app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java",player_manager),
    ):
        actual=blob(args.upstream,tree[name]).decode("utf-8")
        candidate=transform(actual)
        assert candidate!=actual and len(candidate)>len(actual),name
    print("PASS five Exo/manager adapters against public commit "+args.target)
print("PASS guarded 5.8.7 Exo media/session/engine/factory fixture and drift checks")
