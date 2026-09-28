#!/usr/bin/env python3
"""Guard released-APK Xray playback behaviors that current-main intentionally preserves."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    text = read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"{path}: missing Xray parity contract: {missing}")


require(
    "app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java",
    "synchronized void setPlaybackProxy",
    "boolean hasXraySession()",
    "withHttpClient(",
    "onXrayTransitionStarted()",
)

require(
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java",
    '"file".equalsIgnoreCase(scheme)',
    '"content".equalsIgnoreCase(scheme)',
    '"android.resource".equalsIgnoreCase(scheme)',
    "Unsupported data source scheme while Xray is enabled",
)

require(
    "app/src/main/java/com/fongmi/android/tv/player/media/XrayArtworkBitmapLoader.java",
    "Remote artwork blocked while Xray is enabled",
    "cancelRemoteLoads()",
    '"rawresource".equals(value)',
)

require(
    "app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java",
    "XrayArtworkBitmapLoader",
    "DanmakuApi.cancelForXrayTransition()",
    "SubtitleApi.cancelForXrayTransition()",
    "xrayBitmapLoader.cancelRemoteLoads()",
)

require(
    "app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java",
    "cancel(int requestId)",
    "cancelForXrayTransition()",
    "OkHttpClient client",
    "xrayCancelCompletion",
)

require(
    "app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java",
    "cancel(int requestId)",
    "cancelForXrayTransition()",
    "OkHttpClient client",
    "currentDownload",
    "xrayCancelCompletion",
)

require(
    "app/src/main/java/com/fongmi/android/tv/ui/dialog/DanmakuSearchDialog.java",
    "player.withHttpClient(",
    "DanmakuApi.cancel(requestId)",
)

require(
    "app/src/main/java/com/fongmi/android/tv/ui/dialog/SubtitleSearchDialog.java",
    "player.withHttpClient(",
    "SubtitleApi.cancel(requestId)",
    "onXrayTransitionCancelled()",
)

require(
    "app/src/main/java/com/fongmi/android/tv/playback/vod/VodPlaybackMedia.java",
    "OkHttpClient client",
    "DanmakuApi.cancel()",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XrayPlaybackSession.java",
    "supportsDirectLiveSource",
    'endsWith(".strm")',
    'contains("youtube.com")',
    'contains("youtu.be")',
)


require(
    "app/src/main/java/com/fongmi/android/tv/model/VideoViewModel.java",
    "cancelXrayTransitionRequests()",
    "requestTasks.cancel(TaskType.DETAIL)",
    "requestTasks.cancel(TaskType.PLAYBACK)",
    "requestTasks.cancel(TaskType.PRELOAD)",
)

require(
    "app/src/main/java/com/fongmi/android/tv/playback/vod/VodPlaybackController.java",
    "host.resetXrayForPlaybackChange()",
    "clearPreloadForXray()",
)

require(
    "app/src/main/java/com/fongmi/android/tv/ui/dialog/PlayerEngineDialog.java",
    "Runnable onEngineChanged",
    "onEngineChanged.run()",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java",
    "xrayPlaybackReady",
    "mViewModel.cancelXrayTransitionRequests()",
    "Source.get().stop()",
    "OkHttp.cancelAll()",
    "clearArtworkTarget()",
    "DanmakuApi.cancel(mDanmakuRequestId)",
    "this::resetXrayForPlaybackChange",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",
    "clearArtworkTarget()",
    "this::resetXrayForPlaybackChange",
    "mXray.stop(preservePlayback)",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySettingsController.java",
    "public long validate(",
    "replaceClient()",
    "Xray operation timed out",
    "XrayOperationIds.next()",
)

print("Xray playback parity guards passed")
