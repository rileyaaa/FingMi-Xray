package com.fingmi.xray.network;

import java.io.IOException;
import java.util.Arrays;
import java.util.Locale;

import okhttp3.HttpUrl;
import okhttp3.Interceptor;
import okhttp3.Response;

/**
 * Port of the verified published playback destination check.
 *
 * Normal hostnames are not DNS-resolved here. Numeric-looking IPv4 and IPv6
 * literals are parsed locally and private/reserved destinations are blocked.
 */
public final class PublicPlaybackDestinationInterceptor
        implements Interceptor {

    @Override
    public Response intercept(Chain chain) throws IOException {
        HttpUrl url = chain.request().url();

        if (!url.isHttps() && !"http".equals(url.scheme())) {
            throw new IOException(
                    "Xray playback only supports HTTP or HTTPS");
        }

        if (isPrivateOrReserved(url.host())) {
            throw new IOException(
                    "Private or reserved playback destination blocked");
        }

        return chain.proceed(chain.request());
    }

    public static boolean isPrivateOrReserved(String host) {
        if (isBlank(host)) return true;

        String value = host.toLowerCase(Locale.ROOT);
        // The absolute DNS root dot does not change a hostname's destination:
        // localhost. and camera.local. must obey the same deny policy as
        // localhost and camera.local. Inspect only; never rewrite the URL.
        while (value.endsWith(".")) {
            value = value.substring(0, value.length() - 1);
        }
        if (value.isEmpty()) return true;
        if ("localhost".equals(value)
                || value.endsWith(".localhost")
                || value.endsWith(".local")) {
            return true;
        }

        if (value.indexOf(':') < 0) {
            if (!looksNumericIpv4(value)) {
                return false;
            }

            byte[] address = parseIpv4(value);
            if (address == null) return true;

            int a = address[0] & 0xff;
            int b = address[1] & 0xff;
            int c = address[2] & 0xff;
            int d = address[3] & 0xff;

            if (a == 0 || a == 10 || a == 127 || a >= 224) {
                return true;
            }
            if (a == 100 && b >= 64 && b <= 127) return true;
            if (a == 169 && b == 254) return true;
            if (a == 172 && b >= 16 && b <= 31) return true;
            if (a == 192 && b == 168) return true;
            if (a == 192 && b == 0 && (c == 0 || c == 2)) return true;
            if (a == 192 && b == 88 && c == 99 && d == 2) return true;
            if (a == 198 && (b == 18 || b == 19)) return true;
            if (a == 198 && b == 51 && c == 100) return true;
            return a == 203 && b == 0 && c == 113;
        }

        byte[] address = parseIpv6(value);
        if (address == null) return true;

        int a = address[0] & 0xff;
        int b = address[1] & 0xff;

        if (allZero(address, 0, 12)) return true; // ::/96

        if (allZero(address, 0, 10)
                && (address[10] & 0xff) == 0xff
                && (address[11] & 0xff) == 0xff) {
            return true; // ::ffff:0:0/96
        }

        if (allZero(address, 0, 8)
                && (address[8] & 0xff) == 0xff
                && (address[9] & 0xff) == 0xff
                && address[10] == 0
                && address[11] == 0) {
            return true;
        }

        if (a == 0x00
                && b == 0x64
                && (address[2] & 0xff) == 0xff
                && (address[3] & 0xff) == 0x9b
                && address[4] == 0
                && (address[5] & 0xff) == 0x01) {
            return true; // 64:ff9b:1::/48
        }

        if (a == 0x01
                && b == 0x00
                && allZero(address, 2, 8)) {
            return true; // 100::/64
        }

        if (a == 0x01
                && b == 0x00
                && allZero(address, 2, 7)
                && (address[7] & 0xff) == 0x01) {
            return true; // 100:0:0:1::/64
        }

        if (a == 0x20
                && b == 0x01
                && address[2] == 0
                && (address[3] & 0xff) == 0x02
                && address[4] == 0
                && address[5] == 0) {
            return true; // 2001:2::/48
        }

        if (a == 0x20
                && b == 0x01
                && (address[2] & 0xff) == 0x0d
                && (address[3] & 0xff) == 0xb8) {
            return true; // 2001:db8::/32
        }

        if (a == 0x3f
                && b == 0xff
                && (address[2] & 0xf0) == 0) {
            return true; // 3fff::/20
        }

        if (a == 0x5f && b == 0x00) return true; // 5f00::/16
        if ((address[0] & 0xfe) == 0xfc) return true; // fc00::/7
        if (a == 0xfe) return true; // shipped code blocks fe00::/8
        return a == 0xff; // ff00::/8
    }

    private static boolean looksNumericIpv4(String value) {
        if (value.isEmpty()) return false;
        for (int index = 0; index < value.length(); index++) {
            char c = value.charAt(index);
            if (c != '.' && (c < '0' || c > '9')) return false;
        }
        return true;
    }

    private static byte[] parseIpv4(String value) {
        String[] parts = value.split("\\.", -1);
        if (parts.length != 4) return null;

        byte[] result = new byte[4];
        for (int index = 0; index < parts.length; index++) {
            String part = parts[index];
            if (part.isEmpty() || part.length() > 3) return null;

            int number = 0;
            for (int offset = 0; offset < part.length(); offset++) {
                char c = part.charAt(offset);
                if (c < '0' || c > '9') return null;
                number = number * 10 + (c - '0');
            }

            if (number > 255) return null;
            result[index] = (byte) number;
        }
        return result;
    }

    private static byte[] parseIpv6(String value) {
        if (value.isEmpty() || value.indexOf('%') >= 0) return null;

        int compression = value.indexOf("::");
        if (compression >= 0
                && value.indexOf("::", compression + 2) >= 0) {
            return null;
        }

        String left =
                compression < 0
                        ? value
                        : value.substring(0, compression);
        String right =
                compression < 0
                        ? ""
                        : value.substring(compression + 2);

        int[] leftWords =
                parseIpv6Words(left, compression < 0);
        int[] rightWords =
                compression < 0
                        ? new int[0]
                        : parseIpv6Words(right, true);

        if (leftWords == null || rightWords == null) return null;

        int wordCount = leftWords.length + rightWords.length;
        if (compression < 0 && wordCount != 8) return null;
        if (compression >= 0 && wordCount >= 8) return null;

        int[] words = new int[8];
        System.arraycopy(
                leftWords,
                0,
                words,
                0,
                leftWords.length);
        System.arraycopy(
                rightWords,
                0,
                words,
                8 - rightWords.length,
                rightWords.length);

        byte[] result = new byte[16];
        for (int index = 0; index < words.length; index++) {
            result[index * 2] =
                    (byte) (words[index] >>> 8);
            result[index * 2 + 1] =
                    (byte) words[index];
        }
        return result;
    }

    private static int[] parseIpv6Words(
            String value,
            boolean allowIpv4AtEnd) {
        if (value.isEmpty()) return new int[0];

        String[] parts = value.split(":", -1);
        int[] result = new int[parts.length + 1];
        int count = 0;

        for (int index = 0; index < parts.length; index++) {
            String part = parts[index];
            if (part.isEmpty()) return null;

            if (part.indexOf('.') >= 0) {
                if (!allowIpv4AtEnd
                        || index != parts.length - 1) {
                    return null;
                }

                byte[] ipv4 = parseIpv4(part);
                if (ipv4 == null) return null;

                result[count++] =
                        ((ipv4[0] & 0xff) << 8)
                                | (ipv4[1] & 0xff);
                result[count++] =
                        ((ipv4[2] & 0xff) << 8)
                                | (ipv4[3] & 0xff);
                continue;
            }

            if (part.length() > 4) return null;

            int word = 0;
            for (int offset = 0; offset < part.length(); offset++) {
                int digit =
                        Character.digit(
                                part.charAt(offset),
                                16);
                if (digit < 0) return null;
                word = (word << 4) | digit;
            }
            result[count++] = word;
        }

        return Arrays.copyOf(result, count);
    }

    private static boolean allZero(
            byte[] value,
            int start,
            int endExclusive) {
        for (int index = start;
                index < endExclusive;
                index++) {
            if (value[index] != 0) return false;
        }
        return true;
    }

    private static boolean isBlank(String value) {
        if (value == null) return true;

        for (int offset = 0;
                offset < value.length();) {
            int codePoint =
                    value.codePointAt(offset);
            if (!Character.isWhitespace(codePoint)) {
                return false;
            }
            offset += Character.charCount(codePoint);
        }
        return true;
    }
}
