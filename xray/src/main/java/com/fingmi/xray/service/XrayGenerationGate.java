package com.fingmi.xray.service;

import java.util.concurrent.atomic.AtomicLong;

final class XrayGenerationGate {

    private final AtomicLong current = new AtomicLong(Long.MIN_VALUE);

    void begin(long operationId) {
        current.accumulateAndGet(operationId, Math::max);
    }

    boolean isCurrent(long operationId) {
        return current.get() == operationId;
    }

    boolean cancel(long operationId) {
        return current.compareAndSet(operationId, Long.MAX_VALUE);
    }

    void invalidateAll() {
        current.set(Long.MAX_VALUE);
    }
}
