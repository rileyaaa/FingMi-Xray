#!/usr/bin/env python3
"""Differential JVM parity for current vs released Xray playback address policy."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "xray/src/main/java/com/fingmi/xray/session/XrayPlaybackAddress.java"
LEGACY = ROOT / "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayPlaybackAddress.java"

CURRENT_GUARD = r"""
package com.fingmi.xray.network;
public final class PublicPlaybackDestinationInterceptor {
    private PublicPlaybackDestinationInterceptor() {}
    public static boolean isPrivateOrReserved(String host) {
        return PlaybackAddressGuard.isPrivateOrReserved(host);
    }
}
"""

LEGACY_GUARD = r"""
package com.fongmi.android.tv.xray.legacy;
public final class LegacyPublicPlaybackDestinationInterceptor {
    private LegacyPublicPlaybackDestinationInterceptor() {}
    public static boolean isPrivateOrReserved(String host) {
        return com.fingmi.xray.network.PlaybackAddressGuard.isPrivateOrReserved(host);
    }
}
"""

SHARED_GUARD = r"""
package com.fingmi.xray.network;
import java.util.Locale;
public final class PlaybackAddressGuard {
    private PlaybackAddressGuard() {}
    public static boolean isPrivateOrReserved(String host) {
        if (host == null || host.isEmpty()) return true;
        String value = host.toLowerCase(Locale.ROOT);
        if ("localhost".equals(value)
                || value.endsWith(".localhost")
                || value.endsWith(".local")) return true;
        return value.startsWith("10.")
                || value.startsWith("127.")
                || value.startsWith("192.168.")
                || value.equals("::1")
                || value.startsWith("fc")
                || value.startsWith("fd")
                || value.startsWith("fe80:");
    }
}
"""

HARNESS = r"""
package com.fingmi.xray.session;

import com.fongmi.android.tv.xray.legacy.LegacyXrayPlaybackAddress;

import java.util.List;

public final class PlaybackAddressParityTest {

    private static void same(String value) {
        boolean oldValue = LegacyXrayPlaybackAddress.isSupportedPublicAddress(value);
        boolean current = XrayPlaybackAddress.supports(value);
        if (oldValue != current) {
            throw new AssertionError(
                    "supports mismatch: " + value + " old=" + oldValue + " current=" + current);
        }

        boolean oldLive = LegacyXrayPlaybackAddress.isDirectLiveSourceSupported(value);
        boolean currentLive = XrayPlaybackAddress.supportsDirectLiveSource(value);
        if (oldLive != currentLive) {
            throw new AssertionError(
                    "live mismatch: " + value + " old=" + oldLive + " current=" + currentLive);
        }
    }

    public static void main(String[] args) {
        List<String> values = java.util.Arrays.asList(
                null,
                "",
                "   ",
                " https://media.example/video.m3u8 ",
                "HTTP://media.example:8080/video",
                "rtsp://media.example/live",
                "rtspt://media.example/live",
                "ftp://media.example/file",
                "relative/path",
                "https://localhost/video",
                "https://10.0.0.1/video",
                "https://192.168.1.2/video",
                "https://[::1]/video",
                "https://[2001:4860:4860::8888]/video",
                "https://media.example/path/video.strm",
                "https://media.example/path/VIDEO.STRM",
                "https://youtube.com/watch?v=x",
                "https://www.youtube.com/watch?v=x",
                "https://youtu.be/x",
                "rtsp://youtube.com/live",
                "https://media.example/a b",
                "%%%invalid-uri%%%",
                "https://user:pass@media.example:443/video",
                "https://media.example./video",
                "https://xn--fsqu00a.xn--0zwm56d/video");

        for (String value : values) same(value);
        System.out.println("PASS released playback-address parity: " + values.size());
    }
}
"""

with tempfile.TemporaryDirectory(prefix="xray-playback-address-") as directory:
    work = Path(directory)

    files = {
        "com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java": CURRENT_GUARD,
        "com/fongmi/android/tv/xray/legacy/LegacyPublicPlaybackDestinationInterceptor.java": LEGACY_GUARD,
        "com/fingmi/xray/network/PlaybackAddressGuard.java": SHARED_GUARD,
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
