package com.fongmi.android.tv.player.exo;

import androidx.annotation.NonNull;
import androidx.media3.common.Format;
import androidx.media3.common.MediaItem;
import androidx.media3.common.PlaybackException;
import androidx.media3.common.Player;
import androidx.media3.common.Tracks;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.analytics.AnalyticsListener;
import androidx.media3.exoplayer.audio.AudioSink;
import androidx.media3.exoplayer.source.MediaSource;

import com.fongmi.android.tv.player.effect.PlayerEffect;
import com.fongmi.android.tv.player.engine.PlayerEngine;
import com.fongmi.android.tv.player.media.MediaItemFactory;
import com.fongmi.android.tv.player.media.PlaySpec;

import okhttp3.OkHttpClient;

/**
 * FongMi 5.6.0 ExoPlayerEngine reconstructed with the shipped FingMi-Xray delta.
 */
public class ExoPlayerEngine
        implements PlayerEngine, AnalyticsListener {

    private final ExoErrorMessageProvider provider;
    private final ExoPlayerSession session;
    private final ExoPlayerEffect effect;
    private final ExoDiskPreload preload;
    private final ExoPlayer player;
    private final int xrayPort;

    private PlaySpec spec;

    public ExoPlayerEngine(
            int decode,
            Player.Listener listener) {
        this(decode, listener, 0);
    }

    public ExoPlayerEngine(
            int decode,
            Player.Listener listener,
            int xrayPort) {
        this.xrayPort = Math.max(0, xrayPort);
        this.effect = new ExoPlayerEffect();
        this.preload = new ExoDiskPreload();
        this.provider = new ExoErrorMessageProvider();
        this.session =
                new ExoPlayerSession(
                        decode,
                        listener,
                        effect.getAudioProcessor(),
                        this.xrayPort);
        this.player = this.session.player();
        this.player.addAnalyticsListener(this);
        this.effect.setPlayer(player);
    }

    @Override
    public void onAudioTrackInitialized(
            @NonNull EventTime eventTime,
            @NonNull AudioSink.AudioTrackConfig audioTrackConfig) {
        effect.applyAudioEffect();
    }

    @Override
    public void onAudioTrackReleased(
            @NonNull EventTime eventTime,
            @NonNull AudioSink.AudioTrackConfig audioTrackConfig) {
        effect.applyAudioEffect();
    }

    @Override
    public void onTracksChanged(
            @NonNull EventTime eventTime,
            @NonNull Tracks tracks) {
        effect.applyVideoEffect();
    }

    @Override
    public Type getType() {
        return Type.EXO;
    }

    @Override
    public Player getPlayer() {
        return player;
    }

    @Override
    public int getAudioChannelCount() {
        Format format = player.getAudioFormat();
        return format == null
                ? Format.NO_VALUE
                : format.channelCount;
    }

    @Override
    public int getXrayPort() {
        return xrayPort;
    }

    @Override
    public OkHttpClient getXrayHttpClient() {
        return session.xrayResources() == null
                ? null
                : session.xrayResources().client();
    }

    @Override
    public PlayerEffect getEffect() {
        return effect;
    }

    @Override
    public void release() {
        player.removeAnalyticsListener(this);
        preload.release();
        effect.release();
        session.release();
    }

    @Override
    public void setDecode(int decode) {
        session.setDecode(decode);
    }

    @Override
    public void start(
            PlaySpec spec,
            long startPositionMs) {
        this.spec = spec;
        startInternal(startPositionMs);
    }

    @Override
    public void preload(
            PlaySpec spec,
            long startPositionMs) {
        // Shipped behavior: next-item preloading is disabled for an Xray
        // playback engine so the next episode/channel cannot silently inherit
        // the current session proxy.
        if (xrayPort > 0) return;

        session.preload(
                MediaItemFactory.from(spec),
                startPositionMs);
    }

    @Override
    public void clearPreload() {
        session.clearPreload();
    }

    @Override
    public void stop() {
        preload.stop();
        player.stop();
    }

    @Override
    public String getErrorMessage(PlaybackException e) {
        return provider.get(e);
    }

    @Override
    public ErrorAction handleError(PlaybackException e) {
        return switch (e.errorCode) {
            case PlaybackException.ERROR_CODE_BEHIND_LIVE_WINDOW ->
                    seekToDefaultPosition();
            case PlaybackException.ERROR_CODE_DECODER_INIT_FAILED,
                    PlaybackException.ERROR_CODE_DECODER_QUERY_FAILED,
                    PlaybackException.ERROR_CODE_DECODING_FAILED ->
                    ErrorAction.DECODE;
            case PlaybackException.ERROR_CODE_IO_UNSPECIFIED,
                    PlaybackException.ERROR_CODE_PARSING_CONTAINER_MALFORMED,
                    PlaybackException.ERROR_CODE_PARSING_MANIFEST_MALFORMED,
                    PlaybackException.ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED,
                    PlaybackException.ERROR_CODE_PARSING_MANIFEST_UNSUPPORTED ->
                    retryFormat(e.errorCode);
            default ->
                    ErrorAction.FATAL;
        };
    }

    private void startInternal(long position) {
        MediaItem item = MediaItemFactory.from(spec);
        MediaSource source =
                session.usePreloadedMediaSource(item);

        effect.clearAudioEffect();
        if (source == null) {
            player.setMediaItem(item, position);
        } else {
            player.setMediaSource(source, position);
        }

        // Shipped behavior: disk preload is also disabled while a Xray port is
        // attached to this engine.
        if (xrayPort == 0) {
            preload.start(player, item);
        }

        prepareAndPlay();
    }

    private void prepareAndPlay() {
        player.prepare();
        player.play();
    }

    private ErrorAction seekToDefaultPosition() {
        player.seekToDefaultPosition();
        player.prepare();
        return ErrorAction.RECOVERED;
    }

    private ErrorAction retryFormat(int errorCode) {
        spec.setFormat(ExoUtil.getMimeType(errorCode));
        startInternal(player.getCurrentPosition());
        return ErrorAction.RECOVERED;
    }
}
