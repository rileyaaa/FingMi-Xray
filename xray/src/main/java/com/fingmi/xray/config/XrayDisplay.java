package com.fingmi.xray.config;

import java.net.URI;
import java.util.Locale;

/** Behavior-faithful reconstruction of the shipped display helper (R8 name: a04.m20g). */
public final class XrayDisplay {

    private XrayDisplay() {
    }

    public static String describe(String shareLink) {
        if (shareLink.isEmpty()) {
            return "Not configured";
        }

        URI uri = URI.create(shareLink);
        String scheme = uri.getScheme() == null
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
            masked = host.charAt(0)
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
