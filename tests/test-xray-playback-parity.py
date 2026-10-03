#!/usr/bin/env python3
"""Guard released-APK Xray playback behaviors that current-main intentionally preserves."""

from pathlib import Path
import hashlib
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def git_blob_sha(path: str) -> str:
    data = (ROOT / path).read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


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


def require_order(path: str, *needles: str) -> None:
    text = read(path)
    positions = []
    for needle in needles:
        position = text.find(needle)
        if position < 0:
            raise SystemExit(f"{path}: missing ordered Xray parity contract: {needle}")
        positions.append(position)
    if positions != sorted(positions):
        raise SystemExit(f"{path}: released Xray control order changed: {needles}")


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

if git_blob_sha("app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngine.java") != "b245171a5a99c05f4f0630468793d947ad65d0c7":
    raise SystemExit(
        "PlayerEngine.java must remain byte-identical to FongMi/TV@c616c0aa; "
        "Xray proxy state belongs in PlayerManager/ExoPlayerEngine/PlayerEngineFactory"
    )
forbid(
    "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngine.java",
    "getXrayPort",
    "getXrayHttpClient",
    "XrayHttpClient",
)


require(
    "app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java",
    "private void syncPlayerView(Player player)",
    "getPlayerView().setPlayer(player);\n        updatePlaybackDanmakuClient();",
    "danmakuController.setOkHttpClient(player().getPlaybackHttpClient(OkHttp.player()));",
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
    "if (next != null) callback.onXrayTransitionStarted();\n\n        clearPreload();",
    "if (playbackProxy != null || !canPreloadNext()",
    "PlaybackSnapshot.capture(player)",
    "private record PlaybackSnapshot(long positionMs, boolean playWhenReady, PlaybackParameters playbackParameters, int repeatMode, float volume, long audioOffsetMs, long textOffsetMs)",
    "player.setPlaybackParameters(playbackParameters)",
    "player.setRepeatMode(repeatMode)",
    "player.setVolume(volume)",
    "player.setAudioOffsetMs(audioOffsetMs)",
    "player.setTextOffsetMs(textOffsetMs)",
    "player.setPlayWhenReady(playWhenReady)",
)

require_order(
    "app/src/leanback/res/layout/view_control_vod_action.xml",
    'android:id="@+id/next"',
    'android:id="@+id/xray"',
    'android:id="@+id/prev"',
    'android:id="@+id/parse"',
    'android:id="@+id/player"',
)

require(
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java",
    "this.session = new ExoPlayerSession(decode, listener, effect.getAudioProcessor(), proxy);",
    "if (proxy == null) session.preload(MediaItemFactory.from(spec), startPositionMs);",
    "public XrayHttpClient proxy() { return proxy; }",
)

require(
    "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java",
    "return proxy == null ? create(decode, resolve(spec), listener) : new ExoPlayerEngine(decode, listener, proxy);",
    "if (proxy != null) return engine instanceof ExoPlayerEngine exo && exo.proxy() == proxy && !engine.needsRebuild();",
    "if (engine instanceof ExoPlayerEngine exo && exo.proxy() != null) return false;",
)

require(
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java",
    "private static boolean isBlank(String value)",
    "Character.isWhitespace(codePoint)",
    '"file".equalsIgnoreCase(scheme)',
    '"content".equalsIgnoreCase(scheme)',
    '"android.resource".equalsIgnoreCase(scheme)',
    "Unsupported data source scheme while Xray is enabled",
    'if ("rtsp".equalsIgnoreCase(scheme) || "rtspt".equalsIgnoreCase(scheme))',
    ".setSocketFactory(proxy.rtspSocketFactory())",
    "DefaultDrmSessionManagerProvider drm = new DefaultDrmSessionManagerProvider();",
    "drm.setDrmHttpDataSourceFactory(getDataSourceFactory());",
    "factory.setDrmSessionManagerProvider(drm);",
    "new OkHttpDataSource.Factory(proxy == null ? OkHttp.player() : proxy.client())",
    "dataSourceFactory = proxy == null",
    "new GuardedPlaybackDataSource(upstream.createDataSource())",
)

require(
    "app/src/main/java/com/fongmi/android/tv/server/process/Media.java",
    'result.addProperty("state", getState(player));',
    'result.addProperty("speed", player.getSpeed());',
    'result.addProperty("duration", player.getDuration());',
    'result.addProperty("position", player.getPosition());',
    'result.addProperty("url", getString(player.getUrl()));',
    'result.addProperty("artwork", getString(meta.artworkUri));',
)

require(
    "app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java",
    "PlaybackIntent.choose(this, player.getUrl(), player.getHeaders(), player.isVod(), player.getPosition(), player.getMediaTitle());",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java",
    "clearArtworkTarget();\n        if (service() != null && isOwner() && player().hasXraySession()) return;",
)

