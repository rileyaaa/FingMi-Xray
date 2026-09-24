package com.fingmi.xray.session;

final class XrayResult {

    final long operationId;
    final int operation;
    final boolean success;
    final int socksPort;
    final long latencyMs;
    final String message;

    XrayResult(
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
        this.message = message == null ? "" : message;
    }
}
