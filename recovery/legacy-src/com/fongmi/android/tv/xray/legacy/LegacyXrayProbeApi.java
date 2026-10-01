package com.fongmi.android.tv.xray.legacy;

import java.util.List;

/**
 * Readable boundary for the libXray probe calls recovered from the APK.
 */
public interface LegacyXrayProbeApi {

    String probeHysteria2Certificate(
            String server,
            int port,
            String serverName,
            int timeoutMs) throws Exception;

    String probeTlsCertificate(
            String server,
            int port,
            String serverName,
            String fingerprint,
            List<String> alpn,
            int timeoutMs) throws Exception;
}
