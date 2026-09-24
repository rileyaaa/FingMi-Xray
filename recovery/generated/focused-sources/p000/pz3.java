package p000;

import java.net.InetSocketAddress;
import java.net.Proxy;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;
import okhttp3.OkHttpClient;

public final class pz3 {

    public static final ThreadPoolExecutor f14523f;

    public final AtomicBoolean f14524a = new AtomicBoolean();

    public final Dispatcher f14525b;

    public final ConnectionPool f14526c;

    public final OkHttpClient f14527d;

    public final oz3 f14528e;

    static {
        ThreadPoolExecutor threadPoolExecutor = new ThreadPoolExecutor(0, 1, 5L, TimeUnit.SECONDS, new LinkedBlockingQueue(), new ch0(3));
        threadPoolExecutor.allowCoreThreadTimeOut(true);
        f14523f = threadPoolExecutor;
    }

    public pz3(int i) {
        if (i <= 0) {
            C1566re.m8586j("A positive SOCKS port is required");
            throw null;
        }
        Dispatcher dispatcher = new Dispatcher();
        this.f14525b = dispatcher;
        ConnectionPool connectionPool = new ConnectionPool(5, 5L, TimeUnit.MINUTES);
        this.f14526c = connectionPool;
        Proxy proxy = new Proxy(Proxy.Type.SOCKS, InetSocketAddress.createUnresolved("127.0.0.1", i));
        this.f14528e = new oz3(proxy);
        this.f14527d = la2.m5798i().newBuilder().cache(null).dispatcher(dispatcher).connectionPool(connectionPool).proxy(proxy).addNetworkInterceptor(new qz3()).build();
    }
}
