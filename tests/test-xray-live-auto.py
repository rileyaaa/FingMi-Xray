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
        h.select("G","A",true);
        check(!h.policy.hasResolvedRoute(),"first station cannot use route before resolution");
        h.resolved("A",URL);
        check(h.policy.hasResolvedRoute(),"resolved supported URL allows route when Core ready");
        check(h.played.isEmpty() && h.core.starts == 1,"hold initial media until proxy");
        h.core.ready();
        XrayHttpClient first = h.attached;
        check(first != null && h.played.equals(List.of("A:proxy")),"attach before playback");
        h.select("G","B",true);
        check(!h.policy.hasResolvedRoute() && h.attached == first,"retained Core is not a resolved new route");
        h.resolved("B",URL+"2");
        check(h.policy.hasResolvedRoute(),"second station validated independently");
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
        h.select("G","B",true);
        h.core.ready();
        check(!h.policy.hasResolvedRoute() && h.played.isEmpty() && h.attached != null,
              "late Core readiness cannot activate unresolved new station");
        h.resolved("B",URL+"2");
        check(h.core.starts == 1 && h.played.equals(List.of("B:proxy")),"STARTING retains only latest media");
        h.select("G","C",true);
        h.resolved("C","http://192.168.1.2/video");
        check(h.attached == null && h.core.stops == 1 && h.played.get(1).equals("C:direct"),"LAN source never proxied");
        check(!h.policy.hasResolvedRoute() && !h.policy.isAutomatic(),"unsupported source retires automatic route");
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
        h.select("G","A",true);
        check(h.policy.isAwaitingPlayback(),"unresolved automatic request owns pending start");
        h.resolved("A",URL);
        check(h.policy.isAwaitingPlayback(),"resolved automatic request held for START");
        h.policy.suspend(true); h.session.stop(false); h.core.ready();
        check(h.played.isEmpty() && h.attached == null,"background no media or proxy activation");
        h.policy.resume(h.session); h.core.ready();
        check(h.core.starts == 2 && h.played.equals(List.of("A:proxy")),"foreground resumes unfinished request");
        check(!h.policy.isAwaitingPlayback(),"started playback is not a pending request");
        h.select("G","B",true); h.resolved("B",URL);
        XrayHttpClient old = h.attached;
        h.policy.reset(); h.session.begin("new-owner");
        check(old.closed && h.attached == null,"owner or engine change stops transport");
        check(!h.policy.isAwaitingPlayback(),"handoff permits normal reclaim");
        h.select("G","C",true); h.resolved("C",URL); h.close(); h.core.ready();
        check(h.played.equals(List.of("A:proxy","B:proxy")),"close drops waiting media");
    }
    public static void main(String[] args) {
        rules(); retention(); rapidSwitch(); manualAndFailure(); lifecycle();
        System.out.println("PASS: Live auto routing ("+checks+" checks, real rules/session; synthetic I/O)");
    }
}
"""

# The host must apply the same route gate to all new playback metadata,
# and explicitly retire side work on the transport-retention path.
live = (ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java").read_text(encoding="utf-8")
prepare = live.split("public void prepareXrayForPlaybackChange(", 1)[1].split("private void suppressAutoXrayArtwork(", 1)[0]
assert "!mLiveAuto.hasResolvedRoute()" in live
assert "newPlayback && shouldDeferNewLiveMetadata(channel)" in live
assert "if (shouldDeferNewLiveMetadata(channel))" in live
assert prepare.index("cancelXrayMetadataRequests();") < prepare.index("mXray.beginLiveAuto(")
assert prepare.index("service().onXrayTransitionStarted();") < prepare.index("mXray.beginLiveAuto(")
assert "clearPlaybackDanmakuSource();" in prepare
assert "if (!isAutoXrayWaiting()) refreshXrayAwareMetadata();" not in prepare
assert "if (mLiveAuto.isAutomatic()) refreshXrayAwareMetadata();" in live
assert prepare.index("player().reset();") < prepare.index("mXray.beginLiveAuto(")
manual = live.split("private void onXray()", 1)[1].split("private void onPlayer()", 1)[0]
assert manual.index("if (mLiveAuto.isAutomatic() && !mLiveAuto.hasResolvedRoute()) return;") < manual.index("mLiveAuto.enableManually();")

# Execute the real PlayerManager detach methods with synthetic engine/player
# boundaries. A retained Xray engine must be retired even with no PlaySpec.
player_source = (ROOT / "app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java").read_text(encoding="utf-8")
def method(signature, source=player_source):
    start = source.index(signature)
    opening = source.index("{", start)
    end, depth = opening + 1, 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]

# The engine dialog calls the reset hook only for a real engine change.
# URL delivery is asynchronous on main, after PlayerManager.setEngine().
assert "this::resetXrayForEngineChange" in method("private void onPlayer()", live)
stubs["EngineChangeTest.java"] = r"""
import com.fingmi.xray.session.*;
import java.util.List;

