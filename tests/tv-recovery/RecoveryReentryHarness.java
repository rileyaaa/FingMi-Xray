package com.fingmi.tvrecovery;

import java.util.ArrayList;
import java.util.List;

/** JVM-only lifecycle proof of the real recovery coordinator; no Android or rendering. */
public final class RecoveryReentryHarness {
    static int tests;
    static void ok(boolean x, String message) { tests++; if (!x) throw new AssertionError(message); }
    static final class Hooks implements NetworkRecoveryCoordinator.Hooks {
        long generation=1;
        boolean networkReady;
        boolean homeRecoverable=true;
        boolean pauseOnReady;
        boolean advanceOnReady;
        boolean closeDuring;
        int closeAtOccurrence=1;
        String closeAt="";
        Runnable spiderDone, scheduled;
        NetworkRecoveryCoordinator recovery;
        final List<String> events=new ArrayList<>();
        void event(String step) {
            events.add(step);
            if (step.equals(closeAt) && closeDuring && --closeAtOccurrence==0) {
                closeDuring=false;
                recovery.close();
            }
        }
        public long generation() { event("generation"); return generation; }
        public void cancelRequests() { event("cancel"); }
        public void resetApiAndDns() { event("reset"); }
        public void clearSpiders(Runnable after) { event("spider"); spiderDone=after; }
        public boolean canRecoverHome() { event("home"); return homeRecoverable; }
        public boolean networkReady() {
            event("ready");
            if(pauseOnReady) homeRecoverable=false;
            if(advanceOnReady) generation++;
            return networkReady;
        }
        public void schedule(Runnable action,long delay) {
            // Model App.post reentrantly destroying Home before it can enqueue.
            event("schedule:"+delay);
            scheduled=action;
        }
        public void unschedule(Runnable action) {
            event("unschedule"); if(scheduled==action)scheduled=null;
        }
        public void showProgress() { event("progress"); }
        public void refreshHome() { event("refresh"); }
        void finishSpider(){Runnable r=spiderDone;spiderDone=null;ok(r!=null,"expected spider callback");r.run();}
        void tick(){Runnable r=scheduled;scheduled=null;ok(r!=null,"expected poll");r.run();}
        void setup(){ recovery=new NetworkRecoveryCoordinator(0,this); }
    }
    static void normal(){
        Hooks f=new Hooks();f.setup();
        f.recovery.check();ok(f.events.containsAll(List.of("progress","cancel","reset","spider")),"normal recovery order missing");
        f.finishSpider();ok(f.scheduled!=null,"missing first poll");
        f.networkReady=true;f.tick();ok(f.scheduled!=null,"missing stable poll");
        f.tick();ok(f.events.contains("refresh"),"normal ready recovery did not refresh home");
        ok(f.recovery.appliedGeneration()==1&&!f.recovery.recovering(),"normal generation not committed");
        f.recovery.close();
    }
    static void generationSupersedesStaleSpider() {
        Hooks f=new Hooks();f.setup();f.recovery.check();
        Runnable old=f.spiderDone;
        f.generation=2;
        old.run(); // stale completion is allowed to initiate a generation check
        ok(f.scheduled!=null,"stale spider completion did not schedule generation poll");
        f.tick();
        ok(f.events.stream().filter("spider"::equals).count()==2,
                "new generation did not restart spider cleanup");
        f.finishSpider();f.networkReady=true;f.tick();f.tick();
        ok(f.recovery.appliedGeneration()==2,"wrong recovered generation committed");
        ok(f.events.stream().filter("refresh"::equals).count()==1,
                "stale generation refreshed Home");
        f.recovery.close();
    }
    static void duplicateSpiderCompletionKeepsStabilityDelay() {
        Hooks f=new Hooks();f.setup();f.recovery.check();
        Runnable completed=f.spiderDone;
        f.finishSpider();f.networkReady=true;f.tick();
        ok(f.events.get(f.events.size()-1).equals("schedule:500"),"missing stability delay");
        int events=f.events.size();
        completed.run();
        ok(f.events.size()==events,"duplicate spider completion replaced the stability delay");
        ok(f.recovery.recovering()&&f.recovery.appliedGeneration()==0,"duplicate completion committed recovery");
        f.tick();
        ok(f.recovery.appliedGeneration()==1,"stable generation not committed");
        ok(f.events.stream().filter("refresh"::equals).count()==1,"duplicate completion refreshed twice");
        completed.run();
        ok(f.scheduled==null,"completed generation scheduled another poll");
        f.generation=2;f.recovery.check();
        completed.run();
        ok(f.scheduled==null,"old completion scheduled poll for new generation");
        f.finishSpider();f.tick();f.tick();
        ok(f.recovery.appliedGeneration()==2,"next generation failed");
        ok(f.events.stream().filter("refresh"::equals).count()==2,"next generation refresh count wrong");
        f.recovery.close();
    }
    static long count(Hooks f,String event) { return f.events.stream().filter(event::equals).count(); }
    static void slowSpiderThenLiveThenSecondWake() {
        Hooks f=new Hooks();f.setup();f.recovery.check();
        Runnable completed=f.spiderDone;
        f.homeRecoverable=false; // Home onPause, Live remains in the foreground.
        f.generation=2; // second OFF/ON while the first clear is still running
        f.recovery.check();
        ok(count(f,"spider")==1&&count(f,"reset")==1,"overlapping recovery during slow clear");
        f.finishSpider();f.tick();
        ok(count(f,"reset")==1&&count(f,"spider")==1,"background reset/clear on new generation");
        ok(count(f,"refresh")==0&&f.recovery.appliedGeneration()==0,"background generation consumed/refreshed");
        ok(f.scheduled==null,"hidden Home kept polling");
        completed.run();f.recovery.check();
        ok(f.scheduled==null&&count(f,"reset")==1,"hidden duplicate callback or check restarted recovery");
        f.generation=3; // latest must win even if another wake occurs while deferred
        long schedules=count(f,"schedule:0");
        f.homeRecoverable=true;f.recovery.check();f.recovery.check(); // resume and focus
        ok(count(f,"schedule:0")==schedules+1,"resume/focus scheduled two deferred polls");
        f.tick();
        ok(count(f,"reset")==2&&count(f,"spider")==2,"return did not start exactly one latest clear");
        completed.run();
        ok(f.scheduled==null,"old clear callback escaped into the latest clear");
        f.finishSpider();f.networkReady=true;f.tick();f.tick();
        ok(f.recovery.appliedGeneration()==3&&count(f,"refresh")==1,"latest generation was not recovered exactly once");
        f.recovery.check();f.recovery.check();
        ok(count(f,"reset")==2&&f.scheduled==null,"resume/focus repeated completed recovery");
        f.recovery.close();
    }
    static void pauseBeforeCommit() {
        Hooks f=new Hooks();f.setup();f.recovery.check();
        Runnable completed=f.spiderDone;
        f.finishSpider();f.networkReady=true;f.tick();
        f.pauseOnReady=true; // Home becomes unavailable during the last readiness callback.
        f.tick();
        ok(f.recovery.appliedGeneration()==0&&count(f,"refresh")==0,"hidden Home committed/refreshed during final readiness callback");
        ok(f.scheduled==null,"hidden commit kept polling");
        completed.run();f.recovery.check();
        ok(f.scheduled==null,"same-generation duplicate completed a deferred clear");
        f.pauseOnReady=false;f.homeRecoverable=true;
        long schedules=count(f,"schedule:0");
        f.recovery.check();f.recovery.check();
        ok(count(f,"schedule:0")==schedules+1,"same-generation resume/focus scheduled two polls");
        f.tick();ok(count(f,"refresh")==0,"deferred stability reused pre-pause sample");f.tick();
        ok(f.recovery.appliedGeneration()==1&&count(f,"refresh")==1,"same generation did not refresh once after return");
        ok(count(f,"reset")==1&&count(f,"spider")==1,"same generation unnecessarily cleared again");
        f.recovery.close();
    }
    static void hiddenInitialCheck() {
        Hooks f=new Hooks();f.setup();f.homeRecoverable=false;f.recovery.check();
        ok(count(f,"reset")==0&&count(f,"spider")==0&&count(f,"progress")==0,"hidden entry started recovery");
        ok(!f.recovery.recovering()&&f.recovery.appliedGeneration()==0,"hidden entry consumed generation");
        f.homeRecoverable=true;f.recovery.check();f.finishSpider();f.networkReady=true;f.tick();f.tick();
        ok(f.recovery.appliedGeneration()==1&&count(f,"refresh")==1,"visible entry lost pending generation");
        f.recovery.close();
    }
    static void generationChangesDuringFinalReadiness() {
        Hooks f=new Hooks();f.setup();f.recovery.check();f.finishSpider();f.networkReady=true;f.tick();
        f.advanceOnReady=true;f.tick();f.advanceOnReady=false;
        ok(f.recovery.appliedGeneration()==0&&count(f,"refresh")==0,"superseded generation committed during final readiness callback");
        ok(count(f,"spider")==2,"latest generation not started after readiness changed it");
        f.finishSpider();f.tick();f.tick();
        ok(f.recovery.appliedGeneration()==2&&count(f,"refresh")==1,"new generation failed to recover");
        f.recovery.close();
    }
    static void boundedNetworkPoll() {
        Hooks f=new Hooks();f.setup();f.recovery.check();f.finishSpider();
        for(int i=0;i<13;i++) f.tick();
        ok(f.recovery.appliedGeneration()==1,"network recovery never applied bounded fallback");
        ok(f.events.stream().filter("refresh"::equals).count()==1,
                "fallback refresh count wrong");
        ok(!f.recovery.recovering(),"fallback left coordinator recovering");
        f.recovery.close();
    }
    static void closeDuringCheck(String phase,String forbidden){
        Hooks f=new Hooks();f.setup();f.closeAt=phase;f.closeDuring=true;
        f.recovery.check();
        ok(!f.recovery.recovering(),"close left recovery in progress: "+phase);
        if(phase.equals("generation"))ok(!f.events.contains("home"),"retired initial generation queried Home");
        if(forbidden!=null)ok(!f.events.contains(forbidden),"closed recovery still ran "+forbidden+" after "+phase);
        ok(f.spiderDone==null||phase.equals("spider"),"closed recovery started spider cleanup: "+phase);
        ok(f.scheduled==null,"closed recovery scheduled poll: "+phase);
        int count=f.events.size();f.recovery.check();ok(f.events.size()==count,"closed recovery reopened: "+phase);
    }
    static void closeDuringPoll(){
        Hooks f=new Hooks();f.setup();f.recovery.check();f.finishSpider();
        int scheduledBefore=(int) f.events.stream().filter("schedule:500"::equals).count();
        f.closeAt="ready";f.closeDuring=true;
        f.tick();
        ok(f.events.stream().filter("schedule:500"::equals).count()==scheduledBefore,
                "closed recovery still invoked schedule after networkReady callback");
        ok(f.recovery.appliedGeneration()==0,"closed networkReady committed stale generation");
        ok(f.scheduled==null,"closed recovery scheduled retry after networkReady callback");
        ok(!f.events.contains("refresh"),"closed recovery refreshed Home");
        ok(!f.recovery.recovering(),"poll close left recovery in progress");
    }
    static void closeDuringGenerationPoll(boolean finalCommit) {
        Hooks f=new Hooks();f.setup();f.recovery.check();f.finishSpider();
        f.networkReady=true;
        if (finalCommit) f.tick();
        int readyBefore=(int) f.events.stream().filter("ready"::equals).count();
        long homeBefore=count(f,"home");
        f.closeAt="generation";f.closeDuring=true;
        if (finalCommit) f.closeAtOccurrence=2; // first generation read is the poll entry
        f.tick();
        ok(f.events.stream().filter("ready"::equals).count()==readyBefore+(finalCommit?1:0),
                "networkReady crossed a retired generation gate");
        ok(count(f,"home")==homeBefore+(finalCommit?1:0),"generation callback retired owner but Home was queried");
        ok(f.scheduled==null,"closed recovery scheduled after generation callback");
        ok(!f.events.contains("refresh"),"closed recovery refreshed Home after generation callback");
        ok(!f.recovery.recovering(),"generation callback close kept recovery active");
    }
    static void closeDuringSchedule(boolean afterSpiders){
        Hooks f=new Hooks();f.setup();
        if(afterSpiders){
            f.recovery.check();f.closeAt="schedule:0";f.closeDuring=true;
            f.finishSpider();
        }else{
            f.recovery.check();f.finishSpider();
            f.closeAt="schedule:500";f.closeDuring=true;
            f.tick();
        }
        ok(f.scheduled==null,"scheduled runnable resurrected after nested close");
        ok(!f.recovery.recovering(),"close during schedule left recovering");
    }
    static void doubleClose() {
        Hooks f=new Hooks();f.setup();f.recovery.close();
        long first=f.events.stream().filter("unschedule"::equals).count();
        f.recovery.close();
        ok(first==1 && f.events.stream().filter("unschedule"::equals).count()==1,
                "close reentered external unschedule twice");
    }
    public static void main(String[] args){
        if (args.length!=0) {
            switch(args[0]) {
                case "live": slowSpiderThenLiveThenSecondWake(); break;
                case "commit": pauseBeforeCommit(); break;
                case "hidden": hiddenInitialCheck(); break;
                case "latest": generationChangesDuringFinalReadiness(); break;
                default: throw new IllegalArgumentException(args[0]);
            }
            System.out.println("PASS F1 "+args[0]+" "+tests+" assertions");
            return;
        }
        slowSpiderThenLiveThenSecondWake();
        pauseBeforeCommit();
        hiddenInitialCheck();
        generationChangesDuringFinalReadiness();
        normal();
        generationSupersedesStaleSpider();
        boundedNetworkPoll();
        duplicateSpiderCompletionKeepsStabilityDelay();
        doubleClose();
        closeDuringCheck("generation","progress");
        closeDuringCheck("home","progress");
        closeDuringCheck("unschedule","progress");
        closeDuringCheck("progress","cancel");
        closeDuringCheck("cancel","reset");
        closeDuringCheck("reset","spider");
        closeDuringPoll();
        closeDuringGenerationPoll(false);
        closeDuringGenerationPoll(true);
        closeDuringSchedule(true);
        closeDuringSchedule(false);
        ok(tests>=30,"recovery reentry assertions missing");
        System.out.println("PASS: "+tests+" owner teardown/TV network recovery lifecycle assertions with actual Java Coordinator");
    }
}
