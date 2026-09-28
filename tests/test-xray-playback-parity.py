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

def forbid(path: str, *needles: str) -> None:
    text = read(path)
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"{path}: released Xray parity forbids: {present}")


require(
    "xray/src/main/java/com/fingmi/xray/session/XrayPlaybackSession.java",
    "playback.resolved(url);",
    "if (!playback.hasIdentity())",
)
require(
    "xray/src/main/java/com/fingmi/xray/session/XrayPlaybackAddress.java",
    "URI.create(value.trim())",
    "\"http\"",
    "\"https\"",
    "\"rtsp\"",
    "\"rtspt\"",
    "path.endsWith(\".strm\")",
    "host.contains(\"youtube.com\")",
    "host.contains(\"youtu.be\")",
)

forbid(
    "xray/src/main/java/com/fingmi/xray/session/XrayPlaybackSession.java",
    "if (playback.resolved(url)) stop(false);",
    "service.isRunning() && !supports(url)",
    "if (!playback.hasIdentity() || !supports(playback.mediaUrl())) {\n                service.stop();",
)

require(
    "app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java",
    "synchronized void setPlaybackProxy",
    "boolean hasXraySession()",
    "withHttpClient(",
    "onXrayTransitionStarted()",
    "clearPlaybackProxyPreservingState()",
    "XrayRestore",
    "xrayRestore == null",
    "return !hasXraySession()",
    "if (next == null && !preservePlayback)",
    "if (spec != null) ensureEngine(spec.checkUa());",
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
    "XrayPlaybackAddress.supportsDirectLiveSource(url)",
    "onProxyError()",
    "clearResourcesAfterError()",
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
    "player().clearPlaybackProxyPreservingState()",
    "mXrayProxyFailed",
    "state == XraySessionListener.IDLE && !message.isEmpty()",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",
    "clearArtworkTarget()",
    "this::resetXrayForPlaybackChange",
    "mXray.stop(preservePlayback)",
    "player().clearPlaybackProxyPreservingState()",
    "mXrayPendingChannelResume",
    "mXrayStartedFromExistingPlayback",
    "mLive.resumeChannelAfterXrayStart()",
    "boolean startedFromExisting = mXrayStartedFromExistingPlayback;",
    "if (!startedFromExisting && !message.isEmpty()) showError(message);",
    "XrayPlaybackSession.supportsDirectLiveSource(mChannel.getCurrent())",
    "if (!message.isEmpty()) Notify.show(message);",
)

forbid(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",
    "The previous session client may already be closing during a swap.",
    "catch (IllegalStateException ignored)",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySettingsController.java",
    "public long validate(",
    "replaceClient()",
    "Xray operation timed out",
    "XrayOperationIds.next()",
)


require(
    "app/src/main/java/com/fongmi/android/tv/playback/live/LivePlaybackController.java",
    "selectChannel(Channel channel, boolean resetXray)",
    "resumeChannelAfterXrayStart()",
    "if (resetXray) host.resetXrayForPlaybackChange()",
    "requestPlayback(request, true, false)",
)

require(
    "app/src/main/java/com/fongmi/android/tv/playback/live/LivePlaybackHost.java",
    "void resetXrayForPlaybackChange()",
)

require(
    "app/src/main/java/com/fongmi/android/tv/api/LiveApi.java",
    "METADATA_TAG",
    "Thread.currentThread().isInterrupted()",
    "EpgParser.start(item, url, client, METADATA_TAG)",
    "OkHttp.newCall(actual, url, METADATA_TAG)",
)

require(
    "app/src/main/java/com/fongmi/android/tv/api/parser/EpgParser.java",
    "OkHttpClient client, String tag",
    "Download.create(url, file).tag(",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/adapter/ChannelAdapter.java",
    "mRecyclerView",
    "setImageDrawable(null)",
    "onAttachedToRecyclerView",
    "onDetachedFromRecyclerView",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",
    "cancelXrayMetadataRequests()",
    "OkHttp.cancel(normal, LiveApi.METADATA_TAG)",
    "player().getPlaybackHttpClient(normal)",
)

print("Xray playback parity guards passed")