public final class EngineChangeTest {
    static final class EngineHost {
        final LiveAutoTest.Host host = new LiveAutoTest.Host();
        final XrayLiveAutoPlayback mLiveAuto = host.policy;
        final XrayPlaybackSession mXray = host.session;
        long mPlaybackEpoch = 100;
        boolean mXrayPendingChannelResume, mXrayStartedFromExistingPlayback, mXrayRefreshMetadataOnDetach;
        int restored, resumed;
        final Controller mLive = new Controller();
        class Controller {
            void resumeChannelAfterXrayStart() {
                check(!mLiveAuto.isAutomatic() && mXray.state() == XraySessionListener.IDLE,
                        "new resolver must start after retiring the automatic session");
                resumed++;
            }
        }
        void restoreAutoXrayMetadata() {
            check(!mLiveAuto.isAutomatic() && mXray.resources() == null,
                    "metadata restored before retiring proxy");
            restored++;
        }
        __ENGINE_CHANGE__
    }
    static void check(boolean value, String why) {
        if (!value) throw new AssertionError(why);
    }
    static EngineHost select(boolean matched) {
        EngineHost h = new EngineHost();
        h.host.select("G", "A", matched);
        return h;
    }
    public static void main(String[] args) {
        EngineHost h = select(true);
        h.host.resolved("A", LiveAutoTest.URL);
        check(h.mLiveAuto.isAwaitingPlayback() && h.host.played.isEmpty(), "reproduce held START");
        h.resetXrayForEngineChange();
        check(h.resumed == 1 && h.restored == 1, "resolved pending channel lost on engine change");
        h.host.core.ready();
        check(h.host.played.isEmpty(), "late START restarted retired media");
        h.host.resolved("A-new", LiveAutoTest.URL);
        check(h.host.played.equals(List.of("A-new:direct")), "selected engine must use ordinary route");
        h.host.close();

        h = select(true);
        h.resetXrayForEngineChange();
        check(h.resumed == 0 && h.restored == 1, "unresolved request duplicated or metadata not restored");
        h.host.resolved("A", LiveAutoTest.URL);
        check(h.host.played.equals(List.of("A:direct")) && h.host.core.starts == 0,
                "unresolved result should continue direct");
        h.host.close();

        h = select(true);
        h.host.resolved("A", LiveAutoTest.URL);
        h.host.core.fail();
        h.resetXrayForEngineChange();
        check(h.resumed == 1 && h.restored == 1, "failed START result lost");
        h.host.close();

        h = select(true);
        h.host.resolved("A", LiveAutoTest.URL);
        h.host.core.ready();
        h.resetXrayForEngineChange();
        check(h.resumed == 0 && h.restored == 0 && h.host.played.equals(List.of("A:proxy")),
                "already-playing station unnecessarily re-resolved");
        h.host.close();

        h = select(false);
        h.resetXrayForEngineChange();
        check(h.resumed == 0 && h.restored == 0, "ordinary path changed");
        h.host.close();
        System.out.println("PASS: pending/failed/active/unmatched Live engine changes");
    }
}
""".replace("__ENGINE_CHANGE__", "\n".join(method(signature, live) for signature in (
    "private void resetXrayForEngineChange()", "public void resetXrayForPlaybackChange()",
)))

# Exercise the real resume hook against the ordering where onStart could
# not claim the shared player and only onResume obtains the binding.
stubs["LateOwnerResumeTest.java"] = r"""
import com.fingmi.xray.session.*;
import java.util.List;

public final class LateOwnerResumeTest {
    static class Base {
        boolean bindingOwner;
        boolean reclaimOnResume = true;
        boolean isBindingOwner() { return bindingOwner; }
        protected void onResume() { bindingOwner = reclaimOnResume; }
    }
    static final class Activity extends Base {
        final LiveAutoTest.Host host = new LiveAutoTest.Host();
        final XrayLiveAutoPlayback mLiveAuto = host.policy;
        final XrayPlaybackSession mXray = host.session;
        boolean mXrayAutoReclaimPending;
        boolean matched = true;
        int refreshes;
        final Controller mLive = new Controller();
        class Controller {
            void refresh() { refreshes++; host.select("G", "A", matched); }
        }
        void startBoundary() { if (isBindingOwner()) mLiveAuto.resume(mXray); }
        __RESUME_METHODS__
    }
    static void check(boolean ok, String msg) {
        if (!ok) throw new AssertionError(msg);
    }
    static Activity handoff() {
        Activity a = new Activity();
        a.host.select("G", "A", true);
        a.mLiveAuto.suspend(true);
        a.mXray.stop(false);
        a.mLiveAuto.reset();
        a.mXrayAutoReclaimPending = true;
        return a;
    }
    public static void main(String[] args) {
        Activity a = handoff();
        a.startBoundary(); // not yet binding owner
        a.onResume();
        a.host.resolved("A", LiveAutoTest.URL);
        check(a.host.core.starts == 1 && a.host.played.isEmpty(),
                "late owner resume leaves matched channel suspended");
        a.onResume();
        a.host.core.ready();
        a.onResume();
        check(a.host.played.equals(List.of("A:proxy")) && a.host.core.starts == 1 && a.refreshes == 1,
                "duplicate resume started media twice");
        a.host.close();

        Activity b = handoff();
        b.reclaimOnResume = false;
        b.startBoundary(); b.onResume();
        check(b.refreshes == 0 && b.host.core.starts == 0 && b.mXrayAutoReclaimPending,
                "nonowner resumed");
        b.host.close();

        Activity c = handoff();
        c.matched = false;
        c.startBoundary(); c.onResume();
        c.host.resolved("A", LiveAutoTest.URL);
        check(c.host.played.equals(List.of("A:direct")) && c.host.core.starts == 0,
                "unmatched channel no longer direct");
        c.host.close();

        Activity d = handoff();
        d.bindingOwner = true;
        d.startBoundary(); d.onResume();
        d.host.resolved("A", LiveAutoTest.URL); d.host.core.ready();
        check(d.host.played.equals(List.of("A:proxy")) && d.host.core.starts == 1,
                "normal onStart resume regressed");
        d.host.close();

        Activity e = new Activity();
        e.host.select("G", "A", true);
        e.mLiveAuto.suspend(true);
        e.host.resolved("A", LiveAutoTest.URL);
        check(e.host.core.starts == 0, "background began START");
        e.startBoundary(); e.onResume();
        check(e.host.core.starts == 1, "resume did not start already-held result");
        e.host.core.ready();
        check(e.host.played.equals(List.of("A:proxy")), "held result not delivered");
        e.host.close();
        System.out.println("PASS: late-owner foreground, repeated resume, nonowner, held result and ordinary path");
    }
}
""".replace("__RESUME_METHODS__", "\n".join(method(signature, live) for signature in (
    "protected void onResume()", "private void resumeRetiredAutoRequest()",
)))

# Source changes and owner reclaims can retire an automatic request before
# any HTTP resource exists, so the detach callback cannot restore the UI.
stubs["RetiredMetadataTest.java"] = r"""
import com.fingmi.xray.session.XrayLiveAutoPlayback;
import java.util.ArrayList;
import java.util.List;

