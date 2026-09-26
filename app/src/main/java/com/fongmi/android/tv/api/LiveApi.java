package com.fongmi.android.tv.api;

import androidx.annotation.NonNull;

import com.fongmi.android.tv.R;
import com.fongmi.android.tv.api.config.LiveConfig;
import com.fongmi.android.tv.api.parser.EpgParser;
import com.fongmi.android.tv.api.parser.LiveParser;
import com.fongmi.android.tv.bean.Channel;
import com.fongmi.android.tv.bean.Epg;
import com.fongmi.android.tv.bean.EpgData;
import com.fongmi.android.tv.bean.Group;
import com.fongmi.android.tv.bean.Live;
import com.fongmi.android.tv.bean.Result;
import com.fongmi.android.tv.player.extractor.Source;
import com.fongmi.android.tv.utils.Formatters;
import com.github.catvod.net.OkHttp;
import okhttp3.OkHttpClient;
import okhttp3.Response;
import java.io.IOException;

import java.time.LocalDate;
import java.time.ZoneId;

public class LiveApi {

    public static void parse(@NonNull Live item) throws Exception {
        LiveParser.start(item.recent());
        item.getGroups().removeIf(Group::isEmpty);
        if (item.getGroups().isEmpty() || item.getGroups().get(0).isKeep()) return;
        item.getGroups().add(0, Group.create(R.string.keep));
        LiveConfig.get().applyKeepsToGroups(item.getGroups());
    }

    public static boolean parseXml(@NonNull Live item) { return parseXml(item, null); }

    public static boolean parseXml(@NonNull Live item, OkHttpClient client) {
        return item.getEpgXml().stream().map(url -> startXml(item, url, client)).reduce(false, Boolean::logicalOr);
    }

    @NonNull
    public static Epg getEpg(@NonNull Channel item, @NonNull ZoneId zoneId) { return getEpg(item, zoneId, null); }

    @NonNull
    public static Epg getEpg(@NonNull Channel item, @NonNull ZoneId zoneId, OkHttpClient client) {
        String today = LocalDate.now(zoneId).format(Formatters.DATE);
        for (int offset : new int[]{-1, 0, 1}) fetchEpgDay(item, zoneId, offset, client);
        return item.getDataList().stream().filter(epg -> epg.equal(today)).findFirst().orElseGet(Epg::new).selected();
    }

    @NonNull
    public static Result getUrl(@NonNull Channel item) throws Exception {
        Source.get().stop();
        Result result = item.result();
        result.setUrl(Source.get().fetch(result));
        return result;
    }

    @NonNull
    public static Result getUrl(@NonNull Channel item, @NonNull EpgData data) throws Exception {
        Result result = getUrl(item);
        result.setUrl(item.getCatchup().format(result.getRealUrl(), data));
        if (item.isRtsp()) result.getHeader().put("rtsp_range", data.getRange());
        return result;
    }

    private static boolean startXml(Live item, String url, OkHttpClient client) {
        try {
            EpgParser.start(item, url, client);
            return true;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    private static void fetchEpgDay(@NonNull Channel item, @NonNull ZoneId zoneId, int offset, OkHttpClient client) {
        String date = LocalDate.now(zoneId).plusDays(offset).format(Formatters.DATE);
        String url = item.getEpg().replace("{date}", date);
        boolean need = url.startsWith("http") && item.getDataList().stream().noneMatch(epg -> epg.equal(date));
        if (need && client == null) { item.setData(Epg.objectFrom(OkHttp.string(url), item.getTvgId(), zoneId)); return; }
        if (need) {
            try (Response response = (client == null ? OkHttp.newCall(url) : OkHttp.newCall(client, url, "live-metadata")).execute()) {
                if (response.body() != null) item.setData(Epg.objectFrom(response.body().string(), item.getTvgId(), zoneId));
            } catch (IOException ignored) { }
        }
    }
}
