package com.github.catvod.net;

import androidx.annotation.NonNull;

import com.github.catvod.bean.Doh;
import com.github.catvod.utils.Util;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;
import java.util.stream.Collectors;

import okhttp3.Dns;
import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.dnsoverhttps.DnsOverHttps;

public class OkDns implements Dns {

    private final ConcurrentHashMap<String, String> map;
    private volatile Supplier<Doh> supplier;
    private volatile Doh currentDoh;
    private volatile DnsOverHttps doh;
    private volatile OkHttpClient dohClient;

    public OkDns() {
        this.map = new ConcurrentHashMap<>();
    }

    public synchronized void setDoh(Doh item) {
        currentDoh = item;
        supplier = null;
        rebuildDoh(item);
    }

    public synchronized void setDoh(Supplier<Doh> supplier) {
        currentDoh = null;
        this.supplier = supplier;
        rebuildDoh(null);
    }

    /**
     * Recovered TV resume behavior (R8 ha2).
     *
     * If DoH is still lazy, discard its stale transport and keep the supplier
     * for the next lookup. If a concrete DoH selection is already active,
     * rebuild it immediately with a fresh OkHttpClient.
     */
    public synchronized void resetForNetworkChange() {
        if (supplier != null) rebuildDoh(null);
        else rebuildDoh(currentDoh);
    }

    public synchronized void resetAndClear() {
        Supplier<Doh> oldSupplier = supplier;
        Doh oldDoh = currentDoh;
        rebuildDoh(null);
        supplier = oldSupplier;
        currentDoh = oldDoh;
        map.clear();
    }

    private void rebuildDoh(Doh item) {
        OkHttpClient oldClient = dohClient;
        doh = null;
        dohClient = null;

        if (item != null) {
            HttpUrl url = HttpUrl.parse(item.getUrl());
            if (url != null) {
                dohClient = new OkHttpClient();
                doh = new DnsOverHttps.Builder()
                        .client(dohClient)
                        .url(url)
                        .bootstrapDnsHosts(item.getHosts())
                        .build();
            }
        }

        OkHttp.cleanupClientAsync(oldClient);
    }

    public void clear() {
        map.clear();
    }

    public void addAll(List<String> hosts) {
        map.putAll(hosts.stream().filter(Objects::nonNull).map(host -> host.split("=", 2)).filter(splits -> splits.length == 2).collect(Collectors.toMap(s -> s[0].trim(), s -> s[1].trim(), (oldHost, newHost) -> newHost)));
    }

    private String get(String hostname) {
        String target = map.get(hostname);
        if (target != null) return target;
        for (Map.Entry<String, String> entry : map.entrySet()) if (Util.containOrMatch(hostname, entry.getKey())) return entry.getValue();
        return hostname;
    }

    @NonNull
    @Override
    public List<InetAddress> lookup(@NonNull String hostname) throws UnknownHostException {
        Dns resolver;
        synchronized (this) {
            if (doh == null) {
                Supplier<Doh> lazy = supplier;
                if (lazy != null) {
                    initDoh(lazy);
                } else if (currentDoh != null) {
                    rebuildDoh(currentDoh);
                }
            }
            resolver = doh != null ? doh : Dns.SYSTEM;
        }
        return resolver.lookup(get(hostname));
    }

    private synchronized void initDoh(Supplier<Doh> supplier) {
        if (supplier != this.supplier) return;
        Doh item = supplier.get();
        currentDoh = item;
        this.supplier = null;
        rebuildDoh(item);
    }
}
