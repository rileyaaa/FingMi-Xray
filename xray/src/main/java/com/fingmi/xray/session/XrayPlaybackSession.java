package com.fingmi.xray.session;

import android.content.Context;
import android.net.Uri;
import android.os.Looper;

import com.fingmi.xray.network.PublicPlaybackDestinationInterceptor;
import com.fingmi.xray.network.XrayHttpClient;

import java.util.Locale;
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

    /** The first resolved URL belongs to this identity. A later different URL does not. */
    public void mediaUrlChanged(String url) {
        assertMain();
        if (closed || !playback.hasIdentity()) return;
        if (playback.resolved(url)) stop(false);
        if (service.isRunning() && !supports(url)) stop(false);
    }

    public boolean enable() {
        assertMain();
        if (closed || !playback.hasIdentity() || !supports(playback.mediaUrl())) return false;
        service.start();
        return true;
    }

    /** Live may be resolving its direct channel source when START is requested. */
    public boolean enableForPending(String directSource) {
        assertMain();
        if (!supportsDirectLiveSource(directSource)) return false;
        playback.provisional(directSource);
        return enable();
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
        if (isBlank(url)) return false;
        Uri uri = Uri.parse(url);
        String scheme = uri.getScheme();
        String host = uri.getHost();
        if (scheme == null || host == null) return false;
        if (!scheme.equalsIgnoreCase("http") && !scheme.equalsIgnoreCase("https")
                && !scheme.equalsIgnoreCase("rtsp") && !scheme.equalsIgnoreCase("rtspt")) return false;
        return !PublicPlaybackDestinationInterceptor.isPrivateOrReserved(host);
    }

    public static boolean supportsDirectLiveSource(String url) {
        if (!supports(url)) return false;
        try {
            Uri uri = Uri.parse(url.trim());
            String scheme = uri.getScheme();
            if (scheme == null) return false;
            if (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme)) {
                return true;
            }
            String path = uri.getPath();
            String host = uri.getHost();
            String lowerPath = path == null ? "" : path.toLowerCase(Locale.ROOT);
            String lowerHost = host == null ? "" : host.toLowerCase(Locale.ROOT);
            return !lowerPath.endsWith(".strm")
                    && !lowerHost.contains("youtube.com")
                    && !lowerHost.contains("youtu.be");
        } catch (RuntimeException ignored) {
            return false;
        }
    }

    @Override
    public void onXrayStateChanged(int state, int socksPort, String message) {
        assertMain();
        if (closed) return;
        if (state == RUNNING) {
            if (!playback.hasIdentity() || !supports(playback.mediaUrl())) {
                service.stop();
                return;
            }
            clearResources(false);
            resources = new XrayHttpClient(socksPort, baseClient);
            listener.onProxyChanged(resources, true);
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
