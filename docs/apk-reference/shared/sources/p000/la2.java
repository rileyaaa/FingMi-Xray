package p000;

import java.security.SecureRandom;
import java.util.Iterator;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import okhttp3.Call;
import okhttp3.FormBody;
import okhttp3.Headers;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.logging.HttpLoggingInterceptor;

public final class la2 {

    public static final ThreadPoolExecutor f10515i;

    public hs2 f10516a;

    public br2 f10517b;

    public C0550fg f10518c;

    public ga2 f10519d;

    public ta2 f10520e;

    public OkHttpClient f10521f;

    public OkHttpClient f10522g;

    public ha2 f10523h;

    static {
        ThreadPoolExecutor threadPoolExecutor = new ThreadPoolExecutor(0, 1, 5L, TimeUnit.SECONDS, new LinkedBlockingQueue(), new ch0(1));
        threadPoolExecutor.allowCoreThreadTimeOut(true);
        f10515i = threadPoolExecutor;
    }

    public static void m5790a(OkHttpClient okHttpClient, String str) {
        for (Call call : okHttpClient.dispatcher().queuedCalls()) {
            if (str.equals(call.request().tag())) {
                call.cancel();
            }
        }
        for (Call call2 : okHttpClient.dispatcher().runningCalls()) {
            if (str.equals(call2.request().tag())) {
                call2.cancel();
            }
        }
    }

    public static void m5791b(OkHttpClient okHttpClient) {
        if (okHttpClient == null) {
            return;
        }
        f10515i.execute(new yd0(okHttpClient, 28));
    }

    public static synchronized OkHttpClient m5792c() {
        if (ka2.f9765a.f10521f != null) {
            return ka2.f9765a.f10521f;
        }
        la2 la2Var = ka2.f9765a;
        OkHttpClient okHttpClientBuild = m5794e().build();
        la2Var.f10521f = okHttpClientBuild;
        return okHttpClientBuild;
    }

    public static ha2 m5793d() {
        if (ka2.f9765a.f10523h != null) {
            return ka2.f9765a.f10523h;
        }
        la2 la2Var = ka2.f9765a;
        ha2 ha2Var = new ha2();
        la2Var.f10523h = ha2Var;
        return ha2Var;
    }

    public static OkHttpClient.Builder m5794e() {
        br2 br2Var;
        C0550fg c0550fg;
        ga2 ga2Var;
        OkHttpClient.Builder builder = new OkHttpClient.Builder();
        if (ka2.f9765a.f10517b != null) {
            br2Var = ka2.f9765a.f10517b;
        } else {
            la2 la2Var = ka2.f9765a;
            br2 br2Var2 = new br2();
            la2Var.f10517b = br2Var2;
            br2Var = br2Var2;
        }
        OkHttpClient.Builder builderAddInterceptor = builder.addInterceptor(br2Var);
        if (ka2.f9765a.f10518c != null) {
            c0550fg = ka2.f9765a.f10518c;
        } else {
            la2 la2Var2 = ka2.f9765a;
            C0550fg c0550fg2 = new C0550fg();
            la2Var2.f10518c = c0550fg2;
            c0550fg = c0550fg2;
        }
        OkHttpClient.Builder builderAddNetworkInterceptor = builderAddInterceptor.addInterceptor(c0550fg).addNetworkInterceptor(m5799j());
        TimeUnit timeUnit = TimeUnit.MILLISECONDS;
        OkHttpClient.Builder builderHostnameVerifier = builderAddNetworkInterceptor.connectTimeout(30000L, timeUnit).readTimeout(30000L, timeUnit).writeTimeout(30000L, timeUnit).dns(m5793d()).hostnameVerifier(new ia2());
        SSLContext sSLContext = null;
        try {
            SSLContext sSLContext2 = SSLContext.getInstance("TLS");
            sSLContext2.init(null, new TrustManager[]{new ja2()}, new SecureRandom());
            sSLContext = sSLContext2;
        } catch (Throwable unused) {
        }
        OkHttpClient.Builder builderSslSocketFactory = builderHostnameVerifier.sslSocketFactory(sSLContext.getSocketFactory(), new ja2());
        new HttpLoggingInterceptor().setLevel(HttpLoggingInterceptor.Level.BODY);
        if (ka2.f9765a.f10519d != null) {
            ga2Var = ka2.f9765a.f10519d;
        } else {
            la2 la2Var3 = ka2.f9765a;
            ga2 ga2Var2 = new ga2(m5800k());
            la2Var3.f10519d = ga2Var2;
            ga2Var = ga2Var2;
        }
        builderSslSocketFactory.proxyAuthenticator(ga2Var);
        builderSslSocketFactory.proxySelector(m5800k());
        return builderSslSocketFactory;
    }

