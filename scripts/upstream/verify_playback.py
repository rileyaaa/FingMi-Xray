#!/usr/bin/env python3
"""Fail closed when a FongMi upstream upgrade loses the Xray media path.

This guard verifies only minimum Xray transport and lifecycle integration;
normal FongMi playback, media features and native ABI are not validated here.
"""
import argparse
import re
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



# From FongMi 5.8.7 onward Media3, disk preload, new application subtitle
# APIs and ISO navigation must remain upstream-first. These are DIFFERENT
# contracts, not relaxed checks of the obsolete 5.6.3 factory layout.
REQUIRED_587 = {
    "app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java": (
        "setPlaybackProxy(XrayHttpClient next, boolean preservePlayback)",
        "clearPlaybackProxyPreservingState()",
        "XrayPlaybackRouting.activeProxy(playbackProxy, bound)",
        "callback.onXrayTransitionStarted();",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java": (
        "XrayPlaybackRouting.canReuseEngine(",
        "new ExoPlayerEngine(listener, proxy)",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java": (
        "this.session = new ExoPlayerSession(effect.getAudioProcessor(), proxy);",
        "XrayPlaybackDataSourceFactory.create(this.spec.getHeaders(), this.spec.getAuth(), proxy)",
        "if (proxy == null) preload.start(player, item);",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerSession.java": (
        "ExoMediaSourceFactory.supplier(libassPlaybackSession, subtitleTranscriptSession, proxy)",
        "decoderManager.attach(player);",
    ),
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java": (
        "XrayPlaybackDataSourceFactory.create(",
        "proxy.rtspSocketFactory()",
        "createMediaSourceFactory(segmentItem)",
        "drm.setDrmHttpDataSourceFactory(dataSourceFactory)",
        "ContentTypeResolvingMediaSource.Factory",
    ),
    "app/src/main/java/com/fingmi/integration/xray/XraySideRequestGate.java": (
        "getPlaybackHttpClient(null)",
        "OkHttp.cancel(client, tag)",
        "usePlaybackTransport(Download download)",
    ),
    "app/src/main/java/com/fingmi/integration/xray/XrayPlaybackDataSourceFactory.java": (
        "XrayGuardedPlaybackDataSource(delegate.createDataSource())",
        "proxy.client().newCall(applyAuth(request, auth))",
    ),
    "app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java": (
        "XraySideRequestGate.bind(player);",
        "XraySideRequestGate.unbind(player);",
        "onXrayTransitionStarted()",
        "DanmakuApi.cancel();",
        "SubtitleApi.cancel();",
        "xrayBitmapLoader.cancelRemoteLoads();",
    ),
    "app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java": (
        "XraySideRequestGate.newCall(",
        "XraySideRequestGate.cancel(TAG)",
        "REQUEST_ID.incrementAndGet();",
    ),
    "app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java": (
        "XraySideRequestGate.newCall(",
        "XraySideRequestGate.usePlaybackTransport(",
        "XraySideRequestGate.cancel(TAG)",
        "ApiCallback.post(requestId, REQUEST_ID",
    ),
    "catvod/src/main/java/com/github/catvod/net/Download.java": (
        "public Download transport(Call.Factory client)",
        "playbackTransport == null ? OkHttp.client() : playbackTransport",
        "factory.newCall(request)",
    ),
    "app/src/main/java/com/fongmi/android/tv/api/LiveApi.java": (
        "XraySideRequestGate.newCall(",
    ),
    "app/src/main/java/com/fongmi/android/tv/api/parser/EpgParser.java": (
        "XraySideRequestGate.usePlaybackTransport(",
    ),
    # UI session ownership and request cancellation are not yet ported: a
    # prospective 5.8.7 build must STOP here even with all Exo helpers present.
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java": (
        "new XrayPlaybackSession(",
        "player().setPlaybackProxy(",
        "player().clearPlaybackProxyPreservingState()",
    ),
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java": (
        "new XrayPlaybackSession(",
        "player().setPlaybackProxy(",
        "player().hasXraySession()",
    ),
}


def required_for_version(source):
    match = re.search(r'versionName\s+"v(\d+)\.(\d+)\.(\d+)-xray\.(\d+)"', source)
    if not match:
        raise ValueError("Unknown fork versionName: cannot select Xray playback contract")
    version = tuple(map(int, match.groups()[:3]))
    return REQUIRED_587 if version >= (5, 8, 7) else REQUIRED


def audit(sources, requirements=None):
    if requirements is None: requirements = REQUIRED
    errors = []
    for path, anchors in requirements.items():
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
    gradle = (args.root / "app/build.gradle").read_text(encoding="utf-8")
    requirements = required_for_version(gradle)
    sources = {}
    for name in requirements:
        file = args.root / name
        sources[name] = file.read_text(encoding="utf-8") if file.is_file() else None
    errors = audit(sources, requirements)
    if errors:
        raise SystemExit("BLOCKED: Xray playback transport contract incomplete:\n- " + "\n- ".join(errors))
    print(f"PASS Xray playback transport contract: {len(requirements)} upstream integration points")


if __name__ == "__main__":
    main()
