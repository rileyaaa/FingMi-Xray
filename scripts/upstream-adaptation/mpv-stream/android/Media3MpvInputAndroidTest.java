/* SPDX-License-Identifier: Apache-2.0 */
package org.fingmi.mpvprobe;

import static org.junit.Assert.*;
import android.os.Build;
import android.util.Log;
import androidx.media3.datasource.DataSpec;
import androidx.media3.mpvplayer.media.Media3MpvInput;
import androidx.media3.mpvplayer.media.MpvStreamOwner;
import is.xyz.mpv.MPVLib;
import java.io.IOException;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import okhttp3.Call;
import okhttp3.Connection;
import okhttp3.Credentials;
import okhttp3.EventListener;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.mockwebserver.Dispatcher;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import okhttp3.mockwebserver.SocketPolicy;
import okio.Buffer;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** Real Android instrumentation, Media3 OkHttpDataSource, and loopback HTTP.
 * MPVLib Java registry only; no native library, playback, or untagged events. */
public final class Media3MpvInputAndroidTest {
    private static final String AUTH = Credentials.basic("fixture", "not-a-real-secret");
    private static final byte[] WAV = makeWav();
    private final Media3MpvInput input = new Media3MpvInput();
    private final ExecutorService workers = Executors.newCachedThreadPool();
    private final CopyOnWriteArrayList<RecordedRequest> requests = new CopyOnWriteArrayList<>();
    private final ConcurrentHashMap<Call, Trace> traces = new ConcurrentHashMap<>();
    private MockWebServer server, other;
    private OkHttpClient client;
    private MpvStreamOwner.Lease active;

    private static byte[] makeWav() {
        ByteBuffer b = ByteBuffer.allocate(44 + 32768).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(0x46464952).putInt(b.capacity() - 8).putInt(0x45564157);
        b.putInt(0x20746d66).putInt(16).putShort((short)1).putShort((short)1);
        b.putInt(8000).putInt(16000).putShort((short)2).putShort((short)16);
        b.putInt(0x61746164).putInt(32768);
        for (int i = 0; b.hasRemaining(); i++) b.putShort((short)(i * 17));
        return b.array();
    }

    private static final class Trace extends EventListener {
        final AtomicInteger acquired = new AtomicInteger(), released = new AtomicInteger();
        final CountDownLatch terminal = new CountDownLatch(1);
        volatile boolean failed;
        @Override public void connectionAcquired(Call c, Connection connection) { acquired.incrementAndGet(); }
        @Override public void connectionReleased(Call c, Connection connection) { released.incrementAndGet(); }
        @Override public void callEnd(Call c) { terminal.countDown(); }
        @Override public void callFailed(Call c, IOException e) { failed = true; terminal.countDown(); }
    }

    @Before public void setup() throws Exception {
        assertTrue("must run on Android", Build.VERSION.SDK_INT >= 24);
        server = new MockWebServer();
        other = new MockWebServer();
        server.start(InetAddress.getByName("127.0.0.1"), 0);
        other.start(InetAddress.getByName("127.0.0.1"), 0);
        server.setDispatcher(new Fixture(false));
        other.setDispatcher(new Fixture(true));
        client = new OkHttpClient.Builder()
                .connectTimeout(5, TimeUnit.SECONDS).readTimeout(25, TimeUnit.SECONDS)
                .callTimeout(35, TimeUnit.SECONDS)
                .eventListenerFactory(c -> { Trace t = new Trace(); traces.put(c, t); return t; })
                .authenticator((route, response) -> {
                    if (!response.request().url().host().equals(server.url("/").host())
                            || response.request().url().port() != server.getPort()
                            || response.request().header("Authorization") != null) return null;
                    return response.request().newBuilder().header("Authorization", AUTH).build();
                }).build();
    }

