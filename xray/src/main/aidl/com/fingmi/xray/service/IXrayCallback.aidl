package com.fingmi.xray.service;

interface IXrayCallback {
    void onResult(long operationId, int operation, boolean success, int socksPort, long latencyMs, String message);
}