require(
    "app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java",
    "public void onXrayTransitionStarted()",
    "DanmakuApi.cancelForXrayTransition();",
    "SubtitleApi.cancelForXrayTransition();",
    "if (xrayBitmapLoader != null) xrayBitmapLoader.cancelRemoteLoads();",
)

require(
    "app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java",
    "public static void cancelForXrayTransition()",
    "completion = runCompletion ? xrayCancelCompletion : null;",
    "if (completion != null) App.post(completion);",
)

require(
    "app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java",
    "public static void cancelForXrayTransition()",
    "if (call != null) call.cancel();",
    "if (download != null) download.cancel();",
    "if (completion != null) App.post(completion);",
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
    "Throwable clearFailure = clearResources(false);",
    "failRunningTransition(clearFailure);",
    "catch (Exception | LinkageError error)",
    "failRunningTransition(error);",
    "listener.onProxyError();",
    "finally {\n            closeQuietly(failed);\n        }",
    "notifyState(ERROR, XrayErrorSanitizer.sanitize(error));",
    "service.stop();",
    "finally {\n            closeQuietly(old);\n        }",
    "private static void closeQuietly(XrayHttpClient client)",
    "else retryProxyRollback(clearResources(preservePlayback));",
    "retryProxyRollback(clearResourcesAfterError());",
    "retryProxyRollback(clearResources(preserveOnStop));",
    "private void retryProxyRollback(Throwable failure)",
    "closed = true;\n\n        // stop() is asynchronous.",
    "retryProxyRollback(clearResources(false));\n        service.close();",
)



playback_session = read("xray/src/main/java/com/fingmi/xray/session/XrayPlaybackSession.java")
close_body = playback_session.split(
    "public void close()", 1
)[1].split(
    "private static boolean isBlank", 1
)[0]
if close_body.find("closed = true;") > close_body.find("retryProxyRollback(clearResources(false));"):
    raise SystemExit(
        "XrayPlaybackSession.close must seal the owner before synchronous proxy detach"
    )
if close_body.find("retryProxyRollback(clearResources(false));") > close_body.find("service.close();"):
    raise SystemExit(
        "XrayPlaybackSession.close must release playback proxy resources before disposing the Binder controller"
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
    "if (engine != previous && onEngineChanged != null) onEngineChanged.run();",
)
require_order(
    "app/src/main/java/com/fongmi/android/tv/ui/dialog/PlayerEngineDialog.java",
    "if (engine != previous && onEngineChanged != null) onEngineChanged.run();",
    "else player.setEngine(engine);",
)

video_activity = read("app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java")
new_intent = video_activity.split("protected void onNewIntent(Intent intent)", 1)[1].split(
    "protected void initView(Bundle savedInstanceState)", 1
)[0]
if "resetXrayForPlaybackChange();" not in new_intent:
    raise SystemExit(
        "VideoActivity new-intent must invalidate READY state and begin a fresh Xray playback identity"
    )
if 'mXray.begin("vod:" + ++mPlaybackEpoch);' in new_intent or "mXray.end();" in new_intent:
    raise SystemExit(
        "VideoActivity new-intent must use the shared playback-change reset instead of bypassing its READY-state guard"
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
    "if (mXray != null) mXray.stop(preservePlayback);",
    "if (mXray != null) mXray.close();",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",
    "clearArtworkTarget()",
    "this::resetXrayForPlaybackChange",
    "mXray.stop(preservePlayback)",
    "player().clearPlaybackProxyPreservingState()",
    "mXrayPendingChannelResume",
    "mXrayStartedFromExistingPlayback",
    "mXrayRefreshMetadataOnDetach",
    "mLive.resumeChannelAfterXrayStart()",
    "private OkHttpClient xrayMetadataClient()",
    "private void refreshXrayAwareMetadata()",
    "!getHome().getEpgXml().isEmpty() && mChannel.getDataList().isEmpty()",
    "mViewModel.parseXml(getHome(), client);",
    "mViewModel.getEpg(mChannel, client);",
    "boolean startedFromExisting = mXrayStartedFromExistingPlayback;",
    "if (!startedFromExisting && !message.isEmpty()) showError(message);",
    "XrayPlaybackSession.supportsDirectLiveSource(mChannel.getCurrent())",
    "if (!message.isEmpty()) Notify.show(message);",
    "if (mXray != null) mXray.stop(preservePlayback);",
    "if (mXray != null) mXray.close();",
)

forbid(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java",
    "The previous session client may already be closing during a swap.",
    "catch (IllegalStateException ignored)",
)

