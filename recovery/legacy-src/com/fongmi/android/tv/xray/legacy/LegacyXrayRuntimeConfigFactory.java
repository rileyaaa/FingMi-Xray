package com.fongmi.android.tv.xray.legacy;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Reconstructed Xray JSON builder from XrayService.m2089b.
 */
public final class LegacyXrayRuntimeConfigFactory {

    public static final String PROXY_TAG = "fongmi-xray-proxy";
    public static final String PRIVATE_BLOCK_TAG = "fongmi-xray-private-block";
    public static final String SESSION_TAG = "fongmi-xray-session";
    public static final String DNS_TAG = "fongmi-xray-dns";

    private static final String[] RESERVED = {
            "0.0.0.0/8",
            "10.0.0.0/8",
            "100.64.0.0/10",
            "127.0.0.0/8",
            "169.254.0.0/16",
            "172.16.0.0/12",
            "192.0.0.0/24",
            "192.0.2.0/24",
            "192.88.99.2/32",
            "192.168.0.0/16",
            "198.18.0.0/15",
            "198.51.100.0/24",
            "203.0.113.0/24",
            "224.0.0.0/4",
            "240.0.0.0/4",
            "::/96",
            "::ffff:0:0:0/96",
            "64:ff9b:1::/48",
            "100::/64",
            "100:0:0:1::/64",
            "2001:2::/48",
            "2001:db8::/32",
            "3fff::/20",
            "5f00::/16",
            "fc00::/7",
            "fe00::/8",
            "ff00::/8"
    };

    private final LegacyLibXrayApi core;
    private final LegacyXrayTransportSecurity security;

    public LegacyXrayRuntimeConfigFactory(
            LegacyLibXrayApi core,
            LegacyXrayTransportSecurity security) {
        this.core = core;
        this.security = security;
    }

    public JSONObject create(
            int socksPort,
            String shareLink,
            boolean udp) throws Exception {
        String normalized =
                LegacyXrayShareLinkNormalizer.normalize(shareLink);
        String secured = security.secure(normalized);
        String finalLink =
                LegacyXrayShareLinkNormalizer.normalize(secured);

        JSONObject converted = core.convertShareLink(finalLink);
        patchLiteralPlusCredential(finalLink, converted);

        JSONObject config = new JSONObject(converted.toString());
        JSONArray outbounds = config.optJSONArray("outbounds");
        if (outbounds == null || outbounds.length() != 1) {
            throw new JSONException("Exactly one Xray outbound is required");
        }

        JSONObject proxy = outbounds.getJSONObject(0);
        proxy.remove("sendThrough");
        proxy.put("tag", PROXY_TAG);
        proxy.put("targetStrategy", "ForceIP");

        JSONObject streamSettings = proxy.optJSONObject("streamSettings");
        if (streamSettings != null) {
            JSONObject sockopt = streamSettings.optJSONObject("sockopt");
            if (sockopt != null) {
                sockopt.put("domainStrategy", "AsIs");
            }
        }

        outbounds.put(
                new JSONObject()
                        .put("tag", PRIVATE_BLOCK_TAG)
                        .put("protocol", "blackhole")
                        .put("settings", new JSONObject()));

        config.put(
                "inbounds",
                new JSONArray().put(
                        new JSONObject()
                                .put("tag", SESSION_TAG)
                                .put("listen", "127.0.0.1")
                                .put("port", socksPort)
                                .put("protocol", "socks")
                                .put(
                                        "settings",
                                        new JSONObject()
                                                .put("auth", "noauth")
                                                .put("udp", udp)
                                                .put("ip", "127.0.0.1"))));

        config.put(
                "dns",
                new JSONObject()
                        .put("tag", DNS_TAG)
                        .put("queryStrategy", "UseIP")
                        .put("enableParallelQuery", true)
                        .put(
                                "servers",
                                new JSONArray()
                                        .put(dnsServer("https://1.1.1.1/dns-query"))
                                        .put(dnsServer("https://8.8.8.8/dns-query"))
                                        .put(dnsServer("tcp://1.1.1.1:53"))
                                        .put(dnsServer("tcp://8.8.8.8:53"))));

        config.put(
                "routing",
                new JSONObject()
                        .put("domainStrategy", "IPOnDemand")
                        .put(
                                "rules",
                                new JSONArray()
                                        .put(
                                                new JSONObject()
                                                        .put("type", "field")
                                                        .put(
                                                                "inboundTag",
                                                                new JSONArray().put(DNS_TAG))
                                                        .put("outboundTag", PROXY_TAG))
                                        .put(
                                                new JSONObject()
                                                        .put("type", "field")
                                                        .put(
                                                                "inboundTag",
                                                                new JSONArray().put(SESSION_TAG))
                                                        .put(
                                                                "domain",
                                                                new JSONArray()
                                                                        .put("localhost")
                                                                        .put("domain:localhost")
                                                                        .put("regexp:.*\\.localhost$")
                                                                        .put("regexp:.*\\.local$"))
                                                        .put(
                                                                "outboundTag",
                                                                PRIVATE_BLOCK_TAG))
                                        .put(
                                                new JSONObject()
                                                        .put("type", "field")
                                                        .put(
                                                                "inboundTag",
                                                                new JSONArray().put(SESSION_TAG))
                                                        .put("ip", reservedNetworks())
                                                        .put(
                                                                "outboundTag",
                                                                PRIVATE_BLOCK_TAG))
                                        .put(
                                                new JSONObject()
                                                        .put("type", "field")
                                                        .put(
                                                                "inboundTag",
                                                                new JSONArray().put(SESSION_TAG))
                                                        .put("network", "tcp,udp")
                                                        .put("outboundTag", PROXY_TAG))));

        config.put(
                "log",
                new JSONObject().put("loglevel", "warning"));

        return config;
    }

