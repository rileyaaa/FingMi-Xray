package com.fingmi.xray.config;

import java.net.URI;
import java.util.Locale;

public final class XrayDisplay {

    private XrayDisplay() {
    }

    public static String describe(String shareLink) {
        if (shareLink == null || shareLink.isBlank()) return "Not configured";

        try {
            URI uri = URI.create(shareLink);
            String scheme = uri.getScheme() == null
                    ? "Xray"
                    : uri.getScheme().toUpperCase(Locale.ROOT);
            String host = uri.getHost();
            if (host == null || host.isEmpty()) return scheme + " configured";

            String masked;
            if (host.length() <= 2) {
                masked = "**";
            } else {
                int dot = host.lastIndexOf('.');
                masked = host.charAt(0) + "***" + (dot > 0 ? host.substring(dot) : "");
            }
            return scheme + "  " + masked + (uri.getPort() > 0 ? ":" + uri.getPort() : "");
        } catch (Exception ignored) {
            return "Xray configured";
        }
    }
}
