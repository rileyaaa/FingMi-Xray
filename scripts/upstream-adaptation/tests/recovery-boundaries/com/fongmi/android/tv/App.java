package com.fongmi.android.tv;
import android.os.Handler;
import android.os.Looper;
public final class App {
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    public static void post(Runnable action,long delay){MAIN.postDelayed(action,delay);}
    public static void removeCallbacks(Runnable action){MAIN.removeCallbacks(action);}
}
