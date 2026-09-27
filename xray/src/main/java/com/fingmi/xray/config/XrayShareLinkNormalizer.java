package com.fingmi.xray.config;

import java.math.BigDecimal;
import java.net.URI;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Behavior-oriented reconstruction of the shipped node normalizer (R8 name: a04).
 *
 * JADX has several visibly impossible/inverted predicates after R8. All known
 * repaired predicates in this class have now been checked directly against the
 * published v7 and v8 DEX. The comments below retain the relevant decompiler
 * failure mode so later refactors do not accidentally "restore" the bad JADX.
 */
public final class XrayShareLinkNormalizer {

    private static final int MAX_LENGTH = 16_384;
    private static final Set<String> SUPPORTED =
            Set.of("vless", "vmess", "trojan", "ss", "hy2", "hysteria2");
    private static final Pattern VMESS_PORT = Pattern.compile(
            "\"port\"\\s*:\\s*(?:\"([+-]?\\d+)\"|([+-]?\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?))");
    private static final Pattern SHA256 = Pattern.compile("(?i)[0-9a-f]{64}");

    private XrayShareLinkNormalizer() {
    }

    public static String normalize(String input) {
        String value = input == null ? "" : input.trim();
        if (value.isEmpty()) throw new IllegalArgumentException("Xray link is empty");
        if (value.length() > MAX_LENGTH) throw new IllegalArgumentException("Xray link is too long");
        if (value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0) {
            throw new IllegalArgumentException("Only one Xray link is supported");
        }

        int colon = value.indexOf(':');
        if (colon <= 0) throw new IllegalArgumentException("Unsupported Xray link protocol");

        String scheme = value.substring(0, colon);
        String normalizedScheme = scheme.toLowerCase(Locale.ROOT);
        if (!SUPPORTED.contains(normalizedScheme)) {
            throw new IllegalArgumentException("Unsupported Xray link protocol");
        }
        if (!scheme.equals(normalizedScheme)) {
            value = normalizedScheme + value.substring(colon);
        }

        try {
            if ("ss".equals(normalizedScheme)) {
                value = normalizeLegacyShadowsocks(value);
                value = normalizeShadowsocksPlugin(value);
            } else if ("trojan".equals(normalizedScheme)) {
                value = ensureTrojanTls(value);
            } else if ("hy2".equals(normalizedScheme) || "hysteria2".equals(normalizedScheme)) {
                value = normalizeHysteria2(value);
            }

            validateAuthorityPort(value, normalizedScheme);
            if ("vmess".equals(normalizedScheme)) validateVmessJsonPorts(value);

            if (!"vmess".equals(normalizedScheme)) {
                URI uri = URI.create(value);
                if (uri.getScheme() == null) throw new IllegalArgumentException("Invalid Xray link");
                if (!"ss".equals(normalizedScheme) && uri.getHost() == null) {
                    throw new IllegalArgumentException("Invalid Xray link");
                }
            }
            return value;
        } catch (IllegalArgumentException error) {
            if (isKnownValidationError(error.getMessage())) throw error;
            throw new IllegalArgumentException("Invalid Xray link", error);
        }
    }

    private static boolean isKnownValidationError(String message) {
        return message != null && (
                message.startsWith("Xray ")
                        || message.startsWith("Invalid Xray ")
                        || message.startsWith("Shadowsocks ")
                        || message.startsWith("Unsupported Shadowsocks ")
                        || message.startsWith("Hysteria2 ")
                        || message.startsWith("Unsupported Hysteria2 "));
    }

