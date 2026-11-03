#!/usr/bin/env python3
"""Compile actual 5.8.7 XraySideRequestGate together with upstream side APIs.

The sibling JVM lifecycle suite covers detailed request generation with a simple
network stub. This integration suite substitutes only Android/HTTP/Download
boundaries, and compiles the *generated* XraySideRequestGate to catch mismatched
call signatures, direct-mode fallback, cancellation, and proxy leak regressions.
"""
import ast
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / 'app/src/main/java/com/fingmi/integration/xray/XraySideRequestGate.java'
TEMPLATE = ROOT / 'scripts/upstream/templates/XraySideRequestGate.java.in'
SIBLING = ROOT / 'scripts/upstream/tests/test-upstream-side-request-lifecycle.py'
DANMAKU = ROOT / 'app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java'
SUBTITLE = ROOT / 'app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java'
CALLBACK = ROOT / 'app/src/main/java/com/fongmi/android/tv/impl/ApiCallback.java'

version = (ROOT / 'app/build.gradle').read_text(encoding='utf-8')
if not re.search(r'versionName\s+"v5\.8\.7-xray\.\d+"', version):
    raise SystemExit('Side-request integration test is only for the reviewed 5.8.7 candidate')
if not GATE.is_file() or GATE.read_bytes() != TEMPLATE.read_bytes():
    raise SystemExit('Generated 5.8.7 side-request gate drifted from reviewed template')

# Reuse the exact models/parser/Android fixtures from the independently-tested
# 5.8.7 lifecycle harness; parse literals without executing that test twice.
fixture_node = next((node.value for node in ast.parse(SIBLING.read_text(encoding='utf-8')).body
                     if isinstance(node, ast.Assign)
                     and len(node.targets) == 1
                     and isinstance(node.targets[0], ast.Name)
                     and node.targets[0].id == 'STUBS'), None)
if fixture_node is None:
    raise SystemExit('Reviewed 5.8.7 JVM source fixture is missing')
