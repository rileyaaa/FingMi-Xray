package com.fingmi.xray.util;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Reconstruction of the shipped sanitizer (R8 name: kz3), with fail-closed
 * handling of quoted assignments and truncated JSON error text.
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
        result = redactAssignments(result);

        for (String key : SECRET_KEYS) {
            result = redactJsonStringValue(result, key);
        }

        return result.length() > 1024 ? result.substring(0, 1024) : result;
    }

    private static String redactAssignments(String input) {
        Matcher matcher = SECRET_ASSIGNMENT.matcher(input);
        StringBuilder result = new StringBuilder(input.length());
        int copiedThrough = 0;
        while (matcher.find(copiedThrough)) {
            int valueStart = matcher.end(2);
            int valueEnd = matcher.end();
            char quote = input.charAt(valueStart);
            if (quote == '"' || quote == '\'') {
                // A quoted credential may contain spaces, delimiters or escaped
                // quotes. If it is truncated, redact the rest rather than leak it.
                valueEnd = input.length();
                for (int cursor = valueStart + 1; cursor < input.length(); cursor++) {
                    char c = input.charAt(cursor);
                    if (c == '\\') {
                        cursor++;
                    } else if (c == quote) {
                        valueEnd = cursor + 1;
                        break;
                    }
                }
            }
            result.append(input, copiedThrough, valueStart).append("<redacted>");
            copiedThrough = valueEnd;
        }
        return result.append(input, copiedThrough, input.length()).toString();
    }

    private static String redactJsonStringValue(String input, String key) {
        String result = input;
        String needle = "\"" + key + "\"";
        int searchFrom = 0;

        while (true) {
            // Case-folding the whole message can expand Unicode characters
            // (for example U+0130), so its offsets are not offsets in result.
            int keyStart = indexOfIgnoreCase(result, needle, searchFrom);
            if (keyStart < 0) return result;

            int colon = result.indexOf(':', keyStart + needle.length());
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

            if (cursor >= result.length()) {
                return result.substring(0, valueStart) + "<redacted>";
            }

            result = result.substring(0, valueStart)
                    + "<redacted>"
                    + result.substring(cursor);
            searchFrom = valueStart + "<redacted>".length();
        }
    }

    private static int indexOfIgnoreCase(String value, String needle, int from) {
        for (int i = from; i <= value.length() - needle.length(); i++) {
            if (value.regionMatches(true, i, needle, 0, needle.length())) return i;
        }
        return -1;
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

