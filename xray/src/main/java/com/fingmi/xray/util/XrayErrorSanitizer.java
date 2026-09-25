package com.fingmi.xray.util;

import java.util.Locale;
import java.util.regex.Pattern;

/**
 * Behavior-faithful reconstruction of the shipped sanitizer (R8 name: kz3).
 */
public final class XrayErrorSanitizer {

    private static final String[] SECRET_KEYS = {
            "password",
            "passwd",
            "token",
            "secret",
            "auth",
            "obfs-password",
            "uuid",
            "privatekey",
            "publickey",
            "shortid",
            "seed"
    };

    private static final Pattern SHARE_LINK = Pattern.compile(
            "(?i)\\b(?:vmess|vless|trojan|ss|hy2|hysteria2)://[^\\s]+");

    private static final Pattern UUID = Pattern.compile(
            "(?i)\\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\b");

    private static final Pattern SECRET_ASSIGNMENT = Pattern.compile(
            "(?i)\\b(password|passwd|token|secret|auth|obfs-password|uuid|privatekey|publickey|shortid|seed)"
                    + "(\\s*[=:]\\s*)[^\\s,;&}\\]]+");

    private XrayErrorSanitizer() {
    }

    public static String sanitize(Throwable error) {
        if (error == null) return "";
        return error instanceof Exception
                ? fromException((Exception) error)
                : sanitize(error.getMessage());
    }

    public static String fromException(Exception error) {
        String message = error.getMessage();
        if (isBlank(message)) {
            message = error.getClass().getSimpleName();
        }

        String sanitized = sanitize(message);
        return isBlank(sanitized) ? "Xray operation failed" : sanitized;
    }

    public static String sanitize(String value) {
        if (value == null || isBlank(value)) return "";

        String result = SHARE_LINK.matcher(value).replaceAll("<redacted-share-link>");
        result = UUID.matcher(result).replaceAll("<redacted-uuid>");
        result = SECRET_ASSIGNMENT.matcher(result).replaceAll("$1$2<redacted>");

        for (String key : SECRET_KEYS) {
            result = redactJsonStringValue(result, key);
        }

        return result.length() > 1024 ? result.substring(0, 1024) : result;
    }

    private static String redactJsonStringValue(String input, String key) {
        String result = input;
        String needle = "\"" + key + "\"";
        int searchFrom = 0;

        while (true) {
            String lower = result.toLowerCase(Locale.ROOT);
            int keyStart = lower.indexOf(needle, searchFrom);
            if (keyStart < 0) return result;

            int colon = lower.indexOf(':', keyStart + needle.length());
            if (colon < 0) return result;

            int valueQuote = colon + 1;
            while (valueQuote < result.length()
                    && Character.isWhitespace(result.charAt(valueQuote))) {
                valueQuote++;
            }

            if (valueQuote >= result.length() || result.charAt(valueQuote) != '"') {
                searchFrom = colon + 1;
                continue;
            }

            int valueStart = valueQuote + 1;
            int cursor = valueStart;
            boolean escaped = false;

            while (cursor < result.length()) {
                char c = result.charAt(cursor);
                if (c == '"' && !escaped) break;

                if (c == '\\') {
                    escaped = !escaped;
                } else {
                    escaped = false;
                }
                cursor++;
            }

            if (cursor >= result.length()) return result;

            result = result.substring(0, valueStart)
                    + "<redacted>"
                    + result.substring(cursor);
            searchFrom = valueStart + "<redacted>".length();
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

