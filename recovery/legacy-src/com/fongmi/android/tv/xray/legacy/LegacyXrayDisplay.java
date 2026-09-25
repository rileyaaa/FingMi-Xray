package com.fongmi.android.tv.xray.legacy;

import java.net.URI;
import java.util.Locale;

/**
 * Behavior reconstruction of a04.m20g() from the shipped APK.
 */
public final class LegacyXrayDisplay {

    private LegacyXrayDisplay() {
    }

    public static String describe(String shareLink) {
        if (shareLink == null || shareLink.isEmpty()) {
            return "Not configured";
        }

        URI uri = URI.create(shareLink);
        String scheme =
                uri.getScheme() == null
                        ? "Xray"
                        : uri.getScheme().toUpperCase(Locale.ROOT);
        String host = uri.getHost();
        if (host == null || host.isEmpty()) {
            return scheme + " configured";
        }

        String masked;
        if (host.length() <= 2) {
            masked = "**";
        } else {
            int lastDot = host.lastIndexOf('.');
            masked =
                    host.charAt(0)
                            + "***"
                            + (lastDot > 0 ? host.substring(lastDot) : "");
        }

        int port = uri.getPort();
        return scheme
                + "  "
                + masked
                + (port > 0 ? ":" + port : "");
    }
}
