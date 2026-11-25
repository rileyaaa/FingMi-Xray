#!/usr/bin/env python3
"""Exercise actual staged Live Activity ownership with the real auto policy.

Deterministic JVM boundary for Android/PlayerManager/Xray service. Native and
Web navigation structure is preserved; this is not full Android linkage.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/upstream-adaptation"))
from prepare_candidate import LOCK,blob,guard_fork,overlay,verified_checkout
from verify_recovery_batch import method

LIVE="app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java"
AUTO="xray/src/main/java/com/fingmi/xray/session/XrayLiveAutoPlayback.java"

JAVA=r'''
import java.util.*;
class OkHttpClient {}
class OkHttp {
    static final OkHttpClient NORMAL=new OkHttpClient();
    static OkHttpClient player(){return NORMAL;}
    static OkHttpClient client(){return NORMAL;}
    static void cancel(OkHttpClient c,String tag){}
}
class LiveApi {static final String METADATA_TAG="metadata";}
class XrayHttpClient {final OkHttpClient client=new OkHttpClient();}
interface XraySessionListener {int IDLE=0,STARTING=1,RUNNING=2,ERROR=3;}
class XrayPlaybackSession {
    interface Listener {void onProxyChanged(XrayHttpClient resources,boolean preserve);void onProxyError();void onStateChanged(int state,String message);}
    final Listener listener;
    int state,starts,stops,retained,begins;boolean preserve;String id,url;
    XrayHttpClient res;
    XrayPlaybackSession(Object o,OkHttpClient c,Listener l){listener=l;}
    int state(){return state;}
    XrayHttpClient resources(){return res;}
    OkHttpClient client(OkHttpClient fallback){return res==null?fallback:res.client;}
    boolean isActive(){return state==RUNNING();}
    static int RUNNING(){return XraySessionListener.RUNNING;}
    static boolean supportsDirectLiveSource(String s){return s!=null && s.startsWith("https://");}
    void begin(String key){begins++;id=key;stop(false);}
    void beginLiveAuto(String key,boolean retain){begins++;id=key;if(retain && (isActive()||state==1)){retained++;return;}stop(false);}
    void mediaUrlChanged(String value){url=value;}
    boolean enableForResolvedLive(){if(!supportsDirectLiveSource(url))return false;starts++;state=1;return true;}
    void stop(boolean value){stops++;preserve=value;state=0;boolean detach=res!=null;res=null;if(detach)listener.onProxyChanged(null,value);listener.onStateChanged(0,"");}
    void running(){state=2;res=new XrayHttpClient();listener.onProxyChanged(res,false);if(state==2)listener.onStateChanged(2,"");}
}
__AUTO__
class Group {String getName(){return "group";}}
class Channel {
    final String name;final boolean matched;
    Channel(String n,boolean m){name=n;matched=m;}
    Group getGroup(){return new Group();}
    String getName(){return name;}
    String getShow(){return name;}
    List<Object> getDataList(){return List.of();}
    void loadLogo(Object o){}
}
class LivePlayRequest {
    final Channel channel;final boolean catchup;
    LivePlayRequest(Channel c,boolean b){channel=c;catchup=b;}
    Channel getChannel(){return channel;}
    boolean isCatchup(){return catchup;}
}
class Result {final String url;Result(String u){url=u;}String getRealUrl(){return url;}}
class MediaMetadata {}
class Home {int getTimeout(){return 10;} List<String> getEpgXml(){return List.of("https://epg.invalid/xml");}}
class PlayerManager {
    XrayHttpClient proxy;int resets,installs,clears;boolean spec=true;
    void reset(){resets++;}
    boolean hasPlaySpec(){return spec;}
    void setPlaybackProxy(XrayHttpClient p,boolean preserve){proxy=p;if(p!=null)installs++;}
    void clearPlaybackProxyPreservingState(){proxy=null;clears++;}
    OkHttpClient getPlaybackHttpClient(OkHttpClient c){return proxy==null?c:proxy.client;}
}
class Service {int transitions;void onXrayTransitionStarted(){transitions++;}}
class LiveViewModel {
    int metadataCancels,urlCancels,epgs,xmls;OkHttpClient client;
    void cancelPlaybackMetadata(){metadataCancels++;}
    void cancelPlaybackUrl(){urlCancels++;}
    void parseXml(Home h,OkHttpClient c){xmls++;client=c;}
    void getEpg(Channel h,OkHttpClient c){epgs++;client=c;}
}
class LiveController {int refreshes,retired,resumes;void refresh(){refreshes++;}void retirePendingPlayback(){retired++;}void resumeChannelAfterXrayStart(){resumes++;}}
class ChannelAdapter {boolean suppressed;void setXrayLogoSuppressed(boolean b){suppressed=b;}}
class Button {boolean selected;int text;void setSelected(boolean b){selected=b;}void setText(int r){text=r;}}
class Actions {Button xray=new Button();}
class Control {Actions action=new Actions();}
class Binding {Control control=new Control();}
class R {static class string {static final int xray_on=1,xray_starting=2,xray_error=3,xray_off=4;}}
class Notify {static void show(String msg){}}
class Input {int cancels;void cancelSeek(){cancels++;}}
class Clock {int stops,starts;Clock stop(){stops++;return this;}Clock start(){starts++;return this;}}
class PlayerSetting {static boolean backgroundOff;static boolean isBackgroundOff(){return backgroundOff;}}
class Base {
    boolean binding=true,nativeCurrent=false,web=false,finishing=false,destroyed=false;int resumes,stops,starts;
    protected void onResume(){binding=true;resumes++;}
    protected void onStart(){starts++;}
    protected void onStop(){stops++;}
}
class Host extends Base {
    XrayPlaybackSession mXray;
    final XrayLiveAutoPlayback mLiveAuto=new XrayLiveAutoPlayback();
    boolean mXrayPendingChannelResume,mXrayStartedFromExistingPlayback,mXrayRefreshMetadataOnDetach,mXrayAutoReclaimPending;
    long mPlaybackEpoch;
    final Binding mBinding=new Binding();final PlayerManager manager=new PlayerManager();
    final Service svc=new Service(); final LiveViewModel mViewModel=new LiveViewModel();
    final LiveController mLive=new LiveController();final ChannelAdapter mChannelAdapter=new ChannelAdapter();
    final Input mInput=new Input();final Clock mClock=new Clock();
    final Home home=new Home(); Channel mChannel;String mPlaybackKey;
    int nativeStarts,webStarts,clearSources,clientUpdates,suppressions,restores,artworks;
    boolean lastNativeProxy,widgetSuppressed;
    Host(){initXray();}
    void initXray(){__INIT__}
    boolean isBindingOwner(){return binding;}
    boolean isNativePlaybackCurrent(){return binding && nativeCurrent && !web;}
    boolean isFinishing(){return finishing;} boolean isDestroyed(){return destroyed;}
    boolean isWebPlayback(Result result){return result.url.startsWith("web:");}
    boolean startWebPlayback(Result r){if(!isWebPlayback(r)){web=false;return false;}web=true;nativeCurrent=false;webStarts++;return true;}
    void startPlayer(String k,Result r,boolean p,int timeout,long position,MediaMetadata m){nativeStarts++;lastNativeProxy=manager.proxy!=null;nativeCurrent=true;}
    Home getHome(){return home;}PlayerManager player(){return manager;}Service service(){return svc;}
    boolean matchesAutoXray(Channel c){return c.matched;}
    void clearPlaybackDanmakuSource(){clearSources++;}
    void updatePlaybackDanmakuClient(){clientUpdates++;}
    void setWidgetLogoSuppressed(boolean b){widgetSuppressed=b;}
    void setArtwork(){artworks++;}
    void suppressAutoXrayArtwork(){suppressions++;mChannelAdapter.setXrayLogoSuppressed(true);setWidgetLogoSuppressed(true);}
    void restoreAutoXrayMetadata(){restores++;mChannelAdapter.setXrayLogoSuppressed(false);setWidgetLogoSuppressed(false);refreshXrayAwareMetadata();}
    void showError(String m){}
    __HOST__
    void replaceBinding(){onXrayBindingReplaced();binding=false;}
    void reclaim(){onReclaim();}
    void stopHost(){onStop();}
    void startHost(){onStart();}
    void resumeHost(){onResume();}
}
public class LiveHarness {
    static int checks;
    static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
    static void select(Host h,Channel c,boolean catchup){h.mChannel=c;h.prepareXrayForPlaybackChange(new LivePlayRequest(c,catchup));}
    static void play(Host h,String url){h.startPlayback(new Result(url),10,new MediaMetadata());}
    public static void main(String[] args){
        Host h=new Host();
        Channel ordinary=new Channel("ordinary",false), a=new Channel("a",true), b=new Channel("b",true);
        select(h,ordinary,false);play(h,"https://ordinary.invalid/live");
        check(h.nativeStarts==1 && !h.lastNativeProxy && h.mXray.starts==0,"ordinary upstream native");
        select(h,a,false);
        check(h.mChannelAdapter.suppressed && h.isPlaybackStartPending(),"suppress new auto station");
        play(h,"https://a.invalid/live");
        check(h.nativeStarts==1 && h.mXray.starts==1 && h.isPlaybackStartPending(),"wait for Core START");
        h.mXray.running();
        check(h.nativeStarts==2 && h.lastNativeProxy && h.manager.installs==1,"install proxy before held media");
        check(h.mViewModel.client==h.manager.proxy.client,"metadata uses proxy");
        int oldStarts=h.mXray.starts;
        select(h,b,false);
        check(h.mXray.retained==1 && h.svc.transitions==1 && h.isPlaybackStartPending(),"retained transport retires old station");
        play(h,"https://b.invalid/live");
        check(h.nativeStarts==3 && h.lastNativeProxy && h.mXray.starts==oldStarts,"matching next station retains Core");
        select(h,a,false);play(h,"web:https://web.invalid/live");
        check(h.webStarts==1 && h.nativeStarts==3 && !h.mLiveAuto.isAutomatic() && h.manager.proxy==null,"web never uses native Xray");
        check(h.mPlaybackKey.startsWith("web:"),"upstream web playback key");
        select(h,a,true);play(h,"https://catchup.invalid/live");
        check(!h.mLiveAuto.isAutomatic() && !h.lastNativeProxy && h.nativeStarts==4,"catchup not auto-routed");
        select(h,a,false);play(h,"https://pending.invalid/live");
        int started=h.nativeStarts;
        h.reclaim();
        check(h.mLive.refreshes==0,"reclaim does not replace pending auto");
        h.replaceBinding();
        check(h.mLive.retired==1 && h.mViewModel.urlCancels==1 && !h.mLiveAuto.isAwaitingPlayback(),"handoff retires pending URL");
        h.mXray.running();
        check(h.nativeStarts==started && h.manager.proxy==null,"late Core cannot install for retired owner");
        play(h,"https://stale.invalid/live");
        check(h.nativeStarts==started,"stale resolver cannot start");
        h.resumeHost();
        check(h.mLive.refreshes==1 && !h.mXrayAutoReclaimPending,"reclaim refreshes once after binding");
        Host sleep=new Host();
        select(sleep,a,false);play(sleep,"https://sleep.invalid/live");
        int before=sleep.mXray.starts;
        sleep.stopHost();
        check(sleep.mLiveAuto.isAwaitingPlayback() && sleep.mXray.state()==0 && !sleep.mXray.preserve,"standby keeps unfinished identity not Core");
        sleep.binding=false;sleep.startHost();
        check(sleep.mXray.starts==before,"no START before owner reclaimed");
        sleep.resumeHost();
        check(sleep.mXray.starts==before+1 && sleep.nativeStarts==0,"resume starts pending Core only");
        sleep.mXray.running();
        check(sleep.nativeStarts==1 && sleep.lastNativeProxy,"resumed media starts through proxy");
        sleep.stopHost();
        check(sleep.mXray.preserve && !sleep.mLiveAuto.isAwaitingPlayback(),"existing background playback preserved without Core");
        Host switcher=new Host();
        select(switcher,a,false);play(switcher,"https://engine.invalid/live");
        switcher.onPlaybackEngineChanging();
        check(!switcher.mLiveAuto.isAutomatic() && switcher.mLive.resumes==1,"engine switch retires resolved pending and requests fresh media");
        System.out.println("PASS actual Live host and automatic policy "+checks+" assertions");
    }
}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-tv",type=Path,required=True)
    p.add_argument("--tv",type=Path,required=True)
    a=p.parse_args()
    old,tv=a.old_tv.resolve(),a.tv.resolve()
    guard_fork();verified_checkout(old,"old_tv");verified_checkout(tv,"tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-live-host-") as tmp:
        work=Path(tmp);candidate=work/"candidate"
        conflicts,manual=overlay(old,tv,candidate)
        row=next(x for x in LOCK["fork_scope"] if x["path"]==LIVE)
        assert LIVE not in conflicts+manual and blob(candidate/LIVE)==row["resolved"]
        live=(candidate/LIVE).read_text();original=(tv/LIVE).read_text()
        for sig in ("private void onPlayer()","private void checkPlay()","private void onPaused()","private void onPlay()","public void preparePlaybackForRefresh()","public void stopPlaybackForRefresh()","private boolean startWebPlayback(Result result)","protected void onStateChanged(","protected void onPlaybackEnded()","private void setGroup("):
            assert method(live,sig)==method(original,sig),sig
        assert "mBinding.control.action.xray.setVisibility(active ? View.GONE : View.VISIBLE);" in live
        assert "if (isBindingOwner() && isOwner()) Source.get().exit();" in method(live,"protected void onDestroy()")
        init=method(live,"protected void initView(")
        init=init[init.index("        mXray ="):init.index("        mClock =")]
        auto=(candidate/AUTO).read_text()
        auto=auto[auto.index("public final class XrayLiveAutoPlayback"):].replace("public final class","final class",1)
        signatures=("public void prepareXrayForPlaybackChange(","public void startPlayback(","private void startResolvedLive(","private String liveGroupName(","private boolean isAutoXrayWaiting()","public boolean isPlaybackStartPending()","private boolean hasNativePlaybackSession()","private OkHttpClient xrayMetadataClient()","private void refreshXrayAwareMetadata()","private void cancelXrayMetadataRequests()","public void resetXrayForPlaybackChange()","protected void onXrayBindingReplaced()","private void resumeRetiredAutoRequest()","protected void onReclaim()","protected void onStart()","protected void onResume()","protected void onStop()","public void onPlaybackEngineChanging()","private void resetXrayForEngineChange()")
        java=JAVA.replace("__AUTO__",auto).replace("__INIT__",init).replace("__HOST__","\n".join(method(live,s) for s in signatures))
        src=work/"LiveHarness.java"
        def run(code,failure=None):
            src.write_text(code)
            subprocess.run(["javac","--release","17",str(src)],check=True)
            out=subprocess.run(["java","-cp",str(work),"LiveHarness"],capture_output=True,text=True)
            if failure:
                assert out.returncode!=0 and "AssertionError: "+failure in out.stderr,out.stderr
            else:
                assert out.returncode==0,out.stderr
                print(out.stdout.strip(),flush=True)
        run(java)
        for before,after,fail in (
            ("if (mLiveAuto.deferResolved(mXray, url, () -> startResolvedLive(result, position, metadata))) return;","","wait for Core START"),
            ("if (isBindingOwner() && mLiveAuto.isAwaitingPlayback()) return;","","reclaim does not replace pending auto"),
            ("mLiveAuto.suspend(!isFinishing() && isBindingOwner() && !hasNativePlaybackSession());","mLiveAuto.suspend(false);","standby keeps unfinished identity not Core"),
            ("if (isBindingOwner()) mLiveAuto.resume(mXray);\n        mClock.stop().start();","mLiveAuto.resume(mXray);\n        mClock.stop().start();","no START before owner reclaimed")
        ):
            assert java.count(before)==1,before
            run(java.replace(before,after),fail)
        print("PASS four Live negative controls; ordinary Web/native/seek/end structure retained; no full Android linkage",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review",flush=True)

if __name__=="__main__":
    main()
