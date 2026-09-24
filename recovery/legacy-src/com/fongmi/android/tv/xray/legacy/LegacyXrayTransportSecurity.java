package com.fongmi.android.tv.xray.legacy;

import java.net.InetAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Reconstructed transport-security layer from XrayService + R8 helpers j81/x82.
 *
 * It converts an explicitly insecure node into TOFU certificate pinning instead
 * of silently accepting future certificate changes.
 */
public final class LegacyXrayTransportSecurity {

    private static final int PROBE_TIMEOUT_MS = 10_000;
    private static final String SHA256 = "(?i)[0-9a-f]{64}";

    private final LegacyXrayProbeApi probeApi;
    private final LegacyXrayCertificateStore pins;

    public LegacyXrayTransportSecurity(
            LegacyXrayProbeApi probeApi,
            LegacyXrayCertificateStore pins) {
        this.probeApi = probeApi;
        this.pins = pins;
    }

    public String secure(String normalizedLink) throws Exception {
        String value = LegacyXrayShareLinkNormalizer.normalize(normalizedLink);
        URI uri = URI.create(value);
        String scheme = lower(uri.getScheme());

        if ("hy2".equals(scheme) || "hysteria2".equals(scheme)) {
            return secureHysteria2(value, uri, scheme);
        }

        String security = lower(first(parseQuery(uri.getRawQuery()), "security", true));
        boolean tls =
                ("trojan".equals(scheme) && (security.isEmpty() || "tls".equals(security)))
                        || (("vless".equals(scheme) || "vmess".equals(scheme))
                        && "tls".equals(security));

        return tls ? secureTls(value, uri, scheme) : value;
    }

    private String secureHysteria2(String value, URI uri, String scheme) throws Exception {
        List<QueryPart> query = parseQuery(uri.getRawQuery());
        if (!requestsInsecure(query)) return value;

        String existingPcs = first(query, "pcs", true);
        String existingVcn = first(query, "vcn", true);
        if (!existingPcs.isEmpty() || !existingVcn.isEmpty()) {
            return rewriteHysteria2(uri, query, "");
        }

        String host = cleanHost(uri.getHost());
        if (isBlank(host)) {
            throw new IllegalArgumentException("Hysteria2 server is invalid");
        }

        int port = uri.getPort() > 0 ? uri.getPort() : 443;
        String hopping = first(query, "ports", true);
        if (!hopping.isEmpty()) {
            port = firstPort(hopping);
        }

        String serverName = first(query, "sni", true);
        if (serverName.isEmpty() && !isIpLiteral(host)) {
            serverName = host;
        }

        String identity =
                scheme + "\n"
                        + lower(host) + "\n"
                        + port + "\n"
                        + lower(serverName);

        String observed = probeApi.probeHysteria2Certificate(
                host,
                port,
                serverName,
                PROBE_TIMEOUT_MS);
        String trusted = verifyOrTrust(identity, observed, "Hysteria2");
        return rewriteHysteria2(uri, query, trusted);
    }

    private String secureTls(String value, URI uri, String scheme) throws Exception {
        List<QueryPart> query = parseQuery(uri.getRawQuery());
        if (!requestsInsecure(query)) return value;

        String existingPcs = first(query, "pcs", true);
        String existingVcn = first(query, "vcn", true);
        if (!existingPcs.isEmpty() || !existingVcn.isEmpty()) {
            return rewriteTls(uri, query, "");
        }

        String host = cleanHost(uri.getHost());
        if (isBlank(host)) {
            throw new IllegalArgumentException("TLS server is invalid");
        }
        int port = uri.getPort() > 0 ? uri.getPort() : 443;

        String serverName = first(query, "sni", true);
        if (serverName.isEmpty()) {
            // The shipped code intentionally uses exact lower-case keys for the
            // websocket fallback, unlike its case-insensitive SNI lookup.
            String type = first(query, "type", false);
            if ("ws".equals(type) || "websocket".equals(type)) {
                serverName = first(query, "host", false);
            }
        }

        String fingerprint = first(query, "fp", true);
        List<String> alpn = parseAlpn(first(query, "alpn", true));

        String identity =
                "tcp-tls\n"
                        + lower(scheme) + "\n"
                        + lower(host) + "\n"
                        + port + "\n"
                        + lower(serverName);

        String observed = probeApi.probeTlsCertificate(
                host,
                port,
                serverName,
                fingerprint,
                alpn,
                PROBE_TIMEOUT_MS);
        String trusted = verifyOrTrust(identity, observed, "TLS");
        return rewriteTls(uri, query, trusted);
    }

