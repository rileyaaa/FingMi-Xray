#!/usr/bin/env python3
"""Minimal TV network recovery overlays on untouched selected FongMi/TV sources.

All replacements are exact-anchor and fail closed. This file does not change
ordinary upstream business behavior; it restores only the approved recovery
hooks and the stale-network generation lifecycle.
"""


def replace_once(s, old, new, label):
    count = s.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one upstream anchor, saw {count}")
    return s.replace(old, new, 1)


def site_view_model(s):
    if "public void cancelResultRequest()" in s:
        if "tasks.cancel(TaskType.RESULT);" not in s:
            raise ValueError("Upstream cancelResultRequest has unknown semantics")
        return s
    if "tasks.cancel(TaskType.RESULT);" in s:
        raise ValueError("Unexpected duplicate network-result cancellation")
    return replace_once(s, "    public void stopSearch() {",
        """    /** Invalidate pending Home results on a new TV network generation. */
    public void cancelResultRequest() {
        tasks.cancel(TaskType.RESULT);
    }

    public void stopSearch() {""", "SiteViewModel recovery cancellation")


def base_loader(s):
    if "public void clear(Runnable onComplete)" in s:
        return s
    s=replace_once(s,"import android.text.TextUtils;",
         "import android.text.TextUtils;\nimport com.fongmi.android.tv.App;",
         "BaseLoader UI callback")
    s=replace_once(s,"    public void clear() {\n        clear(false);\n    }\n\n    public void destroy() {\n        clear(true);\n    }\n\n    private void clear(boolean exiting) {",
        """    public void clear() {
        clear(false, null);
    }

    /** Called on TV recovery: callback only after retired spider cleanup. */
    public void clear(Runnable onComplete) {
        clear(false, onComplete);
    }

    public void destroy() {
        clear(true, null);
    }

    private void clear(boolean exiting, Runnable onComplete) {""", "BaseLoader asynchronous callback")
    s=replace_once(s,"        Task.execute(() -> clearLoaders(previous, retired));",
        """        Task.execute(() -> {
            try {
                clearLoaders(previous, retired);
            } finally {
                if (onComplete != null) App.post(onComplete);
            }
        });""", "BaseLoader cleanup ordering")
    return s


def ok_http(s):
    if "public static void resetApiNetworkForResume()" in s:
        return s
    s=replace_once(s,"import java.util.Objects;",
        """import java.util.Objects;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;""", "OkHttp executor imports")
    s=replace_once(s,"    private static final long TIMEOUT = TimeUnit.SECONDS.toMillis(30);",
        """    private static final long TIMEOUT = TimeUnit.SECONDS.toMillis(30);

    // Serial daemon cleanup never touches the dedicated playback client.
    private static final ThreadPoolExecutor NETWORK_CLEANUP;

    static {
        NETWORK_CLEANUP = new ThreadPoolExecutor(0, 1, 5L, TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(), runnable -> {
                    Thread thread = new Thread(runnable, "TvNetworkCleanup");
                    thread.setDaemon(true);
                    return thread;
                });
        NETWORK_CLEANUP.allowCoreThreadTimeOut(true);
    }""", "OkHttp cleanup executor")
    s=replace_once(s,"    public void clear() {",
        """    /**
     * Detach only ordinary API transport when Android TV network generation
     * advances. Do not disturb user playback or configured proxy rules.
     */
    public static void resetApiNetworkForResume() {
        OkHttpClient previous;
        synchronized (OkHttp.class) {
            previous = get().client;
            get().client = null;
            dns().resetForNetworkChange();
        }
        cleanupClientAsync(previous);
    }

    public static void cleanupClientAsync(OkHttpClient client) {
        if (client == null) return;
        NETWORK_CLEANUP.execute(() -> {
            try { client.dispatcher().cancelAll(); } catch (Throwable ignored) {}
            try { client.connectionPool().evictAll(); } catch (Throwable ignored) {}
            try { client.dispatcher().executorService().shutdown(); } catch (Throwable ignored) {}
        });
    }

    public void clear() {""", "OkHttp API-only reset")
    return s


