#!/usr/bin/env python3
"""Execute PlaybackActivity's real client-selection path before/after binding."""

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java"


def method(signature):
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index(signature)
    body = text.index("{", start)
    depth = 1
    end = body + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


# Extract the whole production init/configure/accessor/selection methods. Only
# Android UI, service binding and HTTP clients are substitutes; copying the
# selection or testing only the bound path would miss the cold-start failure.
methods = "\n".join(method(signature) for signature in (
    "protected PlayerManager player()",
    "private void configurePlayerView()",
    "protected final void updatePlaybackDanmakuClient()",
    "protected void initView(Bundle savedInstanceState)",
))

HARNESS = r"""
class Bundle {}
class BaseActivity { protected void initView(Bundle state) {} }
class OkHttpClient {}
class OkHttp {
    static final OkHttpClient DIRECT = new OkHttpClient();
    static OkHttpClient player() { return DIRECT; }
}
class PlayerManager {
    OkHttpClient proxy;
    OkHttpClient getPlaybackHttpClient(OkHttpClient fallback) {
        return proxy == null ? fallback : proxy;
    }
}
class PlaybackService {
    final PlayerManager manager = new PlayerManager();
    int accesses;
    PlayerManager player() { accesses++; return manager; }
}
class DanmakuPlayerViewController {
    OkHttpClient client;
    void setOkHttpClient(OkHttpClient next) { client = next; }
    void setEnabled(boolean enabled) {}
    void setConfig(Object config) {}
}
class PlayerView {
    void setRender(int render) {}
    Object getSubtitleView() { return this; }
}
class PlayerSetting { static int getRender() { return 0; } }
class DanmakuSetting {
    static boolean isShow() { return true; }
    static Object getConfig() { return null; }
}
class SubtitleSetting { static void applyStyle(Object view) {} }

public final class PlaybackActivityBindingTest extends BaseActivity {
    private final DanmakuPlayerViewController danmakuController = new DanmakuPlayerViewController();
    private PlaybackService mService;
    private final PlayerView view = new PlayerView();
    private boolean bindingRequested;
    private boolean seekAdded;

    PlayerView getPlayerView() { return view; }
    void bindPlaybackService() {
        check(danmakuController.client == OkHttp.DIRECT,
                "view must use the upstream direct client before requesting service binding");
        bindingRequested = true;
        // Android binding completes asynchronously, not inside this call.
    }
    void addSeekListener() {
        check(bindingRequested, "production initialization order");
        seekAdded = true;
    }

    __PRODUCTION_METHODS__

    static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        PlaybackActivityBindingTest activity = new PlaybackActivityBindingTest();
        activity.initView(null);
        check(activity.seekAdded && activity.mService == null, "cold creation awaits binding");
        check(activity.danmakuController.client == OkHttp.DIRECT, "cold creation direct fallback");

        activity.mService = new PlaybackService();
        PlaybackService service = activity.mService;
        activity.updatePlaybackDanmakuClient();
        check(activity.danmakuController.client == OkHttp.DIRECT, "bound direct playback");
        check(service.accesses == 1, "bound service owns client selection");

        OkHttpClient proxy = new OkHttpClient();
        service.manager.proxy = proxy;
        activity.updatePlaybackDanmakuClient();
        check(activity.danmakuController.client == proxy, "bound Xray playback client");

        service.manager.proxy = null;
        activity.updatePlaybackDanmakuClient();
        check(activity.danmakuController.client == OkHttp.DIRECT, "proxy detach restores direct");

        activity.mService = null;
        int before = service.accesses;
        activity.updatePlaybackDanmakuClient();
        check(activity.danmakuController.client == OkHttp.DIRECT, "disconnected fallback");
        check(service.accesses == before, "disconnected selection never accesses the old service");
        System.out.println("PASS actual PlaybackActivity initialization and 4 client-binding transitions");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-danmaku-binding-") as directory:
    work = Path(directory)
    source = work / "PlaybackActivityBindingTest.java"
    source.write_text(HARNESS.replace("__PRODUCTION_METHODS__", methods), encoding="utf-8")
    subprocess.run(["java", "com.sun.tools.javac.Main", "--release", "17",
                    "-d", str(work), str(source)], check=True)
    subprocess.run(["java", "-cp", str(work), "PlaybackActivityBindingTest"], check=True)
