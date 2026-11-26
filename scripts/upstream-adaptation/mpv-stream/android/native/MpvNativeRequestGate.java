/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.mpvplayer.media;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/** Only native replies with an explicit request ID may enter this gate.
 * Neither global property events nor END_FILE/FILE_LOADED are attributed here. */
public final class MpvNativeRequestGate {
    private final AtomicLong ids = new AtomicLong(1L << 40);
    private final ConcurrentHashMap<Long, MpvStreamOwner.Lease> pending = new ConcurrentHashMap<>();

    public interface Reply {
        void accept(long requestId, int error, long result);
    }

    public long reserve(MpvStreamOwner.Lease owner) {
        if (owner == null) throw new NullPointerException("owner");
        long id = ids.incrementAndGet();
        if (id <= 0) throw new IllegalStateException("request ID exhausted");
        if (!owner.publish(() -> pending.put(id, owner))) {
            throw new IllegalStateException("retired owner");
        }
        return id;
    }

    /** Invoke at the actual delivery boundary, after any queue/handler delay. */
    public boolean deliver(long id, int error, long result, Reply reply) {
        MpvStreamOwner.Lease owner = pending.remove(id);
        return owner != null && owner.publish(() -> reply.accept(id, error, result));
    }

    /** For a rejected submission, expired waiter, or destroyed native context. */
    public void forget(long id) { pending.remove(id); }
    public void clear() { pending.clear(); }
}
