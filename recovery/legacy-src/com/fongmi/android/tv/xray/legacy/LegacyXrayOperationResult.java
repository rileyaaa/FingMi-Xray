package com.fongmi.android.tv.xray.legacy;

/**
 * Recovered callback payload (R8 value class: rz3).
 */
public final class LegacyXrayOperationResult {

    public final long operationId;
    public final int operation;
    public final boolean success;
    public final int socksPort;
    public final long latencyMs;
    public final String message;

    public LegacyXrayOperationResult(
            long operationId,
            int operation,
            boolean success,
            int socksPort,
            long latencyMs,
            String message) {
        this.operationId = operationId;
        this.operation = operation;
        this.success = success;
        this.socksPort = socksPort;
        this.latencyMs = latencyMs;
        this.message = message;
    }
}