    private final class Fixture extends Dispatcher {
        private final boolean cross;
        Fixture(boolean cross) { this.cross = cross; }
        @Override public MockResponse dispatch(RecordedRequest req) {
            requests.add(req);
            String path = req.getRequestUrl().encodedPath();
            if (cross) {
                if (req.getHeader("Authorization") != null) return new MockResponse().setResponseCode(403);
            } else if ("/challenge".equals(path) && req.getHeader("Authorization") == null) {
                return new MockResponse().setResponseCode(401).setHeader("WWW-Authenticate", "Basic realm=\"fixture\"");
            } else if (!AUTH.equals(req.getHeader("Authorization"))) {
                return new MockResponse().setResponseCode(401);
            }
            if ("/redirect-local".equals(path)) return new MockResponse().setResponseCode(302).setHeader("Location", "/media");
            if ("/redirect-cross".equals(path)) return new MockResponse().setResponseCode(302).setHeader("Location", other.url("/target").toString());
            if ("/slow-headers".equals(path)) return new MockResponse().setSocketPolicy(SocketPolicy.NO_RESPONSE);
            String range = req.getHeader("Range");
            long offset = 0;
            if (range != null) {
                if (!range.matches("bytes=[0-9]+-")) return new MockResponse().setResponseCode(400);
                offset = Long.parseLong(range.substring(6, range.length()-1));
            }
            if (offset >= WAV.length) return new MockResponse().setResponseCode(416)
                    .setHeader("Content-Range", "bytes */" + WAV.length);
            boolean ignore = "/ignore-range".equals(path);
            int pos = ignore ? 0 : (int)offset;
            MockResponse response = new MockResponse().setBody(new Buffer().write(WAV, pos, WAV.length-pos));
            if (range != null && !ignore) {
                response.setResponseCode(206).setHeader("Content-Range",
                        "bytes " + ("/bad-range".equals(path) ? pos+1 : pos) + "-" + (WAV.length-1) + "/" + WAV.length);
            }
            if ("/slow-body".equals(path)) response.setBodyDelay(9, TimeUnit.SECONDS);
            if ("/unrelated".equals(path)) response.setBodyDelay(3, TimeUnit.SECONDS);
            if ("/short".equals(path)) response.setSocketPolicy(SocketPolicy.DISCONNECT_DURING_RESPONSE_BODY);
            return response;
        }
    }

    private DataSpec spec(String path, String owner, boolean auth) {
        Map<String,String> headers = new HashMap<>();
        headers.put("X-Playback", owner);
        if (auth) headers.put("Authorization", AUTH);
        return new DataSpec.Builder().setUri(server.url(path).toString()).setHttpRequestHeaders(headers).build();
    }

    private MPVLib.Stream replace(String path, String owner, boolean auth) {
        active = input.replace(client, spec(path, owner, auth));
        MPVLib.Stream s = MPVLib.openStream(active.uri);
        assertNotNull(s);
        return s;
    }

    private static void bytes(MPVLib.Stream s, int position, int size) {
        ByteBuffer buffer = ByteBuffer.allocateDirect(size + 4);
        buffer.position(2); buffer.limit(size + 2);
        while (buffer.hasRemaining()) assertTrue("positive read", s.read(buffer) > 0);
        buffer.flip(); buffer.position(2);
        byte[] result = new byte[size]; buffer.get(result);
        assertArrayEquals(Arrays.copyOfRange(WAV, position, position + size), result);
    }

    private RecordedRequest awaitRequest(String path, String range, String owner, boolean authorization) throws Exception {
        long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        do {
            for (RecordedRequest r : requests) {
                if (path.equals(r.getRequestUrl().encodedPath())
                        && (range == null || range.equals(r.getHeader("Range")))
                        && owner.equals(r.getHeader("X-Playback"))
                        && (authorization ? AUTH.equals(r.getHeader("Authorization")) : r.getHeader("Authorization") == null)) return r;
            }
            Thread.sleep(20);
        } while (System.nanoTime() < until);
        throw new AssertionError("request not observed: " + path + " " + range + " " + owner);
    }

    private Call callFor(String path) {
        for (Call c : traces.keySet()) if (path.equals(c.request().url().encodedPath())) return c;
        throw new AssertionError("missing call for " + path);
    }

