package libXray;
import org.json.*;
import java.util.*;
/** Test-only JNI boundary: replays exact responses collected from published ARM JNI. */
public final class LibXray {
    public static final Map<String,String> responses = new HashMap<>();
    public static int calls;
    public static String invoke(String raw) {
        JSONObject request = new JSONObject(raw);
        if (request.getInt("apiVersion") != 2 || !request.getString("method").equals("convertShareLinksToXrayJson"))
            throw new AssertionError("Unexpected API request: " + raw);
        String link = request.getJSONObject("payload").getString("text");
        String result = responses.get(link);
        if (result == null) throw new AssertionError("No actual native response for: " + link);
        calls++;
        return result;
    }
}
