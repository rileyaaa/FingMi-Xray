#!/usr/bin/env python3
"""Exercise optional TLS fragmentation through the real Java config/bridge chain.

Native conversion and ping I/O are deterministic boundaries; this suite makes no
native compatibility, network performance, TLS-handshake or device assertions.
The separate fixed-core tests cover native schema and wire behavior.
"""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "xray/src/main/java/com/fingmi/xray"

NATIVE_BOUNDARY = r'''
package libXray;
import org.json.JSONArray;
import org.json.JSONObject;

/** Supplies converted input and captures the real LibXrayBridge ping request. */
public final class LibXray {
    public static JSONObject converted;
    public static JSONObject pingRequest;
    public static String invoke(String raw) {
        JSONObject request = new JSONObject(raw);
        if (request.getInt("apiVersion") != 2) throw new AssertionError("API version changed");
        String method = request.getString("method");
        Object data;
        switch (method) {
            case "convertShareLinksToXrayJson" -> data = converted;
            case "pingBatch" -> {
                pingRequest = request;
                data = new JSONObject().put("results", new JSONArray().put(
                        new JSONObject().put("success", true).put("delay", 17)));
            }
            default -> throw new AssertionError("Unexpected native call: " + method);
        }
        return new JSONObject().put("success", true).put("data", data).toString();
    }
}
'''

