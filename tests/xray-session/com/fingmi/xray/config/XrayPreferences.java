package com.fingmi.xray.config;
import android.content.Context;
import com.fingmi.xray.test.Trace;
/** Test-only configured input; production persistence is outside these lifecycle tests. */
public final class XrayPreferences {
    public XrayPreferences(Context context) {}
    public boolean isConfigured() { return true; }
    public String getShareLink() { return "trojan://synthetic@example.invalid:443"; }
    public boolean isUdpEnabled() { return false; }
    public void save(String link, boolean udp) { Trace.add("preferences:save"); }
    public void clear() { Trace.add("preferences:clear"); }
}
