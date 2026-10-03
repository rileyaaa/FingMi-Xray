package com.fingmi.xray.session;

import android.content.Context;
import android.os.Looper;

import com.fingmi.xray.network.PublicPlaybackDestinationInterceptor;
import com.fingmi.xray.network.XrayHttpClient;
import com.fingmi.xray.util.XrayErrorSanitizer;

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
        else retryProxyRollback(clearResources(preservePlayback));
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

            Throwable clearFailure = clearResources(false);
            if (clearFailure != null) {
                failRunningTransition(clearFailure);
                return;
            }

            try {
                resources = new XrayHttpClient(socksPort, baseClient);
                listener.onProxyChanged(resources, preserveOnStart);
            } catch (Exception | LinkageError error) {
                failRunningTransition(error);
                return;
            }
        } else if (state == ERROR) {
            retryProxyRollback(clearResourcesAfterError());
        } else if (state == IDLE) {
            retryProxyRollback(clearResources(preserveOnStop));
        }
        notifyState(state, message);
    }

    private Throwable clearResources(boolean preservePlayback) {
        if (resources == null) return null;
        XrayHttpClient old = resources;
        resources = null;
        Throwable failure = null;
        try {
            listener.onProxyChanged(null, preservePlayback);
        } catch (Exception | LinkageError error) {
            failure = error;
        } finally {
            closeQuietly(old);
        }
        return failure;
    }

    private Throwable clearResourcesAfterError() {
        if (resources == null) return null;
        XrayHttpClient old = resources;
        resources = null;
        Throwable failure = null;
        try {
            listener.onProxyError();
        } catch (Exception | LinkageError error) {
            failure = error;
        } finally {
            closeQuietly(old);
        }
        return failure;
    }

    private void retryProxyRollback(Throwable failure) {
        if (failure == null) return;
        try {
            // Resource cleanup already closed the old client in finally. Retry
            // only the player-side detach in case the first callback failed
            // after partially mutating the playback engine.
            listener.onProxyError();
        } catch (Exception | LinkageError ignored) {
        }
    }

    private void failRunningTransition(Throwable error) {
        XrayHttpClient failed = resources;
        resources = null;
        try {
            // Retry player detachment even when the failure came from clearing
            // the previous proxy and resources is already null. In that case
            // the player may still hold an engine backed by the client that
            // clearResources() just closed.
            listener.onProxyError();
        } catch (Exception | LinkageError ignored) {
        } finally {
            closeQuietly(failed);
        }

        notifyState(ERROR, XrayErrorSanitizer.sanitize(error));
        service.stop();
    }

    private void notifyState(int state, String message) {
        try {
            listener.onStateChanged(state, message == null ? "" : message);
        } catch (Exception | LinkageError ignored) {
        }
    }

    private static void closeQuietly(XrayHttpClient client) {
        if (client == null) return;
        try {
            client.close();
        } catch (Exception | LinkageError ignored) {
        }
    }

    @Override
    public void close() {
        assertMain();
        if (closed) return;
        end();
        closed = true;

        // stop() is asynchronous. Once the controller is disposed its final
        // STOP result intentionally does not emit another IDLE callback, so
        // owner destruction must detach and close playback proxy resources
        // synchronously instead of waiting for that callback.
        retryProxyRollback(clearResources(false));
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
