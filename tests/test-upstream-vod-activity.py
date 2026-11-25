#!/usr/bin/env python3
"""Check the actual staged VOD host, not a rebuilt replacement player.

JVM fixtures isolate activity ownership and side requests; ordinary Web, disc
navigation and playback methods are checked against the exact upstream source.
No complete Android linkage or APK claim.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/upstream-adaptation"))
from prepare_candidate import LOCK, blob, guard_fork, overlay, verified_checkout
from verify_recovery_batch import method

MAIN = "app/src/main/java/com/fongmi/android/tv/"
LEAN = "app/src/leanback/"
VOD = LEAN+"java/com/fongmi/android/tv/ui/activity/VideoActivity.java"
BASE = MAIN+"ui/activity/PlaybackActivity.java"
DIALOG = MAIN+"ui/dialog/PlayerEngineDialog.java"
LAYOUT = LEAN+"res/layout/view_control_vod_action.xml"
NS = "{http://schemas.android.com/apk/res/android}"

JAVA = r'''
import java.util.*;
import java.util.function.*;
class OkHttpClient {}
class OkHttp { static final OkHttpClient normal=new OkHttpClient(); static OkHttpClient player(){return normal;} }
class Result { String getRealUrl(){return "https://example.invalid/video";} }
class History {}
class Episode {}
class Danmaku {}
class XraySessionListener { static final int IDLE=0, STARTING=1, RUNNING=2; }
class XrayPlaybackSession {
    int state, starts, stops, begins; String id, url; boolean supported=true, preserve;
    int state(){return state;}
    void begin(String identity){begins++;id=identity;state=0;}
    void stop(boolean value){stops++;preserve=value;state=0;}
    void mediaUrlChanged(String value){url=value;}
    boolean enable(){if(!supported)return false; starts++;state=1;return true;}
}
class R { static class string {static final int xray_vod_required=1,xray_vod_public_http_required=2;} }
class Notify { static int last; static void show(int msg){last=msg;} }
class DanmakuApi { static int cancelled=-1; static void cancel(int id){if(id>=0)cancelled=id;} }
class PlayerManager {
    boolean suspended, proxy, spec=true; int cleared, engine, selected;
    OkHttpClient client=OkHttp.normal;
    boolean isXrayPlaybackSuspended(){return suspended;}
    boolean hasXraySession(){return proxy;}
    OkHttpClient getPlaybackHttpClient(OkHttpClient fallback){return client;}
    boolean hasPlaySpec(){return spec;}
    String getUrl(){return "https://example.invalid/video";}
    void clearPreload(){cleared++;}
    void setDanmaku(Danmaku value){}
    void addDanmaku(Danmaku value){}
    void setEngine(int value){engine=value;selected++;}
}
class VodController {
    boolean current=true; int clear;
    boolean isCurrentResult(Result result){return current;}
    void clearPreloadForXray(){clear++;}
}
class VodPlaybackMedia {
    static int direct,routed; static OkHttpClient client; static BooleanSupplier callback;
    static void searchDanmaku(Result r,History h,Episode e,BooleanSupplier c,Consumer<Danmaku> s,Consumer<Danmaku> a){direct++;callback=c;}
    static int searchDanmaku(OkHttpClient k,Result r,History h,Episode e,BooleanSupplier c,Consumer<Danmaku> s,Consumer<Danmaku> a){routed++;client=k;callback=c;return 44;}
}
class PlayerSetting {
    static final int ENGINE_MPV=1;
    static boolean backgroundOff;
    static boolean isBackgroundOff(){return backgroundOff;}
}
class Input { int cancels; void cancelSeek(){cancels++;} }
class Clock { int stops; void stop(){stops++;} }
class PlaybackActivity {
    int stops;
    protected void onStop(){stops++;}
    public void onPlaybackEngineChanging(){}
}
class VodHost extends PlaybackActivity {
    boolean nativeCurrent=true, binding=true, finishing, xrayPlaybackReady;
    long mPlaybackEpoch;
    int mDanmakuRequestId=-1, historySaves;
    XrayPlaybackSession mXray=new XrayPlaybackSession();
    PlayerManager manager=new PlayerManager();
    VodController mVod=new VodController();
    Input mInput=new Input();
    Clock mClock=new Clock();
    boolean isNativePlaybackCurrent(){return nativeCurrent;}
    boolean isBindingOwner(){return binding;}
    boolean isFinishing(){return finishing;}
    boolean hasPlaybackSession(){return manager.spec;}
    PlayerManager player(){return manager;}
    void saveHistory(boolean exit){historySaves++;}
    __HOST__
    void toggle(){onXray();}
    void url(String value){onPlaybackUrlChanged(value);}
    void replaced(){onXrayBindingReplaced();}
}
class PlaybackDialog { static boolean current=true; static boolean isCurrentPlayer(Object o,PlayerManager p){return current;} }
class PlaybackAction { static int getEngine(PlayerManager p){return p.engine;} }
class RuntimeModule { static final RuntimeModule MPV=new RuntimeModule(); boolean installed=true; boolean isInstalled(){return installed;} }
class EngineHost extends PlaybackActivity {
    int changes; PlayerManager manager;
    public void onPlaybackEngineChanging(){changes++; if(manager.selected!=0)throw new AssertionError("engine changed before retirement");}
}
class DialogHost {
    final PlayerManager player=new PlayerManager(); final EngineHost activity=new EngineHost();
    int dismisses;
    DialogHost(){activity.manager=player;}
    PlaybackActivity getPlaybackActivity(){return activity;}
    void dismiss(){dismisses++;}
    __DIALOG__
    void select(int value){selectEngine(value);}
}
public class VodHarness {
    static int checks;
    static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    public static void main(String[] args) {
        VodHost h=new VodHost();
        Result r=new Result(); History hist=new History(); Episode e=new Episode();
        h.nativeCurrent=false; h.xrayPlaybackReady=true; h.toggle();
        check(h.mXray.starts==0,"retired owner cannot start");
        h.nativeCurrent=true;h.xrayPlaybackReady=false;h.toggle();
        check(Notify.last==R.string.xray_vod_required,"requires ready native playback");
        h.xrayPlaybackReady=true;h.toggle();
        check(h.mXray.starts==1 && h.mXray.state==1 && h.mVod.clear==1 && h.manager.cleared==1,"start clears preload");
        h.loadDanmaku(r,hist,e);
        check(VodPlaybackMedia.direct==0 && VodPlaybackMedia.routed==0,"starting cannot fetch direct danmaku");
        h.mXray.state=2;h.manager.proxy=true;
        h.loadDanmaku(r,hist,e);
        check(VodPlaybackMedia.routed==0,"no effective proxy no direct fallback");
        h.manager.client=new OkHttpClient();h.loadDanmaku(r,hist,e);
        check(VodPlaybackMedia.routed==1 && VodPlaybackMedia.client==h.manager.client && h.mDanmakuRequestId==44,"routed request ID");
        h.mVod.current=false;
        check(!VodPlaybackMedia.callback.getAsBoolean(),"retired result guard");
        h.mVod.current=true;h.manager.suspended=true;h.loadDanmaku(r,hist,e);
        check(VodPlaybackMedia.routed==1,"suspended cannot fetch");
        h.manager.suspended=false;h.replaced();
        check(!h.xrayPlaybackReady && h.mXray.begins==1 && DanmakuApi.cancelled==44 && h.mDanmakuRequestId==-1,"binding replacement retires");
        h.manager.proxy=false;h.nativeCurrent=false;h.loadDanmaku(r,hist,e);
        check(VodPlaybackMedia.direct==1 && !VodPlaybackMedia.callback.getAsBoolean(),"ordinary initial request before native key");
        h.nativeCurrent=true;
        check(VodPlaybackMedia.callback.getAsBoolean(),"ordinary callback after native key");
        h.binding=false;h.loadDanmaku(r,hist,e);
        check(VodPlaybackMedia.direct==1,"retired binding cannot cancel or submit danmaku");
        h.binding=true;
        h.url("https://example.invalid/redirect");
        check(h.mXray.url.endsWith("redirect") && h.mXray.begins==1,"redirect retains identity");
        h.onPlaybackEngineChanging();
        check(h.mXray.begins==2,"engine change retires identity");
        h.onStop();
        check(h.mXray.preserve && h.stops==1 && h.historySaves==1,"background preserve");
        h.nativeCurrent=false;h.onStop();
        check(!h.mXray.preserve,"retired owner cannot preserve");
        h.nativeCurrent=true;PlayerSetting.backgroundOff=true;h.onStop();
        check(!h.mXray.preserve && h.mClock.stops==1,"background disabled");
        DialogHost d=new DialogHost();PlaybackDialog.current=false;d.select(1);
        check(d.activity.changes==0 && d.player.selected==0,"stale dialog ignored");
        PlaybackDialog.current=true;RuntimeModule.MPV.installed=false;d.select(1);
        check(d.activity.changes==0,"missing MPV does not retire");
        d=new DialogHost();d.select(0);
        check(d.activity.changes==0,"same engine does not retire");
        d=new DialogHost();RuntimeModule.MPV.installed=true;d.select(1);
        check(d.activity.changes==1 && d.player.engine==1 && d.dismisses==1,"retire before real engine switch");
        System.out.println("PASS actual VOD and engine methods "+checks+" assertions");
    }
}
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-tv",type=Path,required=True)
    parser.add_argument("--tv",type=Path,required=True)
    args=parser.parse_args()
    old,tv=args.old_tv.resolve(),args.tv.resolve()
    guard_fork()
    verified_checkout(old,"old_tv")
    verified_checkout(tv,"tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-vod-host-") as tmp:
        work=Path(tmp)
        candidate=work/"candidate"
        conflicts,manual=overlay(old,tv,candidate)
        for path in (VOD,BASE,DIALOG,LAYOUT):
            row=next(x for x in LOCK["fork_scope"] if x["path"]==path)
            assert path not in conflicts+manual and blob(candidate/path)==row["resolved"],path
        vod=(candidate/VOD).read_text()
        original=(tv/VOD).read_text()
        dialog=(candidate/DIALOG).read_text()
        base=(candidate/BASE).read_text()
        assert "public void onPlaybackEngineChanging() { }" in base
        assert "mBinding.control.action.xray.setOnClickListener(view -> onXray());" in vod
        for sig in ("public void stopPlaybackForRefresh()", "protected void onPrepare()", "protected void onReclaim()", "public void onDiscMenuStateChanged(", "protected void onPreloadTransition(", "public void finish()", "protected void onWebFullscreenChanged("):
            assert method(vod,sig)==method(original,sig),sig
        start=method(vod,"public void startPlayback(")
        assert start.index("ExternalPlayback.apply(")<start.index("ExternalPlayback.takePosition(")<start.index("startWebPlayback(")<start.index("startPlayer(")
        assert start.index("resetXrayForPlaybackChange();")<start.index("startWebPlayback(")
        ended=method(vod,"protected void onPlaybackEnded()")
        assert ended.index("mXray.stop(false)")<ended.index("ExternalPlayback.returnsResult")<ended.index("mVod.playbackEnded();")
        state=method(vod,"protected void onStateChanged(")
        assert "if (isDiscMenuTransition()) hideProgress();" in state and "if (isWebPlaybackActive()) onPlaybackEnded();" in state
        assert "mVod.playbackEnded();" not in state
        assert "if (resources != null && !isNativePlaybackCurrent())" in vod
        assert "if (!isBindingOwner()) return;" in vod
        assert "clearPlaybackDanmakuSource();" in vod
        assert "mBinding.control.action.xray.setVisibility(active ? View.GONE : View.VISIBLE);" in vod
        before=ET.parse(tv/LAYOUT).getroot()
        after=ET.parse(candidate/LAYOUT).getroot()
        buttons=[x for x in after.iter() if x.get(NS+"id")=="@+id/xray"]
        assert len(buttons)==1
        for parent in after.iter():
            if buttons[0] in list(parent):
                parent.remove(buttons[0]);break
        def shape(x):return (x.tag,x.attrib,(x.text or "").strip(),[shape(v) for v in x])
        assert shape(before)==shape(after),"ordinary VOD controls changed"
        signatures=("protected void onPlaybackUrlChanged(","protected void onXrayBindingReplaced()","public void onPlaybackEngineChanging()","public void resetXrayForPlaybackChange()","private boolean isXrayStarting()","private void onXray()","public void loadDanmaku(","protected void onStop()")
        java=JAVA.replace("__HOST__","\n".join(method(vod,s) for s in signatures)).replace("__DIALOG__",method(dialog,"private void selectEngine("))
        src=work/"VodHarness.java"
        def run(source,failure=None):
            src.write_text(source)
            subprocess.run(["javac","--release","17",str(src)],check=True)
            out=subprocess.run(["java","-cp",str(work),"VodHarness"],capture_output=True,text=True)
            if failure:
                assert out.returncode!=0 and "AssertionError: "+failure in out.stderr,out.stderr
            else:
                assert out.returncode==0,out.stderr
                print(out.stdout.strip(),flush=True)
        run(java)
        for needle,replacement,label in (
            ("if (!isNativePlaybackCurrent()) return;","","retired owner cannot start"),
            (" || isXrayStarting()","", "starting cannot fetch direct danmaku"),
            ("if (client == fallback) return;","","no effective proxy no direct fallback"),
            ("activity.onPlaybackEngineChanging();","","retire before real engine switch"),
        ):
            assert java.count(needle)==1,needle
            run(java.replace(needle,replacement),label)
        print("PASS four negative controls; upstream VOD Web/disc/navigation structure retained; no full Android linkage",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review",flush=True)

if __name__=="__main__":
    main()
