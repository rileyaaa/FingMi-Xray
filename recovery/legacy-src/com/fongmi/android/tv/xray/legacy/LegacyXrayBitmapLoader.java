package com.fongmi.android.tv.xray.legacy;

import android.graphics.Bitmap;
import android.net.Uri;

import androidx.media3.common.util.BitmapLoader;

import com.fongmi.android.tv.player.PlayerManager;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.MoreExecutors;

import java.io.IOException;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Behavior reconstruction of the shipped MediaSession artwork guard (R8 name: rf2).
 *
 * Remote artwork is blocked while a Xray playback session exists. Local
 * artwork/resource schemes remain available to MediaSession/notifications.
 * Remote futures started before the transition are tracked so PlaybackService
 * can cancel them before installing a Xray port.
 */
public final class LegacyXrayBitmapLoader implements BitmapLoader {

    private static final Set<String> LOCAL_SCHEMES =
            Set.of(
                    "file",
                    "asset",
                    "content",
                    "data",
                    "rawresource",
                    "android.resource");

    private final CopyOnWriteArrayList<ListenableFuture<Bitmap>> remoteLoads =
            new CopyOnWriteArrayList<>();
    private final PlayerManager player;
    private final BitmapLoader delegate;

    public LegacyXrayBitmapLoader(
            PlayerManager player,
            BitmapLoader delegate) {
        this.player = player;
        this.delegate = delegate;
    }

    @Override
    public boolean supportsMimeType(String mimeType) {
        return delegate.supportsMimeType(mimeType);
    }

    @Override
    public ListenableFuture<Bitmap> decodeBitmap(byte[] data) {
        return delegate.decodeBitmap(data);
    }

    @Override
    public ListenableFuture<Bitmap> loadBitmap(Uri uri) {
        boolean local = isLocal(uri);

        if (player != null
                && player.hasXraySession()
                && !local) {
            return Futures.immediateFailedFuture(
                    new IOException(
                            "Remote artwork blocked while Xray is enabled"));
        }

        ListenableFuture<Bitmap> future =
                delegate.loadBitmap(uri);
        if (!local) {
            remoteLoads.add(future);
            future.addListener(
                    () -> remoteLoads.remove(future),
                    MoreExecutors.directExecutor());
        }
        return future;
    }

    public void cancelRemoteLoads() {
        for (ListenableFuture<Bitmap> future : remoteLoads) {
            future.cancel(true);
        }
        remoteLoads.clear();
    }

    private static boolean isLocal(Uri uri) {
        if (uri == null) return true;

        String scheme = uri.getScheme();
        if (scheme == null || scheme.isBlank()) return true;

        return LOCAL_SCHEMES.contains(
                scheme.toLowerCase(Locale.ROOT));
    }
}
