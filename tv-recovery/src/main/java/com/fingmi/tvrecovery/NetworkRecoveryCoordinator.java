package com.fingmi.tvrecovery;

/** Rebuilds the ordinary app/catvod network once per foreground generation. */
public final class NetworkRecoveryCoordinator implements AutoCloseable {
    public interface Hooks {
        long generation();
        boolean canRecoverHome();
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
    private boolean awaitingSpiderCompletion;
    private boolean waitingForHome;
    private boolean closed;

    public NetworkRecoveryCoordinator(long initialGeneration, Hooks hooks) {
        this.appliedGeneration = initialGeneration;
        this.hooks = hooks;
    }

    public void check() {
        if (closed) return;
        long next = hooks.generation();
        if (closed) return;
        // Released HomeActivity serializes recovery. A newer generation is
        // picked up only after the in-flight spider clear / stability poll
        // observes it; never run two loader clears concurrently.
        if (recovering) {
            // A completed clear may be waiting for Home to resume. Recheck
            // the current generation in the poll, without replaying a clear
            // for the same generation or consuming a hidden wake.
            if (!waitingForHome || !hooks.canRecoverHome() || closed) return;
            waitingForHome = false;
            checks = 0;
            stableChecks = 0;
            hooks.schedule(poll, 0);
            if (closed) hooks.unschedule(poll);
            return;
        }
        if (next == appliedGeneration) return;
        if (!hooks.canRecoverHome() || closed) return;
        pendingGeneration = next;
        recovering = true;
        checks = 0;
        stableChecks = 0;
        hooks.unschedule(poll);
        if (closed) return;
        hooks.showProgress();
        if (closed) return;
        hooks.cancelRequests();
        if (closed) return;
        hooks.resetApiAndDns();
        if (closed) return;
        awaitingSpiderCompletion = true;
        hooks.clearSpiders(() -> {
            if (closed || !recovering || pendingGeneration != next || !awaitingSpiderCompletion) return;
            awaitingSpiderCompletion = false;
            // Released HomeActivity always posts the stability check after
            // spider cleanup. A changed generation is handled by that poll,
            // not inline inside the clear completion callback.
            hooks.schedule(poll, 0);
            // schedule() may synchronously retire Home before posting.
            if (closed) hooks.unschedule(poll);
        });
    }

    private boolean deferForHome() {
        if (hooks.canRecoverHome() && !closed) return false;
        // Cleanup is complete, but Home is not available. Keep the generation
        // unapplied; resume/focus will re-read the latest lifecycle generation.
        if (!closed) waitingForHome = true;
        return true;
    }

    private void checkStability() {
        if (closed || !recovering || waitingForHome || awaitingSpiderCompletion) return;
        long latest = hooks.generation();
        if (closed || !recovering) return;
        if (deferForHome()) return;
        if (latest != pendingGeneration) {
            recovering = false;
            check();
            return;
        }
        boolean ready = hooks.networkReady();
        if (closed || !recovering) return;
        stableChecks = ready ? stableChecks + 1 : 0;
        if (stableChecks < 2 && checks < 12) {
            checks++;
            hooks.schedule(poll, 500L);
            if (closed) hooks.unschedule(poll);
            return;
        }
        // Network readiness and generation callbacks may retire or pause the
        // owner. Do not consume the generation until it is still current and
        // Home can actually accept the refresh.
        long commitGeneration = hooks.generation();
        if (closed) return;
        if (commitGeneration != pendingGeneration) {
            recovering = false;
            check();
            return;
        }
        if (deferForHome()) return;
        appliedGeneration = pendingGeneration;
        recovering = false;
        hooks.refreshHome();
        check();
    }

    public long appliedGeneration() { return appliedGeneration; }
    public boolean recovering() { return recovering; }

    @Override public void close() {
        if (closed) return;
        closed = true;
        recovering = false;
        awaitingSpiderCompletion = false;
        waitingForHome = false;
        hooks.unschedule(poll);
    }
}
