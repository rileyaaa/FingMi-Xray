#!/usr/bin/env python3
"""Differential JVM parity for current vs released-reference Xray link normalization."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "xray/src/main/java/com/fingmi/xray/config/XrayShareLinkNormalizer.java"
LEGACY = ROOT / "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayShareLinkNormalizer.java"
CURRENT_DISPLAY = ROOT / "xray/src/main/java/com/fingmi/xray/config/XrayDisplay.java"
LEGACY_DISPLAY = ROOT / "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayDisplay.java"

HARNESS = r"""
package com.fingmi.xray.config;

import com.fongmi.android.tv.xray.legacy.LegacyXrayDisplay;
import com.fongmi.android.tv.xray.legacy.LegacyXrayShareLinkNormalizer;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Objects;

public final class ShareLinkNormalizerParityTest {

    private record Outcome(boolean success, String value, String errorType) {}

    private interface Normalizer {
        String normalize(String input);
    }

    private static Outcome capture(Normalizer normalizer, String input) {
        try {
            return new Outcome(true, normalizer.normalize(input), "");
        } catch (Throwable error) {
            return new Outcome(
                    false,
                    error.getMessage() == null ? "" : error.getMessage(),
                    error.getClass().getName());
        }
    }

    private static void same(String id, String input) {
        Outcome released = capture(LegacyXrayShareLinkNormalizer::normalize, input);
        Outcome current = capture(XrayShareLinkNormalizer::normalize, input);
        if (!Objects.equals(released, current)) {
            throw new AssertionError(
                    id
                            + "\ninput="
                            + input
                            + "\nreleased="
                            + released
                            + "\ncurrent="
                            + current);
        }
    }

    private static void sameDisplay(String id, String input) {
        Outcome released = capture(LegacyXrayDisplay::describe, input);
        Outcome current = capture(XrayDisplay::describe, input);
        if (!Objects.equals(released, current)) {
            throw new AssertionError(
                    id
                            + "\ninput="
                            + input
                            + "\nreleased="
                            + released
                            + "\ncurrent="
                            + current);
        }
    }

    private static void expect(String id, String input, String expected) {
        String actual = XrayShareLinkNormalizer.normalize(input);
        if (!expected.equals(actual)) {
            throw new AssertionError(
                    id + "\nexpected=" + expected + "\nactual=" + actual);
        }
    }

    private static void expectError(String id, String input, String expected) {
        try {
            XrayShareLinkNormalizer.normalize(input);
            throw new AssertionError(id + ": expected error " + expected);
        } catch (IllegalArgumentException error) {
            if (!expected.equals(error.getMessage())) {
                throw new AssertionError(
                        id
                                + "\nexpected error="
                                + expected
                                + "\nactual error="
                                + error.getMessage(),
                        error);
            }
        }
    }

