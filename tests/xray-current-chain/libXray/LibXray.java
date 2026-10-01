package libXray;

import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;

/** Test-only JNI boundary: published conversion replay plus synthetic certificate probes. */
public final class LibXray {

    private static final String PIN =
            "abababababababababababababababababababababababababababababababab";

    public static final Map<String, String> responses = new HashMap<>();
    public static int convertCalls;

    private LibXray() {
    }

    public static String invoke(String raw) {
        JSONObject request = new JSONObject(raw);
        if (request.getInt("apiVersion") != 2) {
            throw new AssertionError("Unexpected API version: " + raw);
        }

        String method = request.getString("method");
        if (method.equals("probeTLSCertificate")
                || method.equals("probeHysteria2Certificate")) {
            return new JSONObject()
                    .put("success", true)
                    .put("data", new JSONObject().put("sha256", PIN))
                    .put("error", "")
                    .toString();
        }

        if (!method.equals("convertShareLinksToXrayJson")) {
            throw new AssertionError("Unexpected API request: " + raw);
        }

        String link =
                request.getJSONObject("payload").getString("text");
        String result = responses.get(link);
        if (result == null) {
            throw new AssertionError(
                    "No actual published native response for: " + link);
        }

        convertCalls++;
        return result;
    }
}