    private void verifyReleased() throws Exception {
        assertFalse("no real OkHttp calls", traces.isEmpty());
        int n = 0, sockets = 0;
        for (Map.Entry<Call,Trace> e : traces.entrySet()) {
            Trace t = e.getValue();
            assertTrue("call not terminal: " + e.getKey().request().url().encodedPath(), t.terminal.await(6,TimeUnit.SECONDS));
            assertEquals("connection not released", t.acquired.get(), t.released.get());
            n++; sockets += t.released.get();
        }
        long until = System.nanoTime()+TimeUnit.SECONDS.toNanos(5);
        while (client.dispatcher().runningCallsCount() != 0 && System.nanoTime() < until) Thread.sleep(20);
        assertEquals(0, client.dispatcher().runningCallsCount());
        assertEquals(0, client.dispatcher().queuedCallsCount());
        client.connectionPool().evictAll();
        assertEquals(0, client.connectionPool().connectionCount());
        Log.i("MpvProbe", "PASS_REAL_OKHTTP_RELEASE calls="+n+" connectionReleases="+sockets);
    }

    private void retire() {
        if (active != null) { input.retire(active); active = null; }
    }

    @Test public void realRangeSeekEofHeadersAndIgnoredRange() throws Exception {
        MPVLib.Stream s = replace("/media", "range", true);
        assertEquals(WAV.length,s.size()); bytes(s,0,512);
        assertEquals(2048,s.seek(2048)); bytes(s,2048,513);
        assertEquals(44,s.seek(44)); bytes(s,44,64);
        assertEquals(-1,s.seek(-1)); assertEquals(-1,s.seek(WAV.length+1L));
        assertEquals(WAV.length-8,s.seek(WAV.length-8)); bytes(s,WAV.length-8,8);
        assertEquals(0,s.read(ByteBuffer.allocateDirect(4)));
        assertEquals(WAV.length,s.seek(WAV.length)); assertEquals(0,s.read(ByteBuffer.allocateDirect(1)));
        for (int pos : new int[]{2048,44,WAV.length-8})
            assertEquals("identity",awaitRequest("/media","bytes="+pos+"-","range",true).getHeader("Accept-Encoding"));
        s.close(); s.close(); retire();
        s = replace("/ignore-range","ignore",true);
        assertEquals(WAV.length,s.size()); assertEquals(512,s.seek(512)); bytes(s,512,32);
        awaitRequest("/ignore-range","bytes=512-","ignore",true);
        retire(); verifyReleased();
        Log.i("MpvProbe","PASS_ANDROID_RANGE_SEEK_EOF_HEADERS");
    }

    @Test public void actualAuthenticationAndRedirectPolicy() throws Exception {
        MPVLib.Stream s = replace("/challenge","challenge",false);
        bytes(s,0,16);
        awaitRequest("/challenge",null,"challenge",false);
        awaitRequest("/challenge",null,"challenge",true);
        retire();
        s = replace("/redirect-local","same",true);
        bytes(s,0,16); assertEquals(128,s.seek(128)); bytes(s,128,16);
        awaitRequest("/media","bytes=128-","same",true); retire();
        s = replace("/redirect-cross","cross",true);
        bytes(s,0,16); assertEquals(256,s.seek(256)); bytes(s,256,16);
        awaitRequest("/redirect-cross","bytes=256-","cross",true);
        awaitRequest("/target","bytes=256-","cross",false);
        for (RecordedRequest r: requests) if ("/target".equals(r.getRequestUrl().encodedPath())) assertNull(r.getHeader("Authorization"));
        retire(); verifyReleased();
        Log.i("MpvProbe","PASS_ANDROID_AUTH_REDIRECT same-origin-auth-retained cross-origin-auth-stripped custom-header-retained");
    }

    @Test public void cancelBlockedHeadersAndKeepOtherCallAlive() throws Exception {
        MPVLib.Stream s = replace("/slow-headers","headers",true);
        Future<Long> opening = workers.submit(s::size);
        awaitRequest("/slow-headers",null,"headers",true);
        Call blocked = callFor("/slow-headers");
        Call unrelated = client.newCall(new Request.Builder().url(server.url("/unrelated"))
                .header("Authorization",AUTH).header("X-Playback","other").build());
        try (Response response = unrelated.execute()) {
            assertTrue(response.isSuccessful()); assertFalse(opening.isDone());
            s.cancel();
            assertEquals(-1L,opening.get(5,TimeUnit.SECONDS).longValue());
            assertTrue(blocked.isCanceled());
            assertTrue(traces.get(blocked).terminal.await(5,TimeUnit.SECONDS));
            assertTrue(traces.get(blocked).failed);
            assertFalse(unrelated.isCanceled());
            assertArrayEquals(WAV,response.body().bytes());
        }
        s.close(); retire(); verifyReleased();
        Log.i("MpvProbe","PASS_ANDROID_CANCEL_HEADERS unrelated-call-unaffected");
    }

