package com.fongmi.android.tv.xray.legacy;

import java.net.URI;
import java.util.Locale;

/**
 * Behavior reconstruction of t11.m9191w() from the shipped APK.
 *
 * Xray playback accepts public HTTP(S) and RTSP/RTSPT destinations. The
 * private/reserved host policy is shared with the HTTP network interceptor.
 */
public final class LegacyXrayPlaybackAddress {

    private LegacyXrayPlaybackAddress() {
    }

    /**
     * Raw live-channel URLs have one extra rule in the shipped APK. HTTP(S)
     * .strm links and YouTube URLs are indirections which must first be
     * resolved by FongMi; they cannot be proxied directly before a real
     * playback session exists. Non-HTTP public RTSP/RTSPT URLs remain valid.
     */
    public static boolean isDirectLiveSourceSupported(String value) {
        if (!isSupportedPublicAddress(value)) return false;

        try {
            URI uri = URI.create(value.trim());
            String scheme =
                    uri.getScheme() == null
                            ? ""
                            : uri.getScheme().toLowerCase(Locale.ROOT);

            if (!"http".equals(scheme) && !"https".equals(scheme)) {
                return true;
            }

            String path =
                    uri.getPath() == null
                            ? ""
                            : uri.getPath().toLowerCase(Locale.ROOT);
            String host =
                    uri.getHost() == null
                            ? ""
                            : uri.getHost().toLowerCase(Locale.ROOT);

            return !path.endsWith(".strm")
                    && !host.contains("youtube.com")
                    && !host.contains("youtu.be");
        } catch (IllegalArgumentException ignored) {
            return false;
        }
    }

    public static boolean isSupportedPublicAddress(String value) {
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

            return !LegacyPublicPlaybackDestinationInterceptor
                    .isPrivateOrReserved(host);
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