    private String verifyOrTrust(
            String identity,
            String observed,
            String kind) throws Exception {
        if (observed == null || !observed.matches(SHA256)) {
            throw new IllegalStateException(
                    kind + " certificate probe returned an invalid fingerprint");
        }

        String normalizedObserved = observed.toLowerCase(Locale.ROOT);
        String stored = pins.get(identity);
        if (stored.isEmpty()) {
            pins.put(identity, normalizedObserved);
            return normalizedObserved;
        }

        if (!stored.matches(SHA256)) {
            throw new IllegalStateException(
                    "Stored " + kind + " certificate fingerprint is invalid");
        }

        String normalizedStored = stored.toLowerCase(Locale.ROOT);
        if (!MessageDigest.isEqual(
                normalizedStored.getBytes(StandardCharsets.US_ASCII),
                normalizedObserved.getBytes(StandardCharsets.US_ASCII))) {
            throw new IllegalStateException(
                    kind
                            + " server certificate changed; delete the saved Xray configuration"
                            + " before trusting the new certificate");
        }
        return normalizedStored;
    }

    private static String rewriteHysteria2(
            URI uri,
            List<QueryPart> source,
            String newPin) {
        List<String> result = new ArrayList<>();
        for (QueryPart part : source) {
            if (isInsecureKey(part.key)) continue;
            if (!newPin.isEmpty() && part.key.equalsIgnoreCase("pcs")) continue;

            String canonical = canonicalHy2Key(part.key);
            result.add(rewriteKey(part, canonical, false));
        }
        if (!newPin.isEmpty()) result.add("pcs=" + newPin);

        // The shipped Hysteria helper always appends '?' even when the resulting
        // query list is empty.
        return rebuild(uri, result, true);
    }

    private static String rewriteTls(
            URI uri,
            List<QueryPart> source,
            String newPin) {
        List<String> result = new ArrayList<>();
        for (QueryPart part : source) {
            if (isInsecureKey(part.key)) continue;
            if (!newPin.isEmpty() && part.key.equalsIgnoreCase("pcs")) continue;

            String canonical = canonicalTlsKey(part.key);
            boolean lowerValue = "security".equals(canonical);
            result.add(rewriteKey(part, canonical, lowerValue));
        }
        if (!newPin.isEmpty()) result.add("pcs=" + newPin);
        return rebuild(uri, result, false);
    }

    private static String canonicalHy2Key(String key) {
        if (key.equalsIgnoreCase("pcs")) return "pcs";
        if (key.equalsIgnoreCase("vcn")) return "vcn";
        if (key.equalsIgnoreCase("sni")) return "sni";
        return null;
    }

    private static String canonicalTlsKey(String key) {
        if (key.equalsIgnoreCase("pcs")) return "pcs";
        if (key.equalsIgnoreCase("vcn")) return "vcn";
        if (key.equalsIgnoreCase("sni")) return "sni";
        if (key.equalsIgnoreCase("fp")) return "fp";
        if (key.equalsIgnoreCase("alpn")) return "alpn";
        if (key.equalsIgnoreCase("security")) return "security";
        return null;
    }

    private static String rewriteKey(
            QueryPart part,
            String canonical,
            boolean lowerValue) {
        if (canonical == null) return part.raw;

        int equals = part.raw.indexOf('=');
        if (equals < 0) return canonical;

        String value = lowerValue ? lower(part.value) : part.raw.substring(equals + 1);
        return canonical + "=" + value;
    }

    private static String rebuild(
            URI uri,
            List<String> query,
            boolean alwaysQuestionMark) {
        StringBuilder result = new StringBuilder(uri.getScheme());
        result.append(':').append(uri.getRawSchemeSpecificPart());

        int question = result.indexOf("?");
        if (question >= 0) result.setLength(question);

        if (alwaysQuestionMark || !query.isEmpty()) {
            result.append('?');
            for (int index = 0; index < query.size(); index++) {
                if (index > 0) result.append('&');
                result.append(query.get(index));
            }
        }

        if (uri.getRawFragment() != null) {
            result.append('#').append(uri.getRawFragment());
        }
        return result.toString();
    }

    private static boolean requestsInsecure(List<QueryPart> query) {
        for (QueryPart part : query) {
            if (!isInsecureKey(part.key)) continue;
            if ("1".equals(part.value) || "true".equalsIgnoreCase(part.value)) return true;
        }
        return false;
    }

    private static boolean isInsecureKey(String key) {
        return key.equalsIgnoreCase("insecure")
                || key.equalsIgnoreCase("allowInsecure");
    }

