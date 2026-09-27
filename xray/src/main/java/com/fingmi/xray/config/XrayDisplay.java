package com.fingmi.xray.config;

import java.net.URI;
import java.util.Locale;

public final class XrayDisplay {

    private XrayDisplay() {
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

    public static String describe(String shareLink) {
        if (isBlank(shareLink)) return "Not configured";

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
