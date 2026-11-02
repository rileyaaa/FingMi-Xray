#!/usr/bin/env python3
"""JVM contract test for the 5.8.7 Xray side request network identity gate."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/"scripts/upstream/templates/XraySideRequestGate.java.in"

sources={
"okhttp3/Call.java":"""package okhttp3;
public interface Call {
  Request request();
  void cancel();
}""",
"okhttp3/RequestBody.java":"package okhttp3; public class RequestBody {}",
"okhttp3/Response.java":"""package okhttp3;
public class Response implements AutoCloseable {
  public ResponseBody body(){return new ResponseBody();}
  public void close(){}
  public static class ResponseBody {
    public String string(){return "xray-metadata";}
  }
}""",
"okhttp3/Request.java":"""package okhttp3;
public class Request {
 private final String url,tag;
 private final RequestBody body;
 public Request(String u,String t,RequestBody b){url=u;tag=t;body=b;}
 public String url(){return url;}
 public String tag(){return tag;}
 public RequestBody body(){return body;}
 public static class Builder {
  String url,tag;RequestBody body;
  public Builder url(String u){url=u;return this;}
  public Builder tag(String t){tag=t;return this;}
  public Builder post(RequestBody b){body=b;return this;}
  public Request build(){return new Request(url,tag,body);}
 }
}""",
"okhttp3/OkHttpClient.java":"""package okhttp3;
import java.util.*;
public class OkHttpClient {
  public final List<FakeCall> calls=new ArrayList<>();
  public Call newCall(Request r){FakeCall c=new FakeCall(r);calls.add(c);return c;}
  public static class FakeCall implements Call {
    public boolean canceled;public final Request req;
    FakeCall(Request r){req=r;}
    public Request request(){return req;}
    public void cancel(){canceled=true;}
    public okhttp3.Response execute(){return new okhttp3.Response();}
  }
}""",
"com/fongmi/android/tv/player/PlayerManager.java":"""package com.fongmi.android.tv.player;
public class PlayerManager {
 public boolean active,missing;
 public final okhttp3.OkHttpClient proxy=new okhttp3.OkHttpClient();
 public boolean hasXraySession(){return active;}
 public okhttp3.OkHttpClient getPlaybackHttpClient(okhttp3.OkHttpClient fallback){
   return active && !missing ? proxy : fallback;
 }
}""",
"com/github/catvod/net/Download.java":"""package com.github.catvod.net;
public class Download {
 public okhttp3.OkHttpClient client;
 public Download transport(okhttp3.Call.Factory factory){throw new AssertionError("unexpected factory");}
 public Download transport(okhttp3.OkHttpClient p){client=p;return this;}
}""",
"com/github/catvod/net/OkHttp.java":"""package com.github.catvod.net;
import okhttp3.*;
public class OkHttp {
 public static final OkHttpClient direct=new OkHttpClient();
 public static Call newCall(String url,String tag){
   return direct.newCall(new Request.Builder().url(url).tag(tag).build());
 }
 public static Call newCall(String url,RequestBody body,String tag){
   return direct.newCall(new Request.Builder().url(url).post(body).tag(tag).build());
 }
 public static String string(String url){return "direct-metadata";}
 public static void cancel(OkHttpClient client,String tag){
   for(OkHttpClient.FakeCall call:client.calls)
     if(tag.equals(call.request().tag()))call.cancel();
 }
}""",
"SideGateHarness.java":"""import com.fingmi.integration.xray.XraySideRequestGate;
import com.fongmi.android.tv.player.PlayerManager;
import com.github.catvod.net.Download;
import com.github.catvod.net.OkHttp;
import okhttp3.*;
public class SideGateHarness {
 static void check(boolean x,String reason){if(!x)throw new AssertionError(reason);}
 public static void main(String[]args){
   PlayerManager player=new PlayerManager();
   XraySideRequestGate.bind(player);
   Call normal=XraySideRequestGate.newCall("https://example.org/direct","danmaku");
   check(OkHttp.direct.calls.size()==1,"direct mode normal behavior");
   player.active=true;
   Call xray=XraySideRequestGate.newCall("https://example.org/proxy","danmaku");
   check(player.proxy.calls.size()==1,"Xray request uses session client");
   check("danmaku".equals(xray.request().tag()),"preserve cancel tag");
   RequestBody body=new RequestBody();
   Call posted=XraySideRequestGate.newCall("https://example.org/post",body,"subtitle");
   check(player.proxy.calls.size()==2 && posted.request().body()==body,"Xray POST request");
   Download dl=XraySideRequestGate.usePlaybackTransport(new Download());
   check(dl.client==player.proxy,"multipart downloads use proxy");
   XraySideRequestGate.cancel("danmaku");
   check(((OkHttpClient.FakeCall)xray).canceled,"cancel active proxy request");
   check(!((OkHttpClient.FakeCall)posted).canceled,"do not cancel other request");
   check("xray-metadata".equals(XraySideRequestGate.string("https://example.org/epg","epg")),
         "EPG metadata uses the bound proxy client");
   check(player.proxy.calls.size()==3,"EPG request did not use Xray client");
   check("xray-metadata".equals(XraySideRequestGate.string("HTTPS://example.org/epg","epg")),
         "case-insensitive HTTPS metadata must still be proxied");
   check(player.proxy.calls.size()==4,"uppercase HTTPS bypassed Xray");
   check("".equals(XraySideRequestGate.string("httpinvalid","epg")),
         "invalid non-HTTP URL must not issue a request");
   check(player.proxy.calls.size()==4,"invalid URL attempted a network request");
   XraySideRequestGate.cancelRemoteDownloads();
   check(dl.canceled,"in-flight Xray downloads canceled on transition");
   player.active=false;
   XraySideRequestGate.newCall("https://example.org/direct2","subtitle");
   check("direct-metadata".equals(XraySideRequestGate.string("https://example.org/epg","epg")),
         "direct metadata retains upstream behavior");
   check(OkHttp.direct.calls.size()==2,"direct restored");
   player.active=true;player.missing=true;
   try{XraySideRequestGate.newCall("https://example.org/leak","subtitle");
     throw new AssertionError("live Xray missing client must fail closed");}
   catch(IllegalStateException expected){}
   check(OkHttp.direct.calls.size()==2,"must not leak to direct");
   XraySideRequestGate.unbind(player);
   XraySideRequestGate.newCall("https://example.org/unbound","subtitle");
   check(OkHttp.direct.calls.size()==3,"unbound manager uses ordinary upstream");
   System.out.println("PASS side request gate: direct/proxy/POST/download/tag cancel/missing client");
 }
}"""
}
# okhttp3 Call.Factory is a separate interface member in actual OkHttp;
# model exactly the parent Call.Factory used by Download.transport().
sources["okhttp3/Call.java"]='''package okhttp3;
public interface Call {
  Request request();
  void cancel();
  okhttp3.Response execute() throws java.io.IOException;
  interface Factory { Call newCall(Request request); }
}'''
sources["okhttp3/OkHttpClient.java"]=sources["okhttp3/OkHttpClient.java"].replace("public class OkHttpClient {","public class OkHttpClient implements Call.Factory {")
sources["com/github/catvod/net/Download.java"]='''package com.github.catvod.net;
public class Download {
 public okhttp3.Call.Factory client;
 public boolean canceled;
 public Download transport(okhttp3.Call.Factory factory){client=factory;return this;}
 public Download cancel(){canceled=true;return this;}
}'''

with tempfile.TemporaryDirectory(prefix="xray-side-request-") as tmp:
    root=Path(tmp)
    parts=[]
    for name,code in sources.items():
        file=root/name
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(code,encoding="utf-8")
        parts.append(str(file))
    gate=root/"com/fingmi/integration/xray/XraySideRequestGate.java"
    gate.parent.mkdir(parents=True,exist_ok=True)
    gate.write_text(JAVA.read_text(encoding="utf-8"),encoding="utf-8")
    subprocess.run(["javac","--release","17","-d",str(root),str(gate),*parts],check=True)
    subprocess.run(["java","-cp",str(root),"SideGateHarness"],check=True)
