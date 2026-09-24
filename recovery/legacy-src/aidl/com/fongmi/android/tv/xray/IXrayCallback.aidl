package com.fongmi.android.tv.xray;

interface IXrayCallback {
    void onResult(long operationId, int operation, boolean success, int socksPort, long latencyMs, String message);
}
