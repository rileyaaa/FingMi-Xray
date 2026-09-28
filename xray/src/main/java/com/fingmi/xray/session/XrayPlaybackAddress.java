package com.fingmi.xray.session;

import com.fingmi.xray.network.PublicPlaybackDestinationInterceptor;

import java.net.URI;
import java.util.Locale;

/** Published-APK playback address policy reconstructed from t11.m9191w(). */
public final class XrayPlaybackAddress {

    private XrayPlaybackAddress() {
    }

    public static boolean supports(String value) {
        if (isBlank(value)) return false;

        try {
            URI uri = URI.create(value.trim());
            String scheme = uri.getScheme();
            String host = uri.getHost();
            if (scheme == null || host == null) return false;

            String normalized = scheme.toLowerCase(Locale.ROOT);
            if (!normalized.equals("http")
                    && !normalized.equals("https")
                    && !normalized.equals("rtsp")
                    && !normalized.equals("rtspt")) {
                return false;
            }

            return !PublicPlaybackDestinationInterceptor
                    .isPrivateOrReserved(host);
        } catch (IllegalArgumentException ignored) {
            return false;
        }
    }

    public static boolean supportsDirectLiveSource(String value) {
        if (!supports(value)) return false;

        try {
            URI uri = URI.create(value.trim());
            String scheme = uri.getScheme() == null
                    ? ""
                    : uri.getScheme().toLowerCase(Locale.ROOT);

            if (!"http".equals(scheme) && !"https".equals(scheme)) {
                return true;
            }

            String path = uri.getPath() == null
                    ? ""
                    : uri.getPath().toLowerCase(Locale.ROOT);
            String host = uri.getHost() == null
                    ? ""
                    : uri.getHost().toLowerCase(Locale.ROOT);

            return !path.endsWith(".strm")
                    && !host.contains("youtube.com")
                    && !host.contains("youtu.be");
        } catch (IllegalArgumentException ignored) {
            return false;
        }
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
}
