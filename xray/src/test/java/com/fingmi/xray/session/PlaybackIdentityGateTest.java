package com.fingmi.xray.session;

import static org.junit.Assert.*;
import org.junit.Test;

public class PlaybackIdentityGateTest {
    @Test public void vodEpisodeAndSourceStartDirect() {
        PlaybackIdentityGate gate = new PlaybackIdentityGate();
        assertTrue(gate.begin("vod:episode-1"));
        assertFalse(gate.resolved("https://media.example/1"));
        long first = gate.generation();
        assertFalse(gate.begin("vod:episode-1"));
        assertEquals(first, gate.generation());
        assertTrue(gate.begin("vod:episode-2"));
        assertNull(gate.mediaUrl());
        assertTrue(gate.begin("vod:other-source"));
        assertNull(gate.mediaUrl());
    }

    @Test public void livePendingResolverRetainsCurrentIdentity() {
        PlaybackIdentityGate gate = new PlaybackIdentityGate();
        gate.begin("live:channel-1/line-1");
        gate.provisional("https://source.example/live");
        long generation = gate.generation();
        // The URL changed; the logical channel/line identity did not.
        assertTrue(gate.resolved("https://cdn.example/resolved"));
        assertEquals(generation, gate.generation());
        assertEquals("https://cdn.example/resolved", gate.mediaUrl());
        assertFalse(gate.resolved("https://cdn.example/resolved"));
        assertTrue(gate.begin("live:channel-1/line-2"));
        assertNull(gate.mediaUrl());
        gate.end();
        assertFalse(gate.hasIdentity());
    }

    @Test public void changedActualUrlStaysInsidePlaybackIdentity() {
        PlaybackIdentityGate gate = new PlaybackIdentityGate();
        gate.begin("vod:episode-1");
        gate.resolved("https://media.example/a");
        long before = gate.generation();
        assertFalse(gate.resolved("https://media.example/a"));
        assertTrue(gate.resolved("https://media.example/b"));
        assertEquals(before, gate.generation());
        assertEquals("https://media.example/b", gate.mediaUrl());
    }
}
