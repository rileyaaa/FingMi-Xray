package com.fingmi.xray.config;
import android.content.Context;
/** Test-only configured input; production persistence is outside these race tests. */
public final class XrayPreferences {
    public XrayPreferences(Context context) {}
    public String getShareLink() { return "trojan://synthetic@example.invalid:443"; }
    public boolean isUdpEnabled() { return false; }
}
