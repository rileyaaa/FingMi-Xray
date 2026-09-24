package com.fingmi.xray.config;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Locale;
import java.util.Set;

public final class XrayShareLinkNormalizer {

    private static final int MAX_LENGTH = 16_384;
    private static final Set<String> SUPPORTED =
            Set.of("vless", "vmess", "trojan", "ss", "hy2", "hysteria2");

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
        if (colon <= 0) throw new IllegalArgumentException("Invalid Xray link");

        String scheme = value.substring(0, colon);
        String normalizedScheme = scheme.toLowerCase(Locale.ROOT);
        if (!SUPPORTED.contains(normalizedScheme)) {
            throw new IllegalArgumentException("Unsupported Xray link protocol");
        }
        if (!scheme.equals(normalizedScheme)) {
            value = normalizedScheme + value.substring(colon);
        }

        if ("ss".equals(normalizedScheme)) value = normalizeLegacyShadowsocks(value);

        if (!"vmess".equals(normalizedScheme)) {
            URI uri = URI.create(value);
            if (uri.getScheme() == null) throw new IllegalArgumentException("Invalid Xray link");
            if (!"ss".equals(normalizedScheme) && uri.getHost() == null) {
                throw new IllegalArgumentException("Invalid Xray link");
            }
        }
        return value;
    }

    private static String normalizeLegacyShadowsocks(String value) {
        if (!value.startsWith("ss://")) return value;

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

        URI endpointUri = URI.create("ss://x@" + endpoint);
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
}