public final class RetiredMetadataTest {
    static class View {
        static final int GONE = 8;
        void setVisibility(int value) {}
        void setText(String value) {}
    }
    static class Adapter {
        boolean suppressed;
        int size = 1;
        void clear() { size = 0; }
        void setXrayLogoSuppressed(boolean value) { suppressed = value; }
    }
    static class Player {
        int resets;
        void reset() { resets++; }
        void clear() {}
        void stop() {}
        void setDefaultArtwork(Object value) {}
    }
    static class Binding {
        final Control control = new Control();
        final Widget widget = new Widget();
        final Player player = new Player();
        static class Control { final Action action = new Action(); }
        static class Action { final View line = new View(); }
        static class Widget { final View title = new View(); }
    }
    record Channel(String name) { String getName() { return name; } }
    record LivePlayRequest(Channel channel, boolean catchup) {
        Channel getChannel() { return channel; }
        boolean isCatchup() { return catchup; }
    }
    static class Live {
        final List<Object> groups = new ArrayList<>();
        boolean isSelected() { return false; }
        List<Object> getGroups() { return groups; }
    }
    static class LiveConfig {
        static final LiveConfig INSTANCE = new LiveConfig();
        static LiveConfig get() { return INSTANCE; }
        void setHome(Live item) {}
    }
    static class Activity {
        final XrayLiveAutoPlayback mLiveAuto = new XrayLiveAutoPlayback();
        final Session mXray = new Session();
        final Binding mBinding = new Binding();
        final Adapter mChannelAdapter = new Adapter(), mGroupAdapter = new Adapter(), mEpgDataAdapter = new Adapter();
        final List<Object> mHides = new ArrayList<>();
        final Model mViewModel = new Model();
        final Controller mLive = new Controller();
        Channel mChannel = new Channel("A");
        Object mGroup = new Object();
        long mPlaybackEpoch;
        boolean mXrayAutoReclaimPending, mXrayPendingChannelResume, mXrayStartedFromExistingPlayback, mXrayRefreshMetadataOnDetach;
        boolean matched = true, owner = true, widgetSuppressed;
        int metadataCancels, restores, retiredLogoRequests, refreshes, sourceLoads;
        class Session {
            Object proxy;
            Object resources() { return proxy; }
            void begin(String identity) {
                if (proxy != null) {
                    proxy = null;
                    cancelXrayMetadataRequests();
                    // Model the detach callback's suppression and guarded artwork path.
                    mChannelAdapter.setXrayLogoSuppressed(false);
                    setWidgetLogoSuppressed(false);
                    if (mChannel != null) retiredLogoRequests++;
                }
            }
            void beginLiveAuto(String identity, boolean retain) { if (!retain) begin(identity); }
        }
        static class Model {
            int urlCancels;
            void cancelPlaybackUrl() { urlCancels++; }
        }
        class Controller {
            void refresh() { refreshes++; prepareXrayForPlaybackChange(new LivePlayRequest(mChannel, false)); }
            void reset() {}
        }
        boolean isBindingOwner() { return owner; }
        boolean matchesAutoXray(Channel channel) { return matched; }
        String liveGroupName(Channel channel) { return "G"; }
        Player player() { return mBinding.player; }
        void cancelXrayMetadataRequests() { metadataCancels++; }
        void clearPlaybackDanmakuSource() {}
        Activity service() { return this; }
        void onXrayTransitionStarted() {}
        void setWidgetLogoSuppressed(boolean value) { widgetSuppressed = value; }
        void suppressAutoXrayArtwork() { mChannelAdapter.setXrayLogoSuppressed(true); widgetSuppressed = true; }
        void restoreAutoXrayMetadata() { restores++; mChannelAdapter.setXrayLogoSuppressed(false); widgetSuppressed = false; }
        void clearArtworkTarget() {}
        void hideControl() {}
        void getLive() { sourceLoads++; }
        __METHODS__
    }
    static void check(boolean ok, String why) { if (!ok) throw new AssertionError(why); }
    static Activity pending() {
        Activity a = new Activity();
        a.prepareXrayForPlaybackChange(new LivePlayRequest(a.mChannel, false));
        check(a.mChannelAdapter.suppressed && a.widgetSuppressed, "auto metadata not suppressed");
        return a;
    }
    static Activity retired(boolean matched) {
        Activity a = pending();
        a.mXrayAutoReclaimPending = true;
        a.resetXrayForPlaybackChange(); // pending has no resources, so no detach callback
        a.matched = matched;
        return a;
    }
    static void sourceChange(boolean active) {
        Activity a = pending();
        if (active) a.mXray.proxy = new Object();
        a.setLive(new Live());
        check(!a.mChannelAdapter.suppressed && !a.widgetSuppressed, "old suppression survived source change");
        check(a.retiredLogoRequests == 0 && a.mChannel == null && a.sourceLoads == 1, "retiring logo reloaded or source not changed");
        check(a.mViewModel.urlCancels == 1 && a.metadataCancels == (active ? 3 : 2), "old auto resolver/metadata not retired");
    }
    static void directReclaim(boolean explicit) {
        Activity a = retired(false);
        if (explicit) a.resumeRetiredAutoRequest();
        else a.mLive.refresh();
        check(a.restores == 1 && !a.mChannelAdapter.suppressed && !a.widgetSuppressed, "retired auto -> direct metadata not restored");
        a.resumeRetiredAutoRequest();
        check(a.refreshes == 1 && !a.mXrayAutoReclaimPending, "reclaim repeated");
    }
    static void matchedAndOrdinary() {
        Activity a = retired(true);
        a.owner = false; a.resumeRetiredAutoRequest();
        check(a.refreshes == 0 && a.mXrayAutoReclaimPending, "nonowner consumed reclaim");
        a.owner = true; a.resumeRetiredAutoRequest();
        check(a.refreshes == 1 && a.restores == 0 && a.mChannelAdapter.suppressed && a.mLiveAuto.isAutomatic(), "matched reclaim exposed direct artwork");
        Activity b = new Activity(); b.matched = false;
        b.prepareXrayForPlaybackChange(new LivePlayRequest(b.mChannel, false));
        b.setLive(new Live());
        check(b.mViewModel.urlCancels == 0 && b.metadataCancels == 0 && b.restores == 0 && !b.mChannelAdapter.suppressed, "ordinary path changed");
    }
    public static void main(String[] args) {
        switch(args[0]) {
            case "source-pending" -> sourceChange(false);
            case "source-active" -> sourceChange(true);
            case "reclaim-explicit" -> directReclaim(true);
            case "reclaim-normal" -> directReclaim(false);
            case "ordinary" -> matchedAndOrdinary();
            default -> throw new IllegalArgumentException();
        }
        System.out.println("PASS: " + args[0]);
    }
}
""".replace("__METHODS__", "\n".join(method(signature, live) for signature in (
    "private void resumeRetiredAutoRequest()",
    "public void prepareXrayForPlaybackChange(",
    "private void resetAdapter()",
    "public void setLive(Live item)",
    "public void resetXrayForPlaybackChange()",
)))

stubs["IdleProxyEngineTest.java"] = r"""
import com.fingmi.xray.network.XrayHttpClient;
import okhttp3.OkHttpClient;
public final class IdleProxyEngineTest {
    static final class Player {
        void removeListener(Object listener) {}
    }
    static class PlayerEngine {
        final Player player = new Player();
        boolean released;
        void release() { released = true; }
        Player getPlayer() { return player; }
    }
    static final class ExoPlayerEngine extends PlayerEngine {
        final XrayHttpClient proxy;
        ExoPlayerEngine(XrayHttpClient proxy) { this.proxy = proxy; }
        XrayHttpClient proxy() { return proxy; }
    }
    static final class PlayerEngineFactory {
        static PlayerEngine create(int decode, Object listener) { return new ExoPlayerEngine(null); }
    }
    static final class PlaySpec {
        PlaySpec checkUa() { return this; }
    }
    record PlaybackSnapshot(long positionMs) {
        static PlaybackSnapshot capture(Player player) { return new PlaybackSnapshot(0); }
        void restore(Player player) {}
    }
    record XrayRestore(PlaySpec spec, PlaybackSnapshot snapshot) {}
    static final class Callback {
        int transitions;
        void onXrayTransitionStarted() { transitions++; }
    }
    static final class Manager {
        XrayHttpClient playbackProxy;
        PlaySpec spec;
        XrayRestore xrayRestore;
        PlayerEngine engine;
        Player player;
        int decode, starts, rebuilds;
        final Object listener = new Object();
        final Callback callback = new Callback();
        Manager(XrayHttpClient proxy, boolean installed) {
            playbackProxy = proxy;
            engine = new ExoPlayerEngine(installed ? proxy : null);
            player = engine.getPlayer();
        }
        void setPlayer(Player next) { player = next; rebuilds++; }
        void clearPreload() {}
        void startCurrent(long position) { starts++; }
        void ensureEngine(PlaySpec spec) { throw new AssertionError("empty spec cannot use media rebuild"); }
        __METHODS__
    }
    static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        OkHttpClient direct = new OkHttpClient();
        for (int mode = 0; mode < 4; mode++) {
            XrayHttpClient proxy = new XrayHttpClient(1234, direct);
            Manager m = new Manager(proxy, true);
            PlayerEngine old = m.engine;
            if (mode == 0) m.setPlaybackProxy(null, false);
            if (mode == 1) m.setPlaybackProxy(null, true);
            if (mode == 2) m.clearPlaybackProxyPreservingState();
            if (mode == 3) {
                m.playbackProxy = null;
                m.setPlaybackProxy(null, false);
            }
            check(old.released && m.engine != old, "idle proxy engine not released: " + mode);
            check(!m.hasXraySession() && m.getPlaybackHttpClient(direct) == direct, "stale network identity: " + mode);
            check(m.starts == 0 && m.rebuilds == 1 && m.callback.transitions == 1, "unexpected playback restart");
            m.setPlaybackProxy(null, false);
            check(m.rebuilds == 1, "repeated detach rebuilt engine");
        }
        XrayHttpClient pending = new XrayHttpClient(1234, direct);
        Manager m = new Manager(pending, false);
        PlayerEngine old = m.engine;
        m.setPlaybackProxy(null, false);
        check(!old.released && m.engine == old && m.rebuilds == 0, "pending-only attach rebuilt direct engine");
        check(!m.hasXraySession(), "pending proxy not cleared");
        System.out.println("PASS: empty Live proxy engine retirement");
    }
}
""".replace("__METHODS__", "\n".join(method(signature) for signature in (
    "private void releaseEmptyProxyEngine(",
    "public synchronized void setPlaybackProxy(",
    "public synchronized void clearPlaybackProxyPreservingState(",
    "public synchronized boolean hasXraySession(",
    "public synchronized OkHttpClient getPlaybackHttpClient(",
)))

script = (ROOT / "app/src/main/assets/js/script.js").read_text(encoding="utf-8")
phone_rules = script.split("function sendXrayLiveRules()", 1)[1].split("function sendDanmaku()", 1)[0]
assert ".done(" in phone_rules and ".fail(" in phone_rules
action = (ROOT / "app/src/main/java/com/fongmi/android/tv/server/process/Action.java").read_text(encoding="utf-8")
phone_handler = action.split("private Response onXrayLiveRules(", 1)[1].split("private void onSetting(", 1)[0]
assert 'Response.Status.BAD_REQUEST' in phone_handler
assert "if (!XrayLiveRulesEvent.post(groups, channels))" in phone_handler
settings = (ROOT / "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingXrayActivity.java").read_text(encoding="utf-8")
apply_rules = method("public void onXrayLiveRulesEvent(", settings)
assert "mOperation == XrayOperation.RESET_SECURITY" in apply_rules
assert apply_rules.index("event.markApplied();") > apply_rules.index("mBinding.liveAutoChannels.setText(event.channels());")

# Compile the actual request/event types and execute extracted controller and
# ViewModel delivery methods against deterministic main-thread queues.
APP_JAVA = ROOT / "app/src/main/java"
controller_source = (APP_JAVA / "com/fongmi/android/tv/playback/live/LivePlaybackController.java").read_text(encoding="utf-8")
model_source = (APP_JAVA / "com/fongmi/android/tv/model/LiveViewModel.java").read_text(encoding="utf-8")
assert "xrayLiveDeliveryGuard = host.usesXrayLiveDeliveryGuard();" in method("public LivePlaybackController createPlaybackController(", model_source)
host_source = (APP_JAVA / "com/fongmi/android/tv/playback/live/LivePlaybackHost.java").read_text(encoding="utf-8")
assert "default boolean usesXrayLiveDeliveryGuard() { return false; }" in host_source
assert "public boolean usesXrayLiveDeliveryGuard() { return true; }" in live
assert "if (xrayLiveDeliveryGuard) latestUrlRequest = request;" in method("public void getUrl(", model_source)
assert "latestUrlRequest = null;" in method("protected void onCleared(", model_source)
resume = method("public void resumeChannelAfterXrayStart(", controller_source)
assert "LivePlayRequest.catchup(channel, request.getCatchupData(), request.getPosition())" in resume
assert "LivePlayRequest.live(channel, request.getPosition())" in resume
assert "if (isBindingOwner() && mLiveAuto.isAwaitingPlayback()) return;" in method("protected void onReclaim(", live)
assert "return isBindingOwner() && mLiveAuto.isAwaitingPlayback();" in method("public boolean isPlaybackStartPending(", live)
assert "mXrayAutoReclaimPending = false;" in prepare
assert "resumeRetiredAutoRequest();" in method("protected void onResume(", live)

stubs["android/os/Looper.java"] = """
package android.os;
public class Looper {
    private static final Thread MAIN_THREAD = Thread.currentThread();
    private static final Looper MAIN = new Looper();
    public static Looper myLooper() { return Thread.currentThread() == MAIN_THREAD ? MAIN : null; }
    public static Looper getMainLooper() { return MAIN; }
}
"""
stubs["com/fongmi/android/tv/App.java"] = """
package com.fongmi.android.tv;
public class App {
    public static final java.util.concurrent.LinkedBlockingQueue<Runnable> queue =
            new java.util.concurrent.LinkedBlockingQueue<>();
    public static void post(Runnable task) { queue.add(task); }
    public static void drain() { Runnable task; while ((task = queue.poll()) != null) task.run(); }
}
"""
stubs["org/greenrobot/eventbus/EventBus.java"] = """
package org.greenrobot.eventbus;
public class EventBus {
    private static final EventBus INSTANCE = new EventBus();
    public java.util.function.Consumer<Object> subscriber = value -> {};
    public static EventBus getDefault() { return INSTANCE; }
    public void post(Object value) { subscriber.accept(value); }
}
"""
for annotation in ("NonNull", "Nullable"):
    stubs["androidx/annotation/" + annotation + ".java"] = "package androidx.annotation; public @interface " + annotation + " {}"
stubs["androidx/media3/common/MediaMetadata.java"] = "package androidx.media3.common; public class MediaMetadata {}"
stubs["androidx/media3/common/C.java"] = "package androidx.media3.common; public class C { public static final long TIME_UNSET = -1; }"
stubs["com/fongmi/android/tv/bean/Group.java"] = """
package com.fongmi.android.tv.bean;
public record Group(String name) { public String getName() { return name; } }
"""
stubs["com/fongmi/android/tv/bean/Channel.java"] = """
package com.fongmi.android.tv.bean;
public class Channel {
    public final Group group;
    public final String name;
    public int line;
    public Channel(Group group, String name) { this.group = group; this.name = name; }
    public Group getGroup() { return group; }
    public int getIndex() { return line; }
    @Override public boolean equals(Object other) {
        return other instanceof Channel c && name.equals(c.name);
    }
    @Override public int hashCode() { return name.hashCode(); }
}
"""
stubs["com/fongmi/android/tv/bean/EpgData.java"] = "package com.fongmi.android.tv.bean; public class EpgData {}"
stubs["com/fongmi/android/tv/bean/Result.java"] = """
package com.fongmi.android.tv.bean;
public class Result {
    public long position = -1;
    public void setPosition(long position) { this.position = position; }
}
"""
stubs["com/fongmi/android/tv/playback/live/LiveDeliveryTest.java"] = r"""
package com.fongmi.android.tv.playback.live;
import android.os.Looper;
import androidx.media3.common.C;
import com.fongmi.android.tv.App;
import com.fongmi.android.tv.bean.*;
import com.fongmi.android.tv.event.XrayLiveRulesEvent;
import com.fongmi.android.tv.playback.PlaybackResult;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import org.greenrobot.eventbus.EventBus;

