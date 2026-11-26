#!/usr/bin/env python3
"""Compile the actual pinned 5.9.0 BaseLoader port and fork coordinator.

Android, Task, Guava FIFO and individual loaders are deterministic doubles.
This is a host contract check, not a runtime or Android build test.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/upstream-adaptation"))
from recovery_loader import adapt_base_loader, git_blob

COORDINATOR = "b235ea6f6bf19420d8b7cdb6e9ec7a5197c934be"
ADAPTED = "9c2f598f91431cccf7de200c05f8473b8fc7e58f"
P = "com/fongmi/android/tv/"
L = P + "api/loader/"
C = "com/github/catvod/"
STUBS = {
    "android/net/Uri.java": 'package android.net; public class Uri { public static Uri parse(String s){return new Uri();} public String getQueryParameter(String k){return null;} }',
    "android/text/TextUtils.java": 'package android.text; public class TextUtils { public static boolean isEmpty(CharSequence s){return s==null||s.length()==0;} }',
    "dalvik/system/DexClassLoader.java": 'package dalvik.system; public class DexClassLoader {}',
    "org/json/JSONObject.java": 'package org.json; public class JSONObject {}',
    C + "Proxy.java": 'package com.github.catvod; public class Proxy { public static String getUrl(boolean b){return "local";} }',
    C + "crawler/Spider.java": 'package com.github.catvod.crawler; public class Spider { public Object[] proxy(java.util.Map<String,String> p){return null;} }',
    C + "crawler/SpiderNull.java": 'package com.github.catvod.crawler; public class SpiderNull extends Spider {}',
    C + "utils/Crypto.java": 'package com.github.catvod.utils; public class Crypto { public static String md5(String s){return s;} }',
    C + "utils/RuntimeModule.java": 'package com.github.catvod.utils; public enum RuntimeModule { NODEJS, PYTHON, QUICKJS; public void require(){} }',
    C + "utils/Task.java": '''package com.github.catvod.utils;
        import java.util.*; import java.util.concurrent.Executor;
        public class Task {
            public static final Queue<Runnable> normal=new ArrayDeque<>();
            public static final Executor worker=normal::add;
            public static Executor executor(){return worker;}
            public static void execute(Runnable r){worker.execute(r);}
            public static void executeSerial(Runnable r){throw new AssertionError("DB lane used");}
        }''',
    "com/google/common/util/concurrent/MoreExecutors.java": '''package com.google.common.util.concurrent;
        import java.util.*; import java.util.concurrent.Executor;
        import com.github.catvod.utils.Task;
        import com.fongmi.android.tv.api.loader.BaseLoader;
        public class MoreExecutors {
            public static int wrappers, failures;
            public static Executor newSequentialExecutor(Executor backend){
                if(backend!=Task.worker)throw new AssertionError("wrong worker lane");
                wrappers++;
                return new Executor(){
                    final Queue<Runnable> pending=new ArrayDeque<>(); boolean scheduled;
                    public void execute(Runnable r){
                        if(!Thread.holdsLock(BaseLoader.get()))throw new AssertionError("swap and enqueue not atomic");
                        pending.add(r);
                        if(!scheduled){scheduled=true;backend.execute(()->{
                            while(!pending.isEmpty())try{pending.remove().run();}catch(RuntimeException e){failures++;}
                            scheduled=false;
                        });}
                    }
                };
            }
        }''',
    P + "App.java": '''package com.fongmi.android.tv;
        import java.util.*; import com.fongmi.android.tv.api.loader.SpiderLoader;
        public class App {
            public static final Queue<Runnable> posts=new ArrayDeque<>();
            public static final List<Integer> postedAfter=new ArrayList<>();
            public static void post(Runnable r){postedAfter.add(SpiderLoader.events.size());posts.add(r);}
        }''',
    L + "SpiderTestSession.java": 'package com.fongmi.android.tv.api.loader; import com.github.catvod.crawler.Spider; public class SpiderTestSession { public static boolean isKey(String k){return false;} public static Spider require(String k){return null;} }',
    L + "SpiderLoader.java": '''package com.fongmi.android.tv.api.loader;
        import java.util.*;
        public class SpiderLoader {
            public static final List<String> events=new ArrayList<>();
            static int next; public static int fail=-1;
            final int id=next++; final String kind;
            SpiderLoader(String k){kind=k;}
            public void clear(){events.add("c:"+kind+id);if(id==fail)throw new IllegalStateException("test");}
            public void destroy(){events.add("d:"+kind+id);}
        }''',
    L + "JarLoader.java": '''package com.fongmi.android.tv.api.loader;
        import java.util.*; import com.github.catvod.crawler.Spider; import dalvik.system.DexClassLoader; import org.json.JSONObject;
        public class JarLoader extends SpiderLoader {
            public JarLoader(){super("jar");}
            public Spider getSpider(String k,String a,String e,String j){return new Spider();}
            public void setRecent(String s){} public Object[] proxy(Map<String,String> p){return null;}
            public void parseJar(String k,String j){} public DexClassLoader dex(String j){return null;}
            public JSONObject jsonExt(String k,LinkedHashMap<String,String> j,String u){return null;}
            public JSONObject jsonExtMix(String f,String k,String n,LinkedHashMap<String,HashMap<String,String>> j,String u){return null;}
        }''',
    L + "NodeLoader.java": '''package com.fongmi.android.tv.api.loader; import com.github.catvod.crawler.Spider;
        public class NodeLoader extends SpiderLoader { public NodeLoader(){super("node");} public Spider getSpider(String k,String a,String e){return new Spider();} }''',
    L + "PyLoader.java": '''package com.fongmi.android.tv.api.loader; import java.util.Map; import com.github.catvod.crawler.Spider;
        public class PyLoader extends SpiderLoader { public PyLoader(){super("py");} public PyLoader(PyLoader old){this();} public Spider getSpider(String k,String a,String e){return new Spider();} public void setRecent(String s){} public Object[] proxy(Map<String,String> p){return null;} }''',
    L + "JsLoader.java": '''package com.fongmi.android.tv.api.loader; import java.util.Map; import com.github.catvod.crawler.Spider;
        public class JsLoader extends SpiderLoader { public JsLoader(){super("js");} public JsLoader(JsLoader old){this();} public Spider getSpider(String k,String a,String e,String j){return new Spider();} public void setRecent(String s){} public Object[] proxy(Map<String,String> p){return null;} }''',
    "RecoveryPortTest.java": '''import java.util.*;
        import com.fongmi.android.tv.App;
        import com.fongmi.android.tv.api.loader.*;
        import com.github.catvod.utils.Task;
        import com.google.common.util.concurrent.MoreExecutors;
        import com.fingmi.tvrecovery.NetworkRecoveryCoordinator;
        public class RecoveryPortTest {
            static void check(boolean b,String msg){if(!b)throw new AssertionError(msg);}
            static final class Owner implements NetworkRecoveryCoordinator.Hooks {
                final NetworkRecoveryCoordinator core=new NetworkRecoveryCoordinator(0,this);
                final Queue<Runnable> polls=new ArrayDeque<>(); int refreshed;
                public long generation(){return 1;}
                public void cancelRequests(){} public void resetApiAndDns(){}
                public void clearSpiders(Runnable after){BaseLoader.get().clear(after);}
                public boolean networkReady(){return true;}
                public void schedule(Runnable r,long d){polls.add(r);}
                public void unschedule(Runnable r){polls.remove(r);}
                public void showProgress(){} public void refreshHome(){refreshed++;}
            }
            static List<String> groups(int n){
                List<String> out=new ArrayList<>();
                for(int i=0;i<n;i++){int j=i*4;out.addAll(List.of("c:node"+(j+1),"c:jar"+j,"c:py"+(j+2),"c:js"+(j+3)));}
                return out;
            }
            public static void main(String[] args){
                BaseLoader loader=BaseLoader.get();
                loader.getSpider("p","a.py","","");loader.getSpider("j","a.js","","");
                Owner old=new Owner(), next=new Owner();
                old.core.check(); old.core.close(); loader.clear(); next.core.check();
                check(MoreExecutors.wrappers==1&&Task.normal.size()==1,"not one FIFO on normal lane");
                check(SpiderLoader.events.isEmpty()&&App.posts.isEmpty(),"clear or callback ran before worker");
                Task.normal.remove().run();
                check(SpiderLoader.events.equals(groups(3)),"retired generation ordering: "+SpiderLoader.events);
                check(App.postedAfter.equals(List.of(4,12)),"completion before own clear or ordinary clear posted");
                App.posts.remove().run();check(old.polls.isEmpty()&&old.refreshed==0,"stale Home resumed");
                App.posts.remove().run();check(next.polls.size()==1,"new Home did not resume");
                next.polls.remove().run();check(next.refreshed==0,"one stable sample refreshed");
                next.polls.remove().run();check(next.refreshed==1&&next.core.appliedGeneration()==1,"recovery did not complete once");
                next.core.close();
                SpiderLoader.fail=13; int[] callback={0};
                loader.clear(()->callback[0]++);loader.destroy();
                check(Task.normal.size()==1&&App.posts.isEmpty(),"failure or destroy escaped FIFO");
                Task.normal.remove().run();
                List<String> expected=groups(5);List<String> retired=new ArrayList<>(expected);
                retired.replaceAll(s->"d:"+s.substring(2));expected.addAll(retired);
                check(SpiderLoader.events.equals(expected),"upstream clear/destroy/retirement changed: "+SpiderLoader.events);
                check(MoreExecutors.failures==1&&App.postedAfter.equals(List.of(4,12,16)),"failure did not post after every loader attempted");
                App.posts.remove().run();check(callback[0]==1&&App.posts.isEmpty(),"callback missing or duplicated");
                System.out.println("PASS actual 5.9 BaseLoader and fork coordinator: FIFO, owner handoff, completion, failure and destroy");
            }
        }''',
}
for name in ("Site", "Live"):
    config = "VodConfig" if name == "Site" else "LiveConfig"
    STUBS[P+"bean/"+name+".java"] = f'package com.fongmi.android.tv.bean; import com.github.catvod.crawler.Spider; public class {name} {{public boolean isEmpty(){{return true;}} public Spider spider(){{return null;}} public String getApi(){{return "";}}}}'
    STUBS[P+"api/config/"+config+".java"] = f'package com.fongmi.android.tv.api.config; import com.fongmi.android.tv.bean.{name}; public class {config} {{public static {config} get(){{return new {config}();}} public {name} get{name}(String k){{return new {name}();}}}}'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-loader", type=Path, required=True, help="BaseLoader.java from pinned public TV 5.9.0 checkout")
    p.add_argument("--coordinator", type=Path, default=ROOT/"tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java")
    args = p.parse_args()
    original = args.base_loader.read_bytes()
    core = args.coordinator.read_bytes()
    assert git_blob(core) == COORDINATOR, "recovery core drift"
    adapted = adapt_base_loader(original)
    assert git_blob(adapted) == ADAPTED, "reviewed adaptation drift"
    with tempfile.TemporaryDirectory(prefix="fingmi-590-recovery-") as td:
        work = Path(td)
        for name, source in STUBS.items():
            path = work/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        base = work/L/"BaseLoader.java"
        coordinator = work/"NetworkRecoveryCoordinator.java"
        coordinator.write_bytes(core)
        classes = work/"classes"
        classes.mkdir()
        def compile_and_run(data, positive):
            base.write_bytes(data)
            cmd = ["javac", "--release", "17", "-d", str(classes)] + [str(f) for f in work.rglob("*.java")]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if not positive and result.returncode:
                assert "clear" in result.stderr, result.stderr
                return
            assert result.returncode == 0, result.stderr
            run = subprocess.run(["java", "-cp", str(classes), "RecoveryPortTest"], capture_output=True, text=True, timeout=20)
            if positive:
                assert run.returncode == 0, run.stdout+run.stderr
                print(run.stdout.strip())
            else:
                assert run.returncode != 0, "negative control unexpectedly passed"
        compile_and_run(original, False)
        compile_and_run(adapted, True)
        compile_and_run(adapted.replace(b"clearExecutor.execute(() -> {", b"Task.execute(() -> {"), False)
        compile_and_run(adapted.replace(b"clearLoaders(previous, retired);", b"if (onComplete != null) App.post(onComplete);\n                    clearLoaders(previous, retired);"), False)
    print("PASS unported source and two mutations rejected; no Android or real loader runtime claim")


if __name__ == "__main__":
    main()
