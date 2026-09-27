import com.fingmi.xray.config.*;
import com.fingmi.xray.core.*;
import com.fingmi.xray.security.*;
import org.json.*;
import java.nio.file.*;
import java.util.*;

/** Executes current :xray Java classes; only native I/O, probes and store are test boundaries. */
public final class V2rayNChain {
    static final String PIN = "ab".repeat(32);
    static XrayShareLinkSecurity security() {
        return new XrayShareLinkSecurity(new LibXrayBridge(),new XrayCertificatePins());
    }
    static void check(boolean value,String message) {if (!value) throw new AssertionError(message);}
    public static void main(String[] args) throws Exception {
        JSONArray inputs = new JSONArray(Files.readString(Path.of(args[1])));
        JSONArray output = new JSONArray();
        if (args[0].equals("normalize")) {
            for (int i=0;i<inputs.length();i++) {
                JSONObject row=inputs.getJSONObject(i);
                while(libXray.LibXray.probes.length()>0) libXray.LibXray.probes.remove(0);
                String raw=row.getString("raw");
                String normalized=XrayShareLinkNormalizer.normalize(raw);
                String secured=security().secure(normalized);
                String finalLink=XrayShareLinkNormalizer.normalize(secured);
                output.put(new JSONObject().put("id",row.getString("id")).put("raw",raw)
                    .put("normalized",normalized).put("secured",secured).put("finalLink",finalLink)
                    .put("probes",new JSONArray(libXray.LibXray.probes.toString()))
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
                JSONObject runtime=new XrayConfigFactory(new LibXrayBridge(),security()).create(10808,row.getString("raw"),true);
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

