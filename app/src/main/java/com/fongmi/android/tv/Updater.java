package com.fongmi.android.tv;

import androidx.fragment.app.FragmentActivity;

/**
 * Upstream self-update is intentionally disabled in this fork.
 *
 * Keeping the tiny API surface as a no-op prevents an upstream call site from
 * downloading and installing FongMi/Release over the Xray-enabled build.
 */
public final class Updater {

    private Updater() {
    }

    public static Updater create() {
        return new Updater();
    }

    public Updater force() {
        return this;
    }

    public void start(FragmentActivity activity) {
        // Intentionally disabled. Releases are installed explicitly by the user.
    }
}
