package com.fingmi.xray.service;

import com.fingmi.xray.service.IXrayCallback;

interface IXrayService {
    void validate(long operationId, String shareLink, boolean udp, IXrayCallback callback);
    void test(long operationId, String shareLink, boolean udp, IXrayCallback callback);
    void start(long operationId, String shareLink, boolean udp, IXrayCallback callback);
    void stop(long operationId, IXrayCallback callback);
    void resetSecurity(long operationId, IXrayCallback callback);
    void cancel(int operation, long operationId);
}
