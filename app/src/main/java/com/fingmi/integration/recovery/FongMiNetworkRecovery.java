package com.fingmi.integration.recovery;

import android.app.Application;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;

import com.fingmi.tvrecovery.NetworkRecoveryCoordinator;
import com.fingmi.tvrecovery.TvNetworkLifecycle;
import com.fongmi.android.tv.App;
import com.fongmi.android.tv.api.loader.BaseLoader;
import com.fongmi.android.tv.utils.ImgUtil;
import com.github.catvod.net.OkHttp;

import java.util.function.BooleanSupplier;

/** The app-owned adapter between the independent recovery core and FongMi resources. */
public final class FongMiNetworkRecovery implements AutoCloseable {

    private final NetworkRecoveryCoordinator coordinator;

    public FongMiNetworkRecovery(
            Application application,
            Runnable cancelRequests,
            Runnable showProgress,
            BooleanSupplier ownerAlive,
            Runnable refreshHome) {
        TvNetworkLifecycle.get(application, new TvNetworkLifecycle.Renderer() {
            @Override public void start() { TvDlnaLifecycle.start(application); }
            @Override public void stop() { TvDlnaLifecycle.stop(application); }
        });
        coordinator = new NetworkRecoveryCoordinator(
                TvNetworkLifecycle.recoveredGeneration(),
                new NetworkRecoveryCoordinator.Hooks() {
                    @Override public long generation() { return TvNetworkLifecycle.generation(); }
                    @Override public void cancelRequests() { cancelRequests.run(); }
                    @Override public void resetApiAndDns() {
                        OkHttp.resetApiNetworkForResume();
                        ImgUtil.resetNetworkFailures();
                    }
                    @Override public void clearSpiders(Runnable after) { BaseLoader.get().clear(after); }
                    @Override public boolean networkReady() { return hasInternetCapability(application); }
                    @Override public void schedule(Runnable action, long delay) { App.post(action, delay); }
                    @Override public void unschedule(Runnable action) { App.removeCallbacks(action); }
                    @Override public void showProgress() { showProgress.run(); }
                    @Override public void refreshHome() {
                        if (!ownerAlive.getAsBoolean()) return;
                        TvNetworkLifecycle.markRecovered(TvNetworkLifecycle.generation());
                        refreshHome.run();
                    }
                });
    }

    private static boolean hasInternetCapability(Context context) {
        try {
            ConnectivityManager connectivity =
                    (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
            if (connectivity == null) return false;
            Network network = connectivity.getActiveNetwork();
            if (network == null) return false;
            NetworkCapabilities capabilities = connectivity.getNetworkCapabilities(network);
            return capabilities != null
                    && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
        } catch (RuntimeException ignored) {
            return false;
        }
    }

    public void check() { coordinator.check(); }

    @Override public void close() { coordinator.close(); }
}
