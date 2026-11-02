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
    s=one(s,
        "    private void onPlaybackReplaced() {\n        playbackReplaced = true;",
        "    private void onPlaybackReplaced() {\n        playbackReplaced = true;\n"
        "        onXrayBindingReplaced();",
        "ownership changed notification")
    for key in ("mService.claimBinding(getNavigationCallback(), this::onPlaybackReplaced);",
                "playbackPlayerState.setValue(null);",
                "getSeekView().setPlayer(null);",
                "releasePlaybackService();"):
        if key not in s:
            raise ValueError("Upstream playback owner behavior changed: "+key)
    return s
