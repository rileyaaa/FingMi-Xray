/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.mpvplayer.media;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** Single playback owner; no global transport settings or untagged event routing. */
public final class MpvStreamOwner {
    /** One open attempt. cancel must be thread-safe, sticky and unblock open/read.
     * cancel is idempotent and must not throw. close is serialized, even after failed open. */
    public interface Source {
        long open(long position) throws IOException; // remaining bytes, or -1
        int read(byte[] target, int length) throws IOException; // -1 = EOF
        void cancel();
        void close() throws IOException;
    }

    public interface Factory {
        Source create(); // no blocking I/O; fresh source per open/seek
    }

    private Lease current;

    public final class Lease {
        public final String uri = "media3iso://" + UUID.randomUUID();
        private final Factory factory;
        private final Set<Cursor> cursors = new HashSet<>();
        private Lease(Factory factory) { this.factory = factory; }

        private boolean isCurrent() {
            synchronized (MpvStreamOwner.this) { return current == this; }
        }

        public Cursor open() {
            synchronized (MpvStreamOwner.this) {
                if (current != this) return null;
                Cursor cursor = new Cursor(this);
                cursors.add(cursor);
                return cursor;
            }
        }

        /** Only for callbacks already associated with this lease. Action must not block
         * or enter stream I/O or owner lifecycle. The check and publication are atomic. */
        public boolean publish(Runnable action) {
            synchronized (MpvStreamOwner.this) {
                if (current != this) return false;
                action.run();
                return true;
            }
        }
    }

    public Lease replace(Factory factory) {
        if (factory == null) throw new NullPointerException("factory");
        Lease next = new Lease(factory);
        List<Cursor> old;
        synchronized (this) {
            old = detach(current);
            current = next;
        }
        dispose(old);
        return next;
    }

    public void retire(Lease lease) {
        List<Cursor> old;
        synchronized (this) {
            if (lease == null || current != lease) return;
            current = null;
            old = detach(lease);
        }
        dispose(old);
    }

    // Must hold the owner lock; do not wait for I/O under that lock.
    private List<Cursor> detach(Lease lease) {
        List<Cursor> result = new ArrayList<>();
        if (lease != null) {
            result.addAll(lease.cursors);
            lease.cursors.clear();
        }
        return result;
    }

    private static void dispose(List<Cursor> cursors) {
        for (Cursor cursor : cursors) cursor.cancel();
        for (Cursor cursor : cursors) cursor.close();
    }

    public final class Cursor {
        private final Lease lease;
        private final Object state = new Object();
        private final Object io = new Object();
        private final byte[] bytes = new byte[64 * 1024];
        private Source source;
        private boolean cancelled;
        private long position;
        private long size = -1;
        private boolean eof;
        private Cursor(Lease lease) { this.lease = lease; }

        // Only the I/O path mutates position, size or eof. Publish source before open
        // so a native cancellation arriving during DNS/headers/read can reach it.
        private boolean openAt(long target) throws IOException {
            closeSource();
            Source next;
            synchronized (state) {
                if (cancelled || !lease.isCurrent()) return false;
                next = lease.factory.create();
                if (next == null) throw new IOException("missing source");
                source = next;
            }
            long remaining = next.open(target);
            if (remaining < -1 || (remaining >= 0 && target > Long.MAX_VALUE - remaining)) {
                throw new IOException("invalid resolved length");
            }
            synchronized (state) {
                if (cancelled || !lease.isCurrent()) return false;
                if (remaining >= 0) {
                    long resolved = target + remaining;
                    if (size >= 0 && resolved != size) throw new IOException("resource length changed");
                    size = resolved;
                }
                position = target;
                eof = remaining == 0;
                return true;
            }
        }

        private boolean live() {
            synchronized (state) { return !cancelled && lease.isCurrent(); }
        }

        private boolean ready() throws IOException {
            synchronized (state) {
                if (cancelled || !lease.isCurrent()) return false;
                if (source != null) return true;
            }
            return openAt(position);
        }

        public int read(ByteBuffer buffer) {
            synchronized (io) {
                try {
                    if (!ready()) return -1;
                    if (!buffer.hasRemaining() || eof) return live() ? 0 : -1;
                    int limit = Math.min(bytes.length, buffer.remaining());
                    if (size >= 0) limit = (int) Math.min(limit, size - position);
                    if (limit == 0) { eof = true; return live() ? 0 : -1; }
                    int count = source.read(bytes, limit);
                    synchronized (state) {
                        synchronized (MpvStreamOwner.this) {
                            if (cancelled || current != lease) return -1;
                            if (count == -1) {
                                if (size >= 0 && position != size) throw new IOException("premature EOF");
                                eof = true;
                                return 0;
                            }
                            if (count <= 0 || count > limit || position > Long.MAX_VALUE - count) {
                                throw new IOException("invalid source read");
                            }
                            buffer.put(bytes, 0, count);
                            position += count;
                            return count;
                        }
                    }
                } catch (IOException | RuntimeException error) {
                    fail();
                    return -1;
                }
            }
        }

        public long seek(long target) {
            synchronized (io) {
                if (target < 0 || (size >= 0 && target > size)) return -1;
                try {
                    if (!ready()) return -1;
                    if (size >= 0 && target > size) return -1;
                    return (target == position || openAt(target)) && live() ? target : -1;
                } catch (IOException | RuntimeException error) {
                    fail();
                    return -1;
                }
            }
        }

        public long size() {
            synchronized (io) {
                try {
                    return ready() && live() ? size : -1;
                } catch (IOException | RuntimeException error) {
                    fail();
                    return -1;
                }
            }
        }

        public void cancel() {
            Source active;
            synchronized (state) {
                if (cancelled) return;
                cancelled = true;
                active = source;
            }
            if (active != null) active.cancel();
        }

        private void closeSource() throws IOException {
            Source old;
            synchronized (state) { old = source; }
            if (old != null) {
                try {
                    old.cancel();
                } finally {
                    try { old.close(); }
                    finally { synchronized (state) { source = null; } }
                }
            }
        }

        private void fail() {
            cancel();
            try { closeSource(); } catch (IOException ignored) { /* terminal I/O failure */ }
        }

        public void close() {
            cancel();
            synchronized (io) {
                try { closeSource(); } catch (IOException ignored) { /* terminal I/O failure */ }
            }
            synchronized (MpvStreamOwner.this) { lease.cursors.remove(this); }
        }
    }
}
