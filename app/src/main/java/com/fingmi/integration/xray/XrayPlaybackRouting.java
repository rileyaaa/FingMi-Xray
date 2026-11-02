package com.fingmi.integration.xray;

import java.util.function.BooleanSupplier;

/**
 * Identity-only playback routing decisions shared by FongMi engine adapters.
 *
 * <p>No Android, Media3 or FongMi API dependencies: a new upstream engine
 * factory only needs to supply its engine type and rebuild state. Distinct
 * Xray endpoint instances must never be treated as equivalent, even when
 * their descriptive values compare equal.
 */
public final class XrayPlaybackRouting {

    private XrayPlaybackRouting() {}

    /** Old engine is authoritative until its media transport is released. */
    public static <T> T activeProxy(T requestedProxy, T engineProxy) {
        return engineProxy != null ? engineProxy : requestedProxy;
    }

    public static <T> boolean hasSession(T requestedProxy, T engineProxy) {
        return requestedProxy != null || engineProxy != null;
    }

    /**
     * A proxy-bound player must be an Exo engine bound to the same endpoint.
     * Direct playback instead follows upstream's engine selection policy.
     */
    public static <T> boolean canReuseEngine(
            T requestedProxy,
            T engineProxy,
            boolean engineIsExo,
            BooleanSupplier upstreamEngineMatches,
            BooleanSupplier needsRebuild) {
        if (requestedProxy != null) {
            return engineIsExo && engineProxy == requestedProxy && !needsRebuild.getAsBoolean();
        }
        return engineProxy == null && upstreamEngineMatches.getAsBoolean() && !needsRebuild.getAsBoolean();
    }
}