    private static String normalizeLegacyShadowsocks(String value) {
        int fragment = value.indexOf('#', 5);
        int end = fragment < 0 ? value.length() : fragment;
        String body = value.substring(5, end);
        if (body.indexOf('@') >= 0) return value;

        String decoded = decodeBase64(body);
        if (decoded == null) return value;

        int at = decoded.lastIndexOf('@');
        if (at <= 0 || at == decoded.length() - 1) {
            throw new IllegalArgumentException("Shadowsocks legacy link is invalid");
        }

        String credentials = decoded.substring(0, at);
        String endpoint = decoded.substring(at + 1);
        if (credentials.indexOf(':') <= 0) {
            throw new IllegalArgumentException("Shadowsocks legacy credentials are invalid");
        }

        URI endpointUri;
        try {
            endpointUri = URI.create("ss://x@" + endpoint);
        } catch (IllegalArgumentException error) {
            throw new IllegalArgumentException("Shadowsocks legacy endpoint is invalid", error);
        }
        if (endpointUri.getHost() == null
                || !endpointUri.getRawPath().isEmpty()
                || endpointUri.getRawQuery() != null
                || endpointUri.getRawFragment() != null) {
            throw new IllegalArgumentException("Shadowsocks legacy endpoint is invalid");
        }
        if (endpointUri.getPort() <= 0) {
            throw new IllegalArgumentException("Shadowsocks legacy endpoint port is invalid");
        }

        String encoded = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(credentials.getBytes(StandardCharsets.UTF_8));
        return "ss://" + encoded + "@" + endpoint
                + (fragment < 0 ? "" : value.substring(fragment));
    }

    private static String normalizeShadowsocksPlugin(String value) {
        URI uri = URI.create(value);
        String rawQuery = uri.getRawQuery();
        if (rawQuery == null || rawQuery.isEmpty()) return value;

        List<QueryPart> parts = parseQuery(rawQuery);
        int pluginIndex = -1;
        String plugin = null;
        for (int i = 0; i < parts.size(); i++) {
            QueryPart part = parts.get(i);
            if (!"plugin".equals(part.key)) continue;
            if (pluginIndex >= 0 || !part.hasEquals) {
                throw new IllegalArgumentException("Shadowsocks SIP003 plugin is ambiguous");
            }
            pluginIndex = i;
            plugin = part.value;
        }
        if (pluginIndex < 0) return value;

        String[] options = plugin.split(";", -1);
        if (options.length == 0 || !"v2ray-plugin".equals(options[0])) {
            throw new IllegalArgumentException("Unsupported Shadowsocks SIP003 plugin");
        }

        String host = null;
        String path = null;
        String mode = "websocket";
        boolean tls = false;
        boolean muxSeen = false;
        boolean modeSeen = false;

        for (int i = 1; i < options.length; i++) {
            String option = options[i];
            if (option.isEmpty()) continue;
            if ("tls".equals(option)) {
                if (tls) throw new IllegalArgumentException("Shadowsocks v2ray-plugin TLS option is ambiguous");
                tls = true;
                continue;
            }

            int equals = option.indexOf('=');
            String key = equals < 0 ? option : option.substring(0, equals);
            String rawValue = equals < 0 ? "" : option.substring(equals + 1);
            String decoded = unescapePluginValue(rawValue);

            switch (key) {
                case "mux" -> {
                    if (muxSeen) throw new IllegalArgumentException("Shadowsocks v2ray-plugin mux is ambiguous");
                    if (!"0".equals(decoded)) {
                        throw new IllegalArgumentException("Unsupported Shadowsocks v2ray-plugin mux mode");
                    }
                    muxSeen = true;
                }
                case "host" -> {
                    if (host != null) throw new IllegalArgumentException("Shadowsocks v2ray-plugin host is ambiguous");
                    host = decoded;
                }
                case "mode" -> {
                    if (modeSeen) throw new IllegalArgumentException("Shadowsocks v2ray-plugin mode is ambiguous");
                    mode = decoded;
                    modeSeen = true;
                }
                case "path" -> {
                    if (path != null) throw new IllegalArgumentException("Shadowsocks v2ray-plugin path is ambiguous");
                    path = decoded;
                }
                default -> throw new IllegalArgumentException(
                        "Unsupported Shadowsocks v2ray-plugin option: " + key);
            }
        }

        if (!"websocket".equals(mode)) {
            throw new IllegalArgumentException("Unsupported Shadowsocks v2ray-plugin mode");
        }
        for (String key : new String[]{"type", "host", "path", "security"}) {
            if (hasQueryKey(parts, key)) {
                throw new IllegalArgumentException("Shadowsocks transport settings are ambiguous");
            }
        }

        List<QueryPart> rewritten = new ArrayList<>();
        for (int i = 0; i < parts.size(); i++) {
            if (i != pluginIndex && !parts.get(i).raw.isEmpty()) rewritten.add(parts.get(i));
        }
        rewritten.add(QueryPart.encoded("type", "ws"));
        if (host != null && !host.isEmpty()) rewritten.add(QueryPart.encoded("host", host));
        if (path != null && !path.isEmpty()) rewritten.add(QueryPart.encoded("path", path));
        if (tls) rewritten.add(QueryPart.encoded("security", "tls"));
        return replaceRawQuery(value, joinRawQuery(rewritten));
    }

