package com.fongmi.android.tv.xray.legacy;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Exact generation gate recovered from e63(mode=5) + iz3.
 */
public final class LegacyXrayGenerationGate {

    private final AtomicLong current =
            new AtomicLong(Long.MIN_VALUE);

    public void begin(long operationId) {
        current.accumulateAndGet(operationId, Math::max);
    }

    public boolean isCurrent(long operationId) {
        return current.get() == operationId;
    }

    public boolean cancelCurrent(long operationId) {
        return current.compareAndSet(operationId, Long.MAX_VALUE);
    }

    public void invalidateAll() {
        current.set(Long.MAX_VALUE);
    }
}
