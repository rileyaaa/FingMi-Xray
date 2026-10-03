package com.fingmi.xray.security;

import com.fingmi.xray.core.LibXrayBridge;
import com.fingmi.xray.config.XrayShareLinkNormalizer;

import org.json.JSONArray;

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
public final class XrayShareLinkSecurity {

    private static final int PROBE_TIMEOUT_MS = 10_000;
    private static final String SHA256 = "(?i)[0-9a-f]{64}";

    private final LibXrayBridge bridge;
    private final XrayCertificatePins pins;

    public XrayShareLinkSecurity(
            LibXrayBridge bridge,
            XrayCertificatePins pins) {
        this.bridge = bridge;
        this.pins = pins;
    }

    public String secure(String normalizedLink) throws Exception {
        PreparedLink prepared = prepare(normalizedLink);
        prepared.commitTrust();
        return prepared.value();
    }

    /**
     * Service-only form of the released security transform. It injects the
     * observed first-trust fingerprint into the normalized link immediately,
     * but defers persistence until the owning operation has actually succeeded.
     * The public secure() method above deliberately keeps released immediate
     * persistence semantics for golden parity and non-Service callers.
     */
    public PreparedLink prepare(String normalizedLink) throws Exception {
        String value = XrayShareLinkNormalizer.normalize(normalizedLink);
        URI uri = URI.create(value);
        String scheme = lower(uri.getScheme());

        if ("hy2".equals(scheme) || "hysteria2".equals(scheme)) {
            return prepareHysteria2(value, uri, scheme);
        }

        String security = lower(first(parseQuery(uri.getRawQuery()), "security", true));
        boolean tls =
                ("trojan".equals(scheme) && (security.isEmpty() || "tls".equals(security)))
                        || (("vless".equals(scheme) || "vmess".equals(scheme))
                        && "tls".equals(security));

        return tls ? prepareTls(value, uri, scheme) : ready(value);
    }

    private PreparedLink prepareHysteria2(String value, URI uri, String scheme) throws Exception {
        List<QueryPart> query = parseQuery(uri.getRawQuery());
        if (!requestsInsecure(query)) return ready(value);

        String existingPcs = first(query, "pcs", true);
        String existingVcn = first(query, "vcn", true);
        if (!existingPcs.isEmpty() || !existingVcn.isEmpty()) {
            return ready(rewriteHysteria2(uri, query, ""));
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

        String observed = bridge.probeHysteria2Certificate(
                host,
                port,
                serverName,
                PROBE_TIMEOUT_MS);
        TrustDecision trust = verifyOrPrepareTrust(identity, observed, "Hysteria2");
        return new PreparedLink(
                rewriteHysteria2(uri, query, trust.fingerprint()),
                trust.pending());
    }

    private PreparedLink prepareTls(String value, URI uri, String scheme) throws Exception {
        List<QueryPart> query = parseQuery(uri.getRawQuery());
        if (!requestsInsecure(query)) return ready(value);

        String existingPcs = first(query, "pcs", true);
        String existingVcn = first(query, "vcn", true);
        if (!existingPcs.isEmpty() || !existingVcn.isEmpty()) {
            return ready(rewriteTls(uri, query, ""));
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
        List<String> alpnItems = parseAlpn(first(query, "alpn", true));
        JSONArray alpn = new JSONArray();
        for (String item : alpnItems) alpn.put(item);

        String identity =
                "tcp-tls\n"
                        + lower(scheme) + "\n"
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
        TrustDecision trust = verifyOrPrepareTrust(identity, observed, "TLS");
        return new PreparedLink(
                rewriteTls(uri, query, trust.fingerprint()),
                trust.pending());
    }

    private TrustDecision verifyOrPrepareTrust(
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
            return new TrustDecision(
                    normalizedObserved,
                    new PendingTrust(identity, normalizedObserved, kind));
        }

        verifyStoredPin(stored, normalizedObserved, kind);
        return new TrustDecision(stored, null);
    }

    private static void verifyStoredPin(
            String stored,
            String observed,
            String kind) {
        if (!stored.matches(SHA256)) {
            throw new IllegalStateException(
                    "Stored " + kind + " certificate fingerprint is invalid");
        }

        // Exact shipped behavior compares the stored ASCII hex text as-is
        // against the newly observed lower-case fingerprint. Do not normalize
        // migrated stored pins here: case differences are treated as a change.
        if (!MessageDigest.isEqual(
                stored.getBytes(StandardCharsets.US_ASCII),
                observed.getBytes(StandardCharsets.US_ASCII))) {
            throw new IllegalStateException(
                    kind
                            + " server certificate changed; delete the saved Xray configuration"
                            + " before trusting the new certificate");
        }
    }

    public final class PreparedLink {
        private final String value;
        private final PendingTrust pending;

        private PreparedLink(String value, PendingTrust pending) {
            this.value = value;
            this.pending = pending;
        }

        public String value() {
            return value;
        }

        public void commitTrust() throws Exception {
            if (pending != null) pending.commit();
        }
    }

    private PreparedLink ready(String value) {
        return new PreparedLink(value, null);
    }

    private record TrustDecision(String fingerprint, PendingTrust pending) {
    }

    private final class PendingTrust {
        private final String identity;
        private final String fingerprint;
        private final String kind;

        private PendingTrust(String identity, String fingerprint, String kind) {
            this.identity = identity;
            this.fingerprint = fingerprint;
            this.kind = kind;
        }

        private void commit() throws Exception {
            String stored = pins.get(identity);
            if (stored.isEmpty()) {
                pins.put(identity, fingerprint);
                return;
            }
            verifyStoredPin(stored, fingerprint, kind);
        }
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

        // Exact shipped behavior: when the value starts with '[', first try
        // Android's JSONArray parser and collect optString(i).trim() values.
        // Any JSON parse failure falls back to comma splitting.
        if (value.startsWith("[")) {
            try {
                JSONArray array = new JSONArray(value);
                for (int index = 0; index < array.length(); index++) {
                    String item = array.optString(index).trim();
                    if (!item.isEmpty()) result.add(item);
                }
                return result;
            } catch (Exception ignored) {
                // Fall through to the shipped comma-splitting fallback.
            }
        }

        for (String part : value.split(",", -1)) {
            String trimmed = part.trim();
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
                            decodeUtf8(rawKey),
                            decodeUtf8(rawValue)));
        }
        return result;
    }

    private static String decodeUtf8(String value) {
        try {
            return URLDecoder.decode(value, StandardCharsets.UTF_8.name());
        } catch (java.io.UnsupportedEncodingException error) {
            throw new IllegalStateException("UTF-8 is unavailable", error);
        }
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

