#!/usr/bin/env python3
"""Differential JVM parity for released Xray transport-security behavior."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "xray/src/main/java/com/fingmi/xray/security/XrayShareLinkSecurity.java"
LEGACY = ROOT / "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayTransportSecurity.java"

STUBS = {
    "org/json/JSONArray.java": r"""
package org.json;
import java.util.ArrayList;
import java.util.List;
public final class JSONArray {
    private final List<String> values = new ArrayList<>();
    public JSONArray() {}
    public JSONArray(String raw) {
        String value = raw == null ? "" : raw.trim();
        if (!value.startsWith("[") || !value.endsWith("]")) {
            throw new IllegalArgumentException("invalid synthetic JSON array");
        }
        String body = value.substring(1, value.length() - 1).trim();
        if (body.isEmpty()) return;
        for (String part : body.split(",", -1)) {
            String item = part.trim();
            if (item.length() >= 2 && item.startsWith("\"") && item.endsWith("\"")) {
                item = item.substring(1, item.length() - 1);
            }
            values.add(item);
        }
    }
    public JSONArray put(Object value) {
        values.add(String.valueOf(value));
        return this;
    }
    public int length() { return values.size(); }
    public String optString(int index) {
        return index >= 0 && index < values.size() ? values.get(index) : "";
    }
}
""",
    "com/fingmi/xray/config/XrayShareLinkNormalizer.java": r"""
package com.fingmi.xray.config;
public final class XrayShareLinkNormalizer {
    private XrayShareLinkNormalizer() {}
    public static String normalize(String value) { return value; }
}
""",
    "com/fingmi/xray/core/LibXrayBridge.java": r"""
package com.fingmi.xray.core;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
public final class LibXrayBridge {
    public String observed;
    public final List<String> calls = new ArrayList<>();
    public LibXrayBridge(String observed) { this.observed = observed; }
    public String probeHysteria2Certificate(
            String server, int port, String serverName, int timeoutMs) {
        calls.add("hy2|" + server + "|" + port + "|" + serverName + "|" + timeoutMs);
        return observed;
    }
    public String probeTlsCertificate(
            String server,
            int port,
            String serverName,
            String fingerprint,
            JSONArray alpn,
            int timeoutMs) {
        List<String> values = new ArrayList<>();
        for (int i = 0; i < alpn.length(); i++) values.add(alpn.optString(i));
        calls.add("tls|" + server + "|" + port + "|" + serverName + "|"
                + fingerprint + "|" + String.join(",", values) + "|" + timeoutMs);
        return observed;
    }
}
""",
    "com/fingmi/xray/security/XrayCertificatePins.java": r"""
package com.fingmi.xray.security;
import java.util.LinkedHashMap;
import java.util.Map;
public final class XrayCertificatePins {
    public final Map<String, String> values = new LinkedHashMap<>();
    public String get(String identity) { return values.getOrDefault(identity, ""); }
    public void put(String identity, String sha256) { values.put(identity, sha256); }
}
""",
    "com/fongmi/android/tv/xray/legacy/LegacyXrayShareLinkNormalizer.java": r"""
package com.fongmi.android.tv.xray.legacy;
public final class LegacyXrayShareLinkNormalizer {
    private LegacyXrayShareLinkNormalizer() {}
    public static String normalize(String value) { return value; }
}
""",
    "com/fongmi/android/tv/xray/legacy/LegacyXrayProbeApi.java": r"""
package com.fongmi.android.tv.xray.legacy;
import java.util.List;
public interface LegacyXrayProbeApi {
    String probeHysteria2Certificate(
            String server, int port, String serverName, int timeoutMs) throws Exception;
    String probeTlsCertificate(
            String server,
            int port,
            String serverName,
            String fingerprint,
            List<String> alpn,
            int timeoutMs) throws Exception;
}
""",
    "com/fongmi/android/tv/xray/legacy/LegacyXrayCertificateStore.java": r"""
package com.fongmi.android.tv.xray.legacy;
import java.util.LinkedHashMap;
import java.util.Map;
public final class LegacyXrayCertificateStore {
    public final Map<String, String> values = new LinkedHashMap<>();
    public String get(String identity) { return values.getOrDefault(identity, ""); }
    public void put(String identity, String sha256) { values.put(identity, sha256); }
}
""",
    "parity/TransportSecurityParityTest.java": r"""
