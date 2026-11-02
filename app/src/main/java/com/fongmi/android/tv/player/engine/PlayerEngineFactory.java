package com.fongmi.android.tv.player.engine;

import static com.fongmi.android.tv.player.engine.PlayerEngine.Type.EXO;
import static com.fongmi.android.tv.player.engine.PlayerEngine.Type.MPV;

import androidx.media3.common.Player;

import com.fongmi.android.tv.player.exo.ExoPlayerEngine;
import com.fingmi.integration.xray.XrayPlaybackRouting;
import com.fingmi.xray.network.XrayHttpClient;
import com.fongmi.android.tv.player.media.PlaySpec;
import com.fongmi.android.tv.player.mpv.MpvPlayerEngine;
import com.fongmi.android.tv.setting.PlayerSetting;
import com.fongmi.android.tv.utils.UrlUtil;

public final class PlayerEngineFactory {

    public static PlayerEngine create(int decode, Player.Listener listener) {
        return create(decode, resolve(), listener);
    }

    public static PlayerEngine create(int decode, PlaySpec spec, Player.Listener listener) {
        return create(decode, spec, null, listener);
    }

    public static PlayerEngine create(int decode, PlaySpec spec, XrayHttpClient proxy, Player.Listener listener) {
        return proxy == null ? create(decode, resolve(spec), listener) : new ExoPlayerEngine(decode, listener, proxy);
    }

    public static PlayerEngine create(int decode, PlayerEngine.Type type, Player.Listener listener) {
        return switch (type) {
            case EXO -> new ExoPlayerEngine(decode, listener);
            case MPV -> new MpvPlayerEngine(decode, listener);
        };
    }

    public static boolean matches(PlayerEngine engine, PlaySpec spec) {
        return matches(engine, spec, null);
    }

    public static boolean matches(PlayerEngine engine, PlaySpec spec, XrayHttpClient proxy) {
        if (engine == null) return false;
        // Defer upstream resolution and rebuild probing until the proxy
        // identity matches. This preserves the old engine release ordering.
        return XrayPlaybackRouting.canReuseEngine(
                proxy,
                engine instanceof ExoPlayerEngine exo ? exo.proxy() : null,
                engine instanceof ExoPlayerEngine,
                () -> engine.getType() == resolve(spec),
                engine::needsRebuild);
    }

    private static PlayerEngine.Type resolve(PlaySpec spec) {
        if (requiresExo(spec)) return EXO;
        if (!isMpvReady()) return EXO;
        return MPV;
    }

    private static PlayerEngine.Type resolve() {
        return isMpvReady() ? MPV : EXO;
    }

    private static boolean requiresExo(PlaySpec spec) {
        return spec.getDrm() != null || "smb".equals(UrlUtil.scheme(spec.getUrl()));
    }

    private static boolean isMpvReady() {
        return PlayerSetting.isMpv() && MpvPlayerEngine.isAvailable();
    }
}
