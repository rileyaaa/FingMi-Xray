package com.fongmi.android.tv.xray.legacy;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

/**
 * Pure-Java regression cases extracted from the recovered APK behavior.
 * Kept outside the Android build until the legacy freeze is complete.
 */
public final class LegacyXrayShareLinkNormalizerCases {

    public static void main(String[] args) {
        assertEquals(
                "vless://abc@example.com:443",
                LegacyXrayShareLinkNormalizer.normalize("VLESS://abc@example.com:443"));

        String legacy = Base64.getEncoder().withoutPadding().encodeToString(
                "aes-256-gcm:pass@example.com:8388".getBytes(StandardCharsets.UTF_8));
        String credentials = Base64.getUrlEncoder().withoutPadding().encodeToString(
                "aes-256-gcm:pass".getBytes(StandardCharsets.UTF_8));
        assertEquals(
                "ss://" + credentials + "@example.com:8388#node",
                LegacyXrayShareLinkNormalizer.normalize("ss://" + legacy + "#node"));

        assertEquals(
                "trojan://pw@example.com:443?security=tls#node",
                LegacyXrayShareLinkNormalizer.normalize("trojan://pw@example.com:443#node"));

        assertEquals(
                "vless://abc@example.com:443?type=kcp&headerType=srtp&seed=test-seed&security=tls&sni=example.com",
                LegacyXrayShareLinkNormalizer.normalize(
                        "vless://abc@example.com:443?type=kcp&headerType=srtp&seed=test-seed&security=tls&sni=example.com"));

        assertEquals(
                "trojan://pw@example.com:443?type=kcp&headerType=wechat-video&seed=seed123&security=tls",
                LegacyXrayShareLinkNormalizer.normalize(
                        "trojan://pw@example.com:443?type=kcp&headerType=wechat-video&seed=seed123&security=tls"));

        assertEquals(
                "vless://abc@example.com:443?type=grpc&serviceName=svc&authority=edge.example.com&mode=multi&security=reality&pbk=PUBKEY&sid=01&spx=%2Ffoo",
                LegacyXrayShareLinkNormalizer.normalize(
                        "vless://abc@example.com:443?type=grpc&serviceName=svc&authority=edge.example.com&mode=multi&security=reality&pbk=PUBKEY&sid=01&spx=%2Ffoo"));

        String vmessKcpJson =
                "{\"v\":\"2\",\"ps\":\"kcp\",\"add\":\"example.com\","
                        + "\"port\":\"443\",\"id\":\"11111111-1111-1111-1111-111111111111\","
                        + "\"scy\":\"auto\",\"net\":\"kcp\",\"type\":\"srtp\","
                        + "\"host\":\"\",\"path\":\"seed-value\",\"tls\":\"\"}";
        String vmessKcp =
                "vmess://"
                        + Base64.getEncoder()
                                .withoutPadding()
                                .encodeToString(vmessKcpJson.getBytes(StandardCharsets.UTF_8));
        assertEquals(vmessKcp, LegacyXrayShareLinkNormalizer.normalize(vmessKcp));

        assertEquals(
                "hy2://pw@example.com:20000?ports=20000-20005",
                LegacyXrayShareLinkNormalizer.normalize(
                        "hy2://pw@example.com:20000-20005"));

        assertEquals(
                "hy2://pw@example.com:443?ports=1000-1002",
                LegacyXrayShareLinkNormalizer.normalize(
                        "hy2://pw@example.com?mport=1000-1002"));

        assertEquals(
                "hy2://pw@example.com:443?obfs=salamander&obfs-password=x",
                LegacyXrayShareLinkNormalizer.normalize(
                        "hy2://pw@example.com?obfs=salamander&obfs-password=x"));

        assertError(
                "Hysteria2 Gecko obfuscation is unsupported by this native core",
                "hy2://pw@example.com?obfs=gecko&obfs-password=x");
        assertError(
                "Hysteria2 obfuscation password is missing",
                "hy2://pw@example.com?obfs=salamander");
        assertError(
                "Hysteria2 obfuscation type is missing",
                "hy2://pw@example.com?obfs-password=x");
        assertError(
                "Xray link port is invalid",
                "vless://id@example.com:65536");

        String vmessBad = Base64.getEncoder().withoutPadding().encodeToString(
                "{\"port\":65536}".getBytes(StandardCharsets.UTF_8));
        assertError("Xray link port is invalid", "vmess://" + vmessBad);
    }

    private static void assertEquals(String expected, String actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError("Expected: " + expected + "\nActual: " + actual);
        }
    }

    private static void assertError(String expected, String input) {
        try {
            LegacyXrayShareLinkNormalizer.normalize(input);
            throw new AssertionError("Expected error: " + expected);
        } catch (IllegalArgumentException error) {
            if (!expected.equals(error.getMessage())) {
                throw new AssertionError(
                        "Expected error: " + expected + "\nActual: " + error.getMessage(),
                        error);
            }
        }
    }
}