public final class LiveDeliveryTest {
    static void check(boolean value, String why) {
        if (!value) throw new AssertionError(why);
    }
    static final class Controller {
        final LivePlaybackState state = new LivePlaybackState();
        static final class Host {
            boolean playing, waiting;
            boolean xrayLiveDeliveryGuard = true;
            boolean usesXrayLiveDeliveryGuard() { return xrayLiveDeliveryGuard; }
            boolean hasPlaybackSession() { return playing; }
            boolean isPlaybackStartPending() { return waiting; }
        }
        final Host host = new Host();
        int refreshes;
        void refresh() { refreshes++; }
        __CONTROLLER__
    }
    static final class Model {
        LivePlayRequest latestUrlRequest;
        boolean xrayLiveDeliveryGuard = true;
        enum TaskType { URL }
        static final class Tasks {
            int cancellations;
            void cancel(TaskType type) { if (type == TaskType.URL) cancellations++; }
        }
        final Tasks tasks = new Tasks();
        final List<PlaybackResult<LivePlayRequest>> published = new ArrayList<>();
        final class Data {
            void setValue(PlaybackResult<LivePlayRequest> value) { published.add(value); }
            void postValue(PlaybackResult<LivePlayRequest> value) { App.post(() -> setValue(value)); }
        }
        final Data playback = new Data();
        __MODEL__
    }
    static void queuedResults() {
        Group group = new Group("G");
        Channel a = new Channel(group, "A"), b = new Channel(group, "B");
        LivePlayRequest oldA = LivePlayRequest.live(a, C.TIME_UNSET);
        LivePlayRequest reqB = LivePlayRequest.live(b, C.TIME_UNSET);
        LivePlayRequest newA = LivePlayRequest.live(a, C.TIME_UNSET);
        check(oldA.matches(newA), "reproduce semantically identical A requests");
        Controller c = new Controller();
        c.state.setChannel(a);
        c.state.setPendingRequest(newA);
        check(c.cannotApply(new PlaybackResult<>(oldA, new Result())), "stale A accepted after A-B-A");
        check(c.cannotApply(new PlaybackResult<>(reqB, new Result())), "stale B accepted");
        check(!c.cannotApply(new PlaybackResult<>(newA, new Result())), "current A rejected");
        c.host.xrayLiveDeliveryGuard = false;
        check(!c.cannotApply(new PlaybackResult<>(oldA, new Result())), "ordinary host no longer uses baseline request matching");
        check(c.cannotApply(new PlaybackResult<>(reqB, new Result())), "ordinary host accepted a different channel");
        c.host.xrayLiveDeliveryGuard = true;
        a.line = 1;
        check(c.cannotApply(new PlaybackResult<>(newA, new Result())), "mutated line accepted");
        a.line = 0;
        c.retirePendingPlayback();
        check(c.cannotApply(new PlaybackResult<>(newA, new Result())), "retired request accepted after handoff");
        check(c.state.getChannel() == a && c.state.getActiveRequest() == null,
                "handoff must preserve station but retire the old request");
        c.state.setPlayingRequest(newA, "synthetic");
        c.host.waiting = true;
        check(c.restorePlaybackIfNeeded() && c.refreshes == 0,
                "same-station selection must keep resolved automatic start");
        c.host.waiting = false;
        check(c.restorePlaybackIfNeeded() && c.refreshes == 1,
                "ordinary missing playback still refreshes");
        c.host.playing = true;
        check(!c.restorePlaybackIfNeeded() && c.refreshes == 1,
                "playing session must not refresh");

        Model m = new Model();
        m.latestUrlRequest = oldA;
        m.postUrl(oldA, new Result());
        m.latestUrlRequest = newA;
        Result current = new Result();
        m.postUrl(newA, current);
        m.postUrl(oldA, new Result()); // late stale result must not overwrite new result
        App.drain();
        check(m.published.size() == 1 && m.published.get(0).request() == newA
                && m.published.get(0).result() == current, "queued old URL displaced current URL");
        m.postUrl(newA, new Result());
        m.cancelPlaybackUrl();
        App.drain();
        check(m.published.size() == 1 && m.tasks.cancellations == 1,
                "retired model delivered old URL or did not cancel resolver");
        Model ordinary = new Model();
        ordinary.xrayLiveDeliveryGuard = false;
        LivePlayRequest ordinaryRequest = LivePlayRequest.live(a, 123);
        Result ordinaryResult = new Result();
        ordinary.postUrl(ordinaryRequest, ordinaryResult);
        App.drain();
        check(ordinary.published.size() == 1 && ordinary.published.get(0).request() == ordinaryRequest
                && ordinaryResult.position == 123, "ordinary URL delivery now requires a Xray request token");
    }
    static void phoneDelivery() throws Exception {
        Looper.getMainLooper();
        EventBus bus = EventBus.getDefault();
        bus.subscriber = event -> {}; // generic Object subscriber, or RESET_SECURITY
        check(!XrayLiveRulesEvent.post("G", "A"), "generic subscriber falsely acknowledged");
        AtomicInteger received = new AtomicInteger();
        bus.subscriber = value -> {
            XrayLiveRulesEvent event = (XrayLiveRulesEvent) value;
            check(Looper.myLooper() == Looper.getMainLooper(), "delivery not on main");
            check(event.groups().isEmpty() && event.channels().isEmpty(), "empty lists must clear both fields");
            received.incrementAndGet();
            event.markApplied();
        };
        check(XrayLiveRulesEvent.post("", ""), "applied empty lists not acknowledged");
        AtomicReference<Boolean> accepted = new AtomicReference<>();
        Thread worker = new Thread(() -> accepted.set(XrayLiveRulesEvent.post("", "")));
        worker.start();
        Runnable delivery = App.queue.poll(2, TimeUnit.SECONDS);
        check(delivery != null, "HTTP thread did not dispatch");
        delivery.run();
        worker.join(2000);
        check(Boolean.TRUE.equals(accepted.get()) && received.get() == 2, "HTTP thread did not receive applied acknowledgement");

        Thread interrupted = new Thread(() -> accepted.set(XrayLiveRulesEvent.post("", "")));
        interrupted.start();
        Runnable canceled = App.queue.poll(2, TimeUnit.SECONDS);
        check(canceled != null, "missing pending delivery");
        interrupted.interrupt();
        interrupted.join(2000);
        canceled.run();
        check(Boolean.FALSE.equals(accepted.get()) && received.get() == 2, "canceled HTTP delivery applied later");
    }
    public static void main(String[] args) throws Exception {
        queuedResults(); phoneDelivery();
        System.out.println("PASS: Live request identity, main-thread delivery and phone acknowledgement");
    }
}
""".replace("__CONTROLLER__", "\n".join(method(signature, controller_source) for signature in (
    "private boolean cannotApply(", "private boolean restorePlaybackIfNeeded(", "public void retirePendingPlayback(",
))).replace("__MODEL__", "\n".join(method(signature, model_source) for signature in (
    "private void postUrl(", "public void cancelPlaybackUrl(",
)))

# Run the actual LiveViewModel metadata methods with controlled worker and
# main-thread queues. In particular, cancellation cannot retract a previously
# queued LiveData.postValue, so validation must happen at delivery time.
assert "cancelPlaybackMetadata();" in method("protected void onCleared(", model_source)
stubs["MetadataDeliveryTest.java"] = r"""
import com.fongmi.android.tv.App;
import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.Consumer;