stubs = ast.literal_eval(fixture_node)
del stubs['com/fingmi/integration/xray/XraySideRequestGate.java']
del stubs['SideRequest587Test.java']
stubs.update({
    'okhttp3/Request.java': '''package okhttp3;
        public final class Request {
            public final String url, tag;
            public final RequestBody body;
            public Request(String url,String tag,RequestBody body) {
                this.url=url; this.tag=tag; this.body=body;
            }
            public static final class Builder {
                private String url,tag;
                private RequestBody body;
                public Builder url(String value){url=value;return this;}
                public Builder tag(String value){tag=value;return this;}
                public Builder post(RequestBody value){body=value;return this;}
                public Request build(){return new Request(url,tag,body);}
            }
        }''',
    'okhttp3/Call.java': '''package okhttp3;
        import java.io.IOException;
        public final class Call {
            public static Call last;
            public interface Factory { Call newCall(Request req); }
            public final Request request;
            public Callback callback;
            public boolean canceled;
            public Call(Request req) { request=req; last=this; }
            public void enqueue(Callback cb) { callback=cb; }
            public void cancel() { canceled=true; }
            public Response execute() throws IOException {return new Response();}
            public void success() throws Exception { callback.onResponse(this,new Response()); }
            public void failure(){callback.onFailure(this,new IOException("fixture failure"));}
        }''',
    'okhttp3/OkHttpClient.java': '''package okhttp3;
        import java.util.ArrayList;
        public final class OkHttpClient implements Call.Factory {
            public final ArrayList<Call> calls = new ArrayList<>();
            public Call newCall(Request request) {
                Call next=new Call(request); calls.add(next); return next;
            }
        }''',
    'com/github/catvod/net/OkHttp.java': '''package com.github.catvod.net;
        import okhttp3.*;
        public final class OkHttp {
            public static final OkHttpClient direct=new OkHttpClient();
            public static int directCancel, proxyCancel;
            public static void cancel(String tag) { directCancel++; cancelTagged(direct,tag); }
            public static void cancel(OkHttpClient client,String tag) {
                proxyCancel++; cancelTagged(client,tag);
            }
            private static void cancelTagged(OkHttpClient client,String tag){
                for(Call call:client.calls) if(tag.equals(call.request.tag))call.cancel();
            }
            public static Call newCall(String url,String tag) {
                return direct.newCall(new Request.Builder().url(url).tag(tag).build());
            }
            public static Call newCall(String url,RequestBody body,String tag) {
                return direct.newCall(new Request.Builder().url(url).post(body).tag(tag).build());
            }
            public static RequestBody toBody(Object o) {return new RequestBody();}
            public static String string(String url) {return "direct metadata";}
        }''',
    'com/fongmi/android/tv/player/PlayerManager.java': '''package com.fongmi.android.tv.player;
        import okhttp3.OkHttpClient;
        public final class PlayerManager {
            public static final OkHttpClient PROXY=new OkHttpClient();
            public boolean active=true, missing=false;
            public boolean hasXraySession(){return active;}
            public OkHttpClient getPlaybackHttpClient(Object normal){
                return missing?null:PROXY;
            }
        }''',
    'com/github/catvod/net/Download.java': '''package com.github.catvod.net;
        import java.io.File;
        import okhttp3.Call;
        public final class Download {
            public static Download last;
            public static int transportCount;
            public Callback callback;
            public boolean canceled;
            public Call.Factory transport;
            public Download tag(String tag){return this;}
            public Download transport(Call.Factory client){
                transport=client;transportCount++;return this;
            }
            public void start(Callback callback){this.callback=callback;}
            public void cancel(){canceled=true;}
            public interface Callback {void success(File file);void error(String text);}
        }''',
    'SideRequestGateIntegrationTest.java': r'''
import com.fongmi.android.tv.App;
import com.fongmi.android.tv.api.DanmakuApi;
import com.fongmi.android.tv.api.SubtitleApi;
import com.fongmi.android.tv.bean.SubtitleSearchItem;
import com.fongmi.android.tv.player.PlayerManager;
import com.fingmi.integration.xray.XraySideRequestGate;
import com.github.catvod.net.Download;
import com.github.catvod.net.OkHttp;
import okhttp3.Call;
import okhttp3.RequestBody;

public final class SideRequestGateIntegrationTest {
    static int delivered, failed, cases;
    static void check(boolean state,String message){if(!state)throw new AssertionError(message);}
    static void next(){delivered=0;failed=0;}
    static Call danmaku(){
        DanmakuApi.search("name","ep",items->delivered++,error->failed++);
        return Call.last;
    }
    static Call subtitle(){
        SubtitleApi.search("keyword",0,items->delivered++,error->failed++);
        return Call.last;
    }
    static void stale(boolean subtitle) throws Exception {
        next(); Call call=subtitle?subtitle():danmaku();
        check(PlayerManager.PROXY.calls.contains(call),"request bypasses Xray client");
        call.success();
        if(subtitle)SubtitleApi.cancel();else DanmakuApi.cancel();
        App.drain();
        check(delivered==0&&failed==0&&call.canceled,"cancellation failed to retire queued response");
        cases++;
    }
    static void replaced(boolean subtitle) throws Exception {
        next();Call old=subtitle?subtitle():danmaku();
        Call current=subtitle?subtitle():danmaku();
        old.success();current.success();App.drain();
        check(delivered==1&&failed==0&&old.canceled&&!current.canceled,
              "new request incorrectly inherits old generation");cases++;
    }
    static void download() {
        next(); SubtitleApi.loadSubtitle(new SubtitleSearchItem(),items->delivered++,error->failed++);
        Download task=Download.last;
        check(task.transport==PlayerManager.PROXY,"subtitle range/multipart transport lost Xray proxy");
        XraySideRequestGate.cancelRemoteDownloads();
        check(task.canceled,"remote download not canceled on transition");
        SubtitleApi.cancel();
        task.callback.success(new java.io.File("late.srt"));
        App.drain();check(delivered==0&&failed==0,"late subtitle download callback leaked");cases++;
    }
    static void direct(PlayerManager owner){
        owner.active=false;next();
        int normal=OkHttp.direct.calls.size();
        Call d=danmaku();
        check(OkHttp.direct.calls.size()==normal+1&&OkHttp.direct.calls.contains(d),
              "ordinary direct mode lost original HTTP routing");
        DanmakuApi.cancel();check(d.canceled,"direct tagged request not canceled");cases++;
        check("direct metadata".equals(XraySideRequestGate.string("https://fixture.invalid","epg")),
              "direct metadata unexpectedly proxied");cases++;
        owner.active=true;
    }
    static void missingProxy(PlayerManager owner){
        owner.missing=true;int direct=OkHttp.direct.calls.size();
        try {danmaku();throw new AssertionError("missing live Xray client fell through to direct");}
        catch(IllegalStateException expected){}
        check(OkHttp.direct.calls.size()==direct,"missing Xray client issued direct request");
        owner.missing=false;cases++;
    }
    public static void main(String[] ignored) throws Exception {
        PlayerManager manager=new PlayerManager();
        XraySideRequestGate.bind(manager);
        stale(false);stale(true);
        replaced(false);replaced(true);
        next();Call detail;
        SubtitleApi.detail(1,items->delivered++,error->failed++);
        detail=Call.last;
        check(PlayerManager.PROXY.calls.contains(detail),"subtitle detail bypassed Xray gate");
        detail.failure();SubtitleApi.cancel();App.drain();
        check(failed==0&&detail.canceled,"stale subtitle detail error delivered");cases++;
        download();
        check("fixture response".equals(XraySideRequestGate.string("HTTPS://fixture.invalid","epg")),
              "uppercase HTTPS metadata did not use proxy");cases++;
        check("".equals(XraySideRequestGate.string("ftp://fixture.invalid","epg")),
              "non-HTTP metadata must be blocked");cases++;
        Call post=XraySideRequestGate.newCall("https://fixture.invalid/post",new RequestBody(),"post");
        check(post.request.body!=null&&"post".equals(post.request.tag),"POST body/tag lost");cases++;
        direct(manager);missingProxy(manager);
        XraySideRequestGate.unbind(manager);int direct=OkHttp.direct.calls.size();
        XraySideRequestGate.newCall("https://fixture.invalid/unbound","subtitle");
        check(OkHttp.direct.calls.size()==direct+1,"unbound side API did not restore upstream");cases++;
        check(OkHttp.directCancel>0 && OkHttp.proxyCancel>0 && Download.transportCount>0,
              "gate never canceled both transports or attached download");
        System.out.println("PASS generated real 5.8.7 side gate + actual Danmaku/Subtitle/ApiCallback: "
              +cases+" integration cases");
    }
}
''',
})

with tempfile.TemporaryDirectory(prefix='fongmi-587-side-integration-') as directory:
    target=Path(directory)
    sources=[]
    for path, source in stubs.items():
        file=target/path
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(source,encoding='utf-8')
        sources.append(str(file))
    sources.extend(map(str,(GATE,DANMAKU,SUBTITLE,CALLBACK)))
    subprocess.run(['javac','--release','17','-encoding','UTF-8','-d',str(target),*sources],check=True)
    subprocess.run(['java','-cp',str(target),'SideRequestGateIntegrationTest'],check=True)
