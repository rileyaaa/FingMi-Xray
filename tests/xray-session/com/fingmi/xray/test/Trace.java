package com.fingmi.xray.test;
import java.util.*;
public final class Trace {
    private static final List<String> EVENTS = new ArrayList<>();
    private Trace() {}
    public static void add(String value) { EVENTS.add(value); }
    public static void reset() { EVENTS.clear(); }
    public static List<String> events() { return List.copyOf(EVENTS); }
    public static int indexOf(String value) { return EVENTS.indexOf(value); }
}
