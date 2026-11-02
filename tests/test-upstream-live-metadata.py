#!/usr/bin/env python3
"""Verify 5.8.7 Live XML/EPG upstream-first Xray request isolation."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/upstream"))
from live_metadata_adapters import live_api,epg_parser,live_view_model
from live_ui_adapters import channel_adapter


def fail_closed(fn,content):
    try: fn(content)
    except ValueError: return
    raise AssertionError("Unknown public upstream "+fn.__name__+" was accepted")

LIVE='''import com.fongmi.android.tv.R;
public class LiveApi {
    void parse() {
        LiveParser.start(item.recent());
        BaseLoader.get().requireProxy(result.getRealUrl());
        item.applyAuth(result);
        if (need) item.setData(Epg.objectFrom(OkHttp.string(url), item.getTvgId(), date, zoneId));
    }
}'''
out=live_api(LIVE)
assert "XraySideRequestGate.string(url, METADATA_TAG)" in out
assert "LiveParser.start(item.recent());" in out
assert 'METADATA_TAG = LiveApi.class.getName().concat(".metadata")' in out
fail_closed(live_api,LIVE.replace("OkHttp.string(url)","OtherHttp.string(url)"))

XML='''import com.fongmi.android.tv.bean.Channel;
class EpgParser {
    void parse() {
            Download.create(url, download).get();
            Archive.gzipDecompress(download, xml);
            checkInterrupted();
            cacheXml(source, file);
            new Persister().read(Tv.class, root, false);
    }
}'''
out=epg_parser(XML)
assert "XraySideRequestGate.usePlaybackTransport(Download.create(url, download)).get();" in out
for requirement in ("Archive.gzipDecompress(download, xml)", "cacheXml(source, file)",
                    "new Persister().read(Tv.class, root, false)"):
    assert requirement in out
fail_closed(epg_parser,XML.replace("Download.create(url, download).get();",
                                   "Download.create(url, download).start();"))

VM='''class LiveViewModel {
    void cancelUrl() {
        tasks.cancel(TaskType.URL);
    }
    @Override
    public void getUrl(LivePlayRequest request) {}
    void execute() { tasks.execute(type, type.timeout, callable, result, fail); }
    void clear() { playbackState.reset(); }
}'''
out=live_view_model(VM)
assert "tasks.cancel(TaskType.XML);" in out
assert "tasks.cancel(TaskType.EPG);" in out
assert "tasks.cancel(TaskType.URL);" in out
fail_closed(live_view_model,VM.replace("public void getUrl(LivePlayRequest request)",
                                     "public void obtainUrl(LivePlayRequest request)"))

CHANNEL='''package com.fongmi.android.tv.ui.adapter;
class ChannelAdapter {
    private final List<Channel> mItems;
    public void addAll(List<Channel> items) {}
    private void updateSelection(int position, Channel selected) {
        notifyItemChanged(position, Boolean.TRUE);
    }
    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        item.loadLogo(holder.binding.logo);
    }
    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position, @NonNull List<Object> payloads) {
        if (!payloads.isEmpty() && payloads.stream().allMatch(Boolean.TRUE::equals)) holder.binding.getRoot().setSelected(mItems.get(position).isSelected());
    }
    @Override
    public void onViewRecycled(@NonNull ViewHolder holder) { }
}'''
out=channel_adapter(CHANNEL)
assert "setXrayLogoSuppressed(boolean suppressed)" in out
assert "notifyItemChanged(position, Boolean.TRUE);" in out
assert "payloads.stream().allMatch(Boolean.TRUE::equals)" in out
assert "Glide.with(channelHolder.binding.logo).clear(channelHolder.binding.logo)" in out
fail_closed(channel_adapter, CHANNEL.replace("item.loadLogo(holder.binding.logo);",
                                            "item.loadLogoElsewhere(holder.binding.logo);"))

parser=argparse.ArgumentParser()
parser.add_argument("--upstream",type=Path)
parser.add_argument("--target")
args=parser.parse_args()
if bool(args.upstream)!=bool(args.target):
    parser.error("--upstream and --target are required together")
if args.upstream:
    from sync import git_tree,blob
    tree=git_tree(args.upstream,args.target)
    for name,fn in (
        ("app/src/main/java/com/fongmi/android/tv/api/LiveApi.java",live_api),
        ("app/src/main/java/com/fongmi/android/tv/api/parser/EpgParser.java",epg_parser),
        ("app/src/main/java/com/fongmi/android/tv/model/LiveViewModel.java",live_view_model),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/adapter/ChannelAdapter.java",channel_adapter),
    ):
        if name not in tree: raise AssertionError("Missing official source "+name)
        raw=blob(args.upstream,tree[name]).decode("utf-8")
        generated=fn(raw)
        assert generated!=raw
    print("PASS public live EPG/XML adapters for "+args.target)
print("PASS LiveApi EPG, XMLTV transport, and request generation cancellation")
