package com.fongmi.android.tv.xray.legacy;

import java.net.InetSocketAddress;
import java.net.Proxy;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;
import okhttp3.OkHttpClient;

/**
 * Behavior reconstruction of per-ExoPlayer Xray resources (R8 name: pz3).
 */
public final class LegacyXrayHttpResources implements AutoCloseable {

    private static final ThreadPoolExecutor CLEANUP_EXECUTOR;

    static {
        CLEANUP_EXECUTOR =
                new ThreadPoolExecutor(
                        0,
                        1,
                        5L,
                        TimeUnit.SECONDS,
                        new LinkedBlockingQueue<>(),
                        runnable -> {
                            Thread thread =
                                    new Thread(
                                            runnable,
                                            "XrayProxyCleanup");
                            thread.setDaemon(true);
                            return thread;
                        });
        CLEANUP_EXECUTOR.allowCoreThreadTimeOut(true);
    }

    private final AtomicBoolean closed =
            new AtomicBoolean();

    private final Dispatcher dispatcher;
    private final ConnectionPool connectionPool;
    private final OkHttpClient client;
    private final LegacyXrayProxySocketFactory rtspSocketFactory;

    public LegacyXrayHttpResources(
            OkHttpClient baseClient,
            int socksPort) {
        if (socksPort <= 0) {
            throw new IllegalArgumentException(
                    "A positive SOCKS port is required");
        }

        dispatcher = new Dispatcher();
        connectionPool =
                new ConnectionPool(
                        5,
                        5L,
                        TimeUnit.MINUTES);

        Proxy proxy =
                new Proxy(
                        Proxy.Type.SOCKS,
                        InetSocketAddress.createUnresolved(
                                "127.0.0.1",
                                socksPort));

        rtspSocketFactory =
                new LegacyXrayProxySocketFactory(proxy);

        client =
                baseClient.newBuilder()
                        .cache(null)
                        .dispatcher(dispatcher)
                        .connectionPool(connectionPool)
                        .proxy(proxy)
                        .addNetworkInterceptor(
                                new LegacyPublicPlaybackDestinationInterceptor())
                        .build();
    }

    public OkHttpClient client() {
        return client;
    }

    public LegacyXrayProxySocketFactory rtspSocketFactory() {
        return rtspSocketFactory;
    }

    @Override
    public void close() {
        if (!closed.compareAndSet(false, true)) {
            return;
        }

        // Exact shipped order: stop accepting/creating Dispatcher work first,
        // then asynchronously cancel calls and evict pooled connections.
        dispatcher.executorService().shutdown();

        CLEANUP_EXECUTOR.execute(
                () -> {
                    try {
                        dispatcher.cancelAll();
                    } catch (Throwable ignored) {
                    }

                    try {
                        connectionPool.evictAll();
                    } catch (Throwable ignored) {
                    }
                });
    }
}
