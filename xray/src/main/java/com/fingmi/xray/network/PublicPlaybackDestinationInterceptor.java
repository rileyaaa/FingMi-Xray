package com.fingmi.xray.network;

import java.io.IOException;
import java.net.InetAddress;
import java.util.Locale;

import okhttp3.HttpUrl;
import okhttp3.Interceptor;
import okhttp3.Response;

public final class PublicPlaybackDestinationInterceptor implements Interceptor {

    @Override
    public Response intercept(Chain chain) throws IOException {
        HttpUrl url = chain.request().url();
        String scheme = url.scheme();
        if (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme)) {
            throw new IOException("Xray playback only supports HTTP or HTTPS");
        }
        if (isPrivateOrReserved(url.host())) {
            throw new IOException("Private or reserved playback destination blocked");
        }
        return chain.proceed(chain.request());
    }

    static boolean isPrivateOrReserved(String host) {
        if (host == null || host.isBlank()) return true;

        String normalized = host.toLowerCase(Locale.ROOT);
        if ("localhost".equals(normalized)
                || normalized.endsWith(".localhost")
                || normalized.endsWith(".local")) {
            return true;
        }

        // Do not resolve ordinary hostnames here. Xray must receive the original
        // public hostname and perform the remote resolution.
        if (!looksLikeIpLiteral(normalized)) return false;

        try {
            InetAddress address = InetAddress.getByName(stripIpv6Brackets(normalized));
            return address.isAnyLocalAddress()
                    || address.isLoopbackAddress()
                    || address.isLinkLocalAddress()
                    || address.isSiteLocalAddress()
                    || address.isMulticastAddress()
                    || isDocumentationOrReserved(address.getAddress());
        } catch (Exception ignored) {
            return true;
        }
    }

    private static boolean looksLikeIpLiteral(String host) {
        if (host.indexOf(':') >= 0) return true;
        for (int i = 0; i < host.length(); i++) {
            char c = host.charAt(i);
            if ((c < '0' || c > '9') && c != '.') return false;
        }
        return true;
    }

    private static String stripIpv6Brackets(String host) {
        return host.startsWith("[") && host.endsWith("]")
                ? host.substring(1, host.length() - 1)
                : host;
    }

    private static boolean isDocumentationOrReserved(byte[] address) {
        if (address.length == 4) {
            int a = address[0] & 0xff;
            int b = address[1] & 0xff;
            int c = address[2] & 0xff;

            if (a == 0 || a >= 224) return true;
            if (a == 100 && b >= 64 && b <= 127) return true;
            if (a == 192 && b == 0 && (c == 0 || c == 2)) return true;
            if (a == 192 && b == 88 && c == 99) return true;
            if (a == 198 && (b == 18 || b == 19)) return true;
            if (a == 198 && b == 51 && c == 100) return true;
            return a == 203 && b == 0 && c == 113;
        }

        if (address.length == 16) {
            int a = address[0] & 0xff;
            int b = address[1] & 0xff;

            // Unspecified/loopback and IPv4-mapped/translated addresses are
            // already covered by InetAddress in common Android runtimes, but
            // keep the major reserved ranges explicit.
            if ((a & 0xfe) == 0xfc) return true;       // fc00::/7
            if (a == 0xfe && (b & 0xc0) == 0x80) return true; // fe80::/10
            if (a == 0x20 && b == 0x01
                    && (address[2] & 0xff) == 0x0d
                    && (address[3] & 0xff) == 0xb8) return true; // 2001:db8::/32
            return a == 0xff;
        }

        return true;
    }
}
