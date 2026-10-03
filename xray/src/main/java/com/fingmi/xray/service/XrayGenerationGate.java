package com.fingmi.xray.service;

import java.util.concurrent.atomic.AtomicLong;

final class XrayGenerationGate {

    interface ThrowingAction {
        void run() throws Exception;
    }

    private final AtomicLong current = new AtomicLong(Long.MIN_VALUE);

    synchronized void begin(long operationId) {
        current.accumulateAndGet(operationId, Math::max);
    }

    boolean isCurrent(long operationId) {
        return current.get() == operationId;
    }

    synchronized boolean cancel(long operationId) {
        return current.compareAndSet(operationId, Long.MAX_VALUE);
    }

    synchronized void invalidateAll() {
        current.set(Long.MAX_VALUE);
    }

    synchronized boolean runIfCurrent(long operationId, ThrowingAction action)
            throws Exception {
        if (current.get() != operationId) return false;
        action.run();
        return current.get() == operationId;
    }
}
