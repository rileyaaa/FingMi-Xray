#!/usr/bin/env python3
"""Verify that 5.8+ TV recovery overlays are scoped, fail-closed and repeatable."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/upstream"))
from recovery_adapters import (
    site_view_model, base_loader, ok_http, ok_dns, img_util, ok_glide,
)


def check_failure(transform, value):
    try:
        transform(value)
    except ValueError:
        return
    raise AssertionError(f"{transform.__name__}: accepted unknown upstream source shape")


site = """class SiteViewModel {
    private final ViewModelTaskRunner<TaskType> tasks;
    private enum TaskType { RESULT }
    public void stopSearch() { searches.stop(); }
}
"""
out=site_view_model(site)
assert "tasks.cancel(TaskType.RESULT);" in out
assert site_view_model(out)==out
check_failure(site_view_model, "class SiteViewModel {}")

loader = """import android.text.TextUtils;
class BaseLoader {
    public void clear() {
        clear(false);
    }

    public void destroy() {
        clear(true);
    }

    private void clear(boolean exiting) {
        Task.execute(() -> clearLoaders(previous, retired));
    }
}
"""
out=base_loader(loader)
assert "public void clear(Runnable onComplete)" in out
assert "clear(false, onComplete);" in out
assert "if (onComplete != null) App.post(onComplete);" in out
assert out.index("clearLoaders(previous, retired);") < out.index("if (onComplete != null) App.post(onComplete);")
assert base_loader(out)==out
check_failure(base_loader, "class BaseLoader { public void clear() {} }")

http = """import java.util.Objects;
class OkHttp {
    private static final long TIMEOUT = TimeUnit.SECONDS.toMillis(30);
    public void clear() { }
}
"""
out=ok_http(http)
assert "public static void resetApiNetworkForResume()" in out
assert "get().client = null;" in out
assert "dns().resetForNetworkChange();" in out
assert "get().player = null" not in out
assert "selector().clear();" not in out
assert "NETWORK_CLEANUP.execute" in out
assert ok_http(out)==out
check_failure(ok_http, "class OkHttp { public void clear() {} }")

dns = """class OkDns {
    private volatile DnsOverHttps doh;
    public synchronized void setDoh(Doh item) {
        HttpUrl url = HttpUrl.parse(item.getUrl());
        this.doh = url == null ? null : new DnsOverHttps.Builder().client(new OkHttpClient()).url(url).bootstrapDnsHosts(item.getHosts()).build();
        this.supplier = null;
    }
    public synchronized void setDoh(Supplier<Doh> supplier) {
        this.supplier = supplier;
    }
    public List<InetAddress> lookup(String hostname) {
        Supplier<Doh> supplier = this.supplier;
        if (supplier != null) initDoh(supplier);
        return (doh != null ? doh : Dns.SYSTEM).lookup(get(hostname));
    }
}
"""
out=ok_dns(dns)
assert "public synchronized void resetForNetworkChange()" in out
assert "resolver = doh != null ? doh : Dns.SYSTEM;" in out
assert "OkHttp.cleanupClientAsync(oldClient);" in out
assert "return resolver.lookup(get(hostname));" in out
assert ok_dns(out)==out
check_failure(ok_dns,"class OkDns { private volatile DnsOverHttps doh; }")

img="""import java.util.regex.Pattern;
class ImgUtil {
    private static final Set<String> failed = Collections.synchronizedSet(new HashSet<>());
    public record Image(String mime, byte[] data) {
    }
    private static RequestListener<Drawable> getListener(String text, String url, ImageView view, boolean vod) {
        return new RequestListener<>() {
            public boolean onLoadFailed(@Nullable GlideException e, Object model, @NonNull Target<Drawable> target, boolean isFirstResource) {
                view.setImageDrawable(getTextDrawable(text, vod));
                failed.add(url);
                return true;
            }
        };
    }
}
"""
out=img_util(img)
assert "private static final AtomicLong networkFailureEpoch" in out
assert "networkFailureEpoch.incrementAndGet();" in out
assert "if (requestEpoch != networkFailureEpoch.get()) return true;" in out
assert img_util(out)==out
check_failure(img_util,"class ImgUtil {}")

glide = "registry.replace(GlideUrl.class, InputStream.class, new OkHttpUrlLoader.Factory(OkHttp.client()));"
out=ok_glide(glide)
assert "new OkHttpUrlLoader.Factory(request -> OkHttp.client().newCall(request))" in out
assert ok_glide(out)==out
check_failure(ok_glide,"registry.replace(null,null,null);")
print("PASS: SiteViewModel, BaseLoader, OkHttp, DoH, Glide epoch and network handoff overlays")
