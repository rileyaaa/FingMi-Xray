#!/usr/bin/env python3
"""Run actual candidate engine selection and the extracted unchanged scheme guard.

Media3/Android/engine/transport objects here are deterministic doubles.
This is not a compile of the unresolved Exo implementation or a playback test.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

BASE = "app/src/main/java/com/fongmi/android/tv/player/"
FACTORY = BASE + "engine/PlayerEngineFactory.java"
MEDIA = BASE + "exo/ExoMediaSourceFactory.java"
LOCK = {
    FACTORY: "d01769375e7da9c488d23278fb59979e43f53424",
    MEDIA: "591bac5944a2e1b95b3ac73a25dfa1eb678b4830",
}
STUBS = {
    "android/net/Uri.java": """package android.net; public record Uri(String scheme) { public String getScheme(){return scheme;} }""",
    "androidx/media3/common/Player.java": "package androidx.media3.common; public interface Player { interface Listener {} }",
    "androidx/media3/exoplayer/hls/CmgConfiguration.java": """package androidx.media3.exoplayer.hls; public class CmgConfiguration {
        public static Object fromMediaUri(String uri){return uri.startsWith("cmg:") ? new Object() : null;}
    }""",
    "androidx/media3/mpvplayer/media/MpvDrmSupport.java": """package androidx.media3.mpvplayer.media; public class MpvDrmSupport {
        public static boolean supports(Object item){return false;}
    }""",
    "com/fingmi/xray/network/XrayHttpClient.java": "package com.fingmi.xray.network; public final class XrayHttpClient {}",
    "com/fongmi/android/tv/player/engine/PlayerEngine.java": """package com.fongmi.android.tv.player.engine;
        public interface PlayerEngine { enum Type { EXO, MPV } Type getType(); default boolean needsRebuild(){return false;}
            default boolean canReuseForPreload(){return true;} }""",
    "com/fongmi/android/tv/player/exo/ExoPlayerEngine.java": """package com.fongmi.android.tv.player.exo;
        import androidx.media3.common.Player; import com.fingmi.xray.network.XrayHttpClient;
        import com.fongmi.android.tv.player.engine.PlayerEngine;
        public class ExoPlayerEngine implements PlayerEngine {
            final XrayHttpClient proxy; public boolean rebuild;
            public ExoPlayerEngine(Player.Listener l){this(l,null);}
            public ExoPlayerEngine(Player.Listener l,XrayHttpClient p){proxy=p;}
            public XrayHttpClient proxy(){return proxy;}
            public Type getType(){return Type.EXO;} public boolean needsRebuild(){return rebuild;}
        }""",
    "com/fongmi/android/tv/player/mpv/MpvPlayerEngine.java": """package com.fongmi.android.tv.player.mpv;
        import androidx.media3.common.Player; import com.fongmi.android.tv.player.engine.PlayerEngine;
        public class MpvPlayerEngine implements PlayerEngine { public static boolean available=true;
            public MpvPlayerEngine(Player.Listener l){} public static boolean isAvailable(){return available;}
            public Type getType(){return Type.MPV;} }""",
    "com/fongmi/android/tv/player/media/PlaySpec.java": """package com.fongmi.android.tv.player.media;
        public record PlaySpec(String url, Object drm){public String getUrl(){return url;} public String getUri(){return url;} public Object getDrm(){return drm;}}""",
    "com/fongmi/android/tv/player/media/MediaItemFactory.java": """package com.fongmi.android.tv.player.media;
        public class MediaItemFactory { public static Object from(PlaySpec s){return s;} }""",
    "com/fongmi/android/tv/setting/PlayerSetting.java": """package com.fongmi.android.tv.setting;
        public class PlayerSetting {public static boolean mpv=true; public static boolean isMpv(){return mpv;} }""",
    "com/github/catvod/utils/UriUtil.java": """package com.github.catvod.utils; public class UriUtil {public static String scheme(String s){return s.split(":",2)[0];}}""",
    "androidx/media3/datasource/DataSource.java": """package androidx.media3.datasource;
        import android.net.Uri; import java.io.IOException; import java.util.*;
        public interface DataSource { void addTransferListener(TransferListener l);long open(DataSpec s)throws IOException;
            int read(byte[] b,int o,int n)throws IOException;Uri getUri();Map<String,List<String>> getResponseHeaders();void close()throws IOException; }
        """,
    "androidx/media3/datasource/DataSpec.java": """package androidx.media3.datasource; import android.net.Uri;
        public class DataSpec { public final Uri uri; public DataSpec(Uri u){uri=u;} }""",
    "androidx/media3/datasource/TransferListener.java": "package androidx.media3.datasource; public interface TransferListener {}",
    "EngineHarness.java": """import com.fingmi.xray.network.XrayHttpClient;
        import com.fongmi.android.tv.player.engine.*;import com.fongmi.android.tv.player.exo.ExoPlayerEngine;
        import com.fongmi.android.tv.player.media.PlaySpec;import com.fongmi.android.tv.player.mpv.MpvPlayerEngine;
        import com.fongmi.android.tv.setting.PlayerSetting;
        public class EngineHarness {
            static int checks;static void check(boolean b,String msg){checks++;if(!b)throw new AssertionError(msg);}
            public static void main(String[] args){
                PlaySpec normal=new PlaySpec("http://media.example/a",null);
                PlayerEngine direct=PlayerEngineFactory.create(normal,null);
                check(direct.getType()==PlayerEngine.Type.MPV,"direct MPV");
                check(PlayerEngineFactory.canPreload(direct,normal),"direct preload");
                check(PlayerEngineFactory.create(new PlaySpec("smb://host/a",null),null).getType()==PlayerEngine.Type.EXO,"SMB upstream EXO");
                check(PlayerEngineFactory.create(new PlaySpec("http://media.example/a",new Object()),null).getType()==PlayerEngine.Type.EXO,"unsupported MPV DRM");
                check(PlayerEngineFactory.create(new PlaySpec("cmg:abc",null),null).getType()==PlayerEngine.Type.EXO,"CMG upstream EXO");
                XrayHttpClient a=new XrayHttpClient(),b=new XrayHttpClient();
                PlayerEngine proxied=PlayerEngineFactory.create(normal,a,null);
                check(proxied instanceof ExoPlayerEngine&&((ExoPlayerEngine)proxied).proxy()==a,"explicit proxy identity");
                check(PlayerEngineFactory.matches(proxied,normal,a),"same resource reuse");
                check(!PlayerEngineFactory.matches(proxied,normal,b),"old resource not reused");
                check(!PlayerEngineFactory.matches(proxied,normal,null),"detach cannot reuse proxied engine");
                check(!PlayerEngineFactory.matches(direct,normal,a),"direct cannot reuse for proxy");
                PlayerSetting.mpv=false;check(!PlayerEngineFactory.matches(proxied,normal,null),"detach cannot reuse proxy even with EXO preference");
                check(!PlayerEngineFactory.canPreload(proxied,normal),"proxy preload forbidden even with EXO preference");
                ((ExoPlayerEngine)proxied).rebuild=true;check(!PlayerEngineFactory.matches(proxied,normal,a),"settings rebuild");
                check(PlayerEngineFactory.create(normal,null,null).getType()==PlayerEngine.Type.EXO,"direct preference unchanged");
                check(PlayerEngineFactory.canPreload(PlayerEngineFactory.create(normal,null),normal),"direct EXO preload retained");
                System.out.println("PASS actual candidate PlayerEngineFactory: "+checks+" assertions");
            }
        }""",
}
GUARD_HARNESS = """
    static int checks;
    static void check(boolean b,String msg){checks++;if(!b)throw new AssertionError(msg);}
    static final class Delegate implements DataSource {
        int opens,closes;boolean fail;Uri uri;
        public void addTransferListener(TransferListener l){}
        public long open(DataSpec s)throws IOException{opens++;uri=s.uri;if(fail)throw new IOException("open");return 7;}
        public int read(byte[] b,int o,int n){return 3;}
        public Uri getUri(){return uri;}
        public Map<String,List<String>> getResponseHeaders(){return Map.of("key",List.of("value"));}
        public void close(){closes++;}
    }
    public static void main(String[] args)throws Exception{
        for(String scheme:new String[]{null,""," ","http","HTTPS","file","asset","content","data","rawresource","android.resource"}){
            Delegate d=new Delegate();DataSource g=new GuardedPlaybackDataSource(d);
            check(g.open(new DataSpec(new Uri(scheme)))==7&&d.opens==1,"allowed "+scheme);
            check(g.read(new byte[8],0,8)==3&&g.getUri()==d.uri&&g.getResponseHeaders().containsKey("key"),"delegate "+scheme);
            g.close();g.close();check(d.closes==1,"exact close");
        }
        for(String scheme:new String[]{"smb","udp","tcp","ftp","rtmp","rtsp","rtspt","custom"}){
            Delegate d=new Delegate();DataSource g=new GuardedPlaybackDataSource(d);
            try{g.open(new DataSpec(new Uri(scheme)));throw new AssertionError("allowed "+scheme);}catch(IOException expected){}
            g.close();check(d.opens==0&&d.closes==0,"blocked without open "+scheme);
        }
        Delegate d=new Delegate();d.fail=true;DataSource g=new GuardedPlaybackDataSource(d);
        try{g.open(new DataSpec(new Uri("https")));throw new AssertionError("missing failure");}catch(IOException expected){}
        g.close();g.close();check(d.opens==1&&d.closes==1,"partial open cleanup");
        System.out.println("PASS extracted candidate scheme guard: "+checks+" assertions");
    }
