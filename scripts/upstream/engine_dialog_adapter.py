#!/usr/bin/env python3
"""Keep 5.8.7 official engine settings and only notify Xray on an actual change."""
from exo_adapters import one


def player_engine_dialog(s):
    s=one(s,
        "        if (!PlaybackDialog.isCurrentPlayer(this, player)) return;\n"
        "        player.setEngine(engine);",
        """        if (!PlaybackDialog.isCurrentPlayer(this, player)) return;
        if (PlaybackAction.getEngine(player) != engine) {
            PlaybackActivity owner = getPlaybackActivity();
            if (owner != null) owner.onXrayEngineChanged();
        }
        player.setEngine(engine);""",
        "engine-change Xray identity notification")
    for needle in ("binding.exo.setOnClickListener(view -> selectEngine(PlayerSetting.ENGINE_EXO));",
                   "binding.mpv.setOnClickListener(view -> selectEngine(PlayerSetting.ENGINE_MPV));",
                   "player.setEngine(engine);",
                   "owner.onXrayEngineChanged();",
                   "PlaybackDialog.isCurrentPlayer(this, player)"):
        if needle not in s:
            raise ValueError("Public engine dialog changed: "+needle)
    return s
