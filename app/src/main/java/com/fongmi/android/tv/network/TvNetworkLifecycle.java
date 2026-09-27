package com.fongmi.android.tv.network;

import android.app.Activity;
import android.app.Application;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.net.ConnectivityManager;
import android.net.Network;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * Behavior reconstruction of the shipped TV foreground/network generation
 * monitor (R8 name: gn3).
 *
 * A generation advances only when the app returns from a real background /
 * screen-off interval. HomeActivity uses it to decide whether stale sockets,
 * DNS/DoH state and spider runtimes must be rebuilt.
 */
public final class TvNetworkLifecycle
        implements Application.ActivityLifecycleCallbacks {

    private static volatile TvNetworkLifecycle instance;

    private final Application application;
    private final BroadcastReceiver screenReceiver;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Set<Runnable> listeners = new CopyOnWriteArraySet<>();
    private Network activeNetwork;
    private boolean networkWasLost;

    private int startedActivities;
    private long generation;
    private long recoveredGeneration;
    private boolean backgroundPending;
    private boolean dlnaStarted;

    private TvNetworkLifecycle(Application application) {
        this.application = application;
        this.screenReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (intent == null) return;
                String action = intent.getAction();
                if (Intent.ACTION_SCREEN_OFF.equals(action)) {
                    markBackground();
                } else if (Intent.ACTION_SCREEN_ON.equals(action)) {
                    boolean hasStartedActivities;
                    synchronized (TvNetworkLifecycle.this) {
                        hasStartedActivities = startedActivities > 0;
                    }
                    if (hasStartedActivities) enterForegroundGeneration();
                }
            }
        };

        application.registerActivityLifecycleCallbacks(this);
        IntentFilter filter = new IntentFilter();
        filter.addAction(Intent.ACTION_SCREEN_OFF);
        filter.addAction(Intent.ACTION_SCREEN_ON);
        application.registerReceiver(screenReceiver, filter);
        try {
            ConnectivityManager connectivity = (ConnectivityManager) application.getSystemService(Context.CONNECTIVITY_SERVICE);
            if (connectivity != null) {
                activeNetwork = connectivity.getActiveNetwork();
                connectivity.registerDefaultNetworkCallback(new ConnectivityManager.NetworkCallback() {
                    @Override public void onAvailable(Network network) { networkAvailable(network); }
                    @Override public void onLost(Network network) { networkLost(network); }
                });
            }
        } catch (RuntimeException ignored) {
            // Lifecycle and screen events still detect a later foreground generation.
        }
    }

    public static TvNetworkLifecycle get(Application application) {
        TvNetworkLifecycle current = instance;
        if (current != null) return current;

        synchronized (TvNetworkLifecycle.class) {
            current = instance;
            if (current == null) {
                current = new TvNetworkLifecycle(application);
                instance = current;
            }
            return current;
        }
    }

    public static long generation() {
        TvNetworkLifecycle current = instance;
        if (current == null) return 0L;
        synchronized (current) {
            return current.generation;
        }
    }

    public static long recoveredGeneration() {
        TvNetworkLifecycle current = instance;
        if (current == null) return 0L;
        synchronized (current) { return current.recoveredGeneration; }
    }

    public static void markRecovered(long generation) {
        TvNetworkLifecycle current = instance;
        if (current == null) return;
        synchronized (current) {
            if (current.generation == generation) current.recoveredGeneration = generation;
        }
    }

    public void addListener(Runnable listener) { listeners.add(listener); }
    public void removeListener(Runnable listener) { listeners.remove(listener); }

    private void networkAvailable(Network network) {
        boolean changed;
        synchronized (this) {
            changed = networkWasLost || (activeNetwork != null && !Objects.equals(activeNetwork, network));
            activeNetwork = network;
            networkWasLost = false;
            if (changed) invalidateNetworkLocked();
        }
        if (changed) notifyListeners();
    }

    private void networkLost(Network network) {
        boolean changed;
        synchronized (this) {
            changed = Objects.equals(activeNetwork, network);
            if (changed) {
                activeNetwork = null;
                networkWasLost = true;
                invalidateNetworkLocked();
            }
        }
        if (changed) notifyListeners();
    }

    private void invalidateNetworkLocked() {
        if (startedActivities > 0) generation++;
        else backgroundPending = true;
    }

    private void notifyListeners() {
        for (Runnable listener : listeners) main.post(listener);
    }

    private void markBackground() {
        boolean stopDlna = false;
        synchronized (this) {
            backgroundPending = true;
            if (dlnaStarted) {
                dlnaStarted = false;
                stopDlna = true;
            }
        }

        if (stopDlna) {
            try {
                TvDlnaLifecycle.stop(application);
            } catch (RuntimeException ignored) {
            }
        }
    }

    private void enterForegroundGeneration() {
        boolean advanced;
        synchronized (this) {
            advanced = backgroundPending;
            if (advanced) {
                backgroundPending = false;
                generation++;
            }
        }
        if (advanced) notifyListeners();
    }

    @Override
    public void onActivityResumed(@NonNull Activity activity) {
        boolean startDlna;
        synchronized (this) {
            startDlna = !dlnaStarted;
            if (startDlna) dlnaStarted = true;
        }

        if (!startDlna) return;

        try {
            TvDlnaLifecycle.start(application);
        } catch (RuntimeException ignored) {
            synchronized (this) {
                dlnaStarted = false;
            }
        }
    }

    @Override
    public void onActivityStarted(@NonNull Activity activity) {
        boolean firstStarted;
        synchronized (this) {
            startedActivities++;
            firstStarted = startedActivities == 1;
        }
        if (firstStarted) enterForegroundGeneration();
    }

    @Override
    public void onActivityStopped(@NonNull Activity activity) {
        boolean noStartedActivities;
        synchronized (this) {
            startedActivities = Math.max(0, startedActivities - 1);
            noStartedActivities = startedActivities == 0;
        }

        if (noStartedActivities && !activity.isChangingConfigurations()) {
            markBackground();
        }
    }

    @Override
    public void onActivityCreated(
            @NonNull Activity activity,
            @Nullable Bundle savedInstanceState) {
    }

    @Override
    public void onActivityPaused(@NonNull Activity activity) {
    }

    @Override
    public void onActivitySaveInstanceState(
            @NonNull Activity activity,
            @NonNull Bundle outState) {
    }

    @Override
    public void onActivityDestroyed(@NonNull Activity activity) {
    }
}
