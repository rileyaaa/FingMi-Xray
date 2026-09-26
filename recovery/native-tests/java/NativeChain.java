import com.fongmi.android.tv.xray.legacy.*;
import org.json.*;
import java.nio.file.*;
import java.util.*;

/** Executes the real recovery Java classes; only native I/O, probes and store are test boundaries. */
public final class NativeChain {
    static final String PIN = "ab".repeat(32);
    static final class SyntheticProbe implements LegacyXrayProbeApi {
        public String probeHysteria2Certificate(String s,int p,String n,int t) {return PIN;}
        public String probeTlsCertificate(String s,int p,String n,String fp,List<String> a,int t) {return PIN;}
    }
    static LegacyXrayTransportSecurity security() {
        return new LegacyXrayTransportSecurity(new SyntheticProbe(),new LegacyXrayCertificateStore());
    }
    static void check(boolean value,String message) {if (!value) throw new AssertionError(message);}
    public static void main(String[] args) throws Exception {
        JSONArray inputs = new JSONArray(Files.readString(Path.of(args[1])));
        JSONArray output = new JSONArray();
        if (args[0].equals("normalize")) {
            for (int i=0;i<inputs.length();i++) {
                JSONObject row=inputs.getJSONObject(i);
                String raw=row.getString("raw");
                String normalized=LegacyXrayShareLinkNormalizer.normalize(raw);
                String secured=security().secure(normalized);
                String finalLink=LegacyXrayShareLinkNormalizer.normalize(secured);
                output.put(new JSONObject().put("id",row.getString("id")).put("raw",raw)
                    .put("normalized",normalized).put("secured",secured).put("finalLink",finalLink)
                    .put("request",new JSONObject().put("apiVersion",2).put("method","convertShareLinksToXrayJson")
                    .put("payload",new JSONObject().put("text",finalLink))));
            }
        } else {
            JSONObject evidence=new JSONObject(Files.readString(Path.of(args[2])));
            check(evidence.getJSONObject("evidence").getString("jni_sha256").equals("6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e"),"Unpinned native evidence");
            JSONArray results=evidence.getJSONArray("cases");
            for (int i=0;i<results.length();i++) {
                JSONObject c=results.getJSONObject(i);
                libXray.LibXray.responses.put(c.getJSONObject("request").getJSONObject("payload").getString("text"),c.getString("raw_response"));
            }
            for (int i=0;i<inputs.length();i++) {
                JSONObject row=inputs.getJSONObject(i);
                JSONObject runtime=new LegacyXrayRuntimeConfigFactory(new LegacyLibXrayApi(),security()).create(10808,row.getString("raw"),true);
                JSONArray out=runtime.getJSONArray("outbounds");
                check(out.length()==2,"proxy + private block required");
                JSONObject proxy=out.getJSONObject(0);
                check(proxy.getString("tag").equals("fongmi-xray-proxy"),"proxy tag");
                check(proxy.getString("targetStrategy").equals("ForceIP"),"ForceIP");
                check(!proxy.has("sendThrough"),"remove display metadata");
                check(out.getJSONObject(1).getString("protocol").equals("blackhole"),"private block");
                JSONObject in=runtime.getJSONArray("inbounds").getJSONObject(0);
                check(in.getString("listen").equals("127.0.0.1") && in.getInt("port")==10808 && in.getJSONObject("settings").getBoolean("udp"),"local session SOCKS");
                check(runtime.getJSONObject("routing").getJSONArray("rules").length()==4,"routing rules");
                check(runtime.getJSONObject("dns").getJSONArray("servers").length()==4,"DNS servers");
                output.put(new JSONObject().put("id",row.getString("id")).put("runtime",runtime)
                    .put("request",new JSONObject().put("apiVersion",2).put("method","testXray")
                    .put("payload",new JSONObject().put("xrayJson",runtime.toString()))));
            }
            check(libXray.LibXray.calls==inputs.length(),"one native conversion per runtime");
        }
        Files.writeString(Path.of(args[args.length-1]),output.toString(2)+"\n");
        System.err.println("PASS Java "+args[0]+": "+output.length()+" chain cases");
    }
}
