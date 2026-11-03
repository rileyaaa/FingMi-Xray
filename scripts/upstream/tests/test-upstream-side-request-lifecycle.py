#!/usr/bin/env python3
"""Run the actual 5.8.7 DanmakuApi, SubtitleApi and ApiCallback with JVM fakes.

This intentionally does not compile the obsolete 5.6.3 request signatures.
Only Android, data models, HTTP, download and executor boundaries are stubs.
No network, Gradle, SDK or user secrets are needed.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
DANMAKU = ROOT / 'app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java'
SUBTITLE = ROOT / 'app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java'
CALLBACK = ROOT / 'app/src/main/java/com/fongmi/android/tv/impl/ApiCallback.java'

# The caller only uses this test for 5.8.7. Refuse an unreviewed version
# rather than silently downgrading the request lifecycle contract.
version = (ROOT / 'app/build.gradle').read_text(encoding='utf-8')
if not re.search(r'versionName\s+"v5\.8\.7-xray\.\d+"', version):
    raise SystemExit('5.8.7 side-request JVM test selected for a different fork version')
for path, required in (
    (DANMAKU, ('new ApiCallback<>(requestId, REQUEST_ID',
               'XraySideRequestGate.cancel(TAG);',
               'return XraySideRequestGate.newCall(')),
    (SUBTITLE, ('new ApiCallback<>(requestId, REQUEST_ID',
                'ApiCallback.post(requestId, REQUEST_ID',
                'XraySideRequestGate.cancel(TAG);',
                'XraySideRequestGate.usePlaybackTransport(',
                'if (download != task) return;')),
    (CALLBACK, ('currentId.get() == requestId', 'App.post(')),
):
    source = path.read_text(encoding='utf-8')
    for anchor in required:
        if anchor not in source:
            raise SystemExit(f'{path}: missing 5.8.7 cancellation/transport invariant: {anchor}')
if DANMAKU.read_text(encoding='utf-8').count('return XraySideRequestGate.newCall(') != 2:
    raise SystemExit('Danmaku search GET/POST must both use the Xray session gate')
if SUBTITLE.read_text(encoding='utf-8').count('return XraySideRequestGate.newCall(') != 2:
    raise SystemExit('Subtitle search/detail must both use the Xray session gate')

STUBS = {
    'android/net/Uri.java': '''package android.net;
        public final class Uri { public static String encode(String s) { return s; } }''',
    'android/text/TextUtils.java': '''package android.text;
        public final class TextUtils { public static boolean isEmpty(CharSequence s) {
            return s == null || s.length() == 0;
        }}''',
    'androidx/annotation/NonNull.java': 'package androidx.annotation; public @interface NonNull {}',
    'androidx/collection/ArrayMap.java': '''package androidx.collection;
        public class ArrayMap<K,V> extends java.util.HashMap<K,V> {}''',
    'com/fongmi/android/tv/App.java': '''package com.fongmi.android.tv;
        public final class App {
            public static final java.util.ArrayDeque<Runnable> queue = new java.util.ArrayDeque<>();
            public static void post(Runnable r) { queue.add(r); }
            public static void drain() { while (!queue.isEmpty()) queue.remove().run(); }
        }''',
    'com/fongmi/android/tv/R.java': '''package com.fongmi.android.tv;
        public final class R { public static class string { public static final int error_empty=1; }}''',
    'com/fongmi/android/tv/setting/DanmakuSetting.java': '''package com.fongmi.android.tv.setting;
        public final class DanmakuSetting {
            public static boolean isLoad() { return true; }
            public static boolean isAuto() { return true; }
            public static String getEffectiveApiUrl() { return "https://fixture.invalid/{name}/{episode}"; }
        }''',
    'com/fongmi/android/tv/setting/SubtitleSetting.java': '''package com.fongmi.android.tv.setting;
        public final class SubtitleSetting {
            public static String getEffectiveToken() { return "synthetic-token"; }
        }''',
    'com/fongmi/android/tv/utils/ResUtil.java': '''package com.fongmi.android.tv.utils;
        public final class ResUtil { public static String getString(int i) { return "empty"; }}''',
    'com/github/catvod/utils/Trans.java': '''package com.github.catvod.utils;
        public final class Trans { public static String t2s(String s) { return s; }}''',
    'com/github/catvod/utils/Task.java': '''package com.github.catvod.utils;
        public final class Task {
            public static final java.util.ArrayDeque<Runnable> queue=new java.util.ArrayDeque<>();
            public static void execute(Runnable r) { queue.add(r); }
            public static void drain() { while (!queue.isEmpty()) queue.remove().run(); }
        }''',
    'okhttp3/Callback.java': '''package okhttp3;
        public interface Callback {
            void onFailure(Call call, java.io.IOException error);
            void onResponse(Call call, Response response) throws java.io.IOException;
        }''',
    'okhttp3/Call.java': '''package okhttp3;
        public class Call {
            public static Call last;
            public Callback callback;
            public boolean canceled;
            public String tag;
            public Call(String tag) { this.tag=tag; last=this; }
            public void enqueue(Callback cb) { this.callback=cb; }
            public void cancel() { canceled=true; }
            public void success() throws Exception { callback.onResponse(this,new Response()); }
            public void failure() { callback.onFailure(this,new java.io.IOException("failure")); }
        }''',
    'okhttp3/Response.java': '''package okhttp3;
        public final class Response implements AutoCloseable {
            public Body body() { return new Body(); }
            public boolean isSuccessful() { return true; }
            public int code() { return 200; }
            public String message() { return "OK"; }
            public void close() {}
            public static final class Body { public String string() { return "fixture response"; }}
        }''',
    'okhttp3/RequestBody.java': 'package okhttp3; public class RequestBody {}',
    'okhttp3/HttpUrl.java': '''package okhttp3;
        public final class HttpUrl {
            public static HttpUrl parse(String value) { return value == null ? null : new HttpUrl(); }
            public Builder newBuilder() { return new Builder(); }
            public String toString() { return "https://fixture.invalid"; }
            public static final class Builder {
                public Builder addQueryParameter(String key,String value) { return this; }
                public HttpUrl build() { return new HttpUrl(); }
            }
        }''',
    'com/github/catvod/net/OkHttp.java': '''package com.github.catvod.net;
        public final class OkHttp {
            public static int cancels;
            public static void cancel(String tag) { cancels++; }
            public static okhttp3.RequestBody toBody(Object params) { return new okhttp3.RequestBody(); }
        }''',
    'com/fingmi/integration/xray/XraySideRequestGate.java': '''package com.fingmi.integration.xray;
        import java.util.ArrayList;
        import okhttp3.Call;
        import okhttp3.RequestBody;
        import com.github.catvod.net.Download;
        public final class XraySideRequestGate {
            public static final ArrayList<Call> calls=new ArrayList<>();
            public static final Object proxy=new Object();
            public static int cancels, transported;
            public static Call newCall(String url,String tag) {
                Call call=new Call(tag); calls.add(call); return call;
            }
            public static Call newCall(String url,RequestBody body,String tag) {
                return newCall(url,tag);
            }
            public static void cancel(String tag) {
                cancels++;
                for(Call call:calls) if(tag.equals(call.tag)) call.cancel();
            }
            public static Download usePlaybackTransport(Download dl) {
                transported++;
                return dl.transport(proxy);
            }
        }''',
    'com/fongmi/android/tv/bean/Danmaku.java': '''package com.fongmi.android.tv.bean;
        public final class Danmaku {
            public static java.util.List<Danmaku> arrayFrom(String s) {
                return java.util.List.of(new Danmaku());
            }
        }''',
    'com/fongmi/android/tv/bean/SubtitleSearchItem.java': '''package com.fongmi.android.tv.bean;
        import java.util.List; import java.io.File;
        public class SubtitleSearchItem {
            public boolean zip;
            public String getName() { return "fixture.srt"; }
            public String getUrl() { return "https://fixture.invalid/sub.srt"; }
            public int getId() { return 1; }
            public String getLang() { return "en"; }
            public boolean isZip() { return zip; }
            public static SubtitleSearchItem from(int id,String name,String url,String lang) {
                return new SubtitleSearchItem();
            }
            public static List<SubtitleSearchItem> fromFiles(List<File> f,String lang) {
                return java.util.List.of(new SubtitleSearchItem());
            }
        }''',
    'com/fongmi/android/tv/bean/SubtitleSearchPage.java': '''package com.fongmi.android.tv.bean;
        public final class SubtitleSearchPage {
            public static SubtitleSearchPage from(java.util.List<SubtitleSearchItem> items,int total) {
                return new SubtitleSearchPage();
            }
        }''',
    'com/fongmi/android/tv/bean/AssrtResponse.java': '''package com.fongmi.android.tv.bean;
        import java.util.List;
        public final class AssrtResponse {
            public static AssrtResponse from(String s) { return new AssrtResponse(); }
            public String getError() { return ""; }
            public List<Subtitle> getSubtitles() { return List.of(new Subtitle()); }
            public static final class Subtitle {
                public int getId() { return 1; }
                public String getNativeName() { return "name"; }
                public String getTitle() { return "title"; }
                public String getFileName() { return "fixture.srt"; }
                public String getVideoName() { return "video"; }
                public String getLanguage() { return "en"; }
                public String getUrl() { return "https://fixture.invalid/sub.srt"; }
                public boolean hasFileList() { return false; }
                public List<SubtitleFile> getFiles() { return List.of(); }
            }
            public static final class SubtitleFile {
                public String getName() { return "fixture.srt"; }
                public String getUrl() { return "https://fixture.invalid/sub.srt"; }
            }
        }''',
    'com/github/catvod/net/Download.java': '''package com.github.catvod.net;
        import java.io.File;
        public final class Download {
            public static Download last;
            public Callback callback;
            public boolean canceled;
            public Object transport;
            public Download tag(String tag) { return this; }
            public Download transport(Object client) { transport=client; return this; }
            public void start(Callback cb) { callback=cb; }
            public void cancel() { canceled=true; }
            public interface Callback { void success(File file); void error(String message); }
        }''',
    'com/fongmi/android/tv/utils/SubtitleArchive.java': '''package com.fongmi.android.tv.utils;
        import java.io.File;
        import java.util.List;
        import com.github.catvod.net.Download;
        public final class SubtitleArchive {
            public static Download createDownload(String name,String url) {
                return Download.last=new Download();
            }
            public static boolean isSupported(String name,String url) { return true; }
            public static File getDir(String url) { return new File("fixture"); }
            public static List<File> unzip(File f,File d) { return List.of(f); }
        }''',
    'SideRequest587Test.java': r'''
import com.fongmi.android.tv.App;
import com.fongmi.android.tv.api.DanmakuApi;
import com.fongmi.android.tv.api.SubtitleApi;
import com.fongmi.android.tv.bean.SubtitleSearchItem;
import com.github.catvod.net.Download;
import com.github.catvod.net.OkHttp;
import com.github.catvod.utils.Task;
import com.fingmi.integration.xray.XraySideRequestGate;
import okhttp3.Call;

public final class SideRequest587Test {
    static int delivered,errorCount,cases;
    static void check(boolean condition,String label) { if (!condition) throw new AssertionError(label); }
    static void drain() { Task.drain(); App.drain(); }
    static void reset() { DanmakuApi.cancel(); SubtitleApi.cancel(); drain(); delivered=errorCount=0; }
    static Call danmaku() { DanmakuApi.search("name","episode",v->delivered++,e->errorCount++); return Call.last; }
    static Call subtitle() { SubtitleApi.search("key",0,v->delivered++,e->errorCount++); return Call.last; }
    static Call detail() { SubtitleApi.detail(1,v->delivered++,e->errorCount++); return Call.last; }
    static void stale(String scenario) {
        drain(); check(delivered==0 && errorCount==0,scenario+": stale callback"); cases++;
    }
    static void queuedCancel(boolean subtitle,boolean fail) throws Exception {
        reset(); Call call=subtitle ? subtitle() : danmaku();
        if(fail) call.failure(); else call.success();
        if(subtitle) SubtitleApi.cancel(); else DanmakuApi.cancel();
        check(call.canceled,"original tagged request not canceled");
        stale((subtitle ? "subtitle" : "danmaku")+(fail ? " error" : " response"));
    }
    static void replacement(boolean subtitle) throws Exception {
        reset(); Call old=subtitle ? subtitle() : danmaku();
        Call next=subtitle ? subtitle() : danmaku();
        old.success(); next.success(); drain();
        check(delivered==1 && errorCount==0,"old result displaced new request");
        check(old.canceled && !next.canceled,"request cancellation crossed generation"); cases++;
    }
    static void completed(boolean subtitle) throws Exception {
        reset(); Call call=subtitle ? subtitle() : danmaku();
        call.success(); drain();
        if(subtitle) SubtitleApi.cancel(); else DanmakuApi.cancel();
        drain(); check(delivered==1 && errorCount==0,"completed result undone by later cancel"); cases++;
    }
    static void downloadInFlight() {
        reset(); SubtitleApi.loadSubtitle(new SubtitleSearchItem(),
                v->delivered++,e->errorCount++);
        Download task=Download.last;
        SubtitleApi.cancel();
        check(task.canceled,"in-flight download must cancel before callback");
        task.callback.success(new java.io.File("late.srt"));
        stale("late in-flight download callback");
    }
    static void download(boolean zip,boolean fail) {
        reset(); SubtitleSearchItem item=new SubtitleSearchItem(); item.zip=zip;
        SubtitleApi.loadSubtitle(item,v->delivered++,e->errorCount++);
        Download task=Download.last;
        check(task.transport==XraySideRequestGate.proxy,"download lost Xray session transport");
        if(fail) task.callback.error("fixture failure");
        else task.callback.success(new java.io.File("fixture.srt"));
        SubtitleApi.cancel();
        // A completed download clears its owner before the UI callback runs;
        // generation invalidation must still suppress the already queued UI work.
        stale("subtitle download "+zip+" failure "+fail);
    }
    public static void main(String[] args) throws Exception {
        int oldDirect=OkHttp.cancels, oldGate=XraySideRequestGate.cancels;
        for(boolean isSubtitle:new boolean[]{false,true}) {
            for(boolean fail:new boolean[]{false,true}) queuedCancel(isSubtitle,fail);
            replacement(isSubtitle); completed(isSubtitle);
        }
        reset(); Call detail=detail(); detail.success(); SubtitleApi.cancel(); stale("subtitle detail");
        downloadInFlight();
        for(boolean zip:new boolean[]{false,true}) {
            download(zip,false); download(zip,true);
        }
        reset(); SubtitleSearchItem item=new SubtitleSearchItem();
        SubtitleApi.loadSubtitle(item,v->delivered++,e->errorCount++);
        Download dl=Download.last;
        dl.callback.success(new java.io.File("fixture.srt"));
        drain(); SubtitleApi.cancel(); drain();
        check(delivered==1 && errorCount==0,"completed subtitle download not delivered"); cases++;
        check(OkHttp.cancels>oldDirect && XraySideRequestGate.cancels>oldGate,
              "both upstream direct and Xray tagged calls must be canceled");
        check(XraySideRequestGate.transported>=6,"multipart subtitle transport did not bind Xray");
        System.out.println("PASS real 5.8.7 Danmaku/Subtitle/ApiCallback: "+cases+
            " request-generation, delayed callback, download and tagged-cancel cases");
    }
}
'''
}

with tempfile.TemporaryDirectory(prefix='fongmi-587-side-request-') as directory:
    work = Path(directory)
    source_files = []
    for path, code in STUBS.items():
        file = work / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(code, encoding='utf-8')
        source_files.append(str(file))
    subprocess.run(['javac', '--release', '17', '-encoding', 'UTF-8', '-d', str(work),
                    *source_files, str(DANMAKU), str(SUBTITLE), str(CALLBACK)], check=True)
    subprocess.run(['java', '-cp', str(work), 'SideRequest587Test'], check=True)
