#!/usr/bin/env python3
"""Exercise shared Spider-clear ordering across Home owners with real Java sources.

Android, Guava adapter and individual Spider loaders are test doubles. Task's
actual JDK executors, BaseLoader's real dispatch and both recovery coordinators
run unchanged. This is not a real Spider/native or TV integration test.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app/src/main/java/com/fongmi/android/tv"
CORE = ROOT / "tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java"

STUBS = {
    "android/text/TextUtils.java": """package android.text;
        public class TextUtils { public static boolean isEmpty(CharSequence s){return s==null||s.length()==0;} }""",
    "androidx/annotation/NonNull.java": "package androidx.annotation; public @interface NonNull {}",
    "androidx/annotation/Nullable.java": "package androidx.annotation; public @interface Nullable {}",
    "dalvik/system/DexClassLoader.java": "package dalvik.system; public class DexClassLoader {}",
    "org/json/JSONObject.java": "package org.json; public class JSONObject {}",
    "com/github/catvod/crawler/Spider.java": """package com.github.catvod.crawler;
        import java.util.Map;
        public class Spider { public Object[] proxy(Map<String,String> p){return null;} }""",
    "com/github/catvod/crawler/SpiderNull.java": "package com.github.catvod.crawler; public class SpiderNull extends Spider {}",
    "com/github/catvod/utils/Crypto.java": "package com.github.catvod.utils; public class Crypto { public static String md5(String s){return s;} }",
    "com/fongmi/android/tv/bean/Site.java": """package com.fongmi.android.tv.bean;
        import com.github.catvod.crawler.Spider;
        public class Site { public boolean isEmpty(){return true;} public Spider spider(){return null;} }""",
    "com/fongmi/android/tv/bean/Live.java": """package com.fongmi.android.tv.bean;
        import com.github.catvod.crawler.Spider;
        public class Live { public boolean isEmpty(){return true;} public Spider spider(){return null;} }""",
    "com/fongmi/android/tv/api/config/VodConfig.java": """package com.fongmi.android.tv.api.config;
        import com.fongmi.android.tv.bean.Site;
        public class VodConfig { public static VodConfig get(){return new VodConfig();} public Site getSite(String s){return new Site();} }""",
    "com/fongmi/android/tv/api/config/LiveConfig.java": """package com.fongmi.android.tv.api.config;
        import com.fongmi.android.tv.bean.Live;
        public class LiveConfig { public static LiveConfig get(){return new LiveConfig();} public Live getLive(String s){return new Live();} }""",
    "com/fongmi/android/tv/App.java": """package com.fongmi.android.tv;
        import java.util.concurrent.*;
        public class App {
            public static final BlockingQueue<Runnable> posts=new LinkedBlockingQueue<>();
            public static void post(Runnable r){posts.add(r);}
        }""",
    "com/google/common/util/concurrent/FutureCallback.java": """package com.google.common.util.concurrent;
        public interface FutureCallback<T> { void onSuccess(T t); void onFailure(Throwable e); }""",
    "com/google/common/util/concurrent/ListeningExecutorService.java": """package com.google.common.util.concurrent;
        import java.util.concurrent.Future;
        public interface ListeningExecutorService { void execute(Runnable r); Future<?> submit(Runnable r); }""",
    "com/google/common/util/concurrent/MoreExecutors.java": """package com.google.common.util.concurrent;
        import java.util.concurrent.*;
        import java.util.List;
        public class MoreExecutors {
            private static final List<ExecutorService> delegates=new CopyOnWriteArrayList<>();
            public static final List<ExecutorService> dispatched=new CopyOnWriteArrayList<>();
            public static ListeningExecutorService listeningDecorator(ExecutorService service){
                delegates.add(service);
                return new ListeningExecutorService(){
                    public void execute(Runnable r){dispatched.add(service);service.execute(r);}
                    public Future<?> submit(Runnable r){return service.submit(r);}
                };
            }
            public static void shutdown(){for(ExecutorService e:delegates)e.shutdownNow();}
        }""",
    "com/fongmi/android/tv/api/loader/ClearTrace.java": """package com.fongmi.android.tv.api.loader;
        import java.util.List;
        import java.util.concurrent.*;
        import java.util.concurrent.atomic.AtomicInteger;
        public class ClearTrace {
            public static final List<String> events=new CopyOnWriteArrayList<>();
            public static final CountDownLatch firstEntered=new CountDownLatch(1);
            public static final CountDownLatch releaseFirst=new CountDownLatch(1);
            public static final CountDownLatch finished=new CountDownLatch(3);
            private static final AtomicInteger ids=new AtomicInteger();
            private static final ThreadLocal<Integer> current=new ThreadLocal<>();
            static void jar(){
                int id=ids.incrementAndGet();current.set(id);events.add("jar"+id);
                if(id==1){
                    firstEntered.countDown();
                    try {if(!releaseFirst.await(10,TimeUnit.SECONDS))throw new AssertionError("first clear blocked");}
                    catch(InterruptedException e){Thread.currentThread().interrupt();throw new AssertionError(e);}
                }
            }
            static void py(){events.add("py"+current.get());}
            static void js(){events.add("js"+current.get());current.remove();finished.countDown();}
        }""",
    "com/fongmi/android/tv/api/loader/JarLoader.java": """package com.fongmi.android.tv.api.loader;
        import java.util.*;
        import com.github.catvod.crawler.Spider;
        import dalvik.system.DexClassLoader;
        import org.json.JSONObject;
        public class JarLoader {
            public void clear(){ClearTrace.jar();}
            public Spider getSpider(String k,String a,String e,String j){return null;}
            public void setRecent(String s){}
            public Object[] proxy(Map<String,String> p){return null;}
            public void parseJar(String k,String j){}
            public DexClassLoader dex(String j){return null;}
            public JSONObject jsonExt(String k,LinkedHashMap<String,String> j,String u){return null;}
            public JSONObject jsonExtMix(String f,String k,String n,LinkedHashMap<String,HashMap<String,String>> j,String u){return null;}
        }""",
    "com/fongmi/android/tv/api/loader/PyLoader.java": """package com.fongmi.android.tv.api.loader;
        import java.util.Map;
        import com.github.catvod.crawler.Spider;
        public class PyLoader {
            public void clear(){ClearTrace.py();}
            public Spider getSpider(String k,String a,String e){return null;}
            public void setRecent(String k){}
            public Object[] proxy(Map<String,String> p){return null;}
        }""",
    "com/fongmi/android/tv/api/loader/JsLoader.java": """package com.fongmi.android.tv.api.loader;
        import java.util.Map;
        import com.github.catvod.crawler.Spider;
        public class JsLoader {
            public void clear(){ClearTrace.js();}
            public Spider getSpider(String k,String a,String e,String j){return null;}
            public void setRecent(String k){}
            public Object[] proxy(Map<String,String> p){return null;}
        }""",
    "SpiderClearHandoffTest.java": """import java.util.*;
        import java.util.concurrent.*;
        import com.fongmi.android.tv.App;
        import com.fongmi.android.tv.api.loader.BaseLoader;
        import com.fongmi.android.tv.api.loader.ClearTrace;
        import com.fongmi.android.tv.utils.Task;
        import com.fingmi.tvrecovery.NetworkRecoveryCoordinator;
        import com.google.common.util.concurrent.MoreExecutors;
        public class SpiderClearHandoffTest {
            static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
            static final class Owner implements NetworkRecoveryCoordinator.Hooks {
                final NetworkRecoveryCoordinator recovery=new NetworkRecoveryCoordinator(0,this);
                final Queue<Runnable> polls=new ArrayDeque<>();
                int refreshes;
                public long generation(){return 1;}
                public void cancelRequests(){}
                public void resetApiAndDns(){}
                public void clearSpiders(Runnable after){BaseLoader.get().clear(after);}
                public boolean networkReady(){return true;}
                public void schedule(Runnable r,long d){polls.add(r);}
                public void unschedule(Runnable r){polls.removeIf(x->x==r);}
                public void showProgress(){}
                public void refreshHome(){refreshes++;}
            }
            static Runnable posted() throws Exception {
                Runnable r=App.posts.poll(5,TimeUnit.SECONDS);
                check(r!=null,"clear completion missing");return r;
            }
            public static void main(String[] args) throws Exception {
                try {
                    CountDownLatch canary=new CountDownLatch(1);
                    Task.executeSerial(canary::countDown);
                    check(canary.await(5,TimeUnit.SECONDS),"serial executor unavailable");
                    ExecutorService serial=MoreExecutors.dispatched.get(0);
                    Owner oldHome=new Owner(), newHome=new Owner();
                    oldHome.recovery.check();
                    check(ClearTrace.firstEntered.await(5,TimeUnit.SECONDS),"old clear never started");
                    oldHome.recovery.close();
                    BaseLoader.get().clear(); // ordinary VodConfig cleanup on owner destruction
                    newHome.recovery.check();
                    // Deterministic routing assertion: a general pooled executor is wrong
                    // even if a slow scheduler has not yet started its second task.
                    check(MoreExecutors.dispatched.equals(List.of(serial,serial,serial,serial)),
                        "all three clears must use the same serial executor");
                    check(ClearTrace.events.equals(List.of("jar1")),"later clear began before old clear finished");
                    ClearTrace.releaseFirst.countDown();
                    check(ClearTrace.finished.await(5,TimeUnit.SECONDS),"queued clear did not finish");
                    check(ClearTrace.events.equals(List.of("jar1","py1","js1","jar2","py2","js2","jar3","py3","js3")),
                        "clear tasks overlapped or changed loader order: "+ClearTrace.events);
                    posted().run();
                    check(oldHome.polls.isEmpty()&&oldHome.refreshes==0,"closed owner resumed recovery");
                    posted().run();
                    check(newHome.polls.size()==1,"new owner must begin stability poll after its clear");
                    newHome.polls.remove().run();
                    check(newHome.refreshes==0,"first ready sample must not refresh");
                    newHome.polls.remove().run();
                    check(newHome.refreshes==1&&newHome.recovery.appliedGeneration()==1,
                        "new owner did not complete recovery exactly once");
                    check(App.posts.isEmpty(),"ordinary clear unexpectedly posted a completion");
                    newHome.recovery.close();
                    System.out.println("PASS: actual BaseLoader/Task FIFO clear and Home owner handoff");
                } finally {
                    ClearTrace.releaseFirst.countDown();
                    MoreExecutors.shutdown();
                    Task.scheduler().shutdownNow();
                }
            }
        }""",
}

with tempfile.TemporaryDirectory(prefix="tv-spider-clear-") as directory:
    work = Path(directory)
    stubs = []
    for name, content in STUBS.items():
        path = work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        stubs.append(str(path))
    classes = work / "classes"
    classes.mkdir()
    subprocess.run(["javac", "--release", "17", "-d", str(classes),
                    *stubs, str(APP / "utils/Task.java"),
                    str(APP / "api/loader/BaseLoader.java"), str(CORE)], check=True)
    subprocess.run(["java", "-cp", str(classes), "SpiderClearHandoffTest"],
                   check=True, timeout=25)
