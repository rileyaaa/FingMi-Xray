package com.fingmi.xray.core;

import com.fingmi.xray.util.XrayErrorSanitizer;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import libXray.LibXray;

public final class LibXrayBridge {

    public static final long API_VERSION = 2;

    public Object invoke(String method, JSONObject payload) throws Exception {
        JSONObject request = new JSONObject()
                .put("apiVersion", API_VERSION)
                .put("method", method);
        if (payload != null) request.put("payload", payload);

        JSONObject response = new JSONObject(LibXray.invoke(request.toString()));
        if (response.optBoolean("success")) return response.opt("data");

        String error = response.optString("error", "Xray operation failed").trim();
        if (error.isEmpty()) error = "Xray operation failed";
        throw new IllegalStateException(XrayErrorSanitizer.sanitize(error));
    }

    public JSONObject invokeObject(String method, JSONObject payload) throws Exception {
        Object data = invoke(method, payload);
        if (data instanceof JSONObject object) return object;
        if (data instanceof String string && !string.isBlank()) return new JSONObject(string);
        return new JSONObject();
    }

    public int getFreePort() throws Exception {
        JSONArray ports = invokeObject("getFreePorts", new JSONObject().put("count", 1))
                .optJSONArray("ports");
        if (ports == null || ports.length() != 1) {
            throw new JSONException("Xray did not return a free port");
        }
        return ports.getInt(0);
    }

    public JSONObject convertShareLink(String shareLink) throws Exception {
        Object data = invoke(
                "convertShareLinksToXrayJson",
                new JSONObject().put("text", shareLink));
        if (data instanceof JSONObject object) return object;
        if (data instanceof String string) return new JSONObject(string);
        throw new JSONException("Xray conversion returned invalid data");
    }

    public String probeHysteria2Certificate(
            String server,
            int port,
            String serverName,
            int timeoutMs) throws Exception {
        String sha256 = invokeObject(
                "probeHysteria2Certificate",
                new JSONObject()
                        .put("server", server)
                        .put("port", port)
                        .put("serverName", serverName)
                        .put("timeout", timeoutMs))
                .optString("sha256", "");
        if (!sha256.matches("(?i)[0-9a-f]{64}")) {
            throw new JSONException("Hysteria2 certificate probe returned an invalid fingerprint");
        }
        return sha256.toLowerCase(java.util.Locale.ROOT);
    }

    public String probeTlsCertificate(
            String server,
            int port,
            String serverName,
            String fingerprint,
            JSONArray alpn,
            int timeoutMs) throws Exception {
        String sha256 = invokeObject(
                "probeTLSCertificate",
                new JSONObject()
                        .put("server", server)
                        .put("port", port)
                        .put("serverName", serverName)
                        .put("fingerprint", fingerprint)
                        .put("alpn", alpn)
                        .put("timeout", timeoutMs))
                .optString("sha256", "");
        if (!sha256.matches("(?i)[0-9a-f]{64}")) {
            throw new JSONException("TLS certificate probe returned an invalid fingerprint");
        }
        return sha256.toLowerCase(java.util.Locale.ROOT);
    }

    public void validateConfig(JSONObject config) throws Exception {
        invoke("testXray", new JSONObject().put("xrayJson", config.toString()));
    }

    public void run(JSONObject config) throws Exception {
        invoke("runXray", new JSONObject().put("xrayJson", config.toString()));
    }

    public void stop() throws Exception {
        invoke("stopXray", null);
    }

    public boolean isRunning() throws Exception {
        return invokeObject("getXrayState", null).optBoolean("running");
    }

    public long testLatency(JSONObject config, String outboundTag) throws Exception {
        JSONObject testConfig = new JSONObject(config.toString());
        JSONArray outbounds = testConfig.optJSONArray("outbounds");
        if (outbounds == null || outbounds.length() == 0) {
            throw new JSONException("Xray ping config has no outbound");
        }

        JSONObject outbound = null;
        for (int i = 0; i < outbounds.length(); i++) {
            JSONObject candidate = outbounds.optJSONObject(i);
            if (candidate != null && outboundTag.equals(candidate.optString("tag"))) {
                outbound = candidate;
                break;
            }
        }
        if (outbound == null) throw new JSONException("Xray ping proxy outbound is missing");

        outbound.put("targetStrategy", "AsIs");

        JSONObject entry = new JSONObject()
                .put("xrayJson", testConfig.toString())
                .put("outboundTag", outboundTag);

        JSONArray results = invokeObject(
                "pingBatch",
                new JSONObject()
                        .put("configs", new JSONArray().put(entry))
                        .put("timeout", 10)
                        .put("url", "https://www.gstatic.com/generate_204"))
                .optJSONArray("results");

        if (results == null || results.length() != 1) {
            throw new JSONException("Xray connectivity test returned no result");
        }

        JSONObject result = results.getJSONObject(0);
        if (!result.optBoolean("success")) {
            String error = result.optString("error", "Xray connectivity test failed").trim();
            if (error.isEmpty()) error = "Xray connectivity test failed";
            throw new IllegalStateException(XrayErrorSanitizer.sanitize(error));
        }
        return result.optLong("delay", -1L);
    }
}
