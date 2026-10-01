package com.fingmi.xray.session;

import java.util.Objects;

/** Identity and resolved URL for exactly one VOD or Live playback request. */
public final class PlaybackIdentityGate {
    private String identity;
    private String mediaUrl;
    private boolean provisional;
    private long generation;

    public boolean begin(String next) {
        if (Objects.equals(identity, next)) return false;
        identity = next;
        mediaUrl = null;
        provisional = false;
        generation++;
        return true;
    }

    /** Returns true when the resolved URL changed without changing playback identity. */
    public boolean resolved(String next) {
        if (identity == null) return false;
        boolean changed = mediaUrl != null && !Objects.equals(mediaUrl, next);
        mediaUrl = next;
        provisional = false;
        return changed;
    }

    public void provisional(String source) {
        if (identity == null || mediaUrl != null) return;
        mediaUrl = source;
        provisional = true;
    }

    public void end() { begin(null); }
    public boolean hasIdentity() { return identity != null; }
    public String mediaUrl() { return mediaUrl; }
    public long generation() { return generation; }
}