package parity;

import com.fingmi.xray.core.LibXrayBridge;
import com.fingmi.xray.security.XrayCertificatePins;
import com.fingmi.xray.security.XrayShareLinkSecurity;
import com.fongmi.android.tv.xray.legacy.LegacyXrayCertificateStore;
import com.fongmi.android.tv.xray.legacy.LegacyXrayProbeApi;
import com.fongmi.android.tv.xray.legacy.LegacyXrayTransportSecurity;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public final class TransportSecurityParityTest {
    private static final String A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    private static final String B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    private interface ThrowingCall { String run() throws Exception; }

    private static final class LegacyProbe implements LegacyXrayProbeApi {
        String observed;
        final List<String> calls = new ArrayList<>();
        LegacyProbe(String observed) { this.observed = observed; }

        @Override
        public String probeHysteria2Certificate(
                String server, int port, String serverName, int timeoutMs) {
            calls.add("hy2|" + server + "|" + port + "|" + serverName + "|" + timeoutMs);
            return observed;
        }

        @Override
        public String probeTlsCertificate(
                String server,
                int port,
                String serverName,
                String fingerprint,
                List<String> alpn,
                int timeoutMs) {
            calls.add("tls|" + server + "|" + port + "|" + serverName + "|"
                    + fingerprint + "|" + String.join(",", alpn) + "|" + timeoutMs);
            return observed;
        }
    }

    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static void same(Object expected, Object actual, String message) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
        }
    }

    private static String outcome(ThrowingCall call) {
        try {
            return "OK\n" + call.run();
        } catch (Throwable error) {
            return "ERR\n" + error.getClass().getName() + "\n" + String.valueOf(error.getMessage());
        }
    }

    private static void sameState(
            LibXrayBridge currentProbe,
            LegacyProbe legacyProbe,
            XrayCertificatePins currentPins,
            LegacyXrayCertificateStore legacyPins,
            String label) {
        same(legacyProbe.calls, currentProbe.calls, label + " probe calls");
        same(legacyPins.values, currentPins.values, label + " pin state");
    }

    private static void hysteriaFirstTrustRepeatAndChange() throws Exception {
        String link = "hy2://auth@example.com:443?insecure=1&ports=8443-8445,9443"
                + "&sni=Media.EXAMPLE&foo=Bar#frag";

        LibXrayBridge currentProbe = new LibXrayBridge(A);
        LegacyProbe legacyProbe = new LegacyProbe(A);
        XrayCertificatePins currentPins = new XrayCertificatePins();
        LegacyXrayCertificateStore legacyPins = new LegacyXrayCertificateStore();
        XrayShareLinkSecurity current = new XrayShareLinkSecurity(currentProbe, currentPins);
        LegacyXrayTransportSecurity legacy =
                new LegacyXrayTransportSecurity(legacyProbe, legacyPins);

        String currentResult = current.secure(link);
        String legacyResult = legacy.secure(link);
        same(legacyResult, currentResult, "Hy2 first trust output");
        check(currentResult.contains("pcs=" + A), "Hy2 pin was not injected");
        same(
                List.of("hy2|example.com|8443|Media.EXAMPLE|10000"),
                currentProbe.calls,
                "Hy2 probe arguments");
        check(
                currentPins.values.containsKey("hy2\nexample.com\n8443\nmedia.example"),
                "Hy2 identity changed");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "Hy2 first trust");

        currentResult = current.secure(link);
        legacyResult = legacy.secure(link);
        same(legacyResult, currentResult, "Hy2 repeat trust output");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "Hy2 repeat trust");

        currentProbe.observed = B;
        legacyProbe.observed = B;
        String currentError = outcome(() -> current.secure(link));
        String legacyError = outcome(() -> legacy.secure(link));
        same(legacyError, currentError, "Hy2 changed certificate result");
        check(currentError.contains("certificate changed"), "Hy2 changed certificate was accepted");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "Hy2 changed certificate");
    }

    private static void tlsWebsocketFallbackAndCanonicalization() throws Exception {
        String link = "trojan://secret@example.com:443?allowInsecure=true&type=ws"
                + "&host=Ws.Example&fp=chrome&alpn=h2,http%2F1.1&security=TLS#tag";

        LibXrayBridge currentProbe = new LibXrayBridge(A);
        LegacyProbe legacyProbe = new LegacyProbe(A);
        XrayCertificatePins currentPins = new XrayCertificatePins();
        LegacyXrayCertificateStore legacyPins = new LegacyXrayCertificateStore();
        XrayShareLinkSecurity current = new XrayShareLinkSecurity(currentProbe, currentPins);
        LegacyXrayTransportSecurity legacy =
                new LegacyXrayTransportSecurity(legacyProbe, legacyPins);

        String currentResult = current.secure(link);
        String legacyResult = legacy.secure(link);
        same(legacyResult, currentResult, "TLS output");
        same(
                List.of("tls|example.com|443|Ws.Example|chrome|h2,http/1.1|10000"),
                currentProbe.calls,
                "TLS probe arguments");
        check(currentResult.contains("security=tls"), "TLS security value not canonicalized");
        check(currentResult.contains("pcs=" + A), "TLS pin was not injected");
        check(
                currentPins.values.containsKey("tcp-tls\ntrojan\nexample.com\n443\nws.example"),
                "TLS identity changed");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "TLS websocket");
    }

    private static void uppercaseWebsocketKeysRemainCaseSensitive() throws Exception {
        String link = "trojan://secret@example.com:443?insecure=1&TYPE=ws&HOST=Ws.Example&security=tls";
        LibXrayBridge currentProbe = new LibXrayBridge(A);
        LegacyProbe legacyProbe = new LegacyProbe(A);
        XrayCertificatePins currentPins = new XrayCertificatePins();
        LegacyXrayCertificateStore legacyPins = new LegacyXrayCertificateStore();

        String currentResult =
                new XrayShareLinkSecurity(currentProbe, currentPins).secure(link);
        String legacyResult =
                new LegacyXrayTransportSecurity(legacyProbe, legacyPins).secure(link);
        same(legacyResult, currentResult, "uppercase websocket output");
        same(
                List.of("tls|example.com|443|||" + "|10000"),
                currentProbe.calls,
                "uppercase websocket fallback");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "uppercase websocket");
    }

    private static void existingPinBypassesProbeAndStripsInsecure() throws Exception {
        String link = "hy2://auth@example.com:443?insecure=true&PCS=already&sni=Media.Example";
        LibXrayBridge currentProbe = new LibXrayBridge(A);
        LegacyProbe legacyProbe = new LegacyProbe(A);
        XrayCertificatePins currentPins = new XrayCertificatePins();
        LegacyXrayCertificateStore legacyPins = new LegacyXrayCertificateStore();

        String currentResult =
                new XrayShareLinkSecurity(currentProbe, currentPins).secure(link);
        String legacyResult =
                new LegacyXrayTransportSecurity(legacyProbe, legacyPins).secure(link);
        same(legacyResult, currentResult, "existing pin output");
        check(!currentResult.toLowerCase().contains("insecure"), "existing pin kept insecure flag");
        check(currentResult.contains("pcs=already"), "existing pin was not preserved");
        check(currentProbe.calls.isEmpty(), "existing pin unexpectedly probed");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "existing pin");
    }

    private static void migratedUppercasePinIsNotSilentlyNormalized() throws Exception {
        String link = "trojan://secret@example.com:443?insecure=1&security=tls";
        LibXrayBridge currentProbe = new LibXrayBridge(A);
        LegacyProbe legacyProbe = new LegacyProbe(A);
        XrayCertificatePins currentPins = new XrayCertificatePins();
        LegacyXrayCertificateStore legacyPins = new LegacyXrayCertificateStore();
        XrayShareLinkSecurity current = new XrayShareLinkSecurity(currentProbe, currentPins);
        LegacyXrayTransportSecurity legacy =
                new LegacyXrayTransportSecurity(legacyProbe, legacyPins);

        current.secure(link);
        legacy.secure(link);
        for (Map.Entry<String, String> entry : currentPins.values.entrySet()) {
            entry.setValue(entry.getValue().toUpperCase(java.util.Locale.ROOT));
        }
        for (Map.Entry<String, String> entry : legacyPins.values.entrySet()) {
            entry.setValue(entry.getValue().toUpperCase(java.util.Locale.ROOT));
        }

        String currentError = outcome(() -> current.secure(link));
        String legacyError = outcome(() -> legacy.secure(link));
        same(legacyError, currentError, "uppercase migrated pin result");
        check(currentError.contains("certificate changed"), "uppercase migrated pin was normalized");
        sameState(currentProbe, legacyProbe, currentPins, legacyPins, "uppercase migrated pin");
    }

    private static void deferredTrustRequiresExplicitCommit() throws Exception {
        String link = "hy2://auth@example.com:443?insecure=1&sni=Media.EXAMPLE";
        LibXrayBridge probe = new LibXrayBridge(A);
        XrayCertificatePins pins = new XrayCertificatePins();
        XrayShareLinkSecurity current = new XrayShareLinkSecurity(probe, pins);

        XrayShareLinkSecurity.PreparedLink prepared = current.prepare(link);
        check(prepared.value().contains("pcs=" + A), "deferred Hy2 pin was not injected");
        check(pins.values.isEmpty(), "prepare() persisted first trust before operation success");

        prepared.commitTrust();
        check(
                A.equals(pins.values.get("hy2\nexample.com\n443\nmedia.example")),
                "commitTrust() did not persist the prepared first trust");

        XrayCertificatePins immediatePins = new XrayCertificatePins();
        String immediate = new XrayShareLinkSecurity(
                new LibXrayBridge(A), immediatePins).secure(link);
        check(immediate.contains("pcs=" + A), "secure() lost released first-trust output");
        check(!immediatePins.values.isEmpty(), "secure() no longer persists trust immediately");
    }

    private static void secureLinksAndInvalidFingerprintsMatch() throws Exception {
        String secureLink = "trojan://secret@example.com:443?security=tls";
        LibXrayBridge currentProbe = new LibXrayBridge(A);
        LegacyProbe legacyProbe = new LegacyProbe(A);
        XrayCertificatePins currentPins = new XrayCertificatePins();
        LegacyXrayCertificateStore legacyPins = new LegacyXrayCertificateStore();

        String currentResult =
                new XrayShareLinkSecurity(currentProbe, currentPins).secure(secureLink);
        String legacyResult =
                new LegacyXrayTransportSecurity(legacyProbe, legacyPins).secure(secureLink);
        same(legacyResult, currentResult, "already-secure link");
        check(currentProbe.calls.isEmpty(), "already-secure link unexpectedly probed");

        String insecure = "hy2://auth@example.com:443?insecure=1";
        currentProbe.observed = "invalid";
        legacyProbe.observed = "invalid";
        String currentError = outcome(
                () -> new XrayShareLinkSecurity(currentProbe, currentPins).secure(insecure));
        String legacyError = outcome(
                () -> new LegacyXrayTransportSecurity(legacyProbe, legacyPins).secure(insecure));
        same(legacyError, currentError, "invalid fingerprint result");
        check(currentError.contains("invalid fingerprint"), "invalid fingerprint was accepted");
    }

    public static void main(String[] args) throws Exception {
        hysteriaFirstTrustRepeatAndChange();
        tlsWebsocketFallbackAndCanonicalization();
        uppercaseWebsocketKeysRemainCaseSensitive();
        existingPinBypassesProbeAndStripsInsecure();
        migratedUppercasePinIsNotSilentlyNormalized();
        deferredTrustRequiresExplicitCommit();
        secureLinksAndInvalidFingerprintsMatch();
        System.out.println("PASS released Xray transport-security parity");
    }
}
""",
}

with tempfile.TemporaryDirectory(prefix="xray-transport-security-") as directory:
    work = Path(directory)
    generated = []
    for relative, source in STUBS.items():
        path = work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source.strip() + "\n", encoding="utf-8")
        generated.append(path)

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
            *map(str, generated),
        ],
        check=True,
    )
    subprocess.run(
        ["java", "-cp", str(classes), "parity.TransportSecurityParityTest"],
        check=True,
    )