"""


def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def compile_run(sources, klass, good):
    with tempfile.TemporaryDirectory(prefix="fingmi-transport-") as t:
        root=Path(t)
        for name, data in sources.items():
            p=root/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(data, encoding="utf-8")
        subprocess.run(["javac","--release","17","-d",str(root/"classes"),*map(str,root.rglob("*.java"))],check=True)
        result=subprocess.run(["java","-cp",str(root/"classes"),klass],capture_output=True,text=True,timeout=20)
        if good:
            assert result.returncode==0,result.stdout+result.stderr
            print(result.stdout.strip())
        else:
            assert result.returncode!=0 and "AssertionError" in result.stderr,result.stdout+result.stderr


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate",type=Path,required=True)
    root=p.parse_args().candidate
    raw={}
    for path,sha in LOCK.items():
        data=(root/path).read_bytes()
        assert blob(data)==sha,path
        raw[path]=data.decode()
    media=raw[MEDIA]
    start=media.index("    private static final class GuardedPlaybackDataSource")
    end=media.index("\n    static DefaultExtractorsFactory",start)
    guard=media[start:end]
    java="import android.net.Uri;import androidx.media3.datasource.*;import java.io.IOException;import java.util.*;\npublic class GuardHarness {\n"+guard+GUARD_HARNESS+"\n}\n"
    fpath="com/fongmi/android/tv/player/engine/PlayerEngineFactory.java"
    sources={**STUBS,fpath:raw[FACTORY],"GuardHarness.java":java}
    compile_run(sources,"EngineHarness",True)
    compile_run(sources,"GuardHarness",True)
    for path,old,new,klass in [
        (fpath,"exo.proxy() == proxy","exo.proxy() != null","EngineHarness"),
        (fpath,"if (engine instanceof ExoPlayerEngine exo && exo.proxy() != null) return false;","", "EngineHarness"),
        (fpath,"!(engine instanceof ExoPlayerEngine exo && exo.proxy() != null) && ","","EngineHarness"),
        ("GuardHarness.java",'|| "android.resource".equalsIgnoreCase(scheme);','|| "android.resource".equalsIgnoreCase(scheme) || "udp".equalsIgnoreCase(scheme);',"GuardHarness"),
    ]:
        assert sources[path].count(old)==1
        changed=dict(sources);changed[path]=changed[path].replace(old,new)
        compile_run(changed,klass,False)
    print("PASS 4 mutations rejected; engine and Media3/Android transport boundaries are doubles")


if __name__=="__main__":
    main()
