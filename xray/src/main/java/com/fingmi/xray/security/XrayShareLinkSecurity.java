package com.fingmi.xray.security;

import com.fingmi.xray.core.LibXrayBridge;

import org.json.JSONArray;

import java.net.InetAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class XrayShareLinkSecurity {

    private static final int PROBE_TIMEOUT_MS = 10_000;
    private static final String SHA256_PATTERN = "(?i)[0-9a-f]{64}";

    private final LibXrayBridge bridge;
    private final XrayCertificatePins pins;

    public XrayShareLinkSecurity(LibXrayBridge bridge, XrayCertificatePins pins) {
        this.bridge = bridge;
        this.pins = pins;
    }

    public String secure(String normalizedLink) throws Exception {
        URI uri = URI.create(normalizedLink);
        String scheme = lower(uri.getScheme());

        if (scheme.equals("hy2") || scheme.equals("hysteria2")) {
            return secureHysteria2(normalizedLink, uri, scheme);
        }

        List<QueryPart> query = parseQuery(uri.getRawQuery());
        String security = lower(firstValue(query, "security"));
        boolean tls =
                scheme.equals("trojan")
                        ? security.isEmpty() || security.equals("tls")
                        : (scheme.equals("vless") || scheme.equals("vmess"))
                                && security.equals("tls");
        if (!tls) return normalizedLink;
        return secureTls(normalizedLink, uri, scheme, query);
    }

    private String secureHysteria2(String link, URI uri, String scheme) throws Exception {
        List<QueryPart> query = parseQuery(uri.getRawQuery());
        if (!requestsInsecure(query)) return link;

        String pcs = firstValueIgnoreCase(query, "pcs");
        String vcn = firstValueIgnoreCase(query, "vcn");
        if (!pcs.isEmpty() || !vcn.isEmpty()) {
            return stripInsecure(link, query);
        }

        String host = cleanHost(uri.getHost());
        if (host.isEmpty()) throw new IllegalArgumentException("Hysteria2 server is invalid");

        int port = uri.getPort() > 0 ? uri.getPort() : 443;
        String ports = firstValueIgnoreCase(query, "ports");
        if (!ports.isEmpty()) port = firstPort(ports);

        String serverName = firstValueIgnoreCase(query, "sni");
        if (serverName.isEmpty() && !isIpLiteral(host)) serverName = host;

        String identity =
                scheme + "\n"
                        + lower(host) + "\n"
                        + port + "\n"
                        + lower(serverName);

        String observed = bridge.probeHysteria2Certificate(
                host,
                port,
                serverName,
                PROBE_TIMEOUT_MS);
        String trusted = verifyOrTrust(
                identity,
                observed,
                "Hysteria2");

        return replaceSecurityQuery(link, query, trusted, true);
    }

    private String secureTls(
            String link,
            URI uri,
            String scheme,
            List<QueryPart> query) throws Exception {
        if (!requestsInsecure(query)) return link;

        String pcs = firstValueIgnoreCase(query, "pcs");
        String vcn = firstValueIgnoreCase(query, "vcn");
        if (!pcs.isEmpty() || !vcn.isEmpty()) {
            return stripInsecure(link, query);
        }

        String host = cleanHost(uri.getHost());
        if (host.isEmpty()) throw new IllegalArgumentException("TLS server is invalid");
        int port = uri.getPort() > 0 ? uri.getPort() : 443;

        String serverName = firstValueIgnoreCase(query, "sni");
        if (serverName.isEmpty()) {
            String type = lower(firstValueIgnoreCase(query, "type"));
            if (type.equals("ws") || type.equals("websocket")) {
                serverName = firstValueIgnoreCase(query, "host");
            }
        }

        String fingerprint = firstValueIgnoreCase(query, "fp");
        JSONArray alpn = parseAlpn(firstValueIgnoreCase(query, "alpn"));

        String identity =
                "tcp-tls\n"
                        + scheme + "\n"
                        + lower(host) + "\n"
                        + port + "\n"
                        + lower(serverName);

        String observed = bridge.probeTlsCertificate(
                host,
                port,
                serverName,
                fingerprint,
                alpn,
                PROBE_TIMEOUT_MS);
        String trusted = verifyOrTrust(
                identity,
                observed,
                "TLS");

        return replaceSecurityQuery(link, query, trusted, false);
    }

    private String verifyOrTrust(String identity, String observed, String kind) throws Exception {
        if (observed == null || !observed.matches(SHA256_PATTERN)) {
            throw new IllegalStateException(kind + " certificate probe returned an invalid fingerprint");
        }

        String normalizedObserved = observed.toLowerCase(Locale.ROOT);
        String stored = pins.get(identity);
        if (stored.isEmpty()) {
            pins.put(identity, normalizedObserved);
            return normalizedObserved;
        }

        if (!stored.matches(SHA256_PATTERN)) {
            throw new IllegalStateException("Stored " + kind + " certificate fingerprint is invalid");
        }

        String normalizedStored = stored.toLowerCase(Locale.ROOT);
        if (!MessageDigest.isEqual(
                normalizedStored.getBytes(StandardCharsets.US_ASCII),
                normalizedObserved.getBytes(StandardCharsets.US_ASCII))) {
            throw new IllegalStateException(
                    kind + " server certificate changed; delete the saved Xray configuration before trusting the new certificate");
        }
        return normalizedStored;
    }

    private static String replaceSecurityQuery(
            String link,
            List<QueryPart> source,
            String pcs,
            boolean hysteria) {
        List<QueryPart> result = new ArrayList<>();
        for (QueryPart part : source) {
            if (part.key.equalsIgnoreCase("insecure")
                    || part.key.equalsIgnoreCase("allowInsecure")) {
                continue;
            }
            if (part.key.equalsIgnoreCase("pcs")) continue;

            String canonical = canonicalSecurityKey(part.key, hysteria);
            result.add(part.withKey(canonical));
        }
        if (!pcs.isEmpty()) result.add(QueryPart.encoded("pcs", pcs));
        return replaceRawQuery(link, joinQuery(result));
    }

    private static String stripInsecure(String link, List<QueryPart> source) {
        List<QueryPart> result = new ArrayList<>();
        for (QueryPart part : source) {
            if (!part.key.equalsIgnoreCase("insecure")
                    && !part.key.equalsIgnoreCase("allowInsecure")) {
                result.add(part);
            }
        }
        return replaceRawQuery(link, joinQuery(result));
    }

    private static String canonicalSecurityKey(String key, boolean hysteria) {
        if (key.equalsIgnoreCase("pcs")) return "pcs";
        if (key.equalsIgnoreCase("vcn")) return "vcn";
        if (key.equalsIgnoreCase("sni")) return "sni";
        if (!hysteria) {
            if (key.equalsIgnoreCase("fp")) return "fp";
            if (key.equalsIgnoreCase("alpn")) return "alpn";
            if (key.equalsIgnoreCase("security")) return "security";
        }
        return key;
    }

    private static boolean requestsInsecure(List<QueryPart> query) {
        for (QueryPart part : query) {
            if (!part.key.equalsIgnoreCase("insecure")
                    && !part.key.equalsIgnoreCase("allowInsecure")) {
                continue;
            }
            if (part.value.equals("1") || part.value.equalsIgnoreCase("true")) return true;
        }
        return false;
    }

    private static JSONArray parseAlpn(String value) {
        JSONArray result = new JSONArray();
        String trimmed = value == null ? "" : value.trim();
        if (trimmed.isEmpty()) return result;

        if (trimmed.startsWith("[")) {
            try {
                JSONArray source = new JSONArray(trimmed);
                for (int i = 0; i < source.length(); i++) {
                    String item = source.optString(i).trim();
                    if (!item.isEmpty()) result.put(item);
                }
                return result;
            } catch (Exception ignored) {
            }
        }

        for (String item : trimmed.split(",", -1)) {
            String valueItem = item.trim();
            if (!valueItem.isEmpty()) result.put(valueItem);
        }
        return result;
    }

    private static int firstPort(String expression) {
        String first = expression.split(",", -1)[0];
        int dash = first.indexOf('-');
        String candidate = dash < 0 ? first : first.substring(0, dash);
        try {
            int port = Integer.parseInt(candidate);
            if (port < 1 || port > 65_535) throw new NumberFormatException();
            return port;
        } catch (NumberFormatException error) {
            throw new IllegalArgumentException("Hysteria2 port hopping is invalid", error);
        }
    }

    private static boolean isIpLiteral(String host) {
        if (host.indexOf(':') >= 0) {
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
            if (part.isEmpty() || part.length() > 3) return false;
            if (part.length() > 1 && part.charAt(0) == '0') return false;
            int value = 0;
            for (int i = 0; i < part.length(); i++) {
                char c = part.charAt(i);
                if (c < '0' || c > '9') return false;
                value = value * 10 + (c - '0');
            }
            if (value > 255) return false;
        }
        return true;
    }

    private static String cleanHost(String host) {
        if (host == null) return "";
        String result = host.trim();
        if (result.startsWith("[") && result.endsWith("]") && result.length() > 2) {
            result = result.substring(1, result.length() - 1);
        }
        return result;
    }

    private static String firstValue(List<QueryPart> query, String key) {
        for (QueryPart part : query) {
            if (part.key.equals(key)) return part.value;
        }
        return "";
    }

    private static String firstValueIgnoreCase(List<QueryPart> query, String key) {
        for (QueryPart part : query) {
            if (part.key.equalsIgnoreCase(key)) return part.value;
        }
        return "";
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
                    URLDecoder.decode(rawKey, StandardCharsets.UTF_8),
                    URLDecoder.decode(rawValue, StandardCharsets.UTF_8),
                    equals >= 0));
        }
        return result;
    }

    private static String replaceRawQuery(String link, String query) {
        int question = link.indexOf('?');
        int fragment = link.indexOf('#');
        int baseEnd = question >= 0 && (fragment < 0 || question < fragment)
                ? question
                : (fragment < 0 ? link.length() : fragment);
        String suffix = fragment < 0 ? "" : link.substring(fragment);
        return link.substring(0, baseEnd)
                + (query.isEmpty() ? "" : "?" + query)
                + suffix;
    }

    private static String joinQuery(List<QueryPart> query) {
        StringBuilder result = new StringBuilder();
        for (QueryPart part : query) {
            if (part.raw.isEmpty()) continue;
            if (!result.isEmpty()) result.append('&');
            result.append(part.raw);
        }
        return result.toString();
    }

    private static String lower(String value) {
        return value == null ? "" : value.toLowerCase(Locale.ROOT);
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

        QueryPart withKey(String canonicalKey) {
            if (canonicalKey.equals(key)) return this;
            return encoded(canonicalKey, value);
        }

        static QueryPart encoded(String key, String value) {
            String encodedKey = URLEncoder.encode(key, StandardCharsets.UTF_8).replace("+", "%20");
            String encodedValue = URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
            return new QueryPart(
                    encodedKey + "=" + encodedValue,
                    key,
                    value,
                    true);
        }
    }
}
