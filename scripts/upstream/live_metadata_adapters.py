#!/usr/bin/env python3
"""Xray-only live EPG/XML request identity over pristine public 5.8.7 code.

All direct-mode behavior and upstream EPG parser, dates and XML cache formats
remain unchanged. Background metadata uses the current PlaybackService Xray
client and is canceled on proxy transitions; Live UI must still suppress
obsolete task callbacks before 5.8.7 may ship.
"""
from exo_adapters import one

def live_api(s):
    s=one(s,"import com.fongmi.android.tv.R;",
        "import com.fongmi.android.tv.R;\n"
        "import com.fingmi.integration.xray.XraySideRequestGate;",
        "live metadata proxy import")
    s=one(s,"public class LiveApi {",
        """public class LiveApi {

    public static final String METADATA_TAG = LiveApi.class.getName().concat(".metadata");""",
        "live metadata cancellation tag")
    s=one(s,
        "Epg.objectFrom(OkHttp.string(url), item.getTvgId(), date, zoneId)",
        "Epg.objectFrom(XraySideRequestGate.string(url, METADATA_TAG), item.getTvgId(), date, zoneId)",
        "EPG day HTTP must use session proxy")
    for item in ("BaseLoader.get().requireProxy(result.getRealUrl());",
                 "item.applyAuth(result);", "LiveParser.start(item.recent());",
                 "METADATA_TAG"):
        if item not in s: raise ValueError("LiveApi upstream behavior lost: "+item)
    return s

def epg_parser(s):
    s=one(s,"import com.fongmi.android.tv.bean.Channel;",
        "import com.fongmi.android.tv.bean.Channel;\n"
        "import com.fingmi.integration.xray.XraySideRequestGate;",
        "XML parser proxy import")
    s=one(s,"            Download.create(url, download).get();",
        "            XraySideRequestGate.usePlaybackTransport(Download.create(url, download)).get();",
        "XMLTV gzip/plain multi-part download")
    for item in ("Archive.gzipDecompress(download, xml)",
                 "checkInterrupted();","cacheXml(source, file)",
                 "new Persister().read(Tv.class, root, false)"):
        if item not in s: raise ValueError("Public XMLTV decoding lost: "+item)
    return s

def live_view_model(s):
    s=one(s,"    @Override\n    public void getUrl(LivePlayRequest request) {",
        """    /** Invalidate stale XML/EPG callbacks when playback proxy changes. */
    public void cancelXrayMetadataRequests() {
        tasks.cancel(TaskType.XML);
        tasks.cancel(TaskType.EPG);
    }

    @Override
    public void getUrl(LivePlayRequest request) {""",
        "LiveViewModel metadata generation barrier")
    for item in ("tasks.execute(type, type.timeout",
                 "tasks.cancel(TaskType.URL);","playbackState.reset();"):
        if item not in s: raise ValueError("LiveViewModel upstream task boundary lost: "+item)
    return s
