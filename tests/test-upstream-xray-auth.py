#!/usr/bin/env python3
"""Compile the 5.8.7-only Xray HTTP/Auth adapter against JVM boundary stubs."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
BRIDGE=ROOT/"scripts/upstream/templates/XrayPlaybackDataSourceFactory.java.in"
GUARD=ROOT/"app/src/main/java/com/fingmi/integration/xray/XrayGuardedPlaybackDataSource.java"
S={
"android/net/Uri.java":'package android.net; public class Uri {String s; public Uri(String s){this.s=s;} public String getScheme(){return s;}}',
"androidx/media3/datasource/TransferListener.java":'package androidx.media3.datasource; public interface TransferListener {}',
"androidx/media3/datasource/DataSpec.java":'package androidx.media3.datasource; public class DataSpec { public final android.net.Uri uri; public DataSpec(String s){uri=new android.net.Uri(s);}}',
"androidx/media3/datasource/DataSource.java":"""package androidx.media3.datasource;
import java.util.*; import java.io.*;
public interface DataSource {
 interface Factory {DataSource createDataSource();}
 void addTransferListener(TransferListener l);
 long open(DataSpec spec) throws IOException;
 int read(byte[] b,int i,int n) throws IOException;
 android.net.Uri getUri();
 Map<String,List<String>> getResponseHeaders();
 void close() throws IOException;
}""",
"androidx/media3/datasource/HttpDataSource.java":"""package androidx.media3.datasource;
import java.util.Map;
public interface HttpDataSource extends DataSource {
 interface Factory extends DataSource.Factory {
  Factory setDefaultRequestProperties(Map<String,String> headers);
 }
}""",
"androidx/media3/datasource/DefaultDataSource.java":"""package androidx.media3.datasource;
public class DefaultDataSource {
 public static class Factory implements DataSource.Factory {
  HttpDataSource.Factory http;
  public Factory(Object app,HttpDataSource.Factory http){this.http=http;}
  public DataSource createDataSource(){return http.createDataSource();}
 }
}""",
"androidx/media3/datasource/okhttp/OkHttpDataSource.java":"""package androidx.media3.datasource.okhttp;
import androidx.media3.datasource.*; import java.util.*; import java.io.*;
public class OkHttpDataSource {
 public static class Factory implements HttpDataSource.Factory {
  okhttp3.Call.Factory calls; Map<String,String> headers=Map.of();
  public Factory(okhttp3.Call.Factory calls){this.calls=calls;}
  public HttpDataSource.Factory setDefaultRequestProperties(Map<String,String> h){headers=h;return this;}
  public DataSource createDataSource(){return new Fake(calls,headers);}
 }
 static class Fake implements HttpDataSource {
  okhttp3.Call.Factory calls; Map<String,String> headers; android.net.Uri uri;
  Fake(okhttp3.Call.Factory c,Map<String,String> h){calls=c;headers=h;}
  public void addTransferListener(TransferListener l){}
  public long open(DataSpec spec){uri=spec.uri;
   okhttp3.Request.Builder req=new okhttp3.Request.Builder().url("https://origin.invalid/live");
   headers.forEach(req::header); calls.newCall(req.build());return 42;}
  public int read(byte[] b,int o,int l){return l;}
  public android.net.Uri getUri(){return uri;}
  public Map<String,List<String>> getResponseHeaders(){return Map.of();}
  public void close() throws IOException{}
 }
}""",
"com/fongmi/android/tv/App.java":'package com.fongmi.android.tv; public class App {public static Object get(){return new Object();}}',
"com/google/common/net/HttpHeaders.java":'package com.google.common.net; public class HttpHeaders {public static final String AUTHORIZATION="Authorization";}',
"okhttp3/Call.java":'package okhttp3; public interface Call {interface Factory {Call newCall(Request req);}}',
"okhttp3/OkHttpClient.java":"""package okhttp3;
public class OkHttpClient implements Call.Factory {
 public int calls; public Request last;
 public Call newCall(Request r){calls++;last=r;return new Call(){};}
}""",
"okhttp3/Request.java":"""package okhttp3;
import java.util.*;
public class Request {
 String url; Map<String,String> headers; Map<Class<?>,Object> tags;
 Request(String u,Map<String,String> h,Map<Class<?>,Object> t){url=u;headers=h;tags=t;}
 public String url(){return url;}
 public String header(String k){return headers.get(k);}
 public <T>T tag(Class<T> c){return c.cast(tags.get(c));}
 public Builder newBuilder(){Builder b=new Builder().url(url);headers.forEach(b::header);tags.forEach(b::anyTag);return b;}
 public static class Builder {
  String url; Map<String,String> h=new HashMap<>(); Map<Class<?>,Object> tags=new HashMap<>();
  public Builder url(String s){url=s;return this;}
  public Builder header(String k,String v){h.put(k,v);return this;}
  public <T>Builder tag(Class<T> k,T v){tags.put(k,v);return this;}
  public void anyTag(Class<?> k,Object v){tags.put(k,v);}
  public Request build(){return new Request(url,Map.copyOf(h),Map.copyOf(tags));}
 }
}""",
"com/fingmi/xray/network/XrayHttpClient.java":"""package com.fingmi.xray.network;
public class XrayHttpClient {
 public final okhttp3.OkHttpClient http=new okhttp3.OkHttpClient();
 public okhttp3.OkHttpClient client(){return http;}
}""",
"com/github/catvod/utils/Auth.java":"""package com.github.catvod.utils;
import java.util.*;
public class Auth {
 public static class Context {
  public int urls,headers;
  public String getUrl(String url,Map<String,String> original){urls++;return url+"?auth=abc";}
  public Map<String,String> getHeaders(String url,Map<String,String> original){headers++;return Map.of("Authorization","Bearer test");}
 }
}""",
"XrayAuthHarness.java":"""import com.fingmi.integration.xray.XrayPlaybackDataSourceFactory;
import com.fingmi.xray.network.XrayHttpClient;
import com.github.catvod.utils.Auth;
import androidx.media3.datasource.*;
import java.util.*;
public class XrayAuthHarness {
 static void ok(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[] args)throws Exception{
  XrayHttpClient p=new XrayHttpClient();
  DataSource http=XrayPlaybackDataSourceFactory.create(Map.of("User-Agent","UA"),null,p).createDataSource();
  ok(http.open(new DataSpec("https"))==42,"media open");http.close();
  ok(p.http.calls==1,"must use Xray client");
  ok("UA".equals(p.http.last.header("User-Agent")),"user agent");
  DataSource bad=XrayPlaybackDataSourceFactory.create(null,null,p).createDataSource();
  try{bad.open(new DataSpec("ftp"));throw new AssertionError("FTP direct escape");}
  catch(java.io.IOException expected){ok(expected.getMessage().contains("Xray"),"error");}
  bad.close();ok(p.http.calls==1,"blocked request must never reach network");
  Auth.Context auth=new Auth.Context();
  DataSource secured=XrayPlaybackDataSourceFactory.create(Map.of(),auth,p).createDataSource();
  secured.open(new DataSpec("http"));secured.close();
  ok(p.http.calls==2,"Auth cannot switch to direct network");
  ok(p.http.last.url().endsWith("?auth=abc"),"Auth URL");
  ok("Bearer test".equals(p.http.last.header("Authorization")),"Auth headers");
  ok(p.http.last.tag(Auth.Context.class)==auth,"Auth origin tag");
  ok(auth.urls==1 && auth.headers==1,"Auth called exactly once");
  System.out.println("PASS Xray HTTP factory: proxy, headers, Auth.Context, unsafe scheme");
 }
}""",
}
with tempfile.TemporaryDirectory(prefix="xray-auth-587-") as temp:
    work=Path(temp)
    paths=[]
    for name,code in S.items():
        p=work/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(code,encoding="utf-8")
        paths.append(str(p))
    src=work/"com/fingmi/integration/xray/XrayPlaybackDataSourceFactory.java"
    src.parent.mkdir(parents=True,exist_ok=True)
    src.write_text(BRIDGE.read_text(encoding="utf-8"),encoding="utf-8")
    subprocess.run(["javac","--release","17","-encoding","UTF-8","-d",str(work),
                    str(src),str(GUARD),*paths],check=True)
    subprocess.run(["java","-cp",str(work),"XrayAuthHarness"],check=True)
