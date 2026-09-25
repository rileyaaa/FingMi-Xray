package com.fongmi.android.tv.playback.vod;

import androidx.media3.common.MediaMetadata;

import com.fongmi.android.tv.api.DanmakuApi;
import com.fongmi.android.tv.api.config.VodConfig;
import com.fongmi.android.tv.bean.Danmaku;
import com.fongmi.android.tv.bean.Episode;
import com.fongmi.android.tv.bean.History;
import com.fongmi.android.tv.bean.Result;
import com.fongmi.android.tv.player.media.MediaItemFactory;
import com.fongmi.android.tv.setting.DanmakuSetting;

import java.util.function.Consumer;

import okhttp3.OkHttpClient;

public final class VodPlaybackMedia {

    public static MediaMetadata metadata(History history, Episode episode) {
        String title = history.getVodName();
        String name = episode.getName();
        if (name.equals(title)) name = "";
        return MediaItemFactory.buildMetadata(title, name, history.getVodPic(), name);
    }

    public static int searchDanmaku(
            OkHttpClient client,
            Result result,
            History history,
            Episode episode,
            Consumer<Danmaku> set,
            Consumer<Danmaku> add) {
        // Final APK cancels the previous request before evaluating whether the
        // new item even needs an automatic danmaku search.
        DanmakuApi.cancel();

        if (!DanmakuApi.canSearch()) return -1;
        if (VodConfig.get().getSite(result.getKey()).getDanmaku() == 0) return -1;

        return DanmakuApi.search(
                client,
                history.getVodName(),
                episode.getName(),
                items -> {
                    Danmaku danmaku =
                            items.stream()
                                    .findFirst()
                                    .orElse(null);
                    if (danmaku == null) return;

                    if (DanmakuSetting.isSpiderFirst()
                            && !result.getDanmaku().isEmpty()) {
                        add.accept(danmaku);
                    } else {
                        set.accept(danmaku);
                    }
                },
                ignored -> {
                },
                null);
    }
}
