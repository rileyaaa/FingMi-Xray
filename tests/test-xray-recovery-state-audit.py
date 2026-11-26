#!/usr/bin/env python3
"""Execute unmodified Xray/recovery state classes with minimal Android boundary stubs.

--model adds independently specified randomized lifecycle/identity event traces,
coordinator invariants and multi-threaded generation tests. This is a JVM test,
not Android framework, Binder, native Xray or device validation.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile

STUBS = {
'android/content/Context.java': 'package android.content; public class Context {}',
'android/content/Intent.java': '''package android.content; public class Intent {
 public static final String ACTION_SCREEN_OFF="OFF", ACTION_SCREEN_ON="ON";
 private final String action; public Intent(String a){action=a;} public String getAction(){return action;}
}''',
'android/content/IntentFilter.java': 'package android.content; public class IntentFilter { public void addAction(String a){} }',
'android/content/BroadcastReceiver.java': 'package android.content; public abstract class BroadcastReceiver { public abstract void onReceive(Context c,Intent i); }',
'android/os/Bundle.java': 'package android.os; public class Bundle {}',
'android/app/Activity.java': 'package android.app; public class Activity { public boolean changing; public boolean isChangingConfigurations(){return changing;} }',
'android/app/Application.java': '''package android.app;
import android.content.*; import android.os.Bundle;
public class Application extends Context {
 public BroadcastReceiver receiver; public ActivityLifecycleCallbacks callbacks;
 public void registerActivityLifecycleCallbacks(ActivityLifecycleCallbacks c){callbacks=c;}
 public Intent registerReceiver(BroadcastReceiver r,IntentFilter f){receiver=r;return null;}
 public interface ActivityLifecycleCallbacks {
  void onActivityCreated(Activity a,Bundle b); void onActivityStarted(Activity a);
  void onActivityResumed(Activity a); void onActivityPaused(Activity a);
  void onActivityStopped(Activity a); void onActivitySaveInstanceState(Activity a,Bundle b);
  void onActivityDestroyed(Activity a);
 }
}''',
'androidx/annotation/NonNull.java': 'package androidx.annotation; public @interface NonNull {}',
'androidx/annotation/Nullable.java': 'package androidx.annotation; public @interface Nullable {}'
}

JAVA=r'''
package com.fingmi.xray.service;
import android.app.*;
import android.content.*;
import com.fingmi.tvrecovery.*;
import com.fingmi.xray.session.PlaybackIdentityGate;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public final class StateAudit {
    static int assertions, scenarios;
    static void check(boolean ok,String name){assertions++;if(!ok)throw new AssertionError(name);}
    static void scenario(String name) { scenarios++; System.out.println("PASS "+name); }
    static final class Hooks implements NetworkRecoveryCoordinator.Hooks {
        long generation; boolean ready=true; int clears,refreshes,networkChecks;
        Runnable done; final ArrayDeque<Runnable> queue=new ArrayDeque<>();
        final List<String> order=new ArrayList<>(); final List<Long> delays=new ArrayList<>();
        final Set<Long> refreshed=new HashSet<>(); NetworkRecoveryCoordinator owner;
        public long generation(){return generation;}
        public boolean canRecoverHome(){return true;}
        public void cancelRequests(){order.add("cancel");}
        public void resetApiAndDns(){order.add("reset");}
        public void clearSpiders(Runnable after){
            check(done==null,"no concurrent spider clears"); done=after; clears++; order.add("clear");
        }
        public boolean networkReady(){networkChecks++;return ready;}
        public void schedule(Runnable r,long d){check(d==0||d==500,"poll delay");queue.add(r);delays.add(d);}
        public void unschedule(Runnable r){queue.removeIf(x->x==r);}
        public void showProgress(){order.add("progress");}
        public void refreshHome(){
            check(done==null,"refresh after spider completion");
            check(owner.appliedGeneration()==generation,"refresh latest generation");
            check(refreshed.add(generation),"refresh at most once per generation");refreshes++;order.add("refresh");
        }
        void finish(){check(done!=null,"clear pending");Runnable r=done;done=null;r.run();}
        void tick(){check(!queue.isEmpty(),"poll pending");queue.remove().run();}
        void settle(){ready=true;for(int i=0;done!=null||!queue.isEmpty();i++){
            check(i<100,"recovery converges");if(done!=null)finish();else tick();}}
        NetworkRecoveryCoordinator core(){return owner=new NetworkRecoveryCoordinator(0,this);}
    }
    static final class Renderer implements TvNetworkLifecycle.Renderer {
        int starts,stops; boolean failStart,failStop;
        public void start(){starts++;if(failStart){failStart=false;throw new IllegalStateException("synthetic");}}
        public void stop(){stops++;if(failStop){failStop=false;throw new IllegalStateException("synthetic");}}
    }
    static TvNetworkLifecycle fresh(Application app,Renderer renderer) throws Exception {
        var field=TvNetworkLifecycle.class.getDeclaredField("instance");field.setAccessible(true);field.set(null,null);
        return TvNetworkLifecycle.get(app,renderer);
    }
    static void fixed() throws Exception {
        Hooks h=new Hooks();var c=h.core();c.check();check(h.clears==0,"cold no reset");scenario("coordinator cold entry");
        h.generation=1;c.check();c.check();check(h.clears==1,"deduplicate checks");
        check(h.order.equals(List.of("progress","cancel","reset","clear")),"recovery resource ordering");
        h.finish();h.tick();check(h.refreshes==0,"needs two ready observations");h.tick();
        check(h.refreshes==1&&!c.recovering()&&c.appliedGeneration()==1,"settled generation");
        check(h.delays.equals(List.of(0L,500L)),"stable poll delays");scenario("coordinator ordering and two stable samples");
        h=new Hooks();c=h.core();h.generation=1;c.check();h.generation=2;c.check();
        check(h.clears==1,"serialize newer generation");h.finish();h.tick();
        check(h.clears==2&&h.refreshes==0,"superseded generation never refreshes");h.settle();
        check(c.appliedGeneration()==2&&h.refreshes==1,"latest recovered");scenario("coordinator superseded generation");
        h=new Hooks();c=h.core();h.generation=1;c.check();h.finish();h.tick();
        h.ready=false;h.tick();h.ready=true;h.tick();check(h.refreshes==0,"readiness reset after failure");h.tick();
        check(h.refreshes==1,"two new stable checks");scenario("coordinator intermittent network");
        h=new Hooks();c=h.core();h.generation=1;h.ready=false;c.check();h.finish();
        while(!h.queue.isEmpty())h.tick();check(h.networkChecks==13&&h.refreshes==1,"bounded fallback unchanged");
        check(Collections.frequency(h.delays,500L)==12,"six second fallback schedule");scenario("coordinator bounded offline fallback");
        h=new Hooks();c=h.core();h.generation=1;c.check();c.close();h.finish();c.check();
        check(h.queue.isEmpty()&&h.refreshes==0&&!c.recovering(),"close before late completion");scenario("coordinator close before clear");
        h=new Hooks();c=h.core();h.generation=1;c.check();h.finish();c.close();
        check(h.queue.isEmpty()&&h.refreshes==0,"close removes poll");scenario("coordinator close after clear");
        Application app=new Application();Renderer r=new Renderer();var l=fresh(app,r);
        Activity a=new Activity(),b=new Activity(),unknown=new Activity();
        l.onActivityStarted(a);l.onActivityStarted(a);l.onActivityStopped(unknown);
        check(TvNetworkLifecycle.generation()==0,"unknown stop did not consume home");
        l.onActivityStarted(b);l.onActivityStopped(a);l.onActivityStopped(a);
        check(TvNetworkLifecycle.generation()==0,"internal transition no generation");
        l.onActivityResumed(b);l.onActivityResumed(b);check(r.starts==1,"one renderer start");
        l.onActivityStopped(b);check(r.stops==1,"last stop stops renderer");
        l.onActivityStarted(a);check(TvNetworkLifecycle.generation()==1,"background return advances");
        scenario("lifecycle duplicates unknown stop and background");
        a.changing=true;l.onActivityStopped(a);l.onActivityStarted(b);
        check(TvNetworkLifecycle.generation()==1,"rotation no new generation");scenario("lifecycle configuration change");
        l.onActivityResumed(b);int starts=r.starts;
        app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_OFF));
        app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_ON));
        app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_ON));
        check(TvNetworkLifecycle.generation()==2,"screen cycle one generation");
        check(r.starts==starts,"SCREEN_ON does not start renderer");l.onActivityResumed(b);
        check(r.starts==starts+1,"resume starts renderer");scenario("lifecycle screen and renderer boundary");
        TvNetworkLifecycle.markRecovered(1);check(TvNetworkLifecycle.recoveredGeneration()==0,"stale mark ignored");
        TvNetworkLifecycle.markRecovered(2);check(TvNetworkLifecycle.recoveredGeneration()==2,"current mark accepted");scenario("lifecycle recovery marker ownership");
        l.onActivityDestroyed(b);l.onActivityStarted(a);
        check(TvNetworkLifecycle.generation()==3,"destroy without stop retires reference");scenario("lifecycle unmatched destroy");
        app=new Application();r=new Renderer();l=fresh(app,r);a=new Activity();b=new Activity();r.failStart=true;
        l.onActivityStarted(a);l.onActivityResumed(a);l.onActivityResumed(a);
        check(r.starts==2,"renderer start retry");r.failStop=true;l.onActivityStopped(a);
        l.onActivityStarted(b);l.onActivityResumed(b);check(r.starts==3&&r.stops==1,"stop failure recovery");scenario("lifecycle renderer failure tolerance");
        app=new Application();r=new Renderer();l=fresh(app,r);
        app.receiver.onReceive(app,null);app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_OFF));
        app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_ON));
        check(TvNetworkLifecycle.generation()==0,"screen-on with no activity defers");
        l.onActivityStarted(a);check(TvNetworkLifecycle.generation()==1,"late activity consumes pending foreground");scenario("lifecycle screen before activity");
        PlaybackIdentityGate p=new PlaybackIdentityGate();check(!p.hasIdentity()&&p.generation()==0,"empty playback");
        check(p.begin("episode:1"),"first identity");p.provisional("https://source.invalid/a");
        p.provisional("https://ignored.invalid/a");check(p.mediaUrl().equals("https://source.invalid/a"),"first provisional wins");
        check(p.resolved("https://cdn.invalid/b"),"resolved URL change");check(p.generation()==1,"URL change keeps identity generation");
        check(!p.begin("episode:1"),"same identity preserved");
        check(p.begin("episode:2")&&p.mediaUrl()==null&&p.generation()==2,"new episode resets URL");
        p.end();check(!p.hasIdentity()&&p.mediaUrl()==null&&p.generation()==3,"end invalidates");
        scenario("playback identity versus resolved URL");
        XrayGenerationGate g=new XrayGenerationGate();g.begin(10);g.begin(9);
        check(g.isCurrent(10)&&!g.isCurrent(9),"old request cannot replace current");
        check(!g.cancel(9)&&g.isCurrent(10),"stale cancel ignored");
        AtomicInteger commits=new AtomicInteger();check(!g.runIfCurrent(9,commits::incrementAndGet),"stale trust blocked");
        check(g.runIfCurrent(10,commits::incrementAndGet)&&commits.get()==1,"current trust committed once");
        check(g.cancel(10),"current cancel succeeds");g.begin(11);check(!g.isCurrent(11),"cancel sealed generation");
        scenario("Xray operation generation and trust ownership");
        System.out.println("Fixed scenarios="+scenarios+" assertions="+assertions+" failures=0");
    }
    static void model() throws Exception {
        int lifecycleSteps=0,identitySteps=0,coordinatorSteps=0;
        for(int seed=0;seed<4;seed++) {
            Random random=new Random(0x5eed+seed);
            Application app=new Application();Renderer r=new Renderer();var l=fresh(app,r);
            Activity[] activities={new Activity(),new Activity(),new Activity(),new Activity()};
            Set<Integer> visible=new HashSet<>();boolean pending=false,running=false;long epoch=0;int starts=0,stops=0;
            for(int i=0;i<2500;i++) {
                int which=random.nextInt(4),event=random.nextInt(6);Activity a=activities[which];
                switch(event) {
                    case 0 -> { l.onActivityStarted(a); boolean newEntry=visible.add(which);
                        if(newEntry&&visible.size()==1&&pending){epoch++;pending=false;} }
                    case 1,2 -> { a.changing=random.nextBoolean();
                        if(event==1)l.onActivityStopped(a);else l.onActivityDestroyed(a);
                        if(visible.remove(which)&&visible.isEmpty()&&!a.changing){pending=true;if(running){running=false;stops++;}} }
                    case 3 -> { app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_OFF));pending=true;if(running){running=false;stops++;} }
                    case 4 -> { app.receiver.onReceive(app,new Intent(Intent.ACTION_SCREEN_ON));if(!visible.isEmpty()&&pending){epoch++;pending=false;} }
                    case 5 -> { l.onActivityResumed(a);if(!running){running=true;starts++;} }
                }
                check(TvNetworkLifecycle.generation()==epoch,"model lifecycle epoch seed="+seed+" step="+i);
                check(r.starts==starts&&r.stops==stops,"model renderer ownership");lifecycleSteps++;
            }
            PlaybackIdentityGate p=new PlaybackIdentityGate();String identity=null,url=null;long gen=0;
            for(int i=0;i<2500;i++) {
                int action=random.nextInt(4);String next="id:"+random.nextInt(10),media="https://cdn.invalid/"+random.nextInt(10);
                if(action==0){boolean changed=!Objects.equals(identity,next);check(p.begin(next)==changed,"identity model begin");
                    if(changed){identity=next;url=null;gen++;}}
                else if(action==1){boolean changed=identity!=null&&url!=null&&!Objects.equals(url,media);check(p.resolved(media)==changed,"identity model resolve");if(identity!=null)url=media;}
                else if(action==2){p.provisional(media);if(identity!=null&&url==null)url=media;}
                else{p.end();if(identity!=null){identity=null;url=null;gen++;}}
                check(p.hasIdentity()==(identity!=null)&&Objects.equals(url,p.mediaUrl())&&gen==p.generation(),"identity model state");identitySteps++;
            }
            Hooks h=new Hooks();var c=h.core();
            for(int i=0;i<2500;i++) {
                switch(random.nextInt(5)) {
                    case 0 -> {h.generation++;c.check();}
                    case 1 -> c.check();
                    case 2 -> {if(h.done!=null)h.finish();}
                    case 3 -> {if(!h.queue.isEmpty())h.tick();}
                    case 4 -> h.ready=random.nextBoolean();
                }
                check(c.appliedGeneration()<=h.generation,"no future generation applied");
                check(h.queue.size()<=1,"single pending stability poll");coordinatorSteps++;
            }
            h.settle();check(c.appliedGeneration()==h.generation,"final generation converged");c.close();
        }
        XrayGenerationGate gate=new XrayGenerationGate();ExecutorService pool=Executors.newFixedThreadPool(4);
        List<Future<?>> futures=new ArrayList<>();
        for(int thread=0;thread<4;thread++){final int offset=thread*2500;futures.add(pool.submit(()->{
            for(int i=2499;i>=0;i--)gate.begin(offset+i+1);
        }));}
        for(var f:futures)f.get(10,TimeUnit.SECONDS);pool.shutdown();
        check(gate.isCurrent(10000),"concurrent starts choose greatest operation id");
        gate.invalidateAll();gate.begin(10001);check(!gate.isCurrent(10001),"invalidation seals later starts");
        System.out.println("Model lifecycle events="+lifecycleSteps+" identity events="+identitySteps
            +" coordinator events="+coordinatorSteps+" concurrent begins=10000 failures=0");
        System.out.println("Model assertions="+assertions);
    }
    public static void main(String[] args) throws Exception {
        if(args.length>0&&args[0].equals("model"))model();else fixed();
    }
}
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--model',action='store_true')
    args=parser.parse_args()
    for tool in ('java','javac'):
        if not shutil.which(tool): raise SystemExit(f'{tool} is required')
    root=args.repo.resolve()
    sources=[root/p for p in (
        'tv-recovery/src/main/java/com/fingmi/tvrecovery/TvNetworkLifecycle.java',
        'tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java',
        'xray/src/main/java/com/fingmi/xray/session/PlaybackIdentityGate.java',
        'xray/src/main/java/com/fingmi/xray/service/XrayGenerationGate.java')]
    with tempfile.TemporaryDirectory(prefix='xray-state-audit-') as directory:
        temp=Path(directory)
        for name,content in STUBS.items():
            p=temp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8');sources.append(p)
        p=temp/'StateAudit.java';p.write_text(JAVA,encoding='utf-8');sources.append(p)
        subprocess.run(['javac','-encoding','UTF-8','-d',str(temp),*[str(p) for p in sources]],check=True)
        subprocess.run(['java','-cp',str(temp),'com.fingmi.xray.service.StateAudit',
                        'model' if args.model else 'fixed'],check=True)

if __name__=='__main__':main()
