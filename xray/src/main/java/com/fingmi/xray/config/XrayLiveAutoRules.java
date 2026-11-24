package com.fingmi.xray.config;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;

/** Opt-in rules for TV Live only. No regular expressions or URL/host matching. */
public final class XrayLiveAutoRules {
    public static final int MAX_LENGTH = 4096;
    private final List<String> groups;
    private final List<String> channels;

    public XrayLiveAutoRules(String groups, String channels) {
        this.groups = parse(groups);
        this.channels = parse(channels);
    }

    public String groups() { return join(groups); }
    public String channels() { return join(channels); }

    private static String join(List<String> items) {
        StringBuilder result = new StringBuilder();
        for (String item : items) {
            if (result.length() != 0) result.append(',');
            result.append(item);
        }
        return result.toString();
    }

    public boolean matches(String group, String channel, String displayName) {
        return matches(groups, group) || matches(channels, channel) || matches(channels, displayName);
    }

    private static List<String> parse(String text) {
        LinkedHashSet<String> items = new LinkedHashSet<>();
        if (text == null) return new ArrayList<>();
        if (text.length() > MAX_LENGTH) throw new IllegalArgumentException("Live Xray rule list is too long");
        for (String item : text.split("[,，\\r\\n]")) {
            item = trim(item);
            if (!item.isEmpty()) items.add(item);
        }
        return new ArrayList<>(items);
    }

    private static String trim(String text) {
        int start = 0, end = text.length();
        while (start < end && space(text.charAt(start))) start++;
        while (end > start && space(text.charAt(end - 1))) end--;
        return text.substring(start, end);
    }

    private static boolean space(char c) {
        return Character.isWhitespace(c) || Character.isSpaceChar(c);
    }

    private static boolean matches(List<String> patterns, String name) {
        if (name == null || trim(name).isEmpty()) return false;
        String value = trim(name).toLowerCase(Locale.ROOT);
        for (String pattern : patterns) {
            if (glob(pattern.toLowerCase(Locale.ROOT), value)) return true;
        }
        return false;
    }

    // Only '*' is special. Everything else, including '.', '?' and brackets,
    // is literal. Iterative matching avoids arbitrary regular-expression work.
    private static boolean glob(String pattern, String value) {
        int p = 0, v = 0, star = -1, retry = 0;
        while (v < value.length()) {
            if (p < pattern.length() && pattern.charAt(p) == '*') {
                star = p++;
                retry = v;
            } else if (p < pattern.length() && pattern.charAt(p) == value.charAt(v)) {
                p++;
                v++;
            } else if (star >= 0) {
                p = star + 1;
                v = ++retry;
            } else {
                return false;
            }
        }
        while (p < pattern.length() && pattern.charAt(p) == '*') p++;
        return p == pattern.length();
    }
}
