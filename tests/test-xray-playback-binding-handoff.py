#!/usr/bin/env python3
"""Run actual Activity binding methods with real XrayPlaybackSession ownership."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java'
SERVICE = ROOT / 'app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java'
LEANBACK = ROOT / 'app/src/leanback/java/com/fongmi/android/tv/ui/activity'


def method(path, signature):
    text = path.read_text(encoding='utf-8')
    start = text.index(signature)
    opening = text.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


base_methods = '\n'.join(method(BASE, signature) for signature in (
    'protected boolean isOwner()', 'protected boolean isBindingOwner()', 'private void claimBinding()',
    'protected void onXrayBindingReplaced()', 'private void activateService()',
    'private void initService()', 'private void closePiP()',
))
service_methods = '\n'.join(method(SERVICE, signature) for signature in (
    'public void claimBinding(', 'public boolean ownsBinding(',
))
activity_methods = {}
for name in ('VideoActivity', 'LiveActivity'):
    activity_methods[name] = '\n'.join(method(LEANBACK / (name + '.java'), signature) for signature in (
        'protected void onXrayBindingReplaced()', 'public void resetXrayForPlaybackChange()',
    ))
    text = (LEANBACK / (name + '.java')).read_text(encoding='utf-8')
    guard = 'isBindingOwner()' if name == 'LiveActivity' else 'isOwner()'
    assert f'if (service() != null && {guard}) {{' in text
    assert 'player().setPlaybackProxy(resources, preserve);' in text

HARNESS = r'''
import com.fingmi.xray.session.*;
import com.fingmi.xray.network.XrayHttpClient;
import okhttp3.OkHttpClient;
import java.util.ArrayList;
import java.util.List;

class PlayerManager {
    String key;
    XrayHttpClient proxy;
    String getKey() { return key; }
    void setPlaybackProxy(XrayHttpClient next, boolean preserve) { proxy = next; }
    void start(String nextKey) { key = nextKey; }
}
class PlaybackService {
    interface NavigationCallback {}
    record ActivityBinding(NavigationCallback owner, Runnable onReplaced) {}
    ActivityBinding binding;
    final PlayerManager manager = new PlayerManager();
    void setSessionActivity(Object intent) {}
    __SERVICE_METHODS__
}
class Activity {
    PlaybackService mService;
    final String key;
    final PlaybackService.NavigationCallback navigation = new PlaybackService.NavigationCallback() {};
    boolean initialized, pip, detached, finished;
    Runnable pending;
    Activity(PlaybackService service, String key) { mService = service; this.key = key; }
    PlayerManager player() { return mService.manager; }
    String getPlaybackKey() { return key; }
    PlaybackService.NavigationCallback getNavigationCallback() { return navigation; }
    Object buildSessionIntent() { return this; }
    boolean canActivate() { return mService != null; }
    boolean isRedirect() { return false; }
    void updateNavigationKey() {}
    void dispatchPendingObservers() { if (pending != null) { Runnable next = pending; pending = null; next.run(); } }
    void onServiceConnected() {}
    boolean isInPictureInPictureMode() { return pip; }
    void detach() { detached = true; mService = null; }
    void finish() { finished = true; }
    void activate() { activateService(); }
    __BASE_METHODS__
}
abstract class XrayActivity extends Activity {
    XrayPlaybackSession mXray;
    final XrayLiveAutoPlayback mLiveAuto = new XrayLiveAutoPlayback();
    int mPlaybackEpoch;
    boolean xrayPlaybackReady, mXrayPendingChannelResume, mXrayStartedFromExistingPlayback, mXrayRefreshMetadataOnDetach;
    boolean stopOnProxyAttach, restartOnProxyAttach;
    boolean restartOnProxyDetach, throwAfterRestartOnProxyAttach;
    boolean throwOnFirstAttach, retryInProxyError, retryAtErrorState;
    XrayHttpClient retiredProxy;
    final List<Integer> states = new ArrayList<>();
    final List<Integer> attachedPorts = new ArrayList<>();
    int attaches, detaches;
    XrayActivity(PlaybackService service, String key) {
        super(service, key);
        mXray = new XrayPlaybackSession(new android.content.Context(), new OkHttpClient(), new XrayPlaybackSession.Listener() {
            public void onProxyChanged(XrayHttpClient resources, boolean preserve) {
                // Same owner guard and player proxy installation as both Leanback Activities.
                if (resources != null && stopOnProxyAttach) {
                    stopOnProxyAttach = false;
                    mXray.stop(false);
                    return;
                }
                if (resources != null && restartOnProxyAttach) {
                    restartOnProxyAttach = false;
                    retiredProxy = resources;
                    mXray.stop(false);
                    if (!mXray.enable()) throw new AssertionError("reentrant retry refused");
                    return;
                }
                if (resources == null && restartOnProxyDetach) {
                    restartOnProxyDetach = false;
                    mXray.stop(false);
                    if (!mXray.enable()) throw new AssertionError("detach retry refused");
                    return;
                }
                if (resources != null && throwAfterRestartOnProxyAttach) {
                    throwAfterRestartOnProxyAttach = false;
                    retiredProxy = resources;
                    mXray.stop(false);
                    if (!mXray.enable()) throw new AssertionError("failure retry refused");
                    throw new IllegalStateException("stale attach failed after replacement");
                }
                if (resources != null && throwOnFirstAttach) {
                    throwOnFirstAttach = false;
                    retiredProxy = resources;
                    throw new IllegalStateException("synthetic initial attach failure");
                }
                if (mService != null && (XrayActivity.this instanceof LiveActivity ? isBindingOwner() : isOwner())) {
                    player().setPlaybackProxy(resources, preserve);
                    if (resources == null) detaches++;
                    else { attaches++; attachedPorts.add(resources.port); }
                }
            }
            @Override public void onProxyError() {
                if (retryInProxyError) {
                    retryInProxyError = false;
                    mXray.stop(false);
                    if (!mXray.enable()) throw new AssertionError("rollback retry refused");
                    return;
                }
                onProxyChanged(null, false);
            }
            public void onStateChanged(int state, String message) {
                states.add(state);
                if (state == XraySessionListener.ERROR && retryAtErrorState) {
                    retryAtErrorState = false;
                    mXray.stop(false);
                    if (!mXray.enable()) throw new AssertionError("ERROR listener retry refused");
                }
            }
        });
        mXray.begin(key + ":initial");
    }
    void enable() {
        mXray.mediaUrlChanged("https://media.example/stream");
        check(mXray.enable(), "manual enable succeeds");
    }
    void lateStop() { mXray.stop(false); }
    static void check(boolean value, String message) { HandoffTest.check(value, message); }
}
class VideoActivity extends XrayActivity {
    VideoActivity(PlaybackService service, String key) { super(service, key); }
    __VIDEO_METHODS__
}
class LiveActivity extends XrayActivity {
    LiveActivity(PlaybackService service, String key) { super(service, key); }
    __LIVE_METHODS__
}
public class HandoffTest {
    static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    static XrayActivity activity(boolean live, PlaybackService service, String key) {
        return live ? new LiveActivity(service, key) : new VideoActivity(service, key);
    }
    static void transfer(boolean oldLive, boolean pendingLiveStart, boolean sameKey) {
        PlaybackService service = new PlaybackService();
        String nextKey = sameKey ? "A" : "B";
        XrayActivity a = activity(oldLive, service, "A");
        service.manager.start("A");
        a.activate(); a.enable();
        XrayHttpClient old = a.mXray.resources();
        check(service.manager.proxy == old && !old.closed, "A owns open client");
        a.activate();
        check(a.mXray.resources() == old && !old.closed, "same binding claim keeps active session");

        XrayActivity b = activity(!oldLive, service, nextKey);
        b.pending = () -> {
            check(old.closed && a.mXray.resources() == null && service.manager.proxy == null,
                    "old session and player client released BEFORE new pending playback starts");
            check(!a.mXray.isActive(), "old service stopped at binding handoff");
            if (pendingLiveStart) {
                check(b.mXray.enableForPending("https://live.example/channel"), "new pending Live session enables");
                // Starting the new PlaySpec must not introduce an unconditional proxy reset.
                XrayHttpClient pending = b.mXray.resources();
                check(pending != null && !pending.closed, "pending session stays owned");
            }
            service.manager.start(nextKey);
            if (!pendingLiveStart) b.enable();
        };
        b.activate();
        XrayHttpClient current = b.mXray.resources();
        check(current != null && !current.closed, "new owner has active resource");
        check(service.manager.proxy == current, "new binding owner client installed, even before its media key");
        a.lateStop(); a.mXray.close();
        check(b.mXray.resources() == current && !current.closed, "late A stop/destroy cannot close B");
        check(service.manager.proxy != old, "shared player does not retain closed A client");
        b.activate();
        check(b.mXray.resources() == current && !current.closed, "repeat new-owner claim preserves pending/active session");
        b.mXray.close();
    }
    static void reentrantStopDuringProxyAttachDoesNotPublishStaleRunning() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.stopOnProxyAttach = true;
        a.enable();
        check(a.mXray.state() == XraySessionListener.IDLE,
                "reentrant owner stop did not leave controller IDLE");
        check(a.mXray.resources() == null && service.manager.proxy == null,
                "reentrant owner stop did not retire the just-created proxy");
        check(!a.states.isEmpty()
                        && a.states.get(a.states.size() - 1) == XraySessionListener.IDLE,
                "stale outer RUNNING callback overwrote reentrant IDLE");
    }
    static void sameStateReentrantRetryDoesNotRepublishOldRunning() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.states.clear();
        a.restartOnProxyAttach = true;
        a.enable();
        check(a.mXray.state() == XraySessionListener.RUNNING,
                "reentrant retry did not leave controller RUNNING");
        check(a.retiredProxy != null && a.retiredProxy.closed,
                "reentrant retry leaked old proxy");
        check(a.mXray.resources() != null && a.mXray.resources() != a.retiredProxy
                        && !a.mXray.resources().closed,
                "reentrant retry lost the replacement proxy");
        check(a.states.equals(List.of(XraySessionListener.IDLE,
                        XraySessionListener.RUNNING)),
                "stale outer RUNNING was published after IDLE -> replacement RUNNING: " + a.states);
        a.mXray.close();
    }
    static void restartInsideOldProxyDetachDoesNotInstallStaleEndpoint() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.enable();
        XrayHttpClient first = a.mXray.resources();
        a.states.clear();
        a.restartOnProxyDetach = true;
        // A duplicate RUNNING result may arrive while the old proxy is bound.
        a.mXray.onXrayStateChanged(XraySessionListener.RUNNING, 9999, "stale");
        check(first.closed, "duplicate RUNNING did not close the previous proxy");
        check(a.mXray.state() == XraySessionListener.RUNNING,
                "detach retry did not reach RUNNING");
        check(a.mXray.resources() != null && !a.mXray.resources().closed
                        && a.mXray.resources().port == 12345,
                "old RUNNING overwrote newer proxy resource");
        check(a.attachedPorts.equals(List.of(12345, 12345)),
                "obsolete proxy port was installed after a reentrant retry: " + a.attachedPorts);
        check(a.states.equals(List.of(XraySessionListener.IDLE, XraySessionListener.RUNNING)),
                "duplicate RUNNING re-published obsolete state: " + a.states);
        a.mXray.close();
    }
    static void throwingOldAttachDoesNotStopNewRetry() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.states.clear();
        a.throwAfterRestartOnProxyAttach = true;
        a.enable();
        check(a.retiredProxy != null && a.retiredProxy.closed,
                "throwing old attach did not close the superseded proxy");
        check(a.mXray.state() == XraySessionListener.RUNNING
                        && a.mXray.resources() != null && !a.mXray.resources().closed
                        && a.mXray.resources() != a.retiredProxy,
                "obsolete attach error rolled back the new RUNNING session");
        check(a.states.equals(List.of(XraySessionListener.IDLE, XraySessionListener.RUNNING)),
                "obsolete attach published ERROR or extra state after new retry: " + a.states);
        a.mXray.close();
    }
    static void proxyRollbackRetryCannotBeStoppedByOldFailure() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.states.clear();
        a.throwOnFirstAttach = true;
        a.retryInProxyError = true;
        a.enable();
        check(a.retiredProxy != null && a.retiredProxy.closed,
                "failed first proxy was not closed");
        check(a.mXray.state() == XraySessionListener.RUNNING
                        && a.mXray.resources() != null && !a.mXray.resources().closed
                        && a.mXray.resources() != a.retiredProxy,
                "old rollback stopped newer proxy");
        check(a.states.equals(List.of(XraySessionListener.IDLE, XraySessionListener.RUNNING)),
                "old rollback emitted stale ERROR/IDLE after retry: " + a.states);
        a.mXray.close();
    }
    static void errorListenerRetryCannotBeStoppedByOldFailure() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.states.clear();
        a.throwOnFirstAttach = true;
        a.retryAtErrorState = true;
        a.enable();
        check(a.retiredProxy != null && a.retiredProxy.closed,
                "ERROR listener failure did not release its old proxy");
        check(a.mXray.state() == XraySessionListener.RUNNING
                        && a.mXray.resources() != null && !a.mXray.resources().closed,
                "old post-ERROR STOP killed the retry");
        check(a.states.equals(List.of(XraySessionListener.ERROR, XraySessionListener.IDLE,
                        XraySessionListener.RUNNING)),
                "old failure published a trailing IDLE over reentrant retry: " + a.states);
        a.mXray.close();
    }
    static void ordinaryAttachFailureStillStops() {
        PlaybackService service = new PlaybackService();
        XrayActivity a = activity(false, service, "A");
        service.manager.start("A");
        a.activate();
        a.states.clear();
        a.throwOnFirstAttach = true;
        a.enable();
        check(a.retiredProxy != null && a.retiredProxy.closed,
                "ordinary failed attach leaked proxy");
        check(a.mXray.state() == XraySessionListener.IDLE && a.mXray.resources() == null,
                "ordinary attach failure did not stop");
        check(a.states.equals(List.of(XraySessionListener.ERROR, XraySessionListener.IDLE)),
                "ordinary failure lost ERROR -> IDLE contract: " + a.states);
        a.mXray.close();
    }
    static void mobile(boolean pip) {
        PlaybackService service = new PlaybackService();
        Activity a = new Activity(service, "A"); a.pip = pip; a.activate();
        Activity b = new Activity(service, "B"); b.activate();
        check(a.detached == pip && a.finished == pip, "default hook preserves upstream Mobile PiP behavior");
    }
    public static void main(String[] args) {
        for (boolean oldLive : new boolean[]{false, true})
            for (boolean sameKey : new boolean[]{false, true}) transfer(oldLive, false, sameKey);
        transfer(false, true, true);
        transfer(false, true, false);
        reentrantStopDuringProxyAttachDoesNotPublishStaleRunning();
        sameStateReentrantRetryDoesNotRepublishOldRunning();
        restartInsideOldProxyDetachDoesNotInstallStaleEndpoint();
        throwingOldAttachDoesNotStopNewRetry();
        proxyRollbackRetryCannotBeStoppedByOldFailure();
        errorListenerRetryCannotBeStoppedByOldFailure();
        ordinaryAttachFailureStillStops();
        mobile(false); mobile(true);
        System.out.println("PASS real Activity/Service binding methods + XrayPlaybackSession: 4 cross-owner/key transfers, reentrant STOP/retry, detach and failure rollback generations, pending Live start, late stop/close, repeated claims and Mobile PiP behavior");
    }
}
'''

STUBS = {
    'android/content/Context.java': 'package android.content; public class Context {}',
    'android/os/Looper.java': 'package android.os; public class Looper { static final Looper MAIN=new Looper(); public static Looper myLooper(){return MAIN;} public static Looper getMainLooper(){return MAIN;} }',
    'okhttp3/OkHttpClient.java': 'package okhttp3; public class OkHttpClient {}',
    'com/fingmi/xray/network/XrayHttpClient.java': 'package com.fingmi.xray.network; import okhttp3.OkHttpClient; public class XrayHttpClient implements AutoCloseable { public boolean closed; public final int port; public XrayHttpClient(int port,OkHttpClient base){this.port=port;} public OkHttpClient client(){return new OkHttpClient();} public void close(){closed=true;} }',
    'com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java': 'package com.fingmi.xray.network; public class PublicPlaybackDestinationInterceptor {}',
    'com/fingmi/xray/util/XrayErrorSanitizer.java': 'package com.fingmi.xray.util; public class XrayErrorSanitizer {public static String sanitize(Throwable error){return "failure";} }',
    'com/fingmi/xray/session/XrayPlaybackAddress.java': 'package com.fingmi.xray.session; public class XrayPlaybackAddress {public static boolean supports(String url){return url!=null && url.startsWith("https://");} public static boolean supportsDirectLiveSource(String url){return supports(url);} }',
    'com/fingmi/xray/session/XraySessionController.java': '''package com.fingmi.xray.session;
import android.content.Context;
public class XraySessionController {
    final XraySessionListener listener; int state=XraySessionListener.IDLE;
    public XraySessionController(Context context,XraySessionListener listener){this.listener=listener;}
    public boolean isRunning(){return state==XraySessionListener.RUNNING;} public int getState(){return state;}
    public void start(){state=XraySessionListener.RUNNING;listener.onXrayStateChanged(state,12345,"");}
    public void stop(){if(state==XraySessionListener.IDLE)return;state=XraySessionListener.IDLE;listener.onXrayStateChanged(state,0,"");}
    public void close(){stop();}
}''',
}

harness = HARNESS.replace('__BASE_METHODS__', base_methods).replace('__SERVICE_METHODS__', service_methods)
harness = harness.replace('__VIDEO_METHODS__', activity_methods['VideoActivity']).replace('__LIVE_METHODS__', activity_methods['LiveActivity'])
with tempfile.TemporaryDirectory(prefix='xray-binding-handoff-') as directory:
    work = Path(directory)
    sources = []
    for name, content in {**STUBS, 'HandoffTest.java': harness}.items():
        file = work / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding='utf-8')
        sources.append(str(file))
    sources += [str(ROOT / 'xray/src/main/java/com/fingmi/xray/session' / name) for name in (
        'XrayPlaybackSession.java', 'XraySessionListener.java', 'PlaybackIdentityGate.java', 'XrayLiveAutoPlayback.java',
    )]
    subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '17', '-d', str(work), *sources], check=True)
    subprocess.run(['java', '-cp', str(work), 'HandoffTest'], check=True)
