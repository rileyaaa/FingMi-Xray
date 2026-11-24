package com.fingmi.xray.session;

import java.util.Objects;

/** Main-thread TV Live policy; Core and HTTP ownership remain in XrayPlaybackSession. */
public final class XrayLiveAutoPlayback {
    private String group;
    private String channel;
    private boolean manuallyOff;
    private boolean automatic;
    private boolean routeResolved;
    private boolean failed;
    private boolean suspended;
    private Runnable pending;

    public boolean wants(String group, String channel, boolean matched) {
        return matched && !(manuallyOff && sameStation(group, channel));
    }

    /** Only consecutive automatic requests may retain the proxy transport. */
    public boolean prepare(String group, String channel, boolean matched) {
        boolean next = wants(group, channel, matched);
        boolean retain = automatic && next;
        if (!sameStation(group, channel)) manuallyOff = false;
        this.group = group;
        this.channel = channel;
        automatic = next;
        routeResolved = false;
        failed = false;
        pending = null;
        return retain;
    }

    private boolean sameStation(String group, String channel) {
        return Objects.equals(this.group, group) && Objects.equals(this.channel, channel);
    }

    public boolean isAutomatic() { return automatic; }

    /** Each playback identity must validate its own URL, even with a retained Core. */
    public boolean hasResolvedRoute() { return routeResolved; }

    /** True means media must not start directly. Unsupported/local targets stay direct. */
    public boolean deferResolved(XrayPlaybackSession session, String url, Runnable start) {
        if (!automatic) return false;
        if (!XrayPlaybackSession.supportsDirectLiveSource(url)) {
            cancelRequest();
            session.stop(false);
            return false;
        }
        routeResolved = true;
        if (!suspended && !failed && session.isActive() && session.resources() != null) return false;
        pending = Objects.requireNonNull(start);
        startIfNeeded(session);
        return true;
    }

    private void startIfNeeded(XrayPlaybackSession session) {
        if (!automatic || suspended || failed || pending == null) return;
        if (session.isActive() && session.resources() != null) {
            proxyReady();
        } else if (session.state() != XraySessionListener.STARTING
                && !session.enableForResolvedLive()) {
            failed = true;
        }
    }

    /** Consume the held result once, after the player receives the proxy. */
    public void proxyReady() {
        if (!automatic || suspended || failed || pending == null) return;
        Runnable start = pending;
        pending = null;
        start.run();
    }

    public void proxyFailed() {
        if (automatic) failed = true;
    }

    public boolean retry(XrayPlaybackSession session) {
        if (!automatic || !failed || pending == null || suspended) return false;
        failed = false;
        startIfNeeded(session);
        return true;
    }

    /** An explicit OFF applies to this station, including its refresh/line changes. */
    public Runnable disableManually(String group, String channel) {
        Runnable start = pending;
        this.group = group;
        this.channel = channel;
        manuallyOff = true;
        cancelRequest();
        return start;
    }

    public void enableManually() {
        manuallyOff = false;
        cancelRequest();
    }

    public void cancelRequest() {
        automatic = false;
        routeResolved = false;
        failed = false;
        pending = null;
    }

    /** Keep an unfinished request across foreground return, never the Core. */
    public void suspend(boolean keepPending) {
        suspended = true;
        if (!keepPending) cancelRequest();
    }

    public void resume(XrayPlaybackSession session) {
        suspended = false;
        startIfNeeded(session);
    }

    public void reset() {
        cancelRequest();
        group = null;
        channel = null;
        manuallyOff = false;
    }
}
