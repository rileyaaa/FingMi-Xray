package com.fingmi.xray.network;

import java.net.InetSocketAddress;
import java.net.Proxy;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;
import okhttp3.OkHttpClient;

public final class XrayHttpClient implements AutoCloseable {

    private final AtomicBoolean closed = new AtomicBoolean();
    private final Dispatcher dispatcher;
    private final ConnectionPool connectionPool;
    private final OkHttpClient client;

    public XrayHttpClient(int socksPort, OkHttpClient baseClient) {
        if (socksPort <= 0) throw new IllegalArgumentException("A positive SOCKS port is required");

        dispatcher = new Dispatcher();
        connectionPool = new ConnectionPool(5, 5, TimeUnit.MINUTES);
        Proxy proxy = new Proxy(
                Proxy.Type.SOCKS,
                InetSocketAddress.createUnresolved("127.0.0.1", socksPort));

        client = baseClient.newBuilder()
                .cache(null)
                .dispatcher(dispatcher)
                .connectionPool(connectionPool)
                .proxy(proxy)
                .addNetworkInterceptor(new PublicPlaybackDestinationInterceptor())
                .build();
    }

    public OkHttpClient client() {
        if (closed.get()) throw new IllegalStateException("Xray HTTP client is closed");
        return client;
    }

    @Override
    public void close() {
        if (!closed.compareAndSet(false, true)) return;
        dispatcher.cancelAll();
        dispatcher.executorService().shutdown();
        connectionPool.evictAll();
    }
}
