#!/usr/bin/env python3
"""Minimal TV playback ownership hook generated from FongMi/TV 5.8.7 source.

The upstream binding/reclaim/Media3 session logic is untouched. An activity
losing the service binding gets one synchronous chance to close its Xray
playback identity before the next owner can start playback.
"""
from exo_adapters import one


def playback_activity(s):
    s=one(s,"    protected void onReclaim() {\n    }",
        """    protected void onReclaim() {
    }

    /** Stop old Xray sessions when another screen claims this playback. */
    protected void onXrayBindingReplaced() {
    }""","Xray owner callback declaration")
    s=one(s,"    protected void onServiceConnected() {",
        """    /** Xray-only hook used when user actually changes the engine choice. */
    public void onXrayEngineChanged() {
    }

    protected void onServiceConnected() {""",
        "engine selection is an Xray playback identity boundary")
    s=one(s,"    private void setDanmakuSource(@Nullable Uri uri) {",
        """    /** Clear both modern upstream LiveDanmaku and DanmakuController. */
    protected final void clearXrayDanmakuSource() {
        setDanmakuSource(null);
    }

    private void setDanmakuSource(@Nullable Uri uri) {""",
        "5.8.7 official media source owner")
    s=one(s,
        "    private void onPlaybackReplaced() {\n        playbackReplaced = true;",
        "    private void onPlaybackReplaced() {\n        playbackReplaced = true;\n"
        "        onXrayBindingReplaced();",
        "ownership changed notification")
    for key in ("mService.claimBinding(getNavigationCallback(), this::onPlaybackReplaced);",
                "playbackPlayerState.setValue(null);",
                "getSeekView().setPlayer(null);",
                "releasePlaybackService();",
                "protected final void clearXrayDanmakuSource()",
                "public void onXrayEngineChanged()"):
        if key not in s:
            raise ValueError("Upstream playback owner behavior changed: "+key)
    return s


def video_view_model(s):
    s=one(s,"    @Override\n    public void cancelContent() {",
        """    /** Invalidate any direct-network VOD requests before Xray attach. */
    public void cancelXrayTransitionRequests() {
        requestTasks.cancel(TaskType.DETAIL);
        requestTasks.cancel(TaskType.PLAYBACK);
        requestTasks.cancel(TaskType.PRELOAD);
        stopSearch();
    }

    @Override
    public void cancelContent() {""","VOD pending direct request cancellation")
    for key in ("requestTasks.cancel(TaskType.PRELOAD);",
                "requestTasks.execute(", "stopSearch();",
                "playbackState.reset();"):
        if key not in s:
            raise ValueError("Upstream VOD request generation changed: "+key)
    return s
