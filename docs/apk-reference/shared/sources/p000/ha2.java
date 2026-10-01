package p000;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import okhttp3.Dns;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.dnsoverhttps.DnsOverHttps;

public final class ha2 implements Dns {

    public final ConcurrentHashMap f7012a = new ConcurrentHashMap();
    public volatile C0923jh f7013b;
    public volatile xh0 f7014c;
    public volatile DnsOverHttps f7015d;
    public volatile OkHttpClient f7016e;

    public final void m3986a(xh0 xh0Var) {
        HttpUrl httpUrl;
        OkHttpClient okHttpClient = this.f7016e;
        this.f7015d = null;
        this.f7016e = null;
        if (xh0Var != null && (httpUrl = HttpUrl.parse(xh0Var.m10549d())) != null) {
            OkHttpClient okHttpClient2 = new OkHttpClient();
            this.f7016e = okHttpClient2;
            this.f7015d = new DnsOverHttps.Builder().client(okHttpClient2).url(httpUrl).bootstrapDnsHosts(xh0Var.m10547b()).build();
        }
        if (okHttpClient != null) {
            la2.m5791b(okHttpClient);
        }
    }

    @Override
    public final List lookup(String str) {
        synchronized (this) {
            try {
                if (this.f7015d == null) {
                    C0923jh c0923jh = this.f7013b;
                    if (c0923jh != null) {
                        xh0 xh0Var = (xh0) c0923jh.get();
                        synchronized (this) {
                            this.f7014c = xh0Var;
                            this.f7013b = null;
                            m3986a(xh0Var);
                        }
                    } else if (this.f7014c != null) {
                        m3986a(this.f7014c);
                    }
                }
            } catch (Throwable th) {
                throw th;
            }
        }
        Dns dns = this.f7015d != null ? this.f7015d : Dns.SYSTEM;
        ConcurrentHashMap concurrentHashMap = this.f7012a;
        String str2 = (String) concurrentHashMap.get(str);
        if (str2 == null) {
            for (Map.Entry entry : concurrentHashMap.entrySet()) {
                if (pp3.m7876a(str, (String) entry.getKey())) {
                    str = (String) entry.getValue();
                    break;
                }
            }
        } else {
            str = str2;
        }
        return dns.lookup(str);
    }
}
