package com.fongmi.android.tv.xray.legacy;
import java.util.*;
/** Test-only memory store. Does not test Android Keystore or persistence. */
public final class LegacyXrayCertificateStore {
    private final Map<String,String> pins = new HashMap<>();
    public String get(String key) {return pins.getOrDefault(key, "");}
    public void put(String key,String pin) {pins.put(key,pin);}
}
