#!/usr/bin/env python3
"""Execute real side-request APIs with deterministic HTTP and main-thread boundaries.

The response is parsed before an Xray transition, but its UI callback is still
queued. That callback must be invalidated and the dialog cancellation completed.
No network, APK build, or credentials are needed.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STUBS = {
    'android/net/Uri.java': 'package android.net; public class Uri { public static String encode(String s) { return s; } }',
    'android/text/TextUtils.java': 'package android.text; public class TextUtils { public static boolean isEmpty(CharSequence s) { return s == null || s.length() == 0; } }',
    'androidx/annotation/NonNull.java': 'package androidx.annotation; public @interface NonNull {}',
    'androidx/collection/ArrayMap.java': 'package androidx.collection; public class ArrayMap<K,V> extends java.util.HashMap<K,V> {}',
    'com/fongmi/android/tv/App.java': '''package com.fongmi.android.tv;
        public class App {
            public static final java.util.ArrayDeque<Runnable> queue = new java.util.ArrayDeque<>();
            public static void post(Runnable r) { queue.add(r); }
            public static void drain() { while (!queue.isEmpty()) queue.remove().run(); }
        }''',
    'com/fongmi/android/tv/R.java': 'package com.fongmi.android.tv; public class R { public static class string { public static final int error_empty=1; } }',
    'com/fongmi/android/tv/setting/DanmakuSetting.java': '''package com.fongmi.android.tv.setting; public class DanmakuSetting {
        public static boolean isLoad() { return true; } public static boolean isAuto() { return true; }
        public static String getEffectiveApiUrl() { return "https://synthetic.invalid/{name}"; }
    }''',
    'com/fongmi/android/tv/setting/SubtitleSetting.java': 'package com.fongmi.android.tv.setting; public class SubtitleSetting { public static String getEffectiveToken() { return "synthetic"; } }',
    'com/fongmi/android/tv/utils/ResUtil.java': 'package com.fongmi.android.tv.utils; public class ResUtil { public static String getString(int i) { return "empty"; } }',
    'com/github/catvod/utils/Trans.java': 'package com.github.catvod.utils; public class Trans { public static String t2s(String s) { return s; } }',
    'okhttp3/Callback.java': '''package okhttp3; public interface Callback {
        void onFailure(Call c, java.io.IOException e); void onResponse(Call c, Response r) throws java.io.IOException;
    }''',
    'okhttp3/Call.java': '''package okhttp3; public class Call {
        public Callback callback; public boolean canceled;
        public void enqueue(Callback c) { callback=c; } public void cancel() { canceled=true; }
        public void success() throws Exception { callback.onResponse(this,new Response()); }
        public void failure() { callback.onFailure(this,new java.io.IOException("synthetic failure")); }
    }''',
    'okhttp3/Request.java': '''package okhttp3; public class Request { public static class Builder {
        public Builder url(String s) { return this; } public Builder post(Object b) { return this; }
        public Builder tag(Object o) { return this; } public Request build() { return new Request(); }
    } }''',
    'okhttp3/Response.java': '''package okhttp3; public class Response implements AutoCloseable {
        public Body body() { return new Body(); } public boolean isSuccessful() { return true; }
        public int code() { return 200; } public String message() { return "OK"; } public void close() {}
        public static class Body { public String string() { return "synthetic response"; } }
    }''',
    'okhttp3/OkHttpClient.java': '''package okhttp3; public class OkHttpClient {
        public static Call last; public Call newCall(Request r) { return last=new Call(); }
    }''',
    'okhttp3/HttpUrl.java': '''package okhttp3; public class HttpUrl {
        public static HttpUrl parse(String s) { return new HttpUrl(); } public Builder newBuilder() { return new Builder(); }
        public String toString() { return "https://synthetic.invalid"; } public static class Builder {
            public Builder addQueryParameter(String k,String v) { return this; } public HttpUrl build() { return new HttpUrl(); }
        }
    }''',
    'com/github/catvod/net/OkHttp.java': '''package com.github.catvod.net; public class OkHttp {
        public static okhttp3.OkHttpClient client() { return new okhttp3.OkHttpClient(); }
        public static okhttp3.Call newCall(okhttp3.OkHttpClient c,String u,String t) { return c.newCall(new okhttp3.Request()); }
        public static Object toBody(Object o) { return o; }
    }''',
    'com/fongmi/android/tv/bean/Danmaku.java': '''package com.fongmi.android.tv.bean; public class Danmaku {
        public static java.util.List<Danmaku> arrayFrom(String s) { return java.util.List.of(new Danmaku()); }
    }''',
    'com/fongmi/android/tv/bean/SubtitleSearchItem.java': '''package com.fongmi.android.tv.bean; public class SubtitleSearchItem {
        public boolean zip; public String getName() { return "synthetic.srt"; } public String getUrl() { return "https://synthetic.invalid/a.srt"; }
        public int getId() { return 1; } public String getLang() { return "en"; } public boolean isZip() { return zip; }
        public static SubtitleSearchItem from(int id,String n,String u,String l) { return new SubtitleSearchItem(); }
        public static java.util.List<SubtitleSearchItem> fromFiles(java.util.List<java.io.File> f,String l) { return java.util.List.of(new SubtitleSearchItem()); }
    }''',
    'com/fongmi/android/tv/bean/SubtitleSearchPage.java': '''package com.fongmi.android.tv.bean; public class SubtitleSearchPage {
        public static SubtitleSearchPage from(java.util.List<SubtitleSearchItem> s,int n) { return new SubtitleSearchPage(); }
    }''',
    'com/fongmi/android/tv/bean/AssrtResponse.java': '''package com.fongmi.android.tv.bean; public class AssrtResponse {
        public static AssrtResponse from(String s) { return new AssrtResponse(); } public String getError() { return ""; }
        public java.util.List<Subtitle> getSubtitles() { return java.util.List.of(new Subtitle()); }
        public static class Subtitle {
            public int getId() { return 1; } public String getNativeName() { return "name"; } public String getTitle() { return "title"; }
            public String getFileName() { return "file.srt"; } public String getVideoName() { return "video"; }
            public String getLanguage() { return "en"; } public String getUrl() { return "https://synthetic.invalid/a.srt"; }
            public boolean hasFileList() { return false; } public java.util.List<SubtitleFile> getFiles() { return java.util.List.of(); }
        }
        public static class SubtitleFile { public String getName() { return "a.srt"; } public String getUrl() { return "https://synthetic.invalid/a.srt"; } }
    }''',
    'com/fongmi/android/tv/utils/Download.java': '''package com.fongmi.android.tv.utils; public class Download {
        public static Download last; public Callback callback; public boolean canceled;
        public Download client(okhttp3.OkHttpClient c) { return this; } public Download tag(String s) { return this; }
        public void start(Callback c) { callback=c; } public void cancel() { canceled=true; }
        public interface Callback { void error(String msg); void success(java.io.File f); }
    }''',
    'com/fongmi/android/tv/utils/SubtitleArchive.java': '''package com.fongmi.android.tv.utils; public class SubtitleArchive {
        public static Download createDownload(String n,String u) { return Download.last=new Download(); }
        public static boolean isSupported(String n,String u) { return true; }
        public static java.io.File getDir(String u) { return new java.io.File("synthetic"); }
        public static java.util.List<java.io.File> unzip(java.io.File f,java.io.File d) { return java.util.List.of(f); }
    }''',
    'com/fongmi/android/tv/utils/Task.java': '''package com.fongmi.android.tv.utils; public class Task {
        public static final java.util.ArrayDeque<Runnable> queue=new java.util.ArrayDeque<>();
        public static void execute(Runnable r) { queue.add(r); }
        public static void drain() { while (!queue.isEmpty()) queue.remove().run(); }
    }''',
    'SideRequestTest.java': '''
import com.fongmi.android.tv.App;
import com.fongmi.android.tv.api.DanmakuApi;
import com.fongmi.android.tv.api.SubtitleApi;
import com.fongmi.android.tv.bean.SubtitleSearchItem;
import com.fongmi.android.tv.utils.Download;
import com.fongmi.android.tv.utils.Task;
import okhttp3.*;

public class SideRequestTest {
    static int delivered, completed, count;
    static void check(boolean value,String message) { if (!value) throw new AssertionError(message); }
    static void reset() { DanmakuApi.cancel(); SubtitleApi.cancel(); App.drain(); Task.drain(); App.drain(); delivered=completed=0; }
    static int danmaku() { return DanmakuApi.search(new OkHttpClient(),"n","e",v->delivered++,e->delivered++,()->completed++); }
    static int subtitle() { return SubtitleApi.search(new OkHttpClient(),"n",0,v->delivered++,e->delivered++,()->completed++); }
    static void canceled(String label) {
        Task.drain(); App.drain(); check(delivered==0,label+": stale callback delivered");
        check(completed==1,label+": cancellation completion missing"); count++;
    }
    public static void main(String[] args) throws Exception {
        for (boolean failed:new boolean[]{false,true}) {
            reset(); danmaku(); if (failed) OkHttpClient.last.failure(); else OkHttpClient.last.success();
            DanmakuApi.cancelForXrayTransition(); canceled("danmaku "+failed);
            reset(); subtitle(); if (failed) OkHttpClient.last.failure(); else OkHttpClient.last.success();
            SubtitleApi.cancelForXrayTransition(); canceled("subtitle "+failed);
        }
        reset(); SubtitleApi.detail(new OkHttpClient(),1,v->delivered++,e->delivered++,()->completed++);
        OkHttpClient.last.success(); SubtitleApi.cancelForXrayTransition(); canceled("subtitle detail");
        for (boolean zip:new boolean[]{false,true}) {
            reset(); SubtitleSearchItem item=new SubtitleSearchItem(); item.zip=zip;
            SubtitleApi.loadSubtitle(new OkHttpClient(),item,v->delivered++,e->delivered++,()->completed++);
            Download.last.callback.success(new java.io.File("synthetic.srt"));
            SubtitleApi.cancelForXrayTransition(); canceled("subtitle download "+zip);
        }
        reset(); SubtitleApi.loadSubtitle(new OkHttpClient(),new SubtitleSearchItem(),v->delivered++,e->delivered++,()->completed++);
        Download.last.callback.error("failed"); SubtitleApi.cancelForXrayTransition(); canceled("download error");
        reset(); int old=danmaku(); OkHttpClient.last.success(); DanmakuApi.cancel(old); App.drain();
        check(delivered==0,"owner close failed to invalidate queued result"); count++;
        reset(); old=subtitle(); OkHttpClient.last.success(); SubtitleApi.cancel(old); App.drain();
        check(delivered==0,"subtitle owner close failed to invalidate queued result"); count++;
        reset(); danmaku(); OkHttpClient.last.success(); App.drain(); DanmakuApi.cancelForXrayTransition(); App.drain();
        check(delivered==1 && completed==0,"completed danmaku canceled later"); count++;
        reset(); subtitle(); OkHttpClient.last.success(); App.drain(); SubtitleApi.cancelForXrayTransition(); App.drain();
        check(delivered==1 && completed==0,"completed subtitle canceled later"); count++;
        reset(); old=danmaku(); Call first=OkHttpClient.last; danmaku(); Call next=OkHttpClient.last;
        first.success(); DanmakuApi.cancel(old); next.success(); App.drain();
        check(delivered==1 && !next.canceled,"old danmaku owner canceled replacement"); count++;
        reset(); old=subtitle(); first=OkHttpClient.last; subtitle(); next=OkHttpClient.last;
        first.success(); SubtitleApi.cancel(old); next.success(); App.drain();
        check(delivered==1 && !next.canceled,"old subtitle owner canceled replacement"); count++;
        reset(); DanmakuApi.search(new OkHttpClient(),"n","e",v->danmaku(),e->{},null);
        OkHttpClient.last.success(); App.drain(); DanmakuApi.cancelForXrayTransition(); canceled("reentrant danmaku");
        reset(); SubtitleApi.search(new OkHttpClient(),"n",0,v->subtitle(),e->{},null);
        OkHttpClient.last.success(); App.drain(); SubtitleApi.cancelForXrayTransition(); canceled("reentrant subtitle");
        System.out.println("PASS Xray side-request lifecycle: "+count+" scenarios");
    }
}''',
}

with tempfile.TemporaryDirectory(prefix='xray-side-request-') as directory:
    tmp = Path(directory)
    for name, source in STUBS.items():
        path = tmp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    sources = list(tmp.rglob('*.java')) + [
        ROOT / 'app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java',
        ROOT / 'app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java',
        ROOT / 'app/src/main/java/com/fongmi/android/tv/impl/ApiCallback.java',
    ]
    subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '17', '-d', str(tmp), *map(str, sources)], check=True)
    subprocess.run(['java', '-cp', str(tmp), 'SideRequestTest'], check=True)
