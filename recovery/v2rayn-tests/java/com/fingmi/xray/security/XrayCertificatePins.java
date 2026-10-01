package com.fingmi.xray.security;
import java.util.*;
/** Test-only memory storage; Android Keystore is not under test here. */
public final class XrayCertificatePins {
    private final Map<String,String> pins=new HashMap<>();
    public String get(String identity){return pins.getOrDefault(identity,"");}
    public void put(String identity,String pin){pins.put(identity,pin);}
}