    public static Call m5795f(String str, Map map) {
        return m5792c().newCall(new Request.Builder().url(str).headers(Headers.m7011of((Map<String, String>) map)).build());
    }

    public static Call m5796g(String str, Map map, C0209cb c0209cb) {
        OkHttpClient okHttpClientM5792c = m5792c();
        Request.Builder builder = new Request.Builder();
        HttpUrl httpUrl = HttpUrl.parse(str);
        Objects.requireNonNull(httpUrl);
        HttpUrl.Builder builderNewBuilder = httpUrl.newBuilder();
        Iterator it = ((C1584rw) c0209cb.entrySet()).iterator();
        while (true) {
            C0012ab c0012ab = (C0012ab) it;
            if (!c0012ab.hasNext()) {
                return okHttpClientM5792c.newCall(builder.url(builderNewBuilder.build()).headers(Headers.m7011of((Map<String, String>) map)).build());
            }
            c0012ab.next();
            builderNewBuilder.addQueryParameter((String) c0012ab.getKey(), (String) c0012ab.getValue());
        }
    }

    public static Call m5797h(OkHttpClient okHttpClient, String str, String str2) {
        return okHttpClient.newCall(new Request.Builder().url(str).tag(str2).build());
    }

    public static synchronized OkHttpClient m5798i() {
        if (ka2.f9765a.f10522g != null) {
            return ka2.f9765a.f10522g;
        }
        la2 la2Var = ka2.f9765a;
        OkHttpClient okHttpClientBuild = m5794e().build();
        la2Var.f10522g = okHttpClientBuild;
        return okHttpClientBuild;
    }

    public static hs2 m5799j() {
        if (ka2.f9765a.f10516a != null) {
            return ka2.f9765a.f10516a;
        }
        la2 la2Var = ka2.f9765a;
        hs2 hs2Var = new hs2();
        la2Var.f10516a = hs2Var;
        return hs2Var;
    }

    public static ta2 m5800k() {
        if (ka2.f9765a.f10520e != null) {
            return ka2.f9765a.f10520e;
        }
        la2 la2Var = ka2.f9765a;
        ta2 ta2Var = new ta2();
        la2Var.f10520e = ta2Var;
        return ta2Var;
    }

    public static String m5801l(String str) {
        if (!str.startsWith("http")) {
            return "";
        }
        try {
            Response responseExecute = m5792c().newCall(new Request.Builder().url(str).build()).execute();
            try {
                String strString = responseExecute.body().string();
                responseExecute.close();
                return strString;
            } catch (Throwable th) {
                if (responseExecute != null) {
                    try {
                        responseExecute.close();
                    } catch (Throwable th2) {
                        th.addSuppressed(th2);
                    }
                }
                throw th;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String m5802m(String str, Map map) {
        if (!str.startsWith("http")) {
            return "";
        }
        try {
            Response responseExecute = m5795f(str, map).execute();
            try {
                String strString = responseExecute.body().string();
                responseExecute.close();
                return strString;
            } catch (Throwable th) {
                if (responseExecute != null) {
                    try {
                        responseExecute.close();
                    } catch (Throwable th2) {
                        th.addSuppressed(th2);
                    }
                }
                throw th;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static FormBody m5803n(C0209cb c0209cb) {
        FormBody.Builder builder = new FormBody.Builder();
        Iterator it = ((C1584rw) c0209cb.entrySet()).iterator();
        while (true) {
            C0012ab c0012ab = (C0012ab) it;
            if (!c0012ab.hasNext()) {
                return builder.build();
            }
            c0012ab.next();
            C0012ab c0012ab2 = c0012ab;
            builder.add((String) c0012ab2.getKey(), (String) c0012ab2.getValue());
        }
    }
}
