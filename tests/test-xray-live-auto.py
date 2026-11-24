#!/usr/bin/env python3
"""Exercise real Live rule and playback-session classes with deterministic I/O substitutes."""
import ast
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "xray/src/main/java/com/fingmi/xray"
# Share platform/HTTP substitutes with the reentrant-session regression without running it.
fixture = ast.parse((ROOT / "tests/test-xray-playback-session-reentry.py").read_text(encoding="utf-8"))
stubs = next(ast.literal_eval(n.value) for n in fixture.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "STUBS" for t in n.targets))
del stubs["com/fingmi/xray/session/XrayPlaybackAddress.java"]
stubs["com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java"] = """
package com.fingmi.xray.network;
public class PublicPlaybackDestinationInterceptor {
    public static boolean isPrivateOrReserved(String host) {
        return host.equals("localhost") || host.startsWith("127.") || host.startsWith("192.168.");
    }
}
"""
stubs["com/fingmi/xray/session/XraySessionController.java"] = """
package com.fingmi.xray.session;
import android.content.Context;
public final class XraySessionController {
    public static XraySessionController latest;
    private final XraySessionListener listener;
    private int state = XraySessionListener.IDLE;
    public int starts, stops;
    public XraySessionController(Context c, XraySessionListener listener) {
        this.listener = listener; latest = this;
    }
    public boolean isRunning() { return state == XraySessionListener.RUNNING; }
    public int getState() { return state; }
    public void start() {
        if (state != XraySessionListener.IDLE) throw new AssertionError("duplicate START");
        starts++; state = XraySessionListener.STARTING;
        listener.onXrayStateChanged(state, 0, "");
    }
    public void ready() {
        if (state != XraySessionListener.STARTING) return;
        state = XraySessionListener.RUNNING;
        listener.onXrayStateChanged(state, 12345, "");
    }
    public void fail() {
        if (state != XraySessionListener.STARTING && state != XraySessionListener.RUNNING) return;
        state = XraySessionListener.IDLE;
        listener.onXrayStateChanged(XraySessionListener.ERROR, 0, "failure");
    }
    public void stop() {
        if (state == XraySessionListener.IDLE) return;
        stops++; state = XraySessionListener.IDLE;
        listener.onXrayStateChanged(state, 0, "");
    }
    public void close() { stop(); }
}
"""
stubs["LiveAutoTest.java"] = r"""
import android.content.Context;
import okhttp3.OkHttpClient;
import com.fingmi.xray.config.XrayLiveAutoRules;
import com.fingmi.xray.session.*;
import com.fingmi.xray.network.XrayHttpClient;
import java.util.*;

public final class LiveAutoTest {
    static final String URL = "https://media.example/stream";
    static int checks;
    static void check(boolean value, String why) {
        if (!value) throw new AssertionError(why);
        checks++;
    }
    static final class Host implements XrayPlaybackSession.Listener {
        final XrayLiveAutoPlayback policy = new XrayLiveAutoPlayback();
        final XrayPlaybackSession session = new XrayPlaybackSession(new Context(), new OkHttpClient(), this);
        final XraySessionController core = XraySessionController.latest;
        final List<String> played = new ArrayList<>();
        XrayHttpClient attached;
        int epoch;
        String group, channel;
        void select(String g, String c, boolean match) {
            group = g; channel = c;
            session.beginLiveAuto("live:" + (++epoch), policy.prepare(g,c,match));
        }
        void resolved(String name, String url) {
            session.mediaUrlChanged(url);
            Runnable play = () -> played.add(name + (attached != null ? ":proxy" : ":direct"));
            if (!policy.deferResolved(session,url,play)) play.run();
        }
        void off() {
            Runnable pending = policy.disableManually(group,channel);
            session.stop(true);
            if (pending != null) pending.run();
        }
        void close() { policy.reset(); session.close(); }
        public void onProxyChanged(XrayHttpClient client, boolean preserve) {
            if (client != null) check(!preserve, "auto START must not resume old media");
            attached = client;
        }
        public void onStateChanged(int state, String message) {
            if (state == XraySessionListener.RUNNING) policy.proxyReady();
            if (state == XraySessionListener.ERROR) policy.proxyFailed();
        }
    }
    static void rules() {
        XrayLiveAutoRules r = new XrayLiveAutoRules(" 港台，海外,\n港台, ", "翡翠台,东森幼幼台,东森*,TV*HD, A.B?[1]");
        check(r.groups().equals("港台,海外"),"normalized groups");
        check(r.matches("港台","other",""),"group OR channel");
        check(r.matches("大陆","翡翠台",""),"exact channel");
        check(r.matches("大陆","东森新闻台",""),"prefix wildcard");
        check(r.matches("大陆","other","东森幼幼台"),"display name");
        check(r.matches("大陆","tv sport hd",""),"wildcard and case");
        check(r.matches("大陆","A.B?[1]",""),"literal punctuation");
        check(!r.matches("大陆","翡翠台HD",""),"exact not substring");
        check(!r.matches("大陆","AxB?[1]",""),"not regex");
        check(!new XrayLiveAutoRules(" ，,\n",null).matches("港台","翡翠台",""),"empty disabled");
        check(new XrayLiveAutoRules("港*台","").matches("港澳台","other",""),"group wildcard");
        check(new XrayLiveAutoRules("","*").matches("","A",""),"all channels");
        check(!new XrayLiveAutoRules("","*").matches("","",""),"blank name not matched");
        try {
            new XrayLiveAutoRules("x".repeat(4097),"");
            throw new AssertionError("length limit");
        } catch (IllegalArgumentException expected) { checks++; }
    }
    static void retention() {
        Host h = new Host();
        h.select("G","A",true); h.resolved("A",URL);
        check(h.played.isEmpty() && h.core.starts == 1,"hold initial media until proxy");
        h.core.ready();
        XrayHttpClient first = h.attached;
        check(first != null && h.played.equals(List.of("A:proxy")),"attach before playback");
        h.select("G","B",true); h.resolved("B",URL+"2");
        h.select("other","C",true); h.resolved("C",URL+"3");
        check(h.attached == first && !first.closed && h.core.starts == 1 && h.core.stops == 0,
              "consecutive matches reuse Core and client even across groups");
        check(h.played.equals(List.of("A:proxy","B:proxy","C:proxy")),"all matched media proxied");
        h.select("other","D",false); h.resolved("D",URL);
        check(h.core.stops == 1 && first.closed && h.attached == null,"unmatched closes proxy");
        check(h.played.get(3).equals("D:direct"),"unmatched direct");
        h.close();
    }
    static void rapidSwitch() {
        Host h = new Host();
        h.select("G","A",true); h.resolved("A",URL);
        h.select("G","B",true); h.resolved("B",URL+"2");
        h.core.ready();
        check(h.core.starts == 1 && h.played.equals(List.of("B:proxy")),"STARTING retains only latest media");
        h.select("G","C",true);
        h.resolved("C","http://192.168.1.2/video");
        check(h.attached == null && h.core.stops == 1 && h.played.get(1).equals("C:direct"),"LAN source never proxied");
        h.select("G","D",true); h.resolved("D",URL);
        h.select("H","E",false); h.core.ready(); h.resolved("E",URL);
        check(h.played.equals(List.of("B:proxy","C:direct","E:direct")),"late START cannot resume retired channel");
        h.close();
    }
    static void manualAndFailure() {
        Host h = new Host();
        h.select("G","A",true); h.resolved("A",URL); h.off(); h.core.ready();
        check(h.played.equals(List.of("A:direct")),"explicit OFF releases pending media direct");
        h.select("G","A",true); h.resolved("A-line2",URL);
        check(h.core.starts == 1 && h.played.get(1).endsWith(":direct"),"OFF survives same station refresh");
        h.select("G","B",true); h.resolved("B",URL); h.core.fail();
        check(h.played.size() == 2 && h.attached == null,"failed START no automatic direct fallback");
        check(h.policy.retry(h.session),"explicit retry");
        h.core.ready();
        check(h.played.get(2).equals("B:proxy") && h.core.starts == 3,"retry latest only");
        h.close();
    }
    static void lifecycle() {
        Host h = new Host();
        h.select("G","A",true); h.resolved("A",URL);
        h.policy.suspend(true); h.session.stop(false); h.core.ready();
        check(h.played.isEmpty() && h.attached == null,"background no media or proxy activation");
        h.policy.resume(h.session); h.core.ready();
        check(h.core.starts == 2 && h.played.equals(List.of("A:proxy")),"foreground resumes unfinished request");
        h.select("G","B",true); h.resolved("B",URL);
        XrayHttpClient old = h.attached;
        h.policy.reset(); h.session.begin("new-owner");
        check(old.closed && h.attached == null,"owner or engine change stops transport");
        h.select("G","C",true); h.resolved("C",URL); h.close(); h.core.ready();
        check(h.played.equals(List.of("A:proxy","B:proxy")),"close drops waiting media");
    }
    public static void main(String[] args) {
        rules(); retention(); rapidSwitch(); manualAndFailure(); lifecycle();
        System.out.println("PASS: Live auto routing ("+checks+" checks, real rules/session; synthetic I/O)");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-live-auto-") as directory:
    work = Path(directory)
    sources = []
    for rel, code in stubs.items():
        path = work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        sources.append(str(path))
    for rel in ("config/XrayLiveAutoRules.java", "session/XrayLiveAutoPlayback.java",
                "session/XrayPlaybackSession.java", "session/PlaybackIdentityGate.java",
                "session/XrayPlaybackAddress.java", "session/XraySessionListener.java"):
        sources.append(str(PRODUCTION / rel))
    subprocess.run(["java", "com.sun.tools.javac.Main", "--release", "17", "-d", str(work), *sources], check=True)
    subprocess.run(["java", "-cp", str(work), "LiveAutoTest"], check=True)
