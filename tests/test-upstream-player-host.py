#!/usr/bin/env python3
"""Execute exact reviewed host methods with deterministic player/Media3 boundaries."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

from sys import path as sys_path
ROOT = Path(__file__).resolve().parents[1]
sys_path.insert(0,str(ROOT/"scripts/upstream-adaptation"))
from verify_recovery_batch import method

BASE="app/src/main/java/com/fongmi/android/tv/"
LOCK={
    BASE+"player/PlayerManager.java":"6d7d4ef2082e04dfc1b7b3e1719792a14d62e3fa",
    BASE+"player/TimeshiftPlayback.java":"d027dbda1472058c732753cfeb6c5e3c6f53b0a8",
    BASE+"service/PlaybackService.java":"f996af637298e95ef4dc19b36a392b1e0aa71a61",
}
JAVA=r'''
import java.util.*;

class C { static final long TIME_UNSET=-9223372036854775807L; }
class Constant { static final long TIMEOUT_PLAY=100; }
class App { static void removeCallbacks(Runnable r){} }
class Request {}
class Call {
    interface Factory { Call newCall(Request request); }
    final OkHttpClient owner; boolean canceled;
    Call(OkHttpClient owner){this.owner=owner;}
    void cancel(){canceled=true;}
}
class OkHttpClient implements Call.Factory {
    public Call newCall(Request request){return new Call(this);}
}
class OkHttp {
    static OkHttpClient api=new OkHttpClient();
    static OkHttpClient client(){return api;}
}
class XrayHttpClient {
    final OkHttpClient http=new OkHttpClient();
    OkHttpClient client(){return http;}
}
class Player {
    long position=73; boolean live,dynamic; int released;
    boolean isCurrentMediaItemLive(){return live;}
    boolean isCurrentMediaItemDynamic(){return dynamic;}
    long getCurrentPosition(){return position;}
    void removeListener(Object listener){}
}
class PlaySpec {
    String url; int edition;
    PlaySpec(String url){this.url=url;}
    PlaySpec checkUa(){return this;}
    void setIsoEditionIndex(int index){edition=index;}
}
interface PlayerEngine {
    enum Type { EXO, MPV }
    Type getType();
    Player getPlayer();
    void release();
    default boolean needsRebuild(){return false;}
}
class ExoPlayerEngine implements PlayerEngine {
    final Player player=new Player(); final XrayHttpClient proxy;
    ExoPlayerEngine(XrayHttpClient p){proxy=p;}
    XrayHttpClient proxy(){return proxy;}
    public Type getType(){return Type.EXO;}
    public Player getPlayer(){return player;}
    public void release(){player.released++;}
}
class MpvEngine implements PlayerEngine {
    final Player player=new Player();
    public Type getType(){return Type.MPV;}
    public Player getPlayer(){return player;}
    public void release(){player.released++;}
}
class PlayerEngineFactory {
    static boolean mpv;
    static PlayerEngine create(Object listener){return mpv?new MpvEngine():new ExoPlayerEngine(null);}
    static PlayerEngine create(PlaySpec spec,Object listener){return create(listener);}
    static PlayerEngine create(PlayerEngine.Type type,Object listener){return type==PlayerEngine.Type.MPV?new MpvEngine():new ExoPlayerEngine(null);}
    static PlayerEngine create(PlaySpec spec,XrayHttpClient proxy,Object listener){return proxy==null?create(spec,listener):new ExoPlayerEngine(proxy);}
    static boolean matches(PlayerEngine engine,PlaySpec spec,XrayHttpClient proxy){
        if(proxy!=null)return engine instanceof ExoPlayerEngine exo&&exo.proxy()==proxy&&!engine.needsRebuild();
        return !(engine instanceof ExoPlayerEngine exo&&exo.proxy()!=null)&&engine.getType()==(mpv?PlayerEngine.Type.MPV:PlayerEngine.Type.EXO)&&!engine.needsRebuild();
    }
}
class Clock { static final Clock DEFAULT=new Clock(); }
class SettableFuture<T> {
    boolean canceled,done;
    void cancel(boolean interrupt){canceled=true;}
    void set(T value){done=true;}
}
class Result {
    boolean hasMsg(){return false;}
    String getRealUrl(){return "https://media.example/replay";}
    String getFormat(){return "hls";}
    Map<String,String> getHeader(){return Map.of();}
    Url getUrl(){return new Url();}
    String getMsg(){return "";}
}
class Url { String v(){return "https://media.example/browse";} }
class TimeshiftPlayback {
    final PlayerManager owner; final Call.Factory requests;
    Call call; SettableFuture<Void> pending;
    boolean active,replaying; int restarts;
    long epochOffset=C.TIME_UNSET;
    TimeshiftPlayback(PlayerManager owner,Call.Factory requests,Clock clock){this.owner=owner;this.requests=requests;}
    boolean isActive(){return active;}
    boolean isReplaying(){return active&&replaying;}
    void onSourceRestart(){restarts++;}
    void deliver(SettableFuture<Void> f){apply(f,new Result(),123);}
    void startRequest(){call=requests.newCall(new Request());pending=new SettableFuture<>();}
    __TIMESHIFT__
}
class PlayerManager {
    PlaySpec spec; Player player; PlayerEngine engine;
    XrayHttpClient playbackProxy; XrayRestore xrayRestore; long xrayTransition;
    long pendingStartPositionMs=C.TIME_UNSET;
    boolean mpvDrmExoFallback;
    final TimeshiftPlayback timeshift;
    final Object listener=new Object(); final Runnable runnable=()->{};
    final List<String> log=new ArrayList<>();
    final Callback callback=new Callback();
    int starts, clears, applies, errors;
    long positionStarted;
    XrayHttpClient routeStarted;
    boolean failBrowse;
    PlayerManager(){engine=PlayerEngineFactory.create(listener);player=engine.getPlayer();timeshift=new TimeshiftPlayback(this);}
    boolean isReleased(){return player==null;}
    boolean isEmpty(){return spec==null||spec.url==null||spec.url.isEmpty();}
    void clearPreload(){clears++;}
    void ensureForTest(){ensureEngine(spec);}
    void setPlayer(Player p){player=p;callback.onPlayerRebuild(p);}
    void setMediaItem(long timeout,long pos,boolean newMedia){if(isXrayPlaybackSuspended())throw new AssertionError("suspended start");ensureEngine(spec);starts++;positionStarted=pos;routeStarted=playbackProxy;}
    void startCurrent(long pos){if(timeshift.isActive()) {timeshift.startRequest();starts++;positionStarted=pos;routeStarted=playbackProxy;}else setMediaItem(Constant.TIMEOUT_PLAY,pos,false);}
    void applyTimeshift(String url,String format,Map<String,String> headers){applies++;spec.url=url;setMediaItem(Constant.TIMEOUT_PLAY,0,false);}
    void onTimeshiftError(){errors++;}
    boolean browse(Result result,String key,Object metadata,long pos){
        log.add("browse"); if(hasXraySession())throw new AssertionError("old proxy reached new browse");
        clear(); spec=new PlaySpec(result.getRealUrl()); return !failBrowse;
    }
    class Callback {
        Runnable transition=()->{},rebuild=()->{};
        void onXrayTransitionStarted(){log.add("cancel");transition.run();}
        void onPlayerRebuild(Player player){rebuild.run();}
    }
    record PlaybackSnapshot(long positionMs,int selectedIsoEditionIndex) {
        static PlaybackSnapshot capture(PlayerManager p){return new PlaybackSnapshot(p.player.position,5);}
        void restorePlayerState(PlayerManager p){p.player.position=positionMs;}
    }
    __MANAGER__
}
class MediaItem { String mediaId="new";Object mediaMetadata=new Object();}
class BrowsePlayback { static BrowsePlayback from(MediaItem item){return new BrowsePlayback();}Result getResult(){return new Result();}void activate(long pos){} }
class Source {static boolean isPush(String url){return false;}}
class SessionError {static final int ERROR_UNKNOWN=0;SessionError(int code,String message){}}
class Service {
    record ActivityBinding(Runnable onReplaced){}
    ActivityBinding binding;
    PlayerManager player;
    BrowsePlayback browsePlayback;
    Service(PlayerManager player){this.player=player;}
    final Session session=new Session();final LiveMetadata liveMetadata=new LiveMetadata();
    class Session {void sendError(SessionError e){}}
    class LiveMetadata {void refresh(){}}
    void cancelNavigation(){}
    void redirectPush(String url){}
    void setNavigationCallback(Object a,Object b){}
    void resetSessionActivity(){}
    boolean browse(){return setBrowseItem(new MediaItem(),0);}
    __SERVICE__
}
public class PlayerHostTest {
    static int count;
    static void check(boolean value,String msg){count++;if(!value)throw new AssertionError(msg);}
    static PlayerManager manager(){PlayerManagerFactoryReset();PlayerManager p=new PlayerManager();p.spec=new PlaySpec("https://media.example/a");return p;}
    static void PlayerManagerFactoryReset(){PlayerEngineFactory.mpv=false;}
    public static void main(String[] args){
        PlayerManager p=manager();
        PlayerManager a=p;
        XrayHttpClient x=new XrayHttpClient(), y=new XrayHttpClient();
        Player original=p.player;
        p.callback.transition=()->check(!a.hasXraySession(),"cancel direct before install");
        p.setPlaybackProxy(x,true);
        check(p.hasXraySession()&&p.getPlaybackHttpClient(OkHttp.client())==x.client(),"selected transport");
        check(original.released==1&&p.starts==1&&p.positionStarted==73&&p.routeStarted==x&&p.spec.edition==5,"snapshot and old release");
        p.callback.transition=()->check(a.getPlaybackHttpClient(OkHttp.client())==x.client(),"cancel old before detach");
        p.timeshift.startRequest(); Call call=p.timeshift.call; SettableFuture<Void> future=p.timeshift.pending;
        check(call.owner==x.client(),"timeshift proxy");
        Player old=p.player;
        p.clearPlaybackProxyPreservingState();
        check(old.released==1&&!p.hasXraySession()&&p.isXrayPlaybackSuspended()&&p.starts==1,"error suspends without direct restart");
        check(call.canceled&&future.canceled,"retired timeshift call and future");
        p.timeshift.deliver(future);check(p.applies==0,"late timeshift result ignored");
        p.callback.transition=()->{};
        p.setPlaybackProxy(null,false);check(p.isXrayPlaybackSuspended(),"late IDLE preserves saved restore");
        p.setPlaybackProxy(y,true);check(p.routeStarted==y&&p.positionStarted==73&&p.starts==2&&!p.isXrayPlaybackSuspended(),"retry restores saved snapshot");
        p.clear();Player retired=p.player;
        p.setPlaybackProxy(null,false);check(retired.released==1&&!p.hasXraySession()&&p.starts==2,"empty-spec detach releases engine without replay");
        p.setPlaybackProxy(x,false);check(p.hasXraySession()&&p.starts==2&&p.getPlaybackHttpClient(OkHttp.client())==x.client(),"pending proxy retained");
        p.setPlaybackProxy(null,false);check(!p.hasXraySession(),"pending proxy removed");
        p.timeshift.startRequest();Call first=p.timeshift.call;
        OkHttp.api=new OkHttpClient();p.timeshift.startRequest();check(first.owner!=p.timeshift.call.owner&&p.timeshift.call.owner==OkHttp.client(),"wake uses new API client");
        p=manager();p.timeshift.active=true;p.timeshift.replaying=true;p.player.position=97;
        p.setPlaybackProxy(x,true);check(p.positionStarted==97&&p.timeshift.restarts==1,"same-engine timeshift raw position");
        p=manager();PlayerEngineFactory.mpv=true;p.engine=PlayerEngineFactory.create(p.listener);p.player=p.engine.getPlayer();p.player.live=true;p.player.dynamic=true;
        p.setPlaybackProxy(x,true);check(p.positionStarted==C.TIME_UNSET,"dynamic live type change restarts at live edge");
        p.mpvDrmExoFallback=true;p.ensureForTest();check(p.getPlaybackHttpClient(OkHttp.client())==x.client(),"MPV DRM fallback cannot bypass active Xray");
        p.setPlaybackProxy(null,true);check(!p.hasXraySession()&&p.engine.getType()==PlayerEngine.Type.EXO,"direct DRM fallback retained");
        p=manager();PlayerManager b=p;p.callback.transition=()->b.clear();
        p.setPlaybackProxy(x,true);check(!p.hasXraySession()&&p.starts==0&&p.spec==null,"retired identity stops outer transition");
        p=manager();PlayerManager c=p;Player displaced=p.player;
        p.callback.rebuild=()->{c.callback.rebuild=()->{};c.setPlaybackProxy(null,false);};
        p.setPlaybackProxy(x,true);check(!p.hasXraySession()&&p.starts==0&&displaced.released==1,"reentrant detach rejects outer start and releases old");
        p=manager();Player failed=p.player;p.callback.rebuild=()->{throw new IllegalStateException("fixture");};
        try{p.setPlaybackProxy(x,true);throw new AssertionError("missing callback error");}catch(IllegalStateException expected){}
        check(failed.released==1,"old engine released even if rebuild callback throws");
        p=manager();p.setPlaybackProxy(x,false);p.log.clear();Service service=new Service(p);PlayerManager d=p;
        service.binding=new Service.ActivityBinding(()->{d.log.add("retire");d.setPlaybackProxy(null,false);});
        check(service.browse()&&d.log.indexOf("retire")<d.log.indexOf("browse")&&!d.hasXraySession(),"remote browse retires Xray owner before prepare");
        p=manager();Service direct=new Service(p);PlayerManager e=p;direct.binding=new Service.ActivityBinding(()->e.log.add("retire"));
        check(direct.browse()&&e.log.equals(List.of("browse","retire")),"normal browse retains upstream order");
        System.out.println("PASS actual 5.9 extracted playback host methods: "+count+" assertions");
    }
}
'''

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate",type=Path,required=True)
    candidate=parser.parse_args().candidate
    src=[]
    for path,digest in LOCK.items():
        data=(candidate/path).read_bytes()
        assert blob(data)==digest,path
        src.append(data.decode())
    manager,timeshift,service=src
    def methods(source,sigs):
        return "\n".join(method(source,sig) for sig in sigs)
    manager_methods=methods(manager,(
        "public void clear()", "private void ensureEngine(PlaySpec spec)",
        "private void replaceEngine(PlayerEngine replacement)", "private boolean engineHasProxy()",
        "private void reconcileProxyEngine()", "private XrayRestore captureXrayRestore()",
        "private boolean ownsXrayTransition(", "public synchronized void setPlaybackProxy(",
        "public synchronized void clearPlaybackProxyPreservingState()","public synchronized boolean hasXraySession()",
        "public synchronized boolean isXrayPlaybackSuspended()","public synchronized OkHttpClient getPlaybackHttpClient(",
        "private void restartMedia(", "private record XrayRestore(",
    ))
    timeshift_methods=methods(timeshift,("TimeshiftPlayback(PlayerManager owner)","void cancelForPlaybackTransition()",
        "private void cancel()", "private void apply(SettableFuture<Void>", "private void fail(SettableFuture<Void>"))
    service_methods=methods(service,("private boolean setBrowseItem(",))
    assert "if (owner.isXrayPlaybackSuspended()) return" in method(timeshift,"public ListenableFuture<?> seekTo(")
    assert "if (isXrayPlaybackSuspended() || spec == null" in method(manager,"private void setMediaItem(")
    assert "callback.onPlaybackUrlChanged(spec.getUrl());" in method(manager,"private void startMediaItem(")
    assert "!hasXraySession() && !isXrayPlaybackSuspended()" in method(manager,"public boolean canPreloadNext()")
    for token in ("DanmakuApi.cancelForXrayTransition();","SubtitleApi.cancelForXrayTransition();","xrayBitmapLoader.cancelRemoteLoads();"):
        assert token in method(service,"public void onXrayTransitionStarted()")
    java=JAVA.replace("__MANAGER__",manager_methods).replace("__TIMESHIFT__",timeshift_methods).replace("__SERVICE__",service_methods)
    def run(text,success):
        with tempfile.TemporaryDirectory(prefix="fingmi-590-player-host-") as d:
            root=Path(d)
            file=root/"PlayerHostTest.java"
            file.write_text(text,encoding="utf-8")
            subprocess.run(["javac","--release","17","-d",str(root),str(file)],check=True)
            r=subprocess.run(["java","-cp",str(root),"PlayerHostTest"],capture_output=True,text=True,timeout=20)
            if success:
                assert r.returncode==0,r.stdout+r.stderr
                print(r.stdout.strip())
            else:
                assert r.returncode!=0 and "AssertionError" in r.stderr,r.stdout+r.stderr
    run(java,True)
    for a,b in (
        ("timeshift.cancelForPlaybackTransition();",""),
        ("if (!ownsXrayTransition(transition, expected) || resume == null || isEmpty()) return;","if (resume == null || isEmpty()) return;"),
        ("request -> owner.getPlaybackHttpClient(OkHttp.client()).newCall(request)","OkHttp.client()"),
        ("if (next != null || hasXraySession()) callback.onXrayTransitionStarted();",""),
        ("if (retireProxy) {","if (false) {"),
    ):
        assert a in java,a
        run(java.replace(a,b),False)
    print("PASS 5 negative controls; source bodies executed with deterministic engine and UI boundaries, no complete app linkage")


if __name__=="__main__":
    main()
