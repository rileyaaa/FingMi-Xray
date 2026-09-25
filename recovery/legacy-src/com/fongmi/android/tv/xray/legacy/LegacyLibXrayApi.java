package com.fongmi.android.tv.xray.legacy;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.List;
import java.util.Locale;

import libXray.LibXray;

/**
 * Exact public libXray Invoke protocol used by the shipped APK.
 */
public final class LegacyLibXrayApi implements LegacyXrayProbeApi {

    public static final long API_VERSION = 2L;

    public Object invoke(String method, JSONObject payload) throws Exception {
        JSONObject request = new JSONObject()
                .put("apiVersion", API_VERSION)
                .put("method", method);
        if (payload != null) request.put("payload", payload);

        JSONObject response = new JSONObject(LibXray.invoke(request.toString()));
        if (response.optBoolean("success")) {
            return response.opt("data");
        }

        String error = response.optString("error");
        // DEX-verified in s11.q: blankness is tested code point by code point
        // with Character.isWhitespace(), not with String.trim().
        if (isBlank(error)) {
            error = "Xray operation failed";
        }
        throw new IllegalStateException(error);
    }

    public JSONObject requireObject(Object value) throws JSONException {
        if (value instanceof JSONObject) return (JSONObject) value;
        throw new JSONException("Xray returned an invalid response");
    }

    public int getFreePort() throws Exception {
        JSONArray ports = requireObject(
                invoke("getFreePorts", new JSONObject().put("count", 1)))
                .optJSONArray("ports");
        if (ports == null || ports.length() != 1) {
            throw new JSONException("Xray did not return a free port");
        }
        return ports.getInt(0);
    }

    public JSONObject convertShareLink(String link) throws Exception {
        Object converted = invoke(
                "convertShareLinksToXrayJson",
                new JSONObject().put("text", link));
        if (!(converted instanceof JSONObject)) {
            throw new JSONException("Xray conversion returned an invalid config");
        }
        return (JSONObject) converted;
    }

    public void validate(JSONObject config) throws Exception {
        invoke(
                "testXray",
                new JSONObject().put("xrayJson", config.toString()));
    }

    public void run(JSONObject config) throws Exception {
        invoke(
                "runXray",
                new JSONObject().put("xrayJson", config.toString()));
    }

    public void stop() throws Exception {
        invoke("stopXray", null);
    }

    public boolean isRunning() throws Exception {
        return requireObject(invoke("getXrayState", null))
                .optBoolean("running");
    }

    public long testLatency(JSONObject config, String outboundTag) throws Exception {
        JSONObject testConfig = new JSONObject(config.toString());
        JSONArray outbounds = testConfig.optJSONArray("outbounds");
        if (outbounds == null || outbounds.length() == 0) {
            throw new JSONException("Xray ping config has no outbound");
        }

        JSONObject outbound = null;
        for (int index = 0; index < outbounds.length(); index++) {
            JSONObject candidate = outbounds.optJSONObject(index);
            if (candidate != null
                    && outboundTag.equals(candidate.optString("tag"))) {
                outbound = candidate;
                break;
            }
        }
        if (outbound == null) {
            throw new JSONException("Xray ping proxy outbound is missing");
        }

        outbound.put("targetStrategy", "AsIs");

        JSONObject pingConfig = new JSONObject()
                .put("xrayJson", testConfig.toString())
                .put("outboundTag", outboundTag);

        JSONArray results = requireObject(
                invoke(
                        "pingBatch",
                        new JSONObject()
                                .put("configs", new JSONArray().put(pingConfig))
                                .put("timeout", 10)
                                .put(
                                        "url",
                                        "https://www.gstatic.com/generate_204")))
                .optJSONArray("results");

        if (results == null || results.length() != 1) {
            throw new JSONException(
                    "Xray connectivity test returned no result");
        }

        JSONObject result = results.getJSONObject(0);
        if (!result.optBoolean("success")) {
            String error = result.optString("error");
            // DEX-verified in et1.c: preserve any non-whitespace error text;
            // only an all-Character.isWhitespace() value falls back.
            if (isBlank(error)) {
                error = "Xray connectivity test failed";
            }
            throw new IllegalStateException(error);
        }
        return result.optLong("delay", -1L);
    }

    private static boolean isBlank(String value) {
        if (value == null) return true;
        for (int offset = 0; offset < value.length();) {
            int codePoint = value.codePointAt(offset);
            if (!Character.isWhitespace(codePoint)) return false;
            offset += Character.charCount(codePoint);
        }
        return true;
    }

    @Override
    public String probeHysteria2Certificate(
            String server,
            int port,
            String serverName,
            int timeoutMs) throws Exception {
        String sha256 = requireObject(
                invoke(
                        "probeHysteria2Certificate",
                        new JSONObject()
                                .put("server", server)
                                .put("port", port)
                                .put("serverName", serverName)
                                .put("timeout", timeoutMs)))
                .optString("sha256");
        if (!sha256.matches("(?i)[0-9a-f]{64}")) {
            throw new JSONException(
                    "Hysteria2 certificate probe returned an invalid fingerprint");
        }
        return sha256.toLowerCase(Locale.ROOT);
    }

    @Override
    public String probeTlsCertificate(
            String server,
            int port,
            String serverName,
            String fingerprint,
            List<String> alpn,
            int timeoutMs) throws Exception {
        String sha256 = requireObject(
                invoke(
                        "probeTLSCertificate",
                        new JSONObject()
                                .put("server", server)
                                .put("port", port)
                                .put("serverName", serverName)
                                .put("fingerprint", fingerprint)
                                .put("alpn", new JSONArray(alpn))
                                .put("timeout", timeoutMs)))
                .optString("sha256");
        if (!sha256.matches("(?i)[0-9a-f]{64}")) {
            throw new JSONException(
                    "TLS certificate probe returned an invalid fingerprint");
        }
        return sha256.toLowerCase(Locale.ROOT);
    }
}
