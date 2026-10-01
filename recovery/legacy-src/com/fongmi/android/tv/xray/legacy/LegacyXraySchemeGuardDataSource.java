package com.fongmi.android.tv.xray.legacy;

import android.net.Uri;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.TransferListener;

import java.io.IOException;
import java.util.Map;
import java.util.Set;

/**
 * Behavior reconstruction of the shipped Xray DataSource guard (R8 name: or2).
 *
 * When Xray is active, only HTTP(S) and Android/local resource schemes may use
 * the generic Exo DataSource path. RTSP/RTSPT are handled separately by the
 * Xray RTSP MediaSource factory. Every other scheme is rejected instead of
 * silently falling back to a non-Xray network implementation.
 */
public final class LegacyXraySchemeGuardDataSource implements DataSource {

    private static final Set<String> ALLOWED_SCHEMES =
            Set.of(
                    "http",
                    "https",
                    "file",
                    "asset",
                    "content",
                    "data",
                    "rawresource",
                    "android.resource");

    private final DataSource delegate;
    private boolean opened;

    public LegacyXraySchemeGuardDataSource(DataSource delegate) {
        this.delegate = delegate;
    }

    @Override
    public void addTransferListener(@NonNull TransferListener transferListener) {
        delegate.addTransferListener(transferListener);
    }

    @Override
    public long open(@NonNull DataSpec dataSpec) throws IOException {
        String scheme = dataSpec.uri.getScheme();
        if (!isAllowed(scheme)) {
            throw new IOException(
                    "Unsupported data source scheme while Xray is enabled");
        }

        opened = true;
        return delegate.open(dataSpec);
    }

    @Override
    public int read(
            @NonNull byte[] buffer,
            int offset,
            int length) throws IOException {
        return delegate.read(buffer, offset, length);
    }

    @Nullable
    @Override
    public Uri getUri() {
        return delegate.getUri();
    }

    @Override
    public Map<String, java.util.List<String>> getResponseHeaders() {
        return delegate.getResponseHeaders();
    }

    @Override
    public void close() throws IOException {
        if (!opened) return;
        opened = false;
        delegate.close();
    }

    private static boolean isAllowed(String scheme) {
        if (isBlank(scheme)) return true;
        return ALLOWED_SCHEMES.contains(
                scheme.toLowerCase(java.util.Locale.ROOT));
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
