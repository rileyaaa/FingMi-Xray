package com.fingmi.xray.session;

import android.content.Context;
import android.os.Looper;

import com.fingmi.xray.network.PublicPlaybackDestinationInterceptor;
import com.fingmi.xray.network.XrayHttpClient;

import java.util.Objects;

import okhttp3.OkHttpClient;

/**
 * Owns the proxy resources for one manually enabled playback identity.
 * A new VOD episode/source or Live channel/line starts direct by default.
 */
public final class XrayPlaybackSession implements XraySessionListener, AutoCloseable {

    public interface Listener {
        void onProxyChanged(XrayHttpClient resources, boolean preservePlayback);

        default void onProxyError() {
            onProxyChanged(null, false);
        }

        void onStateChanged(int state, String message);
    }

    private final XraySessionController service;
    private final OkHttpClient baseClient;
    private final Listener listener;
    private final PlaybackIdentityGate playback = new PlaybackIdentityGate();
    private XrayHttpClient resources;
    private boolean preserveOnStart = true;
    private boolean preserveOnStop;
    private boolean closed;

    public XrayPlaybackSession(Context context, OkHttpClient baseClient, Listener listener) {
        this.baseClient = Objects.requireNonNull(baseClient);
        this.listener = Objects.requireNonNull(listener);
        this.service = new XraySessionController(context, this);
    }

    public void begin(String nextIdentity) {
        assertMain();
        if (closed || !playback.begin(nextIdentity)) return;
        stop(false);
    }

    /**
     * A resolved URL change remains inside the current playback identity.
     * The released APK only drops Xray at explicit VOD/Live identity boundaries;
     * redirects, parser results and CDN changes continue through the same session.
     */
    public void mediaUrlChanged(String url) {
        assertMain();
        if (closed || !playback.hasIdentity()) return;
        playback.resolved(url);
    }

    public boolean enable() {
        assertMain();
        if (closed || !playback.hasIdentity() || !supports(playback.mediaUrl())) return false;
        preserveOnStart = true;
        service.start();
        return true;
    }

    /** Live may be resolving its direct channel source when START is requested. */
    public boolean enableForPending(String directSource) {
        assertMain();
        if (!supportsDirectLiveSource(directSource)) return false;
        playback.provisional(directSource);
        if (closed || !playback.hasIdentity() || !supports(playback.mediaUrl())) return false;
        preserveOnStart = false;
        service.start();
        return true;
    }

    public void stop(boolean preservePlayback) {
        assertMain();
        preserveOnStop = preservePlayback;
        if (service.isRunning() || service.getState() == STARTING) service.stop();
        else clearResources(preservePlayback);
    }

    public void end() {
        assertMain();
        stop(false);
        playback.end();
    }

    public boolean isActive() { return service.isRunning(); }
    public int state() { return service.getState(); }
    public XrayHttpClient resources() { return resources; }
    public OkHttpClient client(OkHttpClient fallback) {
        return resources == null ? fallback : resources.client();
    }

    public static boolean supports(String url) {
        return XrayPlaybackAddress.supports(url);
    }

    public static boolean supportsDirectLiveSource(String url) {
        return XrayPlaybackAddress.supportsDirectLiveSource(url);
    }

    @Override
    public void onXrayStateChanged(int state, int socksPort, String message) {
        assertMain();
        if (closed) return;
        if (state == RUNNING) {
            if (!playback.hasIdentity()) {
                service.stop();
                return;
            }
            clearResources(false);
            resources = new XrayHttpClient(socksPort, baseClient);
            listener.onProxyChanged(resources, preserveOnStart);
        } else if (state == ERROR) {
            clearResourcesAfterError();
        } else if (state == IDLE) {
            clearResources(preserveOnStop);
        }
        listener.onStateChanged(state, message);
    }

    private void clearResources(boolean preservePlayback) {
        if (resources == null) return;
        XrayHttpClient old = resources;
        resources = null;
        listener.onProxyChanged(null, preservePlayback);
        old.close();
    }

    private void clearResourcesAfterError() {
        if (resources == null) return;
        XrayHttpClient old = resources;
        resources = null;
        listener.onProxyError();
        old.close();
    }

    @Override
    public void close() {
        assertMain();
        if (closed) return;
        end();
        closed = true;
        service.close();
    }

    private static boolean isBlank(String value) {
        if (value == null) return true;
        for (int offset = 0; offset < value.length();) {
            int codePoint = value.codePointAt(offset);
            if (!Character.isWhitespace(codePoint)) return false;
            offset += Character.charCount(codePoint);
        }
        return true;
    }

    private static void assertMain() {
        if (Looper.myLooper() != Looper.getMainLooper())
            throw new IllegalStateException("Playback session requires main thread");
    }
}
