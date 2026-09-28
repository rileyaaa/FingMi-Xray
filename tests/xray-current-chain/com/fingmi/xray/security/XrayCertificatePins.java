package com.fingmi.xray.security;

import java.util.HashMap;
import java.util.Map;

/** Test-only memory pin store. Android Keystore persistence is tested elsewhere. */
public final class XrayCertificatePins {

    private final Map<String, String> pins = new HashMap<>();

    public XrayCertificatePins() {
    }

    public String get(String identity) {
        return pins.getOrDefault(identity, "");
    }

    public void put(String identity, String sha256) {
        pins.put(identity, sha256);
    }
}