    private static String b64(String value) {
        return Base64.getEncoder()
                .withoutPadding()
                .encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) {
        String legacySs = b64("aes-256-gcm:pass@example.com:8388");
        String ssCredentials = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString("aes-256-gcm:pass".getBytes(StandardCharsets.UTF_8));

        String vmessKcpJson =
                "{\"v\":\"2\",\"ps\":\"kcp\",\"add\":\"example.com\","
                        + "\"port\":\"443\","
                        + "\"id\":\"11111111-1111-1111-1111-111111111111\","
                        + "\"scy\":\"auto\",\"net\":\"kcp\",\"type\":\"srtp\","
                        + "\"host\":\"\",\"path\":\"seed-value\",\"tls\":\"\"}";
        String vmessKcp = "vmess://" + b64(vmessKcpJson);
        String vmessBad = "vmess://" + b64("{\"port\":65536}");
        String vmessDecimal = "vmess://" + b64("{\"port\":443.5}");
        String vmessExponent = "vmess://" + b64("{\"port\":6.5536e4}");

        expect(
                "uppercase-scheme",
                "VLESS://abc@example.com:443",
                "vless://abc@example.com:443");
        expect(
                "legacy-ss",
                "ss://" + legacySs + "#node",
                "ss://" + ssCredentials + "@example.com:8388#node");
        expect(
                "trojan-default-tls",
                "trojan://pw@example.com:443#node",
                "trojan://pw@example.com:443?security=tls#node");
        expect(
                "kcp-vless",
                "vless://abc@example.com:443?type=kcp&headerType=srtp&seed=test-seed&security=tls&sni=example.com",
                "vless://abc@example.com:443?type=kcp&headerType=srtp&seed=test-seed&security=tls&sni=example.com");
        expect(
                "kcp-trojan",
                "trojan://pw@example.com:443?type=kcp&headerType=wechat-video&seed=seed123&security=tls",
                "trojan://pw@example.com:443?type=kcp&headerType=wechat-video&seed=seed123&security=tls");
        expect(
                "grpc-reality",
                "vless://abc@example.com:443?type=grpc&serviceName=svc&authority=edge.example.com&mode=multi&security=reality&pbk=PUBKEY&sid=01&spx=%2Ffoo",
                "vless://abc@example.com:443?type=grpc&serviceName=svc&authority=edge.example.com&mode=multi&security=reality&pbk=PUBKEY&sid=01&spx=%2Ffoo");
        expect("vmess-kcp", vmessKcp, vmessKcp);
        expect(
                "hy2-authority-range",
                "hy2://pw@example.com:20000-20005",
                "hy2://pw@example.com:20000?ports=20000-20005");
        expect(
                "hy2-mport",
                "hy2://pw@example.com?mport=1000-1002",
                "hy2://pw@example.com:443?ports=1000-1002");
        expect(
                "hy2-salamander",
                "hy2://pw@example.com?obfs=salamander&obfs-password=x",
                "hy2://pw@example.com:443?obfs=salamander&obfs-password=x");

        expectError(
                "hy2-gecko",
                "hy2://pw@example.com?obfs=gecko&obfs-password=x",
                "Hysteria2 Gecko obfuscation is unsupported by this native core");
        expectError(
                "hy2-missing-obfs-password",
                "hy2://pw@example.com?obfs=salamander",
                "Hysteria2 obfuscation password is missing");
        expectError(
                "hy2-missing-obfs-type",
                "hy2://pw@example.com?obfs-password=x",
                "Hysteria2 obfuscation type is missing");
        expectError(
                "invalid-authority-port",
                "vless://id@example.com:65536",
                "Xray link port is invalid");
        expectError("invalid-vmess-port", vmessBad, "Xray link port is invalid");

        List<String> differential = new ArrayList<>();
        differential.add(null);
        differential.add("");
        differential.add("   ");
        differential.add("vless://id@example.com:443");
        differential.add("  vless://id@example.com:443  ");
        differential.add("VMeSs://" + b64("{\"port\":443}"));
        differential.add("ftp://example.com/file");
        differential.add("vless://id@example.com:443\nsecond");
        differential.add("x".repeat(16_385));
        differential.add("trojan://pw@example.com:443?");
        differential.add("trojan://pw@example.com:443?security=reality#node");
        differential.add("vless://id@[2001:4860:4860::8888]:443?type=kcp&headerType=none");
        differential.add("trojan://pw@[2001:4860:4860::8888]:443");
        differential.add("vless://id@example.com:0");
        differential.add("vless://id@example.com:-1");
        differential.add("vless://id@example.com:abc");
        differential.add(vmessDecimal);
        differential.add(vmessExponent);
        differential.add("hy2://pw@example.com");
        differential.add("hy2://pw@example.com:443?mport=1000,1002-1004");
        differential.add("hy2://pw@example.com:443?mport=1004-1002");
        differential.add("hy2://pw@example.com:443?mport=1000-1002&ports=2000-2002");
        differential.add("hy2://pw@example.com:443?obfs=SALAMANDER&obfs-password=x");
        differential.add(
                "hy2://pw@example.com:443?pinSHA256="
                        + "aa".repeat(32));
        differential.add(
                "hy2://pw@example.com:443?pinSHA256="
                        + "AA:".repeat(31)
                        + "AA");
        differential.add("hy2://pw@example.com:443?pinSHA256=bad");
        differential.add(
                "hy2://pw@example.com:443?pcs="
                        + "bb".repeat(32)
                        + "&pinSHA256="
                        + "aa".repeat(32));
        differential.add("ss://not-base64#node");
        differential.add(
                "ss://"
                        + ssCredentials
                        + "@example.com:8388?plugin=v2ray-plugin%3Btls%3Bhost%3Dedge.example%3Bpath%3D%2Fws");
        differential.add(
                "ss://"
                        + ssCredentials
                        + "@example.com:8388?plugin=v2ray-plugin%3Bmode%3Dquic");
        differential.add(
                "ss://"
                        + ssCredentials
                        + "@example.com:8388?plugin=unknown-plugin");
        differential.add(
                "ss://"
                        + ssCredentials
                        + "@example.com:8388?plugin=v2ray-plugin%3Bhost%3Da%3Bhost%3Db");
        differential.add(
                "ss://"
                        + ssCredentials
                        + "@example.com:8388?plugin=v2ray-plugin%3Btls&type=ws");

        int index = 0;
        for (String input : differential) {
            same("differential-" + index++, input);
        }

        List<String> displayInputs = List.of(
                "",
                "vless://id@example.com:443",
                "trojan://pw@ab:443?security=tls",
                "vless://id@localhost:443",
                "vmess://opaque-payload",
                "relative-value",
                "http://[2001:4860:4860::8888]:8443/path",
                "%%%invalid-uri%%%");
        index = 0;
        for (String input : displayInputs) {
            sameDisplay("display-" + index++, input);
        }

        System.out.println(
                "PASS current config text parity: "
                        + differential.size()
                        + " normalizer boundaries + "
                        + displayInputs.size()
                        + " display boundaries + released exact cases");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-normalizer-parity-") as directory:
    work = Path(directory)
    harness = work / "com/fingmi/xray/config/ShareLinkNormalizerParityTest.java"
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text(HARNESS.strip() + "\n")

    classes = work / "classes"
    subprocess.run(
        [
            "java",
            "com.sun.tools.javac.Main",
            "--release",
            "17",
            "-d",
            str(classes),
            str(CURRENT),
            str(LEGACY),
            str(CURRENT_DISPLAY),
            str(LEGACY_DISPLAY),
            str(harness),
        ],
        check=True,
    )
    subprocess.run(
        [
            "java",
            "-cp",
            str(classes),
            "com.fingmi.xray.config.ShareLinkNormalizerParityTest",
        ],
        check=True,
    )