def ok_dns(s):
    if "public synchronized void resetForNetworkChange()" in s:
        return s
    s=replace_once(s,"    private volatile DnsOverHttps doh;",
        """    private volatile DnsOverHttps doh;
    private volatile Doh currentDoh;
    private volatile OkHttpClient dohClient;""", "DoH generation tracking")
    s=replace_once(s,
        """    public synchronized void setDoh(Doh item) {
        HttpUrl url = HttpUrl.parse(item.getUrl());
        this.doh = url == null ? null : new DnsOverHttps.Builder().client(new OkHttpClient()).url(url).bootstrapDnsHosts(item.getHosts()).build();
        this.supplier = null;
    }""",
        """    public synchronized void setDoh(Doh item) {
        currentDoh = item;
        supplier = null;
        rebuildDoh(item);
    }""", "DoH client selection")
    s=replace_once(s,
        """    public synchronized void setDoh(Supplier<Doh> supplier) {
        this.supplier = supplier;
    }""",
        """    public synchronized void setDoh(Supplier<Doh> supplier) {
        currentDoh = null;
        this.supplier = supplier;
        rebuildDoh(null);
    }

    public synchronized void resetForNetworkChange() {
        if (supplier != null) rebuildDoh(null);
        else rebuildDoh(currentDoh);
    }

    private void rebuildDoh(Doh item) {
        OkHttpClient oldClient = dohClient;
        doh = null;
        dohClient = null;
        if (item != null) {
            HttpUrl url = HttpUrl.parse(item.getUrl());
            if (url != null) {
                dohClient = new OkHttpClient();
                doh = new DnsOverHttps.Builder().client(dohClient).url(url)
                        .bootstrapDnsHosts(item.getHosts()).build();
            }
        }
        OkHttp.cleanupClientAsync(oldClient);
    }""", "DoH reset after standby")
    s=replace_once(s,
        """        Supplier<Doh> supplier = this.supplier;
        if (supplier != null) initDoh(supplier);
        return (doh != null ? doh : Dns.SYSTEM).lookup(get(hostname));""",
        """        Dns resolver;
        synchronized (this) {
            if (doh == null) {
                Supplier<Doh> lazy = supplier;
                if (lazy != null) initDoh(lazy);
                else if (currentDoh != null) rebuildDoh(currentDoh);
            }
            resolver = doh != null ? doh : Dns.SYSTEM;
        }
        return resolver.lookup(get(hostname));""", "snapshot DoH resolver under generation lock")
    return s


def img_util(s):
    if "public static void resetNetworkFailures()" in s:
        return s
    s=replace_once(s,"import java.util.regex.Pattern;",
        "import java.util.regex.Pattern;\nimport java.util.concurrent.atomic.AtomicLong;", "Glide network failure epoch import")
    s=replace_once(s,
        "    private static final Set<String> failed = Collections.synchronizedSet(new HashSet<>());",
        """    private static final Set<String> failed = Collections.synchronizedSet(new HashSet<>());
    private static final AtomicLong networkFailureEpoch = new AtomicLong();""", "Glide failure generation")
    s=replace_once(s,"    public record Image(String mime, byte[] data) {",
        """    public static void resetNetworkFailures() {
        networkFailureEpoch.incrementAndGet();
        failed.clear();
    }

    public record Image(String mime, byte[] data) {""", "Glide transient error cleanup")
    s=replace_once(s,"    private static RequestListener<Drawable> getListener(String text, String url, ImageView view, boolean vod) {\n        return new RequestListener<>() {",
        """    private static RequestListener<Drawable> getListener(String text, String url, ImageView view, boolean vod) {
        long requestEpoch = networkFailureEpoch.get();
        return new RequestListener<>() {""", "Glide stale request snapshot")
    s=replace_once(s,
        """            public boolean onLoadFailed(@Nullable GlideException e, Object model, @NonNull Target<Drawable> target, boolean isFirstResource) {
                view.setImageDrawable(getTextDrawable(text, vod));""",
        """            public boolean onLoadFailed(@Nullable GlideException e, Object model, @NonNull Target<Drawable> target, boolean isFirstResource) {
                if (requestEpoch != networkFailureEpoch.get()) return true;
                view.setImageDrawable(getTextDrawable(text, vod));""", "Glide late failure isolation")
    return s


def ok_glide(s):
    if "new OkHttpUrlLoader.Factory(request -> OkHttp.client().newCall(request))" in s:
        return s
    return replace_once(s,
        "new OkHttpUrlLoader.Factory(OkHttp.client())",
        "new OkHttpUrlLoader.Factory(request -> OkHttp.client().newCall(request))",
        "Glide current API client at request time")