    @Test public void cancelBlockedBodyOnOwnerSwitchAndRejectRetiredUri() throws Exception {
        MPVLib.Stream old = replace("/slow-body","old",true);
        MpvStreamOwner.Lease oldLease = active;
        assertEquals(WAV.length,old.size());
        ByteBuffer target = ByteBuffer.allocateDirect(32);
        CountDownLatch entered = new CountDownLatch(1);
        Future<Integer> reading = workers.submit(() -> { entered.countDown(); return old.read(target); });
        assertTrue(entered.await(3,TimeUnit.SECONDS));
        Thread.sleep(150); assertFalse("read must be blocked",reading.isDone());
        Call blocked = callFor("/slow-body");
        Future<MpvStreamOwner.Lease> switching = workers.submit(() -> input.replace(client,spec("/media","new",true)));
        active = switching.get(5,TimeUnit.SECONDS);
        assertNotEquals(oldLease.uri,active.uri);
        assertNull(MPVLib.openStream(oldLease.uri));
        assertEquals(-1,reading.get(5,TimeUnit.SECONDS).intValue()); assertEquals(0,target.position());
        assertTrue(blocked.isCanceled());
        assertTrue(traces.get(blocked).terminal.await(5,TimeUnit.SECONDS));
        assertTrue(traces.get(blocked).failed);
        input.retire(oldLease); old.close();
        String currentUri = active.uri;
        MPVLib.Stream current = MPVLib.openStream(currentUri);
        assertNotNull(current); bytes(current,0,64);
        awaitRequest("/media",null,"new",true);
        retire(); assertNull(MPVLib.openStream(currentUri)); verifyReleased();
        Log.i("MpvProbe","PASS_ANDROID_CANCEL_BODY_OWNER_SWITCH registry-only-no-native-events");
        // Allow the intentionally delayed server-side write to finish before MockWebServer shutdown.
        Thread.sleep(9000);
    }

    @Test public void cancelBeforeCallRegistrationAndRejectInvalidRange() throws Exception {
        CountDownLatch entered = new CountDownLatch(1), release = new CountDownLatch(1);
        AtomicReference<Call> created = new AtomicReference<>();
        Call.Factory delayed = request -> {
            entered.countDown();
            try { if (!release.await(8,TimeUnit.SECONDS)) throw new IllegalStateException("fixture timeout"); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IllegalStateException(e); }
            Call call = client.newCall(request); created.set(call); return call;
        };
        active = input.replace(delayed,spec("/media","early",true));
        MPVLib.Stream s = MPVLib.openStream(active.uri); assertNotNull(s);
        Future<Long> opening = workers.submit(s::size);
        try { assertTrue(entered.await(5,TimeUnit.SECONDS)); s.cancel(); }
        finally { release.countDown(); }
        assertEquals(-1L,opening.get(5,TimeUnit.SECONDS).longValue());
        assertNotNull(created.get()); assertTrue(created.get().isCanceled());
        retire();
        s = replace("/bad-range","bad",true);
        // The pinned DataSource issues Range for progressive content, including offset zero.
        ByteBuffer target = ByteBuffer.allocateDirect(16);
        assertEquals(-1,s.read(target)); assertEquals(0,target.position()); retire();
        s = replace("/short","short",true);
        int count;
        do { count = s.read(ByteBuffer.allocateDirect(4096)); } while (count > 0);
        assertEquals("truncated data must not become clean EOF",-1,count); retire();
        verifyReleased();
        Log.i("MpvProbe","PASS_ANDROID_STICKY_CANCEL_INVALID_RANGE_TRUNCATION");
    }

    @After public void cleanup() throws Exception {
        retire();
        workers.shutdownNow();
        if (client != null) { client.dispatcher().cancelAll(); client.connectionPool().evictAll(); client.dispatcher().executorService().shutdownNow(); }
        if (server != null) server.shutdown();
        if (other != null) other.shutdown();
    }
}