live_activity = (ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java").read_text(encoding="utf-8")
live_proxy_changed = live_activity.split(
    "@Override public void onProxyChanged(XrayHttpClient resources, boolean preserve)", 1
)[1].split("@Override public void onProxyError()", 1)[0]
live_proxy_error = live_activity.split(
    "@Override public void onProxyError()", 1
)[1].split("@Override public void onStateChanged", 1)[0]
if "boolean refreshMetadata = resources != null || mXrayRefreshMetadataOnDetach;" not in live_proxy_changed:
    raise SystemExit("LiveActivity must distinguish proxy install/manual stop from ordinary Xray detach")
if "if (refreshMetadata) refreshXrayAwareMetadata();" not in live_proxy_changed:
    raise SystemExit("LiveActivity proxy transition must restart metadata only for the allowed transition kinds")
if "mXrayRefreshMetadataOnDetach = false;" not in live_proxy_changed:
    raise SystemExit("LiveActivity must consume the one-shot manual-stop metadata refresh flag")
if "refreshXrayAwareMetadata();" not in live_proxy_error:
    raise SystemExit("LiveActivity Xray ERROR rollback must restart XML/EPG metadata on the direct client")

live_on_xray = live_activity.split("private void onXray()", 1)[1].split("private void onPlayer()", 1)[0]
if "mXrayRefreshMetadataOnDetach = mXray.state() == XraySessionListener.RUNNING;" not in live_on_xray:
    raise SystemExit("LiveActivity manual Xray stop must arm direct metadata refresh only for an installed proxy")

live_on_stop = live_activity.split("protected void onStop()", 1)[1].split("protected void onBackInvoked()", 1)[0]
if "mXrayRefreshMetadataOnDetach = false;" not in live_on_stop:
    raise SystemExit("LiveActivity lifecycle stop must not restart Live metadata after Xray detach")

live_identity_reset = live_activity.split(
    "public void resetXrayForPlaybackChange()", 1
)[1].split("public void resetPlaybackForError", 1)[0]
if "mXrayRefreshMetadataOnDetach = false;" not in live_identity_reset:
    raise SystemExit("LiveActivity playback identity changes must clear pending manual-stop metadata refresh")

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
    "setWidgetLogoSuppressed(resources != null)",
    "setWidgetLogoSuppressed(false)",
    "setWidgetLogoSuppressed(mXray != null && mXray.isActive())",
    "Glide.with(mBinding.widget.logo).clear(mBinding.widget.logo)",
    "mBinding.widget.logo.setImageDrawable(null)",
)


IDENTITY_GATE = ROOT / "xray/src/main/java/com/fingmi/xray/session/PlaybackIdentityGate.java"
IDENTITY_HARNESS = r"""
package com.fingmi.xray.session;

public final class PlaybackIdentityGateTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static void same(Object expected, Object actual, String message) {
        if (!java.util.Objects.equals(expected, actual)) {
            throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        PlaybackIdentityGate gate = new PlaybackIdentityGate();

        check(!gate.hasIdentity(), "initial identity");
        same(null, gate.mediaUrl(), "initial media");
        check(gate.generation() == 0L, "initial generation");

        check(gate.begin("vod:a"), "first identity must start");
        check(gate.hasIdentity(), "identity must be active");
        check(gate.generation() == 1L, "first generation");
        same(null, gate.mediaUrl(), "new identity clears media");

        check(!gate.begin("vod:a"), "same identity must not reset");
        check(gate.generation() == 1L, "same identity keeps generation");

        gate.provisional("https://media.example/one");
        same("https://media.example/one", gate.mediaUrl(), "provisional media");
        gate.provisional("https://media.example/two");
        same("https://media.example/one", gate.mediaUrl(), "provisional cannot replace media");

        check(!gate.resolved("https://media.example/one"), "same resolved URL is not a change");
        check(gate.resolved("https://cdn.example/two"), "resolved URL may change inside one identity");
        same("https://cdn.example/two", gate.mediaUrl(), "resolved media updates in place");
        check(gate.generation() == 1L, "resolved URL does not change identity generation");

        check(gate.begin("vod:b"), "new logical identity must reset");
        check(gate.generation() == 2L, "second identity generation");
        same(null, gate.mediaUrl(), "new logical identity clears prior media");

        gate.end();
        check(!gate.hasIdentity(), "end clears identity");
        same(null, gate.mediaUrl(), "end clears media");
        check(gate.generation() == 3L, "end advances identity generation");

        gate.end();
        check(gate.generation() == 3L, "repeated end is idempotent");
        System.out.println("PASS playback identity gate");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-playback-identity-") as directory:
    work = Path(directory)
    harness = work / "com/fingmi/xray/session/PlaybackIdentityGateTest.java"
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text(IDENTITY_HARNESS.strip() + "\n", encoding="utf-8")
    classes = work / "classes"
    subprocess.run(
        [
            "java",
            "com.sun.tools.javac.Main",
            "--release",
            "17",
            "-d",
            str(classes),
            str(IDENTITY_GATE),
            str(harness),
        ],
        check=True,
    )
    subprocess.run(
        [
            "java",
            "-cp",
            str(classes),
            "com.fingmi.xray.session.PlaybackIdentityGateTest",
        ],
        check=True,
    )

print("Xray playback parity guards passed")
