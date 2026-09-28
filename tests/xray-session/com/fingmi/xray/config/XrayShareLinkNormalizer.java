package com.fingmi.xray.config;
/** Settings lifecycle tests isolate lifecycle; production normalizer parity is tested elsewhere. */
public final class XrayShareLinkNormalizer {
    private XrayShareLinkNormalizer() {}
    public static String normalize(String value) { return value == null ? "" : value; }
}
