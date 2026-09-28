package com.fongmi.android.tv.network;

/** Rebuilds the ordinary app/catvod network once per foreground generation. */
public final class NetworkRecoveryCoordinator implements AutoCloseable {
    public interface Hooks {
        long generation();
        void cancelRequests();
        void resetApiAndDns();
        void clearSpiders(Runnable after);
        boolean networkReady();
        void schedule(Runnable action, long delayMillis);
        void unschedule(Runnable action);
        void showProgress();
        void refreshHome();
    }

    private final Hooks hooks;
    private final Runnable poll = this::checkStability;
    private long appliedGeneration;
    private long pendingGeneration;
    private int checks;
    private int stableChecks;
    private boolean recovering;
    private boolean closed;

    public NetworkRecoveryCoordinator(long initialGeneration, Hooks hooks) {
        this.appliedGeneration = initialGeneration;
        this.hooks = hooks;
    }

    public void check() {
        if (closed) return;
        long next = hooks.generation();
        // Released HomeActivity serializes recovery. A newer generation is
        // picked up only after the in-flight spider clear / stability poll
        // observes it; never run two loader clears concurrently.
        if (recovering) return;
        if (next == appliedGeneration) return;
        pendingGeneration = next;
        recovering = true;
        checks = 0;
        stableChecks = 0;
        hooks.unschedule(poll);
        hooks.showProgress();
        hooks.cancelRequests();
        hooks.resetApiAndDns();
        hooks.clearSpiders(() -> {
            if (closed || !recovering || pendingGeneration != next) return;
            if (hooks.generation() != next) {
                recovering = false;
                check();
                return;
            }
            hooks.schedule(poll, 0);
        });
    }

    private void checkStability() {
        if (closed || !recovering) return;
        if (hooks.generation() != pendingGeneration) {
            recovering = false;
            check();
            return;
        }
        stableChecks = hooks.networkReady() ? stableChecks + 1 : 0;
        if (stableChecks < 2 && checks < 12) {
            checks++;
            hooks.schedule(poll, 500L);
            return;
        }
        appliedGeneration = pendingGeneration;
        recovering = false;
        if (hooks.generation() == appliedGeneration) hooks.refreshHome();
        check();
    }

    public long appliedGeneration() { return appliedGeneration; }
    public boolean recovering() { return recovering; }

    @Override public void close() {
        closed = true;
        recovering = false;
        hooks.unschedule(poll);
    }
}
