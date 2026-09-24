package com.fingmi.xray.util;

import java.util.regex.Pattern;

public final class XrayErrorSanitizer {

    private static final Pattern SHARE_LINK = Pattern.compile(
            "(?i)\\b(?:vmess|vless|trojan|ss|hy2|hysteria2)://[^\\s]+");
    private static final Pattern UUID = Pattern.compile(
            "(?i)\\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\b");
    private static final Pattern SECRET = Pattern.compile(
            "(?i)\\b(password|passwd|token|secret|auth|obfs-password|uuid|privatekey|publickey|shortid|seed)(\\s*[=:]\\s*)[^\\s,;&}\\]]+");

    private XrayErrorSanitizer() {
    }

    public static String sanitize(Throwable error) {
        if (error == null) return "";
        String message = error.getMessage();
        return sanitize(message == null ? error.getClass().getSimpleName() : message);
    }

    public static String sanitize(String message) {
        if (message == null) return "";
        String value = SHARE_LINK.matcher(message).replaceAll("<xray-link-redacted>");
        value = UUID.matcher(value).replaceAll("<uuid-redacted>");
        return SECRET.matcher(value).replaceAll("$1$2<redacted>");
    }
}
