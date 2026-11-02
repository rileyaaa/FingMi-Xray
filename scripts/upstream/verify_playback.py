#!/usr/bin/env python3
"""Fail closed when a FongMi upstream upgrade loses the Xray media path.

This guard verifies only minimum Xray transport and lifecycle integration;
normal FongMi playback, media features and native ABI are not validated here.
"""
import argparse
from pathlib import Path

# A changed upstream API must produce an actionable error rather than silently
# building a direct-network player with a visually present Xray switch.
REQUIRED = {
    "app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java": (
        "setPlaybackProxy(",
        "clearPlaybackProxyPreservingState()",
        "hasXraySession()",
        "getPlaybackHttpClient(",
        "XrayPlaybackRouting.activeProxy(",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java": (
        "XrayPlaybackRouting.canReuseEngine(",
        "new ExoPlayerEngine(",
        "XrayHttpClient proxy",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java": (
        "XrayHttpClient proxy",
        "this.proxy = proxy;",
        "ExoPlayerSession(",
        "proxy()",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerSession.java": (
        "XrayHttpClient proxy",
        "ExoMediaSourceFactory.supplier(",
        "libassPlaybackSession, proxy)",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java": (
        "XrayGuardedPlaybackDataSource(",
        "dataSourceFactory = proxy == null",
        ".setSocketFactory(proxy.rtspSocketFactory())",
        "drm.setDrmHttpDataSourceFactory(getDataSourceFactory());",
        "new OkHttpDataSource.Factory(proxy == null ? OkHttp.player() : proxy.client())",
    ),
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java": (
        "new XrayPlaybackSession(",
        "player().setPlaybackProxy(",
        "player().clearPlaybackProxyPreservingState()",
        "player().getPlaybackHttpClient(",
    ),
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java": (
        "new XrayPlaybackSession(",
        "player().setPlaybackProxy(",
        "player().clearPlaybackProxyPreservingState()",
        "player().hasXraySession()",
    ),
    "app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java": (
        "onXrayTransitionStarted()",
        "DanmakuApi.cancelForXrayTransition();",
        "SubtitleApi.cancelForXrayTransition();",
        "xrayBitmapLoader.cancelRemoteLoads();",
    ),
}


def audit(sources):
    errors = []
    for path, anchors in REQUIRED.items():
        code = sources.get(path)
        if code is None:
            errors.append(f"{path}: MISSING SOURCE")
            continue
        for anchor in anchors:
            if anchor not in code:
                errors.append(f"{path}: missing {anchor}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    sources = {}
    for name in REQUIRED:
        file = args.root / name
        sources[name] = file.read_text(encoding="utf-8") if file.is_file() else None
    errors = audit(sources)
    if errors:
        raise SystemExit("BLOCKED: Xray playback transport contract incomplete:\n- " + "\n- ".join(errors))
    print(f"PASS Xray playback transport contract: {len(REQUIRED)} upstream integration points")


if __name__ == "__main__":
    main()
