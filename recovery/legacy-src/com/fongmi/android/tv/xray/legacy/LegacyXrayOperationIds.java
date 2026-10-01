package com.fongmi.android.tv.xray.legacy;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Recovered from the shipped operation-id holder (R8 name: lz3).
 */
public final class LegacyXrayOperationIds {

    private static final AtomicLong NEXT = new AtomicLong(System.nanoTime());

    private LegacyXrayOperationIds() {
    }

    public static long next() {
        return NEXT.incrementAndGet();
    }
}