    private static List<String> parseAlpn(String raw) {
        List<String> result = new ArrayList<>();
        String value = raw == null ? "" : raw.trim();
        if (value.isEmpty()) return result;

        // The APK first tries a JSON string array when the value starts with '['.
        // A small local parser is used here to keep this recovered layer independent
        // from org.json; malformed arrays fall back to comma splitting like the APK.
        if (value.startsWith("[") && value.endsWith("]")) {
            List<String> jsonStrings = parseSimpleJsonStringArray(value);
            if (jsonStrings != null) return jsonStrings;
        }

        for (String part : value.split(",", -1)) {
            String trimmed = part.trim();
            if (!trimmed.isEmpty()) result.add(trimmed);
        }
        return result;
    }

    private static List<String> parseSimpleJsonStringArray(String value) {
        List<String> result = new ArrayList<>();
        int index = 1;
        while (index < value.length() - 1) {
            while (index < value.length() - 1
                    && Character.isWhitespace(value.charAt(index))) index++;
            if (index >= value.length() - 1) return result;
            if (value.charAt(index) == ',') {
                index++;
                continue;
            }
            if (value.charAt(index) != '"') return null;

            StringBuilder item = new StringBuilder();
            index++;
            boolean escaped = false;
            while (index < value.length() - 1) {
                char c = value.charAt(index++);
                if (escaped) {
                    item.append(c);
                    escaped = false;
                } else if (c == '\\') {
                    escaped = true;
                } else if (c == '"') {
                    break;
                } else {
                    item.append(c);
                }
            }
            String trimmed = item.toString().trim();
            if (!trimmed.isEmpty()) result.add(trimmed);
        }
        return result;
    }

    private static List<QueryPart> parseQuery(String rawQuery) {
        List<QueryPart> result = new ArrayList<>();
        if (rawQuery == null || rawQuery.isEmpty()) return result;

        for (String raw : rawQuery.split("&", -1)) {
            int equals = raw.indexOf('=');
            String rawKey = equals < 0 ? raw : raw.substring(0, equals);
            String rawValue = equals < 0 ? "" : raw.substring(equals + 1);
            result.add(
                    new QueryPart(
                            raw,
                            URLDecoder.decode(rawKey, StandardCharsets.UTF_8),
                            URLDecoder.decode(rawValue, StandardCharsets.UTF_8)));
        }
        return result;
    }

    private static String first(
            List<QueryPart> query,
            String key,
            boolean ignoreCase) {
        for (QueryPart part : query) {
            if (ignoreCase
                    ? part.key.equalsIgnoreCase(key)
                    : part.key.equals(key)) {
                return part.value;
            }
        }
        return "";
    }

    private static int firstPort(String expression) {
        String first = expression.split(",", -1)[0];
        int dash = first.indexOf('-');
        String rawPort = dash < 0 ? first : first.substring(0, dash);
        try {
            int port = Integer.parseInt(rawPort);
            if (port < 1 || port > 65_535) throw new NumberFormatException();
            return port;
        } catch (NumberFormatException error) {
            throw new IllegalArgumentException("Hysteria2 port hopping is invalid", error);
        }
    }

    private static boolean isIpLiteral(String host) {
        if (host.indexOf(':') >= 0) {
            if (host.indexOf('%') >= 0 || !host.matches("(?i)^[0-9a-f:.]+$")) {
                return false;
            }
            try {
                InetAddress.getByName(host);
                return true;
            } catch (Exception ignored) {
                return false;
            }
        }

        String[] parts = host.split("\\.", -1);
        if (parts.length != 4) return false;
        for (String part : parts) {
            if (part.isEmpty()
                    || part.length() > 3
                    || (part.length() > 1 && part.charAt(0) == '0')) {
                return false;
            }
            int number = 0;
            for (int index = 0; index < part.length(); index++) {
                char c = part.charAt(index);
                if (c < '0' || c > '9') return false;
                number = number * 10 + (c - '0');
            }
            if (number > 255) return false;
        }
        return true;
    }

    private static String cleanHost(String value) {
        if (value == null) return "";
        String host = value.trim();
        if (host.length() > 1 && host.charAt(0) == '[' && host.charAt(host.length() - 1) == ']') {
            return host.substring(1, host.length() - 1);
        }
        return host;
    }

    private static boolean isBlank(String value) {
        if (value == null) return true;
        for (int offset = 0; offset < value.length();) {
            int cp = value.codePointAt(offset);
            if (!Character.isWhitespace(cp)) return false;
            offset += Character.charCount(cp);
        }
        return true;
    }

    private static String lower(String value) {
        return value == null ? "" : value.toLowerCase(Locale.ROOT);
    }

    private static final class QueryPart {
        final String raw;
        final String key;
        final String value;

        QueryPart(String raw, String key, String value) {
            this.raw = raw;
            this.key = key;
            this.value = value;
        }
    }
}
