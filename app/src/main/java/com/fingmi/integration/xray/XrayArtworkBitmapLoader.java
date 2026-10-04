package com.fingmi.integration.xray;

import android.graphics.Bitmap;
import android.net.Uri;

import androidx.annotation.NonNull;
import androidx.media3.common.util.BitmapLoader;

import com.fongmi.android.tv.player.PlayerManager;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.MoreExecutors;

import java.io.IOException;
import java.util.Locale;
import java.util.concurrent.CopyOnWriteArrayList;

public final class XrayArtworkBitmapLoader implements BitmapLoader {

    private final CopyOnWriteArrayList<ListenableFuture<Bitmap>> remoteLoads =
            new CopyOnWriteArrayList<>();
    private final PlayerManager player;
    private final BitmapLoader delegate;

    public XrayArtworkBitmapLoader(PlayerManager player, BitmapLoader delegate) {
        this.player = player;
        this.delegate = delegate;
    }

    @Override
    public boolean supportsMimeType(@NonNull String mimeType) {
        return delegate.supportsMimeType(mimeType);
    }

    @NonNull
    @Override
    public ListenableFuture<Bitmap> decodeBitmap(@NonNull byte[] data) {
        return delegate.decodeBitmap(data);
    }

    @NonNull
    @Override
    public ListenableFuture<Bitmap> loadBitmap(@NonNull Uri uri) {
        boolean local = isLocal(uri);
        if (player != null && player.hasXraySession() && !local) {
            return Futures.immediateFailedFuture(
                    new IOException("Remote artwork blocked while Xray is enabled"));
        }

        ListenableFuture<Bitmap> future = delegate.loadBitmap(uri);
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
        if (uri == null) return false;
        String scheme = uri.getScheme();
        if (isBlank(scheme)) return true;
        String value = scheme.toLowerCase(Locale.ROOT);
        return "file".equals(value)
                || "asset".equals(value)
                || "content".equals(value)
                || "data".equals(value)
                || "rawresource".equals(value)
                || "android.resource".equals(value);
    }

    private static boolean isBlank(String value) {
        if (value == null) return true;
        for (int offset = 0; offset < value.length();) {
            int codePoint = value.codePointAt(offset);
            if (!Character.isWhitespace(codePoint)) return false;
            offset += Character.charCount(codePoint);
        }
        return true;
    }
}
