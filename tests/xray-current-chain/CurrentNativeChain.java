import com.fingmi.xray.config.XrayConfigFactory;
import com.fingmi.xray.config.XrayShareLinkNormalizer;
import com.fingmi.xray.core.LibXrayBridge;
import com.fingmi.xray.security.XrayCertificatePins;
import com.fingmi.xray.security.XrayShareLinkSecurity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.file.Files;
import java.nio.file.Path;

/** Executes the current Java Xray chain with only JNI/probe/pin persistence as test boundaries. */
public final class CurrentNativeChain {

    private static final String V7_JNI_SHA256 =
            "6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e";
    private static final String ARM64_JNI_SHA256 =
            "40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece";

    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static XrayConfigFactory factory() {
        LibXrayBridge bridge = new LibXrayBridge();
        return new XrayConfigFactory(
                bridge,
                new XrayShareLinkSecurity(
                        bridge,
                        new XrayCertificatePins()));
    }

    public static void main(String[] args) throws Exception {
        JSONArray inputs = new JSONArray(Files.readString(Path.of(args[1])));
        JSONArray output = new JSONArray();

        if (args[0].equals("normalize")) {
            for (int i = 0; i < inputs.length(); i++) {
                JSONObject row = inputs.getJSONObject(i);
                String raw = row.getString("raw");
                String normalized = XrayShareLinkNormalizer.normalize(raw);

                LibXrayBridge bridge = new LibXrayBridge();
                XrayShareLinkSecurity security =
                        new XrayShareLinkSecurity(
                                bridge,
                                new XrayCertificatePins());
                String secured = security.secure(normalized);
                String finalLink = XrayShareLinkNormalizer.normalize(secured);

                output.put(
                        new JSONObject()
                                .put("id", row.getString("id"))
                                .put("raw", raw)
                                .put("normalized", normalized)
                                .put("secured", secured)
                                .put("finalLink", finalLink)
                                .put(
                                        "request",
                                        new JSONObject()
                                                .put("apiVersion", 2)
                                                .put("method", "convertShareLinksToXrayJson")
                                                .put(
                                                        "payload",
                                                        new JSONObject()
                                                                .put("text", finalLink))));
            }
        } else {
            JSONObject evidence =
                    new JSONObject(Files.readString(Path.of(args[2])));
            String nativeSha =
                    evidence.getJSONObject("evidence").getString("jni_sha256");
            check(
                    nativeSha.equals(V7_JNI_SHA256)
                            || nativeSha.equals(ARM64_JNI_SHA256),
                    "Unpinned native evidence");

            JSONArray results = evidence.getJSONArray("cases");
            for (int i = 0; i < results.length(); i++) {
                JSONObject c = results.getJSONObject(i);
                libXray.LibXray.responses.put(
                        c.getJSONObject("request")
                                .getJSONObject("payload")
                                .getString("text"),
                        c.getString("raw_response"));
            }

            for (int i = 0; i < inputs.length(); i++) {
                JSONObject row = inputs.getJSONObject(i);
                JSONObject runtime =
                        factory().create(
                                10808,
                                row.getString("raw"),
                                true);

                JSONArray out = runtime.getJSONArray("outbounds");
                check(out.length() == 2, "proxy + private block required");
                JSONObject proxy = out.getJSONObject(0);
                check(
                        proxy.getString("tag").equals(XrayConfigFactory.PROXY_TAG),
                        "proxy tag");
                check(
                        proxy.getString("targetStrategy").equals("ForceIP"),
                        "ForceIP");
                check(!proxy.has("sendThrough"), "remove display metadata");
                check(
                        out.getJSONObject(1).getString("protocol").equals("blackhole"),
                        "private block");

                JSONObject inbound =
                        runtime.getJSONArray("inbounds").getJSONObject(0);
                check(
                        inbound.getString("listen").equals("127.0.0.1")
                                && inbound.getInt("port") == 10808
                                && inbound.getJSONObject("settings").getBoolean("udp"),
                        "local session SOCKS");
                check(
                        runtime.getJSONObject("routing")
                                        .getJSONArray("rules")
                                        .length()
                                == 4,
                        "routing rules");
                check(
                        runtime.getJSONObject("dns")
                                        .getJSONArray("servers")
                                        .length()
                                == 4,
                        "DNS servers");

                output.put(
                        new JSONObject()
                                .put("id", row.getString("id"))
                                .put("runtime", runtime)
                                .put(
                                        "request",
                                        new JSONObject()
                                                .put("apiVersion", 2)
                                                .put("method", "testXray")
                                                .put(
                                                        "payload",
                                                        new JSONObject()
                                                                .put(
                                                                        "xrayJson",
                                                                        runtime.toString()))));
            }

            check(
                    libXray.LibXray.convertCalls == inputs.length(),
                    "one native conversion per runtime");
        }

        Files.writeString(
                Path.of(args[args.length - 1]),
                output.toString(2) + "\n");
        System.err.println(
                "PASS current Java " + args[0] + ": "
                        + output.length()
                        + " chain cases");
    }
}
