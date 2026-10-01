package com.fongmi.android.tv.api;

import android.net.Uri;
import android.text.TextUtils;

import androidx.collection.ArrayMap;

import com.fongmi.android.tv.App;
import com.fongmi.android.tv.R;
import com.fongmi.android.tv.bean.Danmaku;
import com.fongmi.android.tv.impl.ApiCallback;
import com.fongmi.android.tv.setting.DanmakuSetting;
import com.fongmi.android.tv.utils.ResUtil;
import com.github.catvod.net.OkHttp;
import com.github.catvod.utils.Trans;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class DanmakuApi {

    private static final String TAG = DanmakuApi.class.getSimpleName();
    private static final AtomicInteger REQUEST_ID = new AtomicInteger();

    private static volatile Call currentCall;
    private static volatile int currentRequestId = -1;
    private static volatile Runnable xrayCancelCompletion;

    public static boolean canSearch() {
        return DanmakuSetting.isLoad()
                && DanmakuSetting.isAuto()
                && !TextUtils.isEmpty(DanmakuSetting.getEffectiveApiUrl());
    }

    public static void cancel() {
        cancel(false);
    }

    public static void cancel(int requestId) {
        if (requestId < 0) return;

        Call call = null;
        synchronized (DanmakuApi.class) {
            if (REQUEST_ID.get() != requestId) return;
            REQUEST_ID.incrementAndGet();
            if (currentRequestId == requestId) {
                call = currentCall;
                currentCall = null;
                currentRequestId = -1;
                xrayCancelCompletion = null;
            }
        }
        if (call != null) call.cancel();
    }

    public static void cancelForXrayTransition() {
        cancel(true);
    }

    private static void cancel(boolean runCompletion) {
        Call call;
        Runnable completion;
        synchronized (DanmakuApi.class) {
            if (runCompletion && currentCall == null) return;
            REQUEST_ID.incrementAndGet();
            call = currentCall;
            completion = runCompletion ? xrayCancelCompletion : null;
            currentCall = null;
            currentRequestId = -1;
            xrayCancelCompletion = null;
        }
        if (call != null) call.cancel();
        if (completion != null) App.post(completion);
    }

    public static void search(String name, String episode, Consumer<Danmaku> found) {
        search(
                OkHttp.client(),
                name,
                episode,
                items -> items.stream().findFirst().ifPresent(found),
                error -> { },
                null);
    }

    public static void search(
            String name,
            String episode,
            Consumer<List<Danmaku>> success,
            Consumer<Exception> error) {
        search(OkHttp.client(), name, episode, success, error, null);
    }

    public static int search(
            OkHttpClient client,
            String name,
            String episode,
            Consumer<List<Danmaku>> success,
            Consumer<Exception> error,
            Runnable onXrayCancel) {
        Call next = newCall(client, name, episode);
        int requestId;
        Call previous;
        synchronized (DanmakuApi.class) {
            requestId = REQUEST_ID.incrementAndGet();
            previous = currentCall;
            currentCall = next;
            currentRequestId = requestId;
            xrayCancelCompletion = onXrayCancel;
        }
        if (previous != null) previous.cancel();

        next.enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException exception) {
                try {
                    ApiCallback.post(requestId, REQUEST_ID, () -> error.accept(exception));
                } finally {
                    finish(call);
                }
            }

            @Override
            public void onResponse(Call call, Response response) {
                try (response) {
                    List<Danmaku> result = Danmaku.arrayFrom(read(response));
                    ApiCallback.post(requestId, REQUEST_ID, () -> success.accept(result));
                } catch (Exception exception) {
                    ApiCallback.post(requestId, REQUEST_ID, () -> error.accept(exception));
                } finally {
                    finish(call);
                }
            }
        });
        return requestId;
    }

    private static synchronized void finish(Call call) {
        if (currentCall != call) return;
        currentCall = null;
        currentRequestId = -1;
        xrayCancelCompletion = null;
    }

    private static Call newCall(OkHttpClient client, String name, String episode) {
        name = Trans.t2s(name);
        episode = Trans.t2s(episode);
        String url = DanmakuSetting.getEffectiveApiUrl();
        if (url.contains("{name}") || url.contains("{episode}")) {
            return OkHttp.newCall(
                    client,
                    url.replace("{name}", Uri.encode(name))
                            .replace("{episode}", Uri.encode(episode)),
                    TAG);
        }
        ArrayMap<String, String> params = new ArrayMap<>();
        params.put("name", name);
        params.put("episode", episode);
        return client.newCall(
                new Request.Builder()
                        .url(url)
                        .post(OkHttp.toBody(params))
                        .tag(TAG)
                        .build());
    }

    private static String read(Response response) throws IOException {
        String text = response.body().string();
        if (!response.isSuccessful()) {
            throw new IOException("HTTP " + response.code() + " " + response.message());
        }
        if (TextUtils.isEmpty(text)) {
            throw new IOException(ResUtil.getString(R.string.error_empty));
        }
        return text;
    }
}