    private static void patchLiteralPlusCredential(
            String shareLink,
            JSONObject converted) throws JSONException {
        int colon = shareLink.indexOf(':');
        if (colon <= 0) return;

        String scheme =
                shareLink.substring(0, colon).toLowerCase(Locale.ROOT);
        if (!"trojan".equals(scheme)
                && !"hy2".equals(scheme)
                && !"hysteria2".equals(scheme)) {
            return;
        }

        String authority =
                URI.create(
                                LegacyXrayShareLinkNormalizer.normalize(
                                        shareLink))
                        .getRawAuthority();
        if (authority == null) return;

        int at = authority.lastIndexOf('@');
        if (at < 0) return;

        String credential =
                URLDecoder.decode(
                        authority
                                .substring(0, at)
                                .replace("+", "%2B"),
                        StandardCharsets.UTF_8);
        if (!credential.contains("+")) return;

        JSONArray outbounds = converted.optJSONArray("outbounds");
        // DEX_VERIFY: JADX inverts the null/count predicate here.
        if (outbounds == null || outbounds.length() != 1) {
            throw new JSONException(
                    "Xray conversion returned an invalid outbound count");
        }

        JSONObject outbound = outbounds.optJSONObject(0);
        if (outbound == null) {
            throw new JSONException(
                    "Xray conversion returned an invalid outbound");
        }

        String protocol =
                outbound.optString("protocol").toLowerCase(Locale.ROOT);
        if ("trojan".equals(scheme)) {
            if (!"trojan".equals(protocol)) {
                throw new JSONException(
                        "Trojan conversion returned the wrong protocol");
            }

            JSONObject settings = outbound.optJSONObject("settings");
            if (settings == null) {
                throw new JSONException(
                        "Trojan conversion returned invalid settings");
            }
            settings.put("password", credential);
            return;
        }

        if (!"hysteria".equals(protocol)) {
            throw new JSONException(
                    "Hysteria2 conversion returned the wrong protocol");
        }

        JSONObject stream = outbound.optJSONObject("streamSettings");
        JSONObject hysteria =
                stream == null
                        ? null
                        : stream.optJSONObject("hysteriaSettings");
        if (hysteria == null) {
            throw new JSONException(
                    "Hysteria2 conversion returned invalid settings");
        }
        hysteria.put("auth", credential);
    }

    private static JSONObject dnsServer(String address)
            throws JSONException {
        return new JSONObject()
                .put("address", address)
                .put("unexpectedIPs", reservedNetworks());
    }

    private static JSONArray reservedNetworks() {
        JSONArray values = new JSONArray();
        for (String value : RESERVED) values.put(value);
        return values;
    }
}
