#!/usr/bin/env python3
"""Minimal 5.8.7 side-request Xray transport adapters over pristine upstream.

Keep ordinary upstream APIs and cancellation generations. Side network calls
use the active Xray proxy client (including all subtitle download parts);
new calls during direct playback still use public upstream behavior.
"""
from exo_adapters import one

def danmaku_api(s):
    s=one(s,"import com.fongmi.android.tv.R;",
        "import com.fongmi.android.tv.R;\n"
        "import com.fingmi.integration.xray.XraySideRequestGate;","danmaku gate import")
    s=one(s,"        OkHttp.cancel(TAG);\n    }\n\n    public static void search",
        "        OkHttp.cancel(TAG);\n        XraySideRequestGate.cancel(TAG);\n    }\n\n    public static void search","danmaku cancel")
    s=one(s,
        'return OkHttp.newCall(url.replace("{name}", Uri.encode(name)).replace("{episode}", Uri.encode(episode)), TAG);',
        'return XraySideRequestGate.newCall(url.replace("{name}", Uri.encode(name)).replace("{episode}", Uri.encode(episode)), TAG);',
        "danmaku query")
    s=one(s,'return OkHttp.newCall(url, OkHttp.toBody(params), TAG);',
        'return XraySideRequestGate.newCall(url, OkHttp.toBody(params), TAG);',
        "danmaku post")
    for required in ("ApiCallback<>(requestId, REQUEST_ID","REQUEST_ID.incrementAndGet()",
                     "XraySideRequestGate.cancel(TAG)", "XraySideRequestGate.newCall("):
        if required not in s: raise ValueError("Danmaku request identity lost: "+required)
    return s

def subtitle_api(s):
    s=one(s,"import com.fongmi.android.tv.R;",
        "import com.fongmi.android.tv.R;\n"
        "import com.fingmi.integration.xray.XraySideRequestGate;","subtitle gate import")
    s=one(s,"        OkHttp.cancel(TAG);\n        cancelDownload();",
        "        OkHttp.cancel(TAG);\n        XraySideRequestGate.cancel(TAG);\n        cancelDownload();",
        "subtitle cancellation")
    s=one(s,
        'Download task = SubtitleArchive.createDownload(item.getName(), item.getUrl()).tag(TAG);',
        'Download task = XraySideRequestGate.usePlaybackTransport(SubtitleArchive.createDownload(item.getName(), item.getUrl()).tag(TAG));',
        "subtitle multi-part download proxy")
    s=one(s,'return OkHttp.newCall(builder.build().toString(), TAG);',
        'return XraySideRequestGate.newCall(builder.build().toString(), TAG);',
        "subtitle search")
    # Search and detail have identical source; second occurrence remains.
    s=one(s,'return OkHttp.newCall(builder.build().toString(), TAG);',
        'return XraySideRequestGate.newCall(builder.build().toString(), TAG);',
        "subtitle detail")
    for required in ("ApiCallback.post(requestId, REQUEST_ID",
                     "download != task","XraySideRequestGate.cancel(TAG)",
                     "XraySideRequestGate.usePlaybackTransport("):
        if required not in s: raise ValueError("Subtitle async generation lost: "+required)
    return s

def download(s):
    s=one(s,"    private Call.Factory factory;",
        "    private Call.Factory factory;\n    private Call.Factory playbackTransport;",
        "download optional session client")
    s=one(s,"    public Download tag(String tag) {",
        """    /** Optional Xray-only transport; ordinary downloads stay upstream. */
    public Download transport(Call.Factory client) {
        if (client == null) throw new IllegalArgumentException("client");
        this.playbackTransport = client;
        return this;
    }

    public Download tag(String tag) {""",
        "download public transport")
    s=one(s,"            Call.Factory client = OkHttp.client();",
        "            Call.Factory client = playbackTransport == null ? OkHttp.client() : playbackTransport;",
        "download transfer and range client")
    for required in ("this.factory = factory;", "factory.newCall(request)",
                     "Call.Factory client = playbackTransport == null ? OkHttp.client() : playbackTransport;"):
        if required not in s: raise ValueError("Download multipart transport lost: "+required)
    return s

