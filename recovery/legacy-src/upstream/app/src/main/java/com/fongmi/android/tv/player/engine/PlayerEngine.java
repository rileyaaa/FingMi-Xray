package com.fongmi.android.tv.player.engine;

import androidx.media3.common.C;
import androidx.media3.common.PlaybackException;
import androidx.media3.common.Player;

import com.fongmi.android.tv.bean.Sub;
import com.fongmi.android.tv.player.effect.PlayerEffect;
import com.fongmi.android.tv.player.media.PlaySpec;

import okhttp3.OkHttpClient;

/**
 * FongMi 5.6.0 PlayerEngine reconstructed with the shipped FingMi-Xray delta.
 */
public interface PlayerEngine {

    int SOFT = C.DECODE_SOFTWARE;
    int HARD = C.DECODE_HARDWARE;

    Type getType();

    Player getPlayer();

    int getAudioChannelCount();

    /**
     * Shipped Xray delta: non-Exo engines keep the default 0.
     */
    default int getXrayPort() {
        return 0;
    }

    /**
     * Final APK exposes the per-session proxy client through the active Exo engine.
     * Non-Xray/non-Exo engines return null.
     */
    default OkHttpClient getXrayHttpClient() {
        return null;
    }

    void release();

    void setDecode(int decode);

    default PlayerEffect getEffect() {
        return PlayerEffect.NONE;
    }

    void start(PlaySpec spec, long startPositionMs);

    default void preload(PlaySpec spec, long startPositionMs) {
    }

    default void clearPreload() {
    }

    void stop();

    default void setSubtitleStyle() {
    }

    default boolean addSubtitle(Sub sub) {
        return false;
    }

    String getErrorMessage(PlaybackException e);

    ErrorAction handleError(PlaybackException e);

    enum ErrorAction {
        RECOVERED,
        DECODE,
        FATAL
    }

    enum Type {
        EXO,
        MPV
    }
}
