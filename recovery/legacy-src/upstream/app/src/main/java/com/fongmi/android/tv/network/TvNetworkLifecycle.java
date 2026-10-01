package com.fongmi.android.tv.network;

import android.app.Activity;
import android.app.Application;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.fongmi.android.tv.service.DLNARendererService;

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

    private int startedActivities;
    private long generation;
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
                DLNARendererService.stop(application);
            } catch (RuntimeException ignored) {
            }
        }
    }

    private void enterForegroundGeneration() {
        synchronized (this) {
            if (!backgroundPending) return;
            backgroundPending = false;
            generation++;
        }
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
            DLNARendererService.start(application);
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
