package com.fingmi.xray.session;

import java.util.concurrent.atomic.AtomicLong;

public final class XrayOperationIds {

    private static final AtomicLong NEXT = new AtomicLong(System.nanoTime());

    private XrayOperationIds() {
    }

    public static long next() {
        return NEXT.incrementAndGet();
    }
}
