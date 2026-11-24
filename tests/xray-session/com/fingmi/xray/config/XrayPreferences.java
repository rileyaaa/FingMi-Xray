package com.fingmi.xray.config;
import android.content.Context;
import com.fingmi.xray.test.Trace;
/** Test-only configured input; production persistence is outside these lifecycle tests. */
public final class XrayPreferences {
    public static boolean throwShareLinkLinkage;
    public static boolean throwClearAfterRemoval;
    public static boolean configured = true;
    public static boolean udpEnabled;
    public static boolean tlsFragmentEnabled;
    public XrayPreferences(Context context) {}
    public boolean isConfigured() { return configured; }
    public String getShareLink() {
        if (throwShareLinkLinkage) throw new NoClassDefFoundError("synthetic preference linkage");
        return "trojan://synthetic@example.invalid:443";
    }
    public boolean isUdpEnabled() { return udpEnabled; }
    public boolean isTlsFragmentEnabled() { return tlsFragmentEnabled; }
    public String getLiveAutoGroups() { return ""; }
    public String getLiveAutoChannels() { return ""; }
    public void save(String link, boolean udp, boolean tlsFragment, String groups, String channels) {
        save(link, udp, tlsFragment);
    }
    public void save(String link, boolean udp) { save(link, udp, false); }
    public void save(String link, boolean udp, boolean tlsFragment) {
        udpEnabled = udp;
        tlsFragmentEnabled = tlsFragment;
        configured = true;
        Trace.add("preferences:save");
    }
    public void clear() {
        Trace.add("preferences:clear");
        configured = false;
        udpEnabled = false;
        tlsFragmentEnabled = false;
        if (throwClearAfterRemoval) throw new IllegalStateException("synthetic key deletion failure");
    }
}
