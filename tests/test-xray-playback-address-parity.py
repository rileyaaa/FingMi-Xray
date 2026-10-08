#!/usr/bin/env python3
"""Exercise real current/released address guards and documented IPv6 repairs."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "xray/src/main/java/com/fingmi/xray/session/XrayPlaybackAddress.java"
LEGACY = ROOT / "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayPlaybackAddress.java"
CURRENT_GUARD = ROOT / "xray/src/main/java/com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java"
LEGACY_GUARD = ROOT / "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyPublicPlaybackDestinationInterceptor.java"

# Only the unused HTTP interceptor boundary is stubbed. The address parsing and
# reserved-range checks below compile the real classes, including the legacy
# oracle. Replacing those checks with a shared simplified stub hid the URI
# bracket/IPv6 integration defect even though the old parity suite passed.
HTTP_STUBS = {
    "okhttp3/HttpUrl.java": "package okhttp3; public class HttpUrl { public String scheme(){return \"http\";} public boolean isHttps(){return false;} public String host(){return \"example.com\";} }",
    "okhttp3/Request.java": "package okhttp3; public class Request { public HttpUrl url(){return new HttpUrl();} }",
    "okhttp3/Response.java": "package okhttp3; public class Response {}",
    "okhttp3/Interceptor.java": "package okhttp3; import java.io.IOException; public interface Interceptor { Response intercept(Chain c) throws IOException; interface Chain { Request request(); Response proceed(Request r) throws IOException; } }",
}

HARNESS = r"""
package com.fingmi.xray.session;

import com.fongmi.android.tv.xray.legacy.LegacyXrayPlaybackAddress;
import com.fingmi.xray.network.PublicPlaybackDestinationInterceptor;
import java.net.URI;

public final class PlaybackAddressParityTest {
    private static int checks;

    private static void check(String value, boolean supported, boolean directLive,
                              boolean repairedIpv6) {
        boolean oldValue = LegacyXrayPlaybackAddress.isSupportedPublicAddress(value);
        boolean current = XrayPlaybackAddress.supports(value);
        if (current != supported || oldValue != (repairedIpv6 ? false : supported)) {
            throw new AssertionError(
                    "supports: " + value + " expected=" + supported
                            + " old=" + oldValue + " current=" + current);
        }

        boolean oldLive = LegacyXrayPlaybackAddress.isDirectLiveSourceSupported(value);
        boolean currentLive = XrayPlaybackAddress.supportsDirectLiveSource(value);
        if (currentLive != directLive || oldLive != (repairedIpv6 ? false : directLive)) {
            throw new AssertionError(
                    "live: " + value + " expected=" + directLive
                            + " old=" + oldLive + " current=" + currentLive);
        }
        checks++;
    }

    public static void main(String[] args) {
        for (String value : new String[] {
                null,
                "",
                "   ",
                "\u2003\u2003",
                "ftp://media.example/file",
                "relative/path",
                "https://localhost/video",
                "https://media.localhost/video",
                "https://media.local/video",
                "https://10.0.0.1/video",
                "https://192.168.1.2/video",
                "https://100.64.0.1/video",
                "https://192.0.2.1/video",
                "https://203.0.113.1/video",
                "https://224.0.0.1/video",
                "https://[2001:::1]/video",
                "https://2001:4860:4860::8888/video",
                "https://media.example/a b",
                "%%%invalid-uri%%%"}) {
            check(value, false, false, false);
        }
        for (String value : new String[] {
                " https://media.example/video.m3u8 ",
                "HTTP://media.example:8080/video",
                "https://1.1.1.1/video",
                "rtsp://media.example/live",
                "rtspt://media.example/live",
                "rtsp://youtube.com/live",
                "https://fc.example/video",
                "https://fd.example/video",
                "https://user:pass@media.example:443/video",
                "https://media.example./video",
                "https://xn--fsqu00a.xn--0zwm56d/video"}) {
            check(value, true, true, false);
        }
        for (String value : new String[] {
                "https://media.example/path/video.strm",
                "https://media.example/path/VIDEO.STRM",
                "https://youtube.com/watch?v=x",
                "https://www.youtube.com/watch?v=x",
                "https://youtu.be/x"}) {
            check(value, true, false, false);
        }

        for (String scheme : new String[] {"http", "https", "rtsp", "rtspt"}) {
            for (String host : new String[] {
                    "2606:4700:4700::1111", "2001:4860:4860::8888",
                    "2606:4700:4700:0:0:0:0:1111"}) {
                String value = scheme + "://[" + host + "]:443/video";
                // java.net.URI preserves brackets; OkHttp's host() does not.
                // The published guard expects a bare host, so only the current
                // URI-to-guard adapter intentionally differs from the oracle.
                if (!URI.create(value).getHost().equals("[" + host + "]")
                        || PublicPlaybackDestinationInterceptor.isPrivateOrReserved(host)) {
                    throw new AssertionError("invalid public IPv6 test boundary: " + value);
                }
                check(value, true, true, true);
                check(scheme + "://user:pass@[" + host + "]:443/video", true, true, true);
                boolean directLive = scheme.equals("rtsp") || scheme.equals("rtspt");
                check(scheme + "://[" + host + "]/video.strm", true, directLive, true);
            }
            for (String host : new String[] {
                    "::", "::1", "fc00::1", "fd00::1", "fe80::1", "ff02::1",
                    "2001:db8::1", "::ffff:127.0.0.1", "::ffff:8.8.8.8",
                    "64:ff9b:1::1", "100::1", "2001:2::1", "3fff::1", "5f00::1",
                    "fe80::1%25eth0", "2606:4700:4700::1111%25eth0"}) {
                check(scheme + "://[" + host + "]/video", false, false, false);
            }
        }
        System.out.println("PASS real playback-address guards: " + checks
                + " cases, including documented public IPv6 repair");
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-playback-address-") as directory:
    work = Path(directory)

    files = {
        **HTTP_STUBS,
        "com/fingmi/xray/session/PlaybackAddressParityTest.java": HARNESS,
    }
    generated = []
    for relative, content in files.items():
        path = work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n")
        generated.append(path)

    classes = work / "classes"
    subprocess.run(
        [
            "java",
            "com.sun.tools.javac.Main",
            "--release",
            "17",
            "-d",
            str(classes),
            str(CURRENT),
            str(LEGACY),
            str(CURRENT_GUARD),
            str(LEGACY_GUARD),
            *map(str, generated),
        ],
        check=True,
    )
    subprocess.run(
        [
            "java",
            "-cp",
            str(classes),
            "com.fingmi.xray.session.PlaybackAddressParityTest",
        ],
        check=True,
    )