public class MetadataDeliveryTest {
    static class Epg {
        final String name;
        Epg() { this(""); }
        Epg(String name) { this.name = name; }
    }
    record Live(String name) {}
    record Channel(String name) {}
    static class OkHttpClient {}
    static class LiveApi {
        static boolean parseXml(Live item, OkHttpClient client) { return true; }
        static Epg getEpg(Channel item, Object zone, OkHttpClient client) { return new Epg(item.name()); }
    }
    static class Data<T> {
        List<T> delivered = new ArrayList<>();
        void setValue(T value) { delivered.add(value); }
        void postValue(T value) { App.post(() -> setValue(value)); }
    }
    enum TaskType { EPG, XML }
    static class Model {
        final Object zoneId = new Object();
        final Data<Epg> epg = new Data<>();
        final Data<Boolean> xml = new Data<>();
        final Tasks tasks = new Tasks();
        boolean xrayLiveDeliveryGuard = true;
        private long epgGeneration;
        private long xmlGeneration;
        static class Tasks {
            int cancels;
            void cancel(TaskType type) { cancels++; }
        }
        final List<Runnable> successes = new ArrayList<>();
        final List<Runnable> failures = new ArrayList<>();
        <T> void execute(TaskType type, Callable<T> work, Consumer<T> onSuccess, Consumer<Throwable> onError) {
            successes.add(() -> { try { onSuccess.accept(work.call()); } catch (Exception e) { throw new RuntimeException(e); } });
            failures.add(() -> onError.accept(new RuntimeException("old failure")));
        }
        __METADATA_METHODS__
    }
    static void check(boolean value, String msg) { if (!value) throw new AssertionError(msg); }
    public static void main(String[] args) {
        Model m = new Model();
        m.getEpg(new Channel("old"), null);
        m.parseXml(new Live("old"), null);
        m.successes.get(0).run(); m.successes.get(1).run();
        m.cancelPlaybackMetadata();
        App.drain();
        check(m.epg.delivered.isEmpty() && m.xml.delivered.isEmpty(), "canceled EPG/XML delivered to new playback");
        check(m.tasks.cancels == 2, "metadata workers not canceled");
        m.getEpg(new Channel("A"), null);
        m.parseXml(new Live("A"), null);
        m.getEpg(new Channel("B"), null);
        m.parseXml(new Live("B"), null);
        m.successes.get(4).run(); m.successes.get(5).run();
        m.failures.get(2).run(); m.failures.get(3).run();
        App.drain();
        check(m.epg.delivered.size() == 1 && m.epg.delivered.get(0).name.equals("B"), "stale EPG failure displaced latest");
        check(m.xml.delivered.equals(List.of(true)), "stale XML failure displaced latest");
        m.getEpg(new Channel("current"), null);
        m.parseXml(new Live("current"), null);
        m.failures.get(6).run(); m.failures.get(7).run();
        App.drain();
        check(m.epg.delivered.size() == 2 && m.epg.delivered.get(1).name.isEmpty(), "latest EPG error dropped");
        check(m.xml.delivered.equals(List.of(true, false)), "latest XML error dropped");
        Model ordinary = new Model();
        ordinary.xrayLiveDeliveryGuard = false;
        ordinary.getEpg(new Channel("ordinary"), null);
        ordinary.parseXml(new Live("ordinary"), null);
        ordinary.successes.get(0).run(); ordinary.successes.get(1).run();
        App.drain();
        check(ordinary.epg.delivered.size() == 1 && ordinary.epg.delivered.get(0).name.equals("ordinary")
                && ordinary.xml.delivered.equals(List.of(true)), "ordinary metadata delivery changed");
        check(ordinary.epgGeneration == 0 && ordinary.xmlGeneration == 0, "ordinary metadata used Xray generations");
        System.out.println("PASS: guarded EPG/XML delivery and unguarded ordinary path");
    }
}
""".replace("__METADATA_METHODS__", "\n".join(method(signature, model_source) for signature in (
    "public void parseXml(Live item, OkHttpClient client)",
    "private void postXml(",
    "public void getEpg(Channel item, OkHttpClient client)",
    "private void postEpg(",
    "public void cancelPlaybackMetadata(",
)))

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
    for rel in ("com/fongmi/android/tv/event/XrayLiveRulesEvent.java",
                "com/fongmi/android/tv/playback/PlaybackResult.java",
                "com/fongmi/android/tv/playback/live/LivePlayRequest.java",
                "com/fongmi/android/tv/playback/live/LivePlaybackState.java"):
        sources.append(str(APP_JAVA / rel))
    subprocess.run(["java", "com.sun.tools.javac.Main", "--release", "17", "-d", str(work), *sources], check=True)
    subprocess.run(["java", "-cp", str(work), "LiveAutoTest"], check=True)
    subprocess.run(["java", "-cp", str(work), "EngineChangeTest"], check=True)
    subprocess.run(["java", "-cp", str(work), "LateOwnerResumeTest"], check=True)
    for case in ("source-pending", "source-active", "reclaim-explicit", "reclaim-normal", "ordinary"):
        subprocess.run(["java", "-cp", str(work), "RetiredMetadataTest", case], check=True)
    subprocess.run(["java", "-cp", str(work), "IdleProxyEngineTest"], check=True)
    subprocess.run(["java", "-cp", str(work), "com.fongmi.android.tv.playback.live.LiveDeliveryTest"], check=True)
    subprocess.run(["java", "-cp", str(work), "MetadataDeliveryTest"], check=True)
