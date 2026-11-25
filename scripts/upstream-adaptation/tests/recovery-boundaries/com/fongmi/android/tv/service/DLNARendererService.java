package com.fongmi.android.tv.service;
import android.content.Context;
public final class DLNARendererService {
    public static int starts,stops;
    public static void start(Context context){starts++;}
    public static void stop(Context context){stops++;}
}
