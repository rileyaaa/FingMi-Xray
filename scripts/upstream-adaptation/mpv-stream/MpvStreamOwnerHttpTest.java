/* SPDX-License-Identifier: Apache-2.0 */
import androidx.media3.mpvplayer.media.MpvStreamOwner;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Actual loopback HTTP + synthetic PCM WAV; no Android or libmpv runtime. */
public final class MpvStreamOwnerHttpTest {
    private static final byte[] WAV = wav();
    private static final String AUTH = "Basic " + Base64.getEncoder().encodeToString("owner:fixture".getBytes(StandardCharsets.US_ASCII));
    private static final AtomicInteger CREATED = new AtomicInteger(), CLOSED = new AtomicInteger();
    private static final List<String> REQUESTS = Collections.synchronizedList(new ArrayList<>());
    private static final CountDownLatch SLOW_HEADERS = new CountDownLatch(1), SLOW_BODY = new CountDownLatch(1);
    private static final CountDownLatch RELEASE = new CountDownLatch(1);
    private static int port;
    private static void check(boolean ok, String reason) { if (!ok) throw new AssertionError(reason); }
    private static byte[] wav() {
        ByteBuffer b = ByteBuffer.allocate(44 + 32768).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(0x46464952).putInt(b.capacity() - 8).putInt(0x45564157).putInt(0x20746d66).putInt(16);
        b.putShort((short)1).putShort((short)1).putInt(8000).putInt(16000).putShort((short)2).putShort((short)16);
        b.putInt(0x61746164).putInt(32768);
        for (int i = 0; b.hasRemaining(); i++) b.putShort((short)(i * 17));
        return b.array();
    }
    private static void serve(HttpExchange e) throws IOException {
        try {
            String path = e.getRequestURI().getPath();
            String range = e.getRequestHeaders().getFirst("Range");
            String id = e.getRequestHeaders().getFirst("X-Playback");
            if (!AUTH.equals(e.getRequestHeaders().getFirst("Authorization")) || id == null || range == null) {
                e.sendResponseHeaders(401, -1); return;
            }
            REQUESTS.add(id + ":" + range);
            int pos = Integer.parseInt(range.substring(6, range.length() - 1));
            if (pos >= WAV.length) {
                e.getResponseHeaders().set("Content-Range", "bytes */" + WAV.length);
                e.sendResponseHeaders(416, -1); return;
            }
            if (path.equals("/slow-headers")) { SLOW_HEADERS.countDown(); awaitRelease(); }
            e.getResponseHeaders().set("Content-Range", "bytes " + pos + "-" + (WAV.length - 1) + "/" + WAV.length);
            e.sendResponseHeaders(206, WAV.length - pos);
            if (path.equals("/slow-body")) { SLOW_BODY.countDown(); awaitRelease(); }
            if (path.equals("/short")) e.getResponseBody().write(WAV, pos, 2);
            else e.getResponseBody().write(WAV, pos, WAV.length - pos);
        } finally { e.close(); }
    }
    private static void awaitRelease() throws IOException {
        try { if (!RELEASE.await(10, TimeUnit.SECONDS)) throw new IOException("fixture timeout"); }
        catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IOException(e); }
    }
    // A real socket-backed test transport, not a Media3 mock or product implementation.
    // Its sticky socket.close is the cancellation contract exercised by the owner core.
    private static final class HttpSource implements MpvStreamOwner.Source {
        private final String path, id, authorization;
        private Socket socket;
        private InputStream input;
        private boolean cancelled, closed;
        HttpSource(String path, String id, String authorization) {
            this.path = path; this.id = id; this.authorization = authorization; CREATED.incrementAndGet();
        }
        public long open(long p) throws IOException {
            Socket next = new Socket();
            synchronized (this) {
                if (cancelled) { next.close(); throw new IOException("cancelled before open"); }
                socket = next;
            }
            next.connect(new InetSocketAddress("127.0.0.1", port), 3000);
            next.setSoTimeout(8000);
            String request = "GET " + path + " HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\nRange: bytes=" + p
                    + "-\r\nAuthorization: " + authorization + "\r\nX-Playback: " + id + "\r\n\r\n";
            next.getOutputStream().write(request.getBytes(StandardCharsets.US_ASCII));
            input = new BufferedInputStream(next.getInputStream());
            String status = line(input);
            long length = -1;
            for (String h; !(h = line(input)).isEmpty();) {
                if (h.toLowerCase(Locale.ROOT).startsWith("content-length:")) length = Long.parseLong(h.substring(15).trim());
            }
            if (status.contains(" 416 ") && p == WAV.length) return 0;
            if (!status.contains(" 206 ") || length < 0) throw new IOException("unexpected response");
            return length;
        }
        private static String line(InputStream in) throws IOException {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            for (int c; (c = in.read()) != -1;) {
                if (c == '\n') return bytes.toString("US-ASCII");
                if (c != '\r') bytes.write(c);
                if (bytes.size() > 8192) throw new IOException("large header");
            }
            throw new EOFException();
        }
        public int read(byte[] b, int n) throws IOException { return input.read(b, 0, n); }
        public synchronized void cancel() {
            cancelled = true;
            if (socket != null) try { socket.close(); } catch (IOException e) { throw new UncheckedIOException(e); }
        }
        public synchronized void close() throws IOException {
            check(!closed, "double source close"); closed = true; CLOSED.incrementAndGet();
            if (socket != null) socket.close();
        }
    }
    private static MpvStreamOwner.Factory factory(String path, String id) { return () -> new HttpSource(path, id, AUTH); }
    private static void bytes(MpvStreamOwner.Cursor cursor, int position, int length) {
        ByteBuffer b = ByteBuffer.allocateDirect(length + 4); b.position(2); b.limit(length + 2);
        int n = 0;
        while (b.hasRemaining()) { int count = cursor.read(b); check(count > 0, "expected data"); n += count; }
        check(n == length, "read length"); b.flip(); b.position(2);
        for (int i = 0; i < n; i++) check(b.get() == WAV[position + i], "incorrect bytes at " + (position + i));
    }
    private static void waitFor(CountDownLatch latch) throws InterruptedException { check(latch.await(3, TimeUnit.SECONDS), "server did not receive request"); }
    private static void pass(String name) { System.out.println("PASS " + name); }
    public static void main(String[] args) throws Exception {
        ExecutorService serverThreads = Executors.newCachedThreadPool(), readers = Executors.newCachedThreadPool();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.setExecutor(serverThreads); server.createContext("/", MpvStreamOwnerHttpTest::serve); server.start(); port = server.getAddress().getPort();
        try {
            MpvStreamOwner owners = new MpvStreamOwner();
            MpvStreamOwner.Lease a = owners.replace(factory("/wav", "A"));
            MpvStreamOwner.Cursor c = a.open();
            check(c.size() == WAV.length, "size"); bytes(c, 0, 512);
            check(c.seek(2048) == 2048, "forward seek"); bytes(c, 2048, 513);
            check(c.seek(44) == 44, "backward seek"); bytes(c, 44, 1024);
            check(c.seek(-1) == -1 && c.seek(WAV.length + 1) == -1, "out of range");
            check(c.seek(WAV.length - 8) == WAV.length - 8, "tail seek"); bytes(c, WAV.length - 8, 8);
            check(c.read(ByteBuffer.allocateDirect(8)) == 0, "EOF");
            check(c.seek(WAV.length) == WAV.length && c.read(ByteBuffer.allocateDirect(8)) == 0, "seek EOF");
            check(REQUESTS.containsAll(Arrays.asList("A:bytes=0-", "A:bytes=2048-", "A:bytes=44-", "A:bytes=" + (WAV.length - 8) + "-")), "range/auth/headers");
            c.close(); c.close(); check(CREATED.get() == CLOSED.get(), "seek/close resource leak"); pass("range seek size EOF direct buffer auth headers and idempotent close");
            MpvStreamOwner.Cursor second = a.open(); bytes(second, 0, 16);
            MpvStreamOwner.Lease b = owners.replace(factory("/wav", "B"));
            check(!a.uri.equals(b.uri) && a.open() == null && second.read(ByteBuffer.allocateDirect(1)) == -1, "retired cursor/URI");
            AtomicInteger events = new AtomicInteger(); check(!a.publish(events::incrementAndGet) && b.publish(events::incrementAndGet), "owner callback gate");
            owners.retire(a); check(events.get() == 1 && b.open() != null, "stale retirement affected current owner");
            MpvStreamOwner.Cursor live = b.open(); bytes(live, 0, 32); owners.retire(b);
            check(CREATED.get() == CLOSED.get(), "retirement leak"); pass("distinct owner URI, stale callback and retirement isolation");
            MpvStreamOwner.Lease slow = owners.replace(factory("/slow-headers", "C"));
            MpvStreamOwner.Cursor opening = slow.open(); Future<Long> openingResult = readers.submit(opening::size);
            waitFor(SLOW_HEADERS); opening.cancel(); check(openingResult.get(2, TimeUnit.SECONDS) == -1, "cancel blocked open"); opening.close(); owners.retire(slow);
            check(CREATED.get() == CLOSED.get(), "cancel open leak"); pass("cancel while waiting HTTP headers");
            MpvStreamOwner.Lease old = owners.replace(factory("/slow-body", "D"));
            MpvStreamOwner.Cursor reading = old.open(); check(reading.size() == WAV.length, "slow body open");
            ByteBuffer stale = ByteBuffer.allocateDirect(8); CountDownLatch started = new CountDownLatch(1);
            Future<Integer> read = readers.submit(() -> { started.countDown(); return reading.read(stale); });
            waitFor(SLOW_BODY); waitFor(started); Thread.sleep(100); check(!read.isDone(), "read not blocked");
            Future<MpvStreamOwner.Lease> replacement = readers.submit(() -> owners.replace(factory("/wav", "E")));
            MpvStreamOwner.Lease next = replacement.get(2, TimeUnit.SECONDS);
            check(read.get(2, TimeUnit.SECONDS) == -1 && stale.position() == 0, "retired read published bytes");
            check(!old.publish(events::incrementAndGet), "late event"); owners.retire(old);
            bytes(next.open(), 0, 128); owners.retire(next); check(CREATED.get() == CLOSED.get(), "cancel read leak");
            pass("cancel blocked HTTP read on owner switch; new owner still reads");
            MpvStreamOwner.Lease denied = owners.replace(() -> new HttpSource("/wav", "F", "wrong"));
            check(denied.open().read(ByteBuffer.allocateDirect(16)) == -1, "401 not error"); owners.retire(denied);
            MpvStreamOwner.Lease shortBody = owners.replace(factory("/short", "G"));
            MpvStreamOwner.Cursor shortRead = shortBody.open(); check(shortRead.read(ByteBuffer.allocateDirect(8)) == 2, "short body first bytes");
            check(shortRead.read(ByteBuffer.allocateDirect(8)) == -1, "truncated body treated as EOF"); owners.retire(shortBody);
            MpvStreamOwner.Lease never = owners.replace(factory("/wav", "H")); MpvStreamOwner.Cursor unopened = never.open(); unopened.cancel();
            check(unopened.read(ByteBuffer.allocateDirect(1)) == -1 && !REQUESTS.contains("H:bytes=0-"), "cancel before open"); owners.retire(never);
            check(CREATED.get() == CLOSED.get(), "failure resource leak"); pass("401 premature EOF cancel-before-open and failure cleanup");
            System.out.println("PASS HOST_HTTP sources=" + CREATED.get() + " closed=" + CLOSED.get() + " authenticatedRequests=" + REQUESTS.size());
        } finally { RELEASE.countDown(); server.stop(0); serverThreads.shutdownNow(); readers.shutdownNow(); }
    }
}
