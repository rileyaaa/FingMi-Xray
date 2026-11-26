/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.mpvplayer.media;

import androidx.media3.common.C;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.okhttp.OkHttpDataSource;
import is.xyz.mpv.MPVLib;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import okhttp3.Call;
import okhttp3.Request;

/** Isolated HTTP byte-stream input, not a replacement for ordinary MPV or disc navigation.
 * The caller supplies its existing per-playback authenticated Call.Factory and DataSpec. */
public final class Media3MpvInput {
    private final MpvStreamOwner owner = new MpvStreamOwner();
    private MpvStreamOwner.Lease active;

    public synchronized MpvStreamOwner.Lease replace(Call.Factory client, DataSpec spec) {
        if (client == null || spec == null) throw new NullPointerException();
        String scheme = spec.uri.getScheme();
        if (!("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme))
                || spec.httpMethod != DataSpec.HTTP_METHOD_GET || spec.httpBody != null
                || spec.position != 0 || spec.uriPositionOffset != 0 || spec.length != C.LENGTH_UNSET
                || spec.isFlagSet(DataSpec.FLAG_ALLOW_GZIP)) {
            throw new IllegalArgumentException("expected unbounded identity HTTP GET");
        }
        for (String key : spec.httpRequestHeaders.keySet()) {
            if ("Range".equalsIgnoreCase(key) || "Accept-Encoding".equalsIgnoreCase(key)) {
                throw new IllegalArgumentException("byte-range headers are managed by the data source");
            }
        }
        if (active != null) MPVLib.unregisterStream(active.uri);
        MpvStreamOwner.Lease lease = owner.replace(() -> new HttpSource(client, spec));
        active = lease;
        MPVLib.registerStream(lease.uri, () -> {
            MpvStreamOwner.Cursor cursor = lease.open();
            if (cursor == null) return null;
            return new MPVLib.Stream() {
                public int read(ByteBuffer b) { return cursor.read(b); }
                public long seek(long p) { return cursor.seek(p); }
                public long size() { return cursor.size(); }
                public void cancel() { cursor.cancel(); }
                public void close() { cursor.close(); }
            };
        });
        return lease;
    }

    public synchronized void retire(MpvStreamOwner.Lease lease) {
        if (lease == null || active != lease) return;
        MPVLib.unregisterStream(lease.uri);
        active = null;
        owner.retire(lease);
    }

    /** Media3's generic DataSource has no concurrent cancel contract. Capture only
     * the actual OkHttp Call created for this open, never dispatcher.cancelAll(). */
    private static final class OwnedCall implements Call.Factory {
        private final Call.Factory client;
        private Call call;
        private boolean cancelled;
        OwnedCall(Call.Factory client) { this.client = client; }
        @Override public Call newCall(Request request) {
            Call next = client.newCall(request);
            synchronized (this) {
                if (call != null) throw new IllegalStateException("one call per source");
                call = next;
                if (cancelled) next.cancel();
            }
            return next;
        }
        synchronized void cancel() {
            cancelled = true;
            if (call != null) call.cancel();
        }
    }

    private static final class HttpSource implements MpvStreamOwner.Source {
        private static final Pattern RANGE = Pattern.compile("bytes ([0-9]+)-([0-9]+)/([0-9]+)");
        private final DataSpec base;
        private final OwnedCall call;
        private final OkHttpDataSource source;
        HttpSource(Call.Factory client, DataSpec base) {
            this.base = base;
            call = new OwnedCall(client);
            source = new OkHttpDataSource.Factory(call).createDataSource();
        }
        public long open(long position) throws IOException {
            long remaining = source.open(base.buildUpon().setPosition(position).build());
            String encoding = header(source.getResponseHeaders(), "Content-Encoding");
            if (encoding != null && !"identity".equalsIgnoreCase(encoding)) {
                throw new IOException("encoded byte stream");
            }
            if (source.getResponseCode() == 206) {
                String value = header(source.getResponseHeaders(), "Content-Range");
                Matcher range = RANGE.matcher(value == null ? "" : value);
                if (!range.matches()) throw new IOException("invalid Content-Range");
                long start = Long.parseLong(range.group(1));
                long end = Long.parseLong(range.group(2));
                long total = Long.parseLong(range.group(3));
                if (start != position || end < start || end != total - 1 || remaining != total - start) {
                    throw new IOException("unexpected byte range");
                }
            }
            return remaining;
        }
        private static String header(Map<String, List<String>> headers, String name) throws IOException {
            for (Map.Entry<String, List<String>> entry : headers.entrySet()) {
                if (name.equalsIgnoreCase(entry.getKey())) {
                    List<String> values = entry.getValue();
                    if (values.size() != 1) throw new IOException("ambiguous response header");
                    return values.get(0);
                }
            }
            return null;
        }
        public int read(byte[] bytes, int length) throws IOException { return source.read(bytes, 0, length); }
        public void cancel() { call.cancel(); }
        public void close() throws IOException { source.close(); }
    }
}