def playback_service(s):
    s=one(s,"import com.fongmi.android.tv.bean.History;",
        "import com.fongmi.android.tv.bean.History;\n"
        "import com.fongmi.android.tv.api.DanmakuApi;\n"
        "import com.fongmi.android.tv.api.SubtitleApi;\n"
        "import com.fongmi.android.tv.api.LiveApi;\n"
        "import com.github.catvod.net.OkHttp;\n"
        "import com.fingmi.integration.xray.XrayArtworkBitmapLoader;\n"
        "import com.fingmi.integration.xray.XraySideRequestGate;","service media gate imports")
    s=one(s,"    private PlayerManager player;",
        "    private PlayerManager player;\n"
        "    private XrayArtworkBitmapLoader xrayBitmapLoader;",
        "service tracked remote artwork")
    s=one(s,"        player = new PlayerManager(this);\n"
        "        sessionPlayer = new SessionPlayer(player.getPlayer());",
        "        player = new PlayerManager(this);\n"
        "        XraySideRequestGate.bind(player);\n"
        "        sessionPlayer = new SessionPlayer(player.getPlayer());",
        "service side transport lifecycle")
    s=one(s,
        "session = new MediaLibrarySession.Builder(this, sessionPlayer, this).setBitmapLoader(new ArtworkBitmapLoader(this)).build();",
        "xrayBitmapLoader = new XrayArtworkBitmapLoader(player, new ArtworkBitmapLoader(this));\n"
        "        session = new MediaLibrarySession.Builder(this, sessionPlayer, this).setBitmapLoader(xrayBitmapLoader).build();",
        "service remote artwork gate")
    s=one(s,"    public void onDestroy() {\n        running = false;",
        """    public void onDestroy() {
        // Retire callbacks and proxy clients before the service disappears.
        DanmakuApi.cancel();
        SubtitleApi.cancel();
        // Cancel metadata calls before the old HTTP session disappears.
        OkHttp.cancel(LiveApi.METADATA_TAG);
        XraySideRequestGate.cancel(LiveApi.METADATA_TAG);
        if (xrayBitmapLoader != null) xrayBitmapLoader.cancelRemoteLoads();
        XraySideRequestGate.cancelRemoteDownloads();
        XraySideRequestGate.unbind(player);
        running = false;""",
        "service exit session cleanup")
    s=one(s,"    @Override\n    public void onPlayerRebuild(Player newPlayer) {",
        """    @Override
    public void onXrayTransitionStarted() {
        // Called while PlayerManager still exposes the old proxy.
        // Also invalidates upstream request IDs for delayed callbacks.
        DanmakuApi.cancel();
        SubtitleApi.cancel();
        // Cancel metadata calls before the old HTTP session disappears.
        OkHttp.cancel(LiveApi.METADATA_TAG);
        XraySideRequestGate.cancel(LiveApi.METADATA_TAG);
        if (xrayBitmapLoader != null) xrayBitmapLoader.cancelRemoteLoads();
        XraySideRequestGate.cancelRemoteDownloads();
    }

    @Override
    public void onPlayerRebuild(Player newPlayer) {""",
        "service Xray switching callback")
    for required in ("liveMetadata = new LiveMetadata(player, library)",
                     "XraySideRequestGate.bind(player);",
                     "XraySideRequestGate.unbind(player);",
                     "xrayBitmapLoader.cancelRemoteLoads()",
                     "XraySideRequestGate.cancelRemoteDownloads();",
                     "OkHttp.cancel(LiveApi.METADATA_TAG);",
                     "XraySideRequestGate.cancel(LiveApi.METADATA_TAG);",
                     "DanmakuApi.cancel();","SubtitleApi.cancel();"):
        if required not in s: raise ValueError("PlaybackService 5.8.7 lifecycle dropped: "+required)
    return s