HARNESS = r'''
import com.fingmi.xray.config.XrayConfigFactory;
import com.fingmi.xray.core.LibXrayBridge;
import com.fingmi.xray.security.XrayCertificatePins;
import com.fingmi.xray.security.XrayShareLinkSecurity;
import libXray.LibXray;
import org.json.JSONArray;
import org.json.JSONObject;

public final class TlsFragmentConfigTest {
    private static final String LINK = "vless://11111111-1111-4111-8111-111111111111@example.invalid:443?security=tls&type=ws";
    private static final LibXrayBridge BRIDGE = new LibXrayBridge();
    private static int cases;

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static XrayConfigFactory factory() {
        return new XrayConfigFactory(BRIDGE,
                new XrayShareLinkSecurity(BRIDGE, new XrayCertificatePins()));
    }

    private static JSONObject input(String network, String security) {
        JSONObject stream = new JSONObject().put("security", security);
        if (network != null) stream.put("network", network);
        // Keep unrelated transport fields present to detect accidental rewrites.
        stream.put("tlsSettings", new JSONObject().put("serverName", "tls.example.invalid")
                .put("fingerprint", "chrome"));
        stream.put("wsSettings", new JSONObject().put("path", "/?ed=2560")
                .put("host", "ws.example.invalid"));
        return new JSONObject().put("outbounds", new JSONArray().put(
                new JSONObject().put("protocol", "vless")
                        .put("settings", new JSONObject().put("address", "198.51.100.1").put("port", 443))
                        .put("streamSettings", stream)));
    }

    private static JSONObject stream(JSONObject config) {
        return config.getJSONArray("outbounds").getJSONObject(0).getJSONObject("streamSettings");
    }

    private static JSONArray masks(JSONObject config) {
        return stream(config).getJSONObject("finalmask").getJSONArray("tcp");
    }

    private static JSONObject generated(JSONObject converted, boolean enabled) throws Exception {
        LibXray.converted = converted;
        return factory().prepare(10808, LINK, false, enabled).config();
    }

    private static void expectedPreset(JSONObject fragment) {
        check(fragment.getString("type").equals("fragment"), "first mask is not fragmentation");
        JSONObject settings = fragment.getJSONObject("settings");
        check(settings.getString("packets").equals("tlshello"), "not ClientHello-only fragmentation");
        check(settings.getString("length").equals("80-120"), "fragment length changed");
        check(settings.getString("delay").equals("5-10"), "fixed-core delay field/preset changed");
        check(!settings.has("interval"), "v2rayN UI interval leaked into fixed-core mask schema");
    }

    private static void defaultsPreserveLegacyConfig() throws Exception {
        JSONObject converted = input("ws", "tls");
        LibXray.converted = converted;
        XrayConfigFactory factory = factory();
        JSONObject legacy = factory.create(10808, LINK, false);
        JSONObject explicitOff = factory.create(10808, LINK, false, false);
        check(legacy.similar(explicitOff), "explicit off changed the legacy create entrypoint");
        check(legacy.similar(factory.prepare(10808, LINK, false).config()),
                "legacy prepare changed default configuration");
        check(legacy.similar(factory.prepare(10808, LINK, false, false).config()),
                "explicit-off prepare changed configuration");
        check(!stream(legacy).has("finalmask"), "default-off added a mask");
        cases++;
    }

    private static void supportedTransportsOnlyAddFragment() throws Exception {
        for (String security : new String[]{"tls", "reality"}) {
            for (String network : new String[]{null, "tcp", "raw", "ws", "websocket", "httpupgrade", "grpc", "xhttp", "splithttp"}) {
                JSONObject converted = input(network, security);
                JSONObject snapshot = new JSONObject(converted.toString());
                JSONObject off = generated(converted, false);
                JSONObject on = generated(converted, true);
                check(masks(on).length() == 1, "wrong mask count for " + network + "/" + security);
                expectedPreset(masks(on).getJSONObject(0));
                JSONObject stripped = new JSONObject(on.toString());
                stream(stripped).remove("finalmask");
                check(stripped.similar(off), "fragmentation changed unrelated config for " + network + "/" + security);
                check(converted.similar(snapshot), "factory modified the native converter input");
                cases++;
            }
        }
    }

    private static void unsupportedTransportsRemainUntouched() throws Exception {
        for (String network : new String[]{"kcp", "mkcp", "quic", "hysteria", "hysteria2", "udp", "http", "h2", "unknown"}) {
            JSONObject converted = input(network, "tls");
            check(generated(converted, false).similar(generated(converted, true)),
                    "unsupported transport changed when fragment enabled: " + network);
            cases++;
        }
        for (String security : new String[]{"", "none"}) {
            JSONObject converted = input("tcp", security);
            check(generated(converted, false).similar(generated(converted, true)),
                    "plaintext stream unexpectedly gained fragmentation");
            cases++;
        }
        JSONObject hy2 = input("hysteria", "tls");
        hy2.getJSONArray("outbounds").getJSONObject(0).put("protocol", "hysteria");
        check(generated(hy2, false).similar(generated(hy2, true)),
                "Hysteria2 UDP stream gained a TCP mask");
        JSONObject missingStream = input("tcp", "tls");
        missingStream.getJSONArray("outbounds").getJSONObject(0).remove("streamSettings");
        check(generated(missingStream, false).similar(generated(missingStream, true)),
                "missing stream settings were invented for fragmentation");
        cases += 2;
    }

    private static void xhttpHttp3IsNotTcp() throws Exception {
        for (String network : new String[]{"xhttp", "splithttp"}) {
            JSONObject converted = input(network, "tls");
            stream(converted).getJSONObject("tlsSettings").put("alpn", new JSONArray().put("h3"));
            check(generated(converted, false).similar(generated(converted, true)),
                    "HTTP/3-only transport gained TCP fragmentation");
            stream(converted).put("security", "reality");
            expectedPreset(masks(generated(converted, true)).getJSONObject(0));
            stream(converted).put("security", "tls");
            stream(converted).getJSONObject("tlsSettings").put("alpn", new JSONArray().put("h2"));
            expectedPreset(masks(generated(converted, true)).getJSONObject(0));
            cases++;
        }
    }

    private static void preexistingMasksArePreserved() throws Exception {
        JSONObject converted = input("ws", "tls");
        JSONObject originalMask = new JSONObject()
                .put("tcp", new JSONArray()
                        .put(new JSONObject().put("type", "header-http").put("settings", new JSONObject().put("host", "mask.example.invalid")))
                        .put(new JSONObject().put("type", "noise").put("settings", new JSONObject().put("packet", "abc"))))
                .put("udp", new JSONArray().put(new JSONObject().put("type", "noise")))
                .put("quic", new JSONObject().put("congestion", "bbr"));
        stream(converted).put("finalmask", originalMask);
        JSONObject convertedSnapshot = new JSONObject(converted.toString());
        JSONObject result = generated(converted, true);
        JSONArray applied = masks(result);
        check(applied.length() == 3, "existing TCP masks were replaced");
        expectedPreset(applied.getJSONObject(0));
        check(applied.getJSONObject(1).similar(originalMask.getJSONArray("tcp").getJSONObject(0))
                        && applied.getJSONObject(2).similar(originalMask.getJSONArray("tcp").getJSONObject(1)),
                "existing TCP masks/order changed");
        check(stream(result).getJSONObject("finalmask").getJSONArray("udp").similar(originalMask.getJSONArray("udp"))
                        && stream(result).getJSONObject("finalmask").getJSONObject("quic").similar(originalMask.getJSONObject("quic")),
                "non-TCP mask configuration changed");
        check(converted.similar(convertedSnapshot), "mask injection mutated converter-owned input");

        // Feed the resulting outbound back through the converter boundary.
        JSONObject repeatedInput = new JSONObject().put("outbounds", new JSONArray().put(
                result.getJSONArray("outbounds").getJSONObject(0)));
        JSONObject repeated = generated(repeatedInput, true);
        check(masks(repeated).similar(applied), "repeated application duplicated fragmentation");

        JSONObject customFragment = new JSONObject().put("type", "fragment")
                .put("settings", new JSONObject().put("packets", "tlshello").put("length", "30-50").put("delay", "1-2"));
        originalMask.getJSONArray("tcp").put(customFragment);
        JSONObject customResult = generated(converted, true);
        check(masks(customResult).similar(originalMask.getJSONArray("tcp")),
                "an explicit existing fragment mask was duplicated or overwritten");
        cases++;
    }

    private static void pingPreservesFragmentAndSourceConfig() throws Exception {
        JSONObject config = generated(input("ws", "tls"), true);
        JSONObject snapshot = new JSONObject(config.toString());
        check(BRIDGE.testLatency(config, XrayConfigFactory.PROXY_TAG) == 17, "ping result handling changed");
        JSONObject payload = LibXray.pingRequest.getJSONObject("payload");
        JSONObject entry = payload.getJSONArray("configs").getJSONObject(0);
        JSONObject testConfig = new JSONObject(entry.getString("xrayJson"));
        check(entry.getString("outboundTag").equals(XrayConfigFactory.PROXY_TAG), "ping lost the selected outbound");
        check(masks(testConfig).similar(masks(config)), "pingBatch lost fragmentation");
        check(testConfig.getJSONArray("outbounds").getJSONObject(0).getString("targetStrategy").equals("AsIs"),
                "ping test target strategy changed");
        check(config.similar(snapshot), "pingBatch mutated the playback configuration");
        check(payload.getInt("timeout") == 10, "fragmentation changed the ping timeout");
        cases++;
    }

    public static void main(String[] args) throws Exception {
        defaultsPreserveLegacyConfig();
        supportedTransportsOnlyAddFragment();
        unsupportedTransportsRemainUntouched();
        xhttpHttp3IsNotTcp();
        preexistingMasksArePreserved();
        pingPreservesFragmentAndSourceConfig();
        System.out.println("PASS " + cases + " TLS fragmentation Java configuration cases; native/network boundaries are doubles");
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, required=True)
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(
        "current_native_chain", ROOT / "tests/test-current-native-share-chain.py")
    chain = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chain)
    url, digest = chain.JARS["json.jar"]
    jar = args.workdir / "json.jar"
    if not jar.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            jar.write_bytes(response.read())
    assert hashlib.sha256(jar.read_bytes()).hexdigest() == digest, "org.json JAR digest mismatch"

    with tempfile.TemporaryDirectory(prefix="xray-tls-fragment-", dir=args.workdir) as directory:
        work = Path(directory)
        native = work / "libXray/LibXray.java"
        native.parent.mkdir()
        native.write_text(NATIVE_BOUNDARY, encoding="utf-8")
        harness = work / "TlsFragmentConfigTest.java"
        harness.write_text(HARNESS, encoding="utf-8")
        classes = work / "classes"
        classes.mkdir()
        sources = [native, harness,
                   ROOT / "tests/xray-current-chain/com/fingmi/xray/security/XrayCertificatePins.java"]
        sources.extend(PRODUCTION / path for path in (
            "config/XrayConfigFactory.java", "config/XrayShareLinkNormalizer.java",
            "core/LibXrayBridge.java", "security/XrayShareLinkSecurity.java"))
        subprocess.run(["java", "com.sun.tools.javac.Main", "--release", "17",
                        "-cp", str(jar.resolve()), "-d", str(classes), *map(str, sources)],
                       check=True, timeout=60)
        subprocess.run(["java", "-cp", os.pathsep.join((str(jar.resolve()), str(classes))),
                        "TlsFragmentConfigTest"], check=True, timeout=60)


if __name__ == "__main__":
    main()
