#!/usr/bin/env python3
"""Actual 5.9 Live controller/host contracts, with deterministic boundary doubles."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

LIVE = 'app/src/main/java/com/fongmi/android/tv/playback/live/'
INPUTS = {
    'LivePlaybackController.java': 'c7f79c6e44f664b138ff19d20133d884e116cad0',
    'LivePlaybackHost.java': 'b8774f566e9ad4f430ccac68e3b7e48feadab6ad',
    'LivePlayRequest.java': 'f8b158f2dc7fbf16c45ef123ca6782c622e99417',
    'LivePlaybackState.java': '03c4c2cdc603f9f220447864b760dc9191505b05',
    'LiveDataSource.java': '0b6ba0d3527b4fc398e432f2b1c347657ce982f5',
    'PlaybackResult.java': '915a5a2c2fa32f293ed7d4d7635692b804252995',
}
STUBS = {
    'android/text/TextUtils.java': 'package android.text; public class TextUtils { public static boolean isEmpty(String s){return s==null||s.isEmpty();}}',
    'androidx/annotation/Nullable.java': 'package androidx.annotation; public @interface Nullable {}',
    'androidx/annotation/NonNull.java': 'package androidx.annotation; public @interface NonNull {}',
    'androidx/media3/common/C.java': 'package androidx.media3.common; public class C { public static final long TIME_UNSET=-9223372036854775807L; }',
    'androidx/media3/common/MediaMetadata.java': '''package androidx.media3.common; public class MediaMetadata {
      public static final int MEDIA_TYPE_VIDEO=1, MEDIA_TYPE_TV_CHANNEL=2; public final int type;
      public MediaMetadata(){this(0);} public MediaMetadata(int t){type=t;}
      public Builder buildUpon(){return new Builder();} public static class Builder {
        private int t; public Builder setMediaType(int v){t=v; return this;} public MediaMetadata build(){return new MediaMetadata(t);}}
    }''',
    'com/fongmi/android/tv/R.java': 'package com.fongmi.android.tv; public class R { public static class string { public static int error_play_url=1; }}',
    'com/fongmi/android/tv/api/config/LiveConfig.java': 'package com.fongmi.android.tv.api.config; import com.fongmi.android.tv.bean.Channel; public class LiveConfig { public static LiveConfig get(){return new LiveConfig();} public void setKeep(Channel c){} }',
    'com/fongmi/android/tv/bean/Channel.java': '''package com.fongmi.android.tv.bean; import java.time.ZoneId; public class Channel {
      private int index; public int getIndex(){return index;} public Group getGroup(){return null;}
      public boolean isOnly(){return false;} public boolean isLast(){return false;} public void switchLine(boolean next){index++;}
      public boolean hasCatchup(){return true;} public boolean isRtsp(){return false;}
      public String getShow(){return "channel";} public String getLogo(){return "";} public Epg getData(ZoneId z){return new Epg();}}''',
    'com/fongmi/android/tv/bean/Group.java': '''package com.fongmi.android.tv.bean; import java.util.*; public class Group {
      public String getName(){return "group";} public boolean isEmpty(){return true;} public List<Channel> getChannel(){return List.of();}
      public int getPosition(){return 0;} public void setPosition(int p){} public boolean skip(){return false;} public Channel current(){return null;}}''',
    'com/fongmi/android/tv/bean/EpgData.java': 'package com.fongmi.android.tv.bean; public class EpgData { public boolean isSelected(){return true;} }',
    'com/fongmi/android/tv/bean/Epg.java': 'package com.fongmi.android.tv.bean; import java.util.*; public class Epg { public int getInRange(){return 0;} public int getSelected(){return -1;} public List<EpgData> getList(){return List.of();} public Epg selected(){return this;} }',
    'com/fongmi/android/tv/bean/Result.java': '''package com.fongmi.android.tv.bean; public class Result {
      private final String url; public Result(String u){url=u;} public boolean hasMsg(){return false;} public String getMsg(){return "";}
      public String getRealUrl(){return url;} public boolean hasPosition(){return false;} public long getPosition(){return 0;}
      public Url getUrl(){return new Url(url);} public record Url(String v){} }''',
    'com/fongmi/android/tv/player/extractor/Source.java': 'package com.fongmi.android.tv.player.extractor; public class Source { public static boolean isPush(String u){return u.startsWith("push://");} }',
    'com/fongmi/android/tv/player/media/MediaItemFactory.java': 'package com.fongmi.android.tv.player.media; import androidx.media3.common.MediaMetadata; import com.fongmi.android.tv.bean.EpgData; public class MediaItemFactory { public static MediaMetadata buildLiveMetadata(String t,EpgData d,String l){return new MediaMetadata();} }',
    'com/fongmi/android/tv/setting/LiveSetting.java': 'package com.fongmi.android.tv.setting; public class LiveSetting { public static boolean isAcross(){return false;} public static boolean isChange(){return false;} }',
    'com/fongmi/android/tv/utils/ResUtil.java': 'package com.fongmi.android.tv.utils; public class ResUtil { public static String getString(int i){return "error";} }',
}
HARNESS = '''package com.fongmi.android.tv.playback.live;
import java.util.*;
import java.time.ZoneId;
import androidx.media3.common.*;
import com.fongmi.android.tv.bean.*;
import com.fongmi.android.tv.playback.PlaybackResult;
public class LiveHostHarness {
    static int assertions;
    static void check(boolean b,String name){ assertions++; if(!b) throw new AssertionError(name); }
    static class Host implements LivePlaybackHost {
        int prepared, stopped, started, errors, metadata, pushes;
        boolean hasSession, ready=true; String restored, pushed; long pos=C.TIME_UNSET;
        public int getGroupCount(){return 0;} public int getGroupPosition(){return 0;} public Group getGroup(int i){return null;}
        public boolean isPlayerLive(){return false;} public boolean hasPlaybackSession(){return hasSession;}
        public boolean isPlaybackServiceReady(){return ready;} public void restorePlaybackKey(String key){restored=key;}
        public long getPlayerPosition(){return pos;} public ZoneId getZoneId(){return ZoneId.of("UTC");}
        public void onCatchupRequested(){} public void preparePlaybackForRefresh(){prepared++;} public void stopPlaybackForRefresh(){stopped++;}
        public void openPush(String t){pushes++;pushed=t;} public void startPlayback(Result r,long p,MediaMetadata m){started++;}
        public void resetPlaybackForError(String msg){errors++;} public void renderGroupSelection(Group g){} public void renderGroupChannels(Group g){}
        public void renderChannelSelection(Channel c){} public void renderLineSelection(Channel c,boolean show){}
        public void renderEpgSelection(EpgData e){} public void renderPlaybackMetadata(MediaMetadata m){metadata++;} public void showProgress(){}
    }
    static class Tv extends Host {
        int generations,resets; boolean held,newSelection; Runnable onPrepare;
        public boolean usesXrayLiveDeliveryGuard(){return true;} public boolean isPlaybackStartPending(){return held;}
        public void prepareXrayForPlaybackChange(LivePlayRequest r){generations++; if(onPrepare!=null) onPrepare.run();}
        public void resetXrayForPlaybackChange(){resets++;held=false;}
        public void renderChannelSelection(Channel c,boolean n){newSelection=n;}
    }
    static class Data implements LiveDataSource {
        final List<LivePlayRequest> requests=new ArrayList<>(); int cancels;
        public void getUrl(LivePlayRequest r){requests.add(r);} public void cancelUrl(){cancels++;}
        LivePlayRequest last(){return requests.get(requests.size()-1);}
    }
    static void result(LivePlaybackController c,LivePlayRequest r,String url){c.onPlaybackResult(new PlaybackResult<>(r,new Result(url)));}
    public static void main(String[] args){
        Channel a=new Channel(),b=new Channel();
        Host direct=new Host(); Data d=new Data(); LivePlaybackState s=new LivePlaybackState(); LivePlaybackController c=new LivePlaybackController(direct,d,s);
        c.selectChannel(a); result(c,d.last(),"a"); c.selectChannel(b);
        check("a".equals(s.getPlaybackKey())&&direct.stopped==0&&direct.prepared==2,"ordinary upstream seamless replacement");
        c.onPlaybackServiceReady(); check("a".equals(direct.restored)&&d.requests.size()==2,"ordinary pending reconnect");
        result(c,LivePlayRequest.live(b,C.TIME_UNSET),"stale"); check(direct.started==1,"ordinary stale object rejected");
        result(c,d.last(),"b"); check(direct.started==2,"ordinary current object accepted");
        c.selectEpg(new EpgData(),120); result(c,d.last(),"catchup"); direct.hasSession=true; c.refresh();
        check(d.last().isCatchup()&&d.last().getPosition()==120,"upstream catchup TIME_UNSET fallback");
        Tv tv=new Tv(); d=new Data(); s=new LivePlaybackState(); c=new LivePlaybackController(tv,d,s);
        c.selectChannel(a); check(tv.generations==1&&tv.newSelection,"TV new playback hook"); LivePlayRequest first=d.last();
        c.resumeChannelAfterXrayStart(); LivePlayRequest manual=d.last(); check(manual!=first&&manual.matches(first)&&tv.generations==1,"manual START fresh request, same generation");
        result(c,first,"old"); check(tv.started==0,"old request must not start");
        c.playbackError("late"); c.playbackEnded(); c.onEpgChanged(null); check(tv.errors==0&&tv.metadata==0&&d.requests.size()==2,"pending request guards retained");
        result(c,manual,"current"); tv.held=true; c.selectChannel(a); c.onPlaybackServiceReady();
        check(!tv.newSelection&&d.requests.size()==2&&tv.generations==1,"held automatic START not duplicated");
        c.selectChannel(b); check(s.getPlaybackKey()==null&&s.getPlayingRequest()==null&&tv.generations==2,"TV old identity cleared");
        c.onPlaybackServiceReady(); check(tv.restored==null&&d.requests.size()==3,"old key not restored");
        LivePlayRequest retired=d.last(); c.retirePendingPlayback(); result(c,retired,"retired");
        check(tv.started==1&&s.getPendingRequest()==null&&d.cancels==1,"retired request cannot deliver");
        c.onPlaybackServiceReady(); check(d.requests.size()==4&&tv.generations==3,"new owner can re-resolve");
        result(c,d.last(),"push://target"); check(tv.pushes==1&&"target".equals(tv.pushed)&&tv.resets==1&&tv.stopped==1&&s.getActiveRequest()==null,"push dispatch retires Xray");
        final LivePlaybackController owner=c; tv.onPrepare=owner::retirePendingPlayback;
        int n=d.requests.size(); c.refresh(); check(d.requests.size()==n&&s.getPendingRequest()==null,"synchronous retirement aborts resolver submission");
        System.out.println("PASS actual 5.9 Live controller/host: "+assertions+" assertions");
    }
}
'''


def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    args=parser.parse_args()
    inputs={}
    for name,expected in INPUTS.items():
        path=LIVE+name if name!='PlaybackResult.java' else LIVE.removesuffix('live/')+name
        p=args.candidate/path
        data=p.read_bytes()
        assert blob(data)==expected, (path,blob(data),expected)
        inputs[path]=data.decode()
    def run(sources, success):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); files=[]
            for path,data in sources.items():
                p=root/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(data); files.append(str(p))
            subprocess.run(['javac','--release','17','-d',str(root/'out'),*files],check=True)
            r=subprocess.run(['java','-cp',str(root/'out'),'com.fongmi.android.tv.playback.live.LiveHostHarness'],capture_output=True,text=True)
            if success:
                assert r.returncode==0,r.stderr; print(r.stdout.strip())
            else:
                assert r.returncode!=0 and 'AssertionError' in r.stderr, r.stdout+r.stderr
    sources={**STUBS,**inputs,'LiveHostHarness.java':HARNESS}
    run(sources,True)
    path=LIVE+'LivePlaybackController.java'
    for old,new in [('pending != request','!pending.matches(request)'),('if (!host.isPlaybackStartPending()) refresh();','refresh();'),('if (resetXray) host.prepareXrayForPlaybackChange(request);','host.prepareXrayForPlaybackChange(request);'),('if (state.getPendingRequest() != request) return;','')]:
        mutated=dict(sources); assert old in mutated[path]; mutated[path]=mutated[path].replace(old,new); run(mutated,False)
    print('PASS 4 negative controls rejected; media, Android, resolver, and Xray owner are doubles')


if __name__=='__main__': main()
