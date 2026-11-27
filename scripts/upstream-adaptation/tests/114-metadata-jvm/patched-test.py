#!/usr/bin/env python3
"""Pinned 5.9 Live metadata and VOD owner regression; no APK or Android linkage."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/upstream-adaptation"))
from prepare_candidate import LOCK, blob, guard_fork, overlay, verified_checkout
from verify_recovery_batch import method

BASE = "app/src/main/java/com/fongmi/android/tv/"
FIXTURE = r'''
import java.io.*;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.*;

@interface NonNull {}
class OkHttpClient {}
class Formatters { static final DateTimeFormatter DATE = DateTimeFormatter.ISO_LOCAL_DATE; }
class Epg {
    String day;
    Epg() {}
    Epg(String day) { this.day = day; }
    boolean equal(String date) { return date.equals(day); }
    static Epg objectFrom(String body, String id, String date, ZoneId zone) { return new Epg(date); }
}
class EpgSelection { Epg selected() { return new Epg(); } }
class Channel {
    final List<Epg> days = new ArrayList<>();
    String getEpg() { return "https://example.invalid/{date}"; }
    List<Epg> getDataList() { return days; }
    String getTvgId() { return "tv"; }
    void setData(Epg value) { days.add(value); }
    EpgSelection getData(ZoneId zone) { return new EpgSelection(); }
}
class Live {
    final List<String> urls = new ArrayList<>();
    int bound;
    Live(String... values) { urls.addAll(Arrays.asList(values)); }
    List<String> getEpgXml() { return urls; }
    ZoneId getZoneId() { return ZoneId.of("UTC"); }
}
class Response implements AutoCloseable {
    Response body() { return this; }
    String string() { if (OkHttp.interrupt) Thread.currentThread().interrupt(); return "epg"; }
    public void close() {}
}
class Call { Response execute() { return new Response(); } }
class OkHttp {
    static int direct, routed;
    static boolean interrupt;
    static OkHttpClient chosen;
    static String tag;
    static String string(String url) { direct++; return "epg"; }
    static Call newCall(OkHttpClient client, String url, String value) {
        routed++; chosen = client; tag = value; return new Call();
    }
}
class Path {
    static File dir;
    static File epg() { return dir; }
    static File epg(String name) { return new File(dir, name); }
    static void clear(File file) throws IOException { if (file != null) Files.deleteIfExists(file.toPath()); }
    static void move(File from, File to) throws IOException {
        Files.move(from.toPath(), to.toPath(), StandardCopyOption.REPLACE_EXISTING);
    }
}
class Crypto { static String md5(String url) { return Integer.toHexString(url.hashCode()); } }
class Archive { static boolean gzipDecompress(File from, File to) { throw new AssertionError("not gzip fixture"); } }
class Log { static void i(String tag, String message) {} static void w(String tag, String message) {} }
class Download {
    static int downloads;
    static OkHttpClient chosen;
    static String chosenTag;
    static boolean interrupt;
    final File file;
    Download(File file) { this.file = file; }
    static Download create(String url, File file) { return new Download(file); }
    Download client(OkHttpClient client) { chosen = client; return this; }
    Download tag(String tag) { chosenTag = tag; return this; }
    void get() throws IOException {
        downloads++;
        Files.writeString(file.toPath(), "epg");
        if (interrupt) Thread.currentThread().interrupt();
    }
}
class EpgParser {
    static final String TAG = "EpgParser";
    static class XmlData {}
    static class ProgrammeResult {}
    static boolean isFresh(File file) { return file.isFile(); }
    static boolean isGzip(File file) { return false; }
    static XmlData parseXmlData(File file) throws IOException {
        if (!Files.readString(file.toPath()).equals("epg")) throw new IOException("bad fixture");
        return new XmlData();
    }
    static Object prepareLiveChannels(Live live) { return live; }
    static ProgrammeResult processProgramme(XmlData data, Object channels, ZoneId zone) { return new ProgrammeResult(); }
    static void bindResultsToLive(Live live, ProgrammeResult result) { live.bound++; }
    __XML__
}
class LiveApi {
    static final String METADATA_TAG = LiveApi.class.getName().concat(".metadata");
    __LIVE__
    static void parse(Live live) {}
    static Result getUrl(Channel channel) { return new Result(); }
    static Result getUrl(Channel channel, Object catchup) { return new Result(); }
}
class Result {
    long position;
    void setPosition(long value) { position = value; }
    static Result error(String s) { return new Result(); }
    String getKey() { return "key"; }
    String getDanmaku() { return ""; }
}
class C { static final long TIME_UNSET = -1; }
class App {
    static final Queue<Runnable> queue = new ArrayDeque<>();
    static void post(Runnable callback) { queue.add(callback); }
    static void drain() { while (!queue.isEmpty()) queue.remove().run(); }
}
class LiveData<T> { T value; int deliveries; }
class MutableLiveData<T> extends LiveData<T> {
    void setValue(T value) { this.value = value; deliveries++; }
    void postValue(T value) { setValue(value); }
}
class ViewModel { protected void onCleared() {} }
interface LiveDataSource { void getUrl(LivePlayRequest request); void cancelUrl(); }
class LivePlaybackHost {
    final boolean guard;
    LivePlaybackHost(boolean guard) { this.guard = guard; }
    boolean usesXrayLiveDeliveryGuard() { return guard; }
}
class LivePlaybackState { void reset() {} }
class LivePlaybackController {
    LivePlaybackController(LivePlaybackHost host, LiveViewModel model, LivePlaybackState state) {}
}
class LivePlayRequest {
    final long position;
    LivePlayRequest(long position) { this.position = position; }
    long getPosition() { return position; }
    Channel getChannel() { return new Channel(); }
    boolean isCatchup() { return false; }
    Object getCatchupData() { return null; }
}
class PlaybackResult<T> {
    final T request; final Result result;
    PlaybackResult(T request, Result result) { this.request = request; this.result = result; }
}
class Notify { static String getError(Throwable t) { return t.toString(); } }
class Constant {
    static final long TIMEOUT_LIVE = 1, TIMEOUT_EPG = 1, TIMEOUT_XML = 1, TIMEOUT_PARSE_LIVE = 1;
}
class ViewModelTaskRunner<T extends Enum<T>> {
    ViewModelTaskRunner(Class<T> kind) {}
    void cancel(T type) {}
    void cancelAll() {}
    <V> void execute(T type, long timeout, Callable<V> call, Consumer<V> success, Consumer<Throwable> error) {
        try { success.accept(call.call()); } catch (Exception e) { error.accept(e); }
    }
}
__VIEWMODEL__
class History { String getVodName() { return "title"; } }
class Episode { String getName() { return "episode"; } }
class Danmaku {}
class VodConfig {
    static VodConfig get() { return new VodConfig(); }
    VodConfig getSite(String key) { return this; }
    int getDanmaku() { return 1; }
}
class DanmakuSetting { static boolean isSpiderFirst() { return false; } }
class DanmakuApi {
    static int cancels, active, direct;
    static OkHttpClient chosen;
    static Consumer<List<Danmaku>> callback;
    static boolean canSearch() { return true; }
    static void cancel() { cancels++; active = -1; }
    static int search(OkHttpClient client, String name, String episode, Consumer<List<Danmaku>> done, Consumer<Exception> error, Runnable cancelled) {
        chosen = client; callback = done; return active = 42;
    }
    static void search(String name, String episode, Consumer<Danmaku> done) { direct++; done.accept(new Danmaku()); }
}
class VodPlaybackMedia {
    __DANMAKU__
}
public class MetadataHarness {
    static int checks;
    static void check(boolean ok, String message) {
        checks++;
        if (!ok) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        Path.dir = Files.createTempDirectory("epg-fixture-").toFile();
        try {
            OkHttpClient proxy = new OkHttpClient();
            ZoneId zone = ZoneId.of("UTC");
            Channel normal = new Channel(), routed = new Channel();
            LiveApi.getEpg(normal, zone);
            check(OkHttp.direct == 3 && normal.days.size() == 3, "ordinary three-day EPG");
            LiveApi.getEpg(routed, zone, proxy);
            check(OkHttp.routed == 3 && OkHttp.chosen == proxy && LiveApi.METADATA_TAG.equals(OkHttp.tag), "explicit EPG client and tag");
            LiveApi.getEpg(routed, zone, proxy);
            check(OkHttp.routed == 3, "EPG cached days");
            OkHttp.interrupt = true;
            Channel interrupted = new Channel();
            LiveApi.getEpg(interrupted, zone, proxy);
            check(interrupted.days.isEmpty() && OkHttp.routed == 4, "interrupt before EPG publication");
            Thread.interrupted(); OkHttp.interrupt = false;
            Live xml = new Live("proxy.xml");
            check(LiveApi.parseXml(xml, proxy) && xml.bound == 1 && Download.chosen == proxy && LiveApi.METADATA_TAG.equals(Download.chosenTag), "explicit XML client and tag");
            check(LiveApi.parseXml(xml, proxy) && Download.downloads == 1 && xml.bound == 2, "XML cache");
            Download.chosen = null; Download.chosenTag = null;
            check(LiveApi.parseXml(new Live("direct.xml")) && Download.chosen == null && Download.chosenTag == null, "ordinary XML route");
            Download.interrupt = true;
            Live cancelled = new Live("cancelled.xml");
            check(!LiveApi.parseXml(cancelled, proxy) && cancelled.bound == 0, "interrupted XML not bound");
            Thread.interrupted(); Download.interrupt = false;
            LiveViewModel vm = new LiveViewModel();
            vm.createPlaybackController(new LivePlaybackHost(true));
            LivePlayRequest a = new LivePlayRequest(10), b = new LivePlayRequest(20);
            vm.getUrl(a); vm.getUrl(b); App.drain();
            check(vm.playback().deliveries == 1 && vm.playback().value.request == b && vm.playback().value.result.position == 20, "latest URL only");
            vm.getUrl(a); vm.cancelPlaybackUrl(); App.drain();
            check(vm.playback().deliveries == 1, "cancel URL delivery");
            vm.getEpg(new Channel(), proxy); vm.parseXml(xml, proxy);
            vm.cancelPlaybackMetadata(); App.drain();
            check(vm.epg().deliveries == 0 && vm.xml().deliveries == 0, "retired metadata delivery");
            vm.getEpg(new Channel(), proxy); vm.getEpg(new Channel(), proxy);
            vm.parseXml(xml, proxy); vm.parseXml(xml, proxy); App.drain();
            check(vm.epg().deliveries == 1 && vm.xml().deliveries == 1, "latest metadata only");
            vm.getUrl(a); vm.getEpg(new Channel(), proxy); vm.parseXml(xml, proxy);
            vm.onCleared(); App.drain();
            check(vm.playback().deliveries == 1 && vm.epg().deliveries == 1 && vm.xml().deliveries == 1, "cleared owner delivery");
            LiveViewModel plain = new LiveViewModel();
            plain.createPlaybackController(new LivePlaybackHost(false)); plain.getUrl(a);
            check(plain.playback().deliveries == 1 && App.queue.isEmpty(), "ordinary URL path");
            boolean[] owner = {true}; int[] accepted = {0};
            Consumer<Danmaku> accept = value -> accepted[0]++;
            Result result = new Result(); History history = new History(); Episode episode = new Episode();
            int id = VodPlaybackMedia.searchDanmaku(proxy, result, history, episode, () -> owner[0], accept, accept);
            check(id == 42 && DanmakuApi.chosen == proxy, "explicit Danmaku ID/client");
            DanmakuApi.callback.accept(List.of(new Danmaku()));
            check(accepted[0] == 1, "current Danmaku result");
            owner[0] = false; DanmakuApi.callback.accept(List.of(new Danmaku()));
            check(accepted[0] == 1, "retired Danmaku callback");
            int cancels = DanmakuApi.cancels;
            check(VodPlaybackMedia.searchDanmaku(proxy, result, history, episode, () -> false, accept, accept) == -1 && DanmakuApi.cancels == cancels && DanmakuApi.active == 42, "retired owner cannot cancel new Danmaku");
            VodPlaybackMedia.searchDanmaku(result, history, episode, () -> true, accept, accept);
            check(DanmakuApi.direct == 1 && accepted[0] == 2, "ordinary Danmaku route");
            System.out.println("PASS actual candidate Live metadata/URL and VOD Danmaku methods: " + checks + " assertions");
        } finally {
            for (File f : Path.dir.listFiles()) Path.clear(f);
            Path.clear(Path.dir);
        }
    }
}
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-tv", type=Path, required=True)
    parser.add_argument("--tv", type=Path, required=True)
    args = parser.parse_args()
    old, tv = args.old_tv.resolve(), args.tv.resolve()
    guard_fork()
    verified_checkout(old, "old_tv")
    verified_checkout(tv, "tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-metadata-vod-") as temp:
        root = Path(temp)
        candidate = root / "candidate"
        conflicts, manual = overlay(old, tv, candidate)
        names = ("api/LiveApi.java", "api/parser/EpgParser.java", "model/LiveViewModel.java",
                 "playback/vod/VodPlaybackHost.java", "playback/vod/VodPlaybackController.java",
                 "playback/vod/VodPlaybackMedia.java")
        texts = {}
        for name in names:
            path = BASE + name
            row = next(r for r in LOCK["fork_scope"] if r["path"] == path)
            assert path not in conflicts + manual and blob(candidate / path) == row["resolved"], path
            texts[name] = (candidate / path).read_text()
        live, xml, vm, host, ctl, media = (texts[n] for n in names)
        def upstream(name):
            return (tv / (BASE + name)).read_text()
        # Normal non-Xray paths and the upstream catch-up auth sequence.
        for sig in ("public static Result getUrl(@NonNull Channel item)", "public static Result getUrl(@NonNull Channel item, @NonNull EpgData data)"):
            assert method(live, sig) == method(upstream(names[0]), sig), sig
        assert method(media, "public static void searchDanmaku(Result result") == method(upstream(names[5]), "public static void searchDanmaku(Result result")
        assert "default void resetXrayForPlaybackChange() { }" in host
        for anchor in ("String target = url.substring(PUSH_PREFIX.length());", "if (!force && selected.isSelected()) return;",
                       "if (explicit) host.clearVodPlayId();", "state.setQualityPosition(result.getUrl().getPosition());",
                       "state.setAutoFallback(autoFallback);", "private void reloadPlayback()"):
            pos = ctl.index(anchor)
            assert "host.resetXrayForPlaybackChange();" in ctl[max(0, pos - 60):pos + len(anchor) + 80], anchor
        assert ctl.count("host.resetXrayForPlaybackChange();") == 6
        assert "preloader.clear();" in method(ctl, "public void clearPreloadForXray()")
        assert method(ctl, "public void onPreloadResult(") == method(upstream(names[4]), "public void onPreloadResult(")
        from metadata_114_jvm import render, run, methods, CHANNEL_SIGS
        bean = candidate / (BASE + "bean")
        assert blob(bean / "Channel.java") == "0359a173571ddd4a3784f06d35c6810ee67aa0b3"
        java = render(FIXTURE, live, xml, vm,
            methods(media, ("public static int searchDanmaku(OkHttpClient client",
                            "public static void searchDanmaku(Result result")),
            (bean / "Epg.java").read_text(), (bean / "EpgData.java").read_text(),
            methods((bean / "Channel.java").read_text(), CHANNEL_SIGS))
        run(java, root, "public static Callable<Supplier<Epg>> prepareEpg(" in live)
        print("PASS three negative controls; controller reset placement checked at source level, not full Android host", flush=True)
        print("REMAINING_SCOPE", len(conflicts), "unresolved", len(manual), "old-media-review", flush=True)

if __name__ == "__main__":
    main()