    private static String unescapePluginValue(String value) {
        StringBuilder result = new StringBuilder(value.length());
        boolean escaped = false;
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (escaped) {
                result.append(c);
                escaped = false;
            } else if (c == '\\') {
                escaped = true;
            } else {
                result.append(c);
            }
        }
        if (escaped) {
            throw new IllegalArgumentException("Shadowsocks v2ray-plugin option has a dangling escape");
        }
        return result.toString();
    }

    private static String ensureTrojanTls(String value) {
        int fragment = value.indexOf('#');
        int end = fragment < 0 ? value.length() : fragment;
        int query = value.indexOf('?');
        if (query < 0 || query >= end) {
            return value.substring(0, end) + "?security=tls" + value.substring(end);
        }
        if (query + 1 == end) {
            return value.substring(0, query + 1) + "security=tls" + value.substring(end);
        }
        return value;
    }

    private static String normalizeHysteria2(String value) {
        // Match the final APK's transformation order exactly:
        // authority hopping -> mport -> default :443 -> pinSHA256 -> obfs.
        value = normalizeHysteriaAuthorityPortHopping(value);

        List<QueryPart> parts = parseQuery(rawQuery(value));

        int portsIndex = firstIndex(parts, "ports");
        int mportIndex = uniqueIndex(
                parts,
                "mport",
                "Hysteria2 port hopping is ambiguous");
        if (mportIndex >= 0) {
            QueryPart mport = parts.get(mportIndex);
            if (portsIndex >= 0 || !mport.hasEquals) {
                throw new IllegalArgumentException("Hysteria2 port hopping is ambiguous");
            }
            validatePortExpression(mport.value);

            // Final a04 preserves the original raw mport value byte-for-byte
            // and only renames the key to ports.
            int equals = mport.raw.indexOf('=');
            parts.set(
                    mportIndex,
                    new QueryPart(
                            "ports=" + mport.raw.substring(equals + 1),
                            "ports",
                            mport.value,
                            true));
        }

        value = replaceRawQuery(value, joinRawQuery(parts));
        value = ensureHysteriaDefaultPort(value);
        parts = parseQuery(rawQuery(value));

        int pcsIndex = firstIndex(parts, "pcs");
        int pinIndex = uniqueIndex(
                parts,
                "pinSHA256",
                "Hysteria2 certificate pin is invalid");
        if (pinIndex >= 0) {
            QueryPart pin = parts.get(pinIndex);
            if (!pin.hasEquals) {
                throw new IllegalArgumentException("Hysteria2 certificate pin is invalid");
            }
            if (pcsIndex >= 0) {
                throw new IllegalArgumentException("Hysteria2 certificate pin is ambiguous");
            }

            String fingerprint = pin.value.replace(":", "").replace("-", "");
            if (!SHA256.matcher(fingerprint).matches()) {
                throw new IllegalArgumentException("Hysteria2 certificate pin is invalid");
            }
            parts.set(
                    pinIndex,
                    QueryPart.encoded(
                            "pcs",
                            fingerprint.toLowerCase(Locale.ROOT)));
        }

        validateHysteriaObfuscation(parts);
        return replaceRawQuery(value, joinRawQuery(parts));
    }

    private static String normalizeHysteriaAuthorityPortHopping(String value) {
        AuthorityRange range = authority(value);
        if (range == null) return value;

        HostPort hostPort = splitHostPort(range.authority);
        // DEX-verified against both published ABIs. In a04.f the two indexOf(I)
        // results are each followed by if-gez to the same hopping block; only
        // when neither ',' nor '-' is present does execution jump past it.
        if (hostPort.port == null || (!hostPort.port.contains(",") && !hostPort.port.contains("-"))) {
            return value;
        }

        List<QueryPart> parts = parseQuery(rawQuery(value));
        if (hasQueryKey(parts, "ports")) {
            throw new IllegalArgumentException("Hysteria2 port hopping is ambiguous");
        }

        int firstPort = validatePortExpression(hostPort.port);
        String rewrittenAuthority = hostPort.prefix + firstPort;
        String rewritten = value.substring(0, range.start)
                + rewrittenAuthority
                + value.substring(range.end);
        parts = parseQuery(rawQuery(rewritten));
        // a04 inserts the original expression literally ("ports=" + raw),
        // not through URLEncoder. Commas/hyphens therefore remain unchanged.
        parts.add(
                0,
                new QueryPart(
                        "ports=" + hostPort.port,
                        "ports",
                        hostPort.port,
                        true));
        return replaceRawQuery(rewritten, joinRawQuery(parts));
    }

    private static String ensureHysteriaDefaultPort(String value) {
        try {
            URI uri = URI.create(value);
            if (uri.getPort() >= 0 || uri.getHost() == null || uri.getRawAuthority() == null) {
                return value;
            }
        } catch (IllegalArgumentException error) {
            throw new IllegalArgumentException("Invalid Xray link", error);
        }

        AuthorityRange range = authority(value);
        if (range == null) return value;
        return value.substring(0, range.end) + ":443" + value.substring(range.end);
    }

    private static void validateHysteriaObfuscation(List<QueryPart> parts) {
        int obfsIndex = uniqueIndex(parts, "obfs", "Hysteria2 obfuscation is ambiguous");
        int passwordIndex = uniqueIndex(
                parts,
                "obfs-password",
                "Hysteria2 obfuscation password is ambiguous");

        String obfs = obfsIndex < 0 ? null : parts.get(obfsIndex).value;
        String password = passwordIndex < 0 ? null : parts.get(passwordIndex).value;

        // DEX-verified: a null obfs value skips this block; for non-null values,
        // String.isEmpty()==false enters the validation block. JADX emitted the
        // impossible "obfs == null && !obfs.isEmpty()".
        if (obfs != null && !obfs.isEmpty()) {
            String lower = obfs.toLowerCase(Locale.ROOT);
            if (!obfs.equals(lower)) {
                throw new IllegalArgumentException("Hysteria2 obfuscation type must be lowercase");
            }
            if ("gecko".equals(lower)) {
                throw new IllegalArgumentException(
                        "Hysteria2 Gecko obfuscation is unsupported by this native core");
            }
            if (!"salamander".equals(lower)) {
                throw new IllegalArgumentException("Unsupported Hysteria2 obfuscation type");
            }
            if (password == null || password.isEmpty()) {
                throw new IllegalArgumentException("Hysteria2 obfuscation password is missing");
            }
        } else if (password != null && !password.isEmpty()) {
            throw new IllegalArgumentException("Hysteria2 obfuscation type is missing");
        }
    }

    private static int validatePortExpression(String expression) {
        if (expression == null || expression.isEmpty()) {
            throw new IllegalArgumentException("Hysteria2 port hopping is invalid");
        }
        String[] values = expression.split(",", -1);
        int first = -1;
        for (String value : values) {
            if (value.isEmpty()) throw new IllegalArgumentException("Hysteria2 port hopping is invalid");
            int dash = value.indexOf('-');
            int candidate;
            if (dash < 0) {
                candidate = parsePort(value);
            } else {
                if (dash == 0 || dash != value.lastIndexOf('-') || dash == value.length() - 1) {
                    throw new IllegalArgumentException("Hysteria2 port hopping is invalid");
                }
                int start = parsePort(value.substring(0, dash));
                int end = parsePort(value.substring(dash + 1));
                if (start > end) {
                    throw new IllegalArgumentException("Hysteria2 port hopping range is invalid");
                }
                candidate = start;
            }
            if (first < 0) first = candidate;
        }
        return first;
    }

    private static int parsePort(String value) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException("Xray link port is invalid");
        }
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException("Xray link port is invalid");
            }
        }
        try {
            int port = Integer.parseInt(value);
            if (port < 1 || port > 65_535) {
                throw new IllegalArgumentException("Xray link port is invalid");
            }
            return port;
        } catch (NumberFormatException error) {
            throw new IllegalArgumentException("Xray link port is invalid", error);
        }
    }

    private static void validateAuthorityPort(String value, String scheme) {
        if ("vmess".equals(scheme)) return;
        AuthorityRange range = authority(value);
        if (range == null) return;
        HostPort hostPort = splitHostPort(range.authority);
        if (hostPort.port != null) parsePort(hostPort.port);
    }

    private static void validateVmessJsonPorts(String value) {
        String body = value.substring("vmess://".length());
        if (body.indexOf('@') >= 0) return;
        // The shipped method feeds the complete text after vmess:// to the base64 decoder.
        String decoded = decodeBase64(body);
        if (decoded == null || !decoded.trim().startsWith("{")) return;

        Matcher matcher = VMESS_PORT.matcher(decoded);
        while (matcher.find()) {
            String portValue = matcher.group(1) != null ? matcher.group(1) : matcher.group(2);
            try {
                BigDecimal port = new BigDecimal(portValue).stripTrailingZeros();
                // DEX-verified: BigDecimal.scale() is followed by if-gtz to
                // the invalid-port branch. Integral values (scale <= 0) remain
                // valid here; JADX inverted this comparison.
                if (port.scale() > 0
                        || port.compareTo(BigDecimal.ONE) < 0
                        || port.compareTo(BigDecimal.valueOf(65_535L)) > 0) {
                    throw new IllegalArgumentException("Xray link port is invalid");
                }
                port.intValueExact();
            } catch (ArithmeticException | NumberFormatException error) {
                throw new IllegalArgumentException("Xray link port is invalid", error);
            }
        }
    }

    private static AuthorityRange authority(String value) {
        int scheme = value.indexOf("://");
        if (scheme < 0) return null;
        int start = scheme + 3;
        int end = value.length();
        for (char delimiter : new char[]{'/', '?', '#'}) {
            int index = value.indexOf(delimiter, start);
            if (index >= 0 && index < end) end = index;
        }
        if (end <= start) return null;
        return new AuthorityRange(start, end, value.substring(start, end));
    }

    private static HostPort splitHostPort(String authority) {
        int at = authority.lastIndexOf('@');
        String userInfo = at >= 0 ? authority.substring(0, at + 1) : "";
        String endpoint = at >= 0 ? authority.substring(at + 1) : authority;

        if (endpoint.startsWith("[")) {
            int close = endpoint.indexOf(']');
            if (close < 0) throw new IllegalArgumentException("Invalid Xray link");
            if (close + 1 == endpoint.length()) {
                return new HostPort(userInfo + endpoint, null);
            }
            // DEX-verified: charAt(close + 1) is compared with ':' and if-ne
            // jumps to the invalid-port branch. '[host]:port' is the valid form.
            if (endpoint.charAt(close + 1) != ':') {
                throw new IllegalArgumentException("Xray link port is invalid");
            }
            return new HostPort(
                    userInfo + endpoint.substring(0, close + 2),
                    endpoint.substring(close + 2));
        }

        int lastColon = endpoint.lastIndexOf(':');
        if (lastColon < 0) return new HostPort(userInfo + endpoint, null);
        // DEX-verified: indexOf(':') is compared with lastIndexOf(':') and
        // if-ne jumps to the invalid-port branch. A single colon is valid;
        // multiple unbracketed colons are rejected.
        if (endpoint.indexOf(':') != lastColon) {
            throw new IllegalArgumentException("Xray link port is invalid");
        }
        return new HostPort(
                userInfo + endpoint.substring(0, lastColon + 1),
                endpoint.substring(lastColon + 1));
    }

    private static String rawQuery(String value) {
        int query = value.indexOf('?');
        if (query < 0) return "";
        int fragment = value.indexOf('#', query + 1);
        int end = fragment < 0 ? value.length() : fragment;
        return value.substring(query + 1, end);
    }

    private static String replaceRawQuery(String value, String rawQuery) {
        int query = value.indexOf('?');
        int fragment = value.indexOf('#');
        int baseEnd = query >= 0 && (fragment < 0 || query < fragment)
                ? query
                : (fragment < 0 ? value.length() : fragment);
        String suffix = fragment < 0 ? "" : value.substring(fragment);
        return value.substring(0, baseEnd)
                + (rawQuery.isEmpty() ? "" : "?" + rawQuery)
                + suffix;
    }

    private static List<QueryPart> parseQuery(String rawQuery) {
        List<QueryPart> result = new ArrayList<>();
        if (rawQuery == null || rawQuery.isEmpty()) return result;
        for (String raw : rawQuery.split("&", -1)) {
            int equals = raw.indexOf('=');
            String rawKey = equals < 0 ? raw : raw.substring(0, equals);
            String rawValue = equals < 0 ? "" : raw.substring(equals + 1);
            result.add(new QueryPart(
                    raw,
                    decodeQuery(rawKey),
                    decodeQuery(rawValue),
                    equals >= 0));
        }
        return result;
    }

    private static boolean hasQueryKey(List<QueryPart> parts, String key) {
        for (QueryPart part : parts) {
            if (key.equals(part.key)) return true;
        }
        return false;
    }

    private static int firstIndex(List<QueryPart> parts, String key) {
        for (int i = 0; i < parts.size(); i++) {
            if (key.equals(parts.get(i).key)) return i;
        }
        return -1;
    }

    private static int uniqueIndex(List<QueryPart> parts, String key, String duplicateMessage) {
        int index = -1;
        for (int i = 0; i < parts.size(); i++) {
            if (!key.equals(parts.get(i).key)) continue;
            if (index >= 0) throw new IllegalArgumentException(duplicateMessage);
            index = i;
        }
        return index;
    }

    private static String joinRawQuery(List<QueryPart> parts) {
        StringBuilder result = new StringBuilder();
        for (QueryPart part : parts) {
            if (part.raw.isEmpty()) continue;
            if (result.length() != 0) result.append('&');
            result.append(part.raw);
        }
        return result.toString();
    }

    private static String decodeQuery(String value) {
        return URLDecoder.decode(value, StandardCharsets.UTF_8);
    }

    private static String encodeQuery(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
    }

    private static String decodeBase64(String value) {
        String padded = value;
        int remainder = padded.length() & 3;
        if (remainder != 0) padded += "=".repeat(4 - remainder);

        for (Base64.Decoder decoder : new Base64.Decoder[]{
                Base64.getDecoder(),
                Base64.getUrlDecoder()
        }) {
            try {
                return new String(decoder.decode(padded), StandardCharsets.UTF_8);
            } catch (IllegalArgumentException ignored) {
            }
        }
        return null;
    }

    private record AuthorityRange(int start, int end, String authority) {
    }

    private record HostPort(String prefix, String port) {
    }

    private static final class QueryPart {
        final String raw;
        final String key;
        final String value;
        final boolean hasEquals;

        QueryPart(String raw, String key, String value, boolean hasEquals) {
            this.raw = raw;
            this.key = key;
            this.value = value;
            this.hasEquals = hasEquals;
        }

        static QueryPart encoded(String key, String value) {
            return new QueryPart(
                    encodeQuery(key) + "=" + encodeQuery(value),
                    key,
                    value,
                    true);
        }
    }
}

