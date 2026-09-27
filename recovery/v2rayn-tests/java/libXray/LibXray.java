package libXray;
import org.json.*;
import java.util.*;
/** Test-only native I/O boundary. Converter responses must come from pinned published execution. */
public final class LibXray {
    public static final Map<String,String> responses=new HashMap<>();
    public static final JSONArray probes=new JSONArray();
    public static int calls;
    public static String invoke(String raw) {
        JSONObject req=new JSONObject(raw);
        if(req.getLong("apiVersion")!=2) throw new AssertionError("API version");
        String method=req.getString("method");
        JSONObject payload=req.getJSONObject("payload");
        if(method.equals("convertShareLinksToXrayJson")) {
            calls++;
            String response=responses.get(payload.getString("text"));
            if(response==null)throw new AssertionError("No published response for input");
            return response;
        }
        if(method.equals("probeHysteria2Certificate")) {
            probes.put(payload);
            return new JSONObject().put("success",true).put("data",new JSONObject().put("sha256","ab".repeat(32))).toString();
        }
        throw new AssertionError("Unexpected native method "+method);
    }
}
