package com.fingmi.integration.xray;

import android.net.Uri;

import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.TransferListener;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Xray-only media transport boundary, independent of FongMi's source factory.
 *
 * <p>Normal FongMi media sources remain untouched. For an active Xray session,
 * HTTP(S) uses its own SOCKS-backed client; Android/local resource schemes are
 * allowed to delegate locally. Generic non-HTTP network protocols must not
 * silently escape to the direct network. RTSP/RTSPT have a separate socket path.
 *
 * <p>This wrapper does not own the underlying DataSource or the Xray client.
 * Its open/close ordering matches the existing release: after an attempted
 * delegate open, close still reaches the delegate even when opening throws.
 */
public final class XrayGuardedPlaybackDataSource implements DataSource {

    private final DataSource delegate;
    private boolean opened;

    public XrayGuardedPlaybackDataSource(DataSource delegate) {
        this.delegate = Objects.requireNonNull(delegate, "delegate");
    }

    @Override
    public void addTransferListener(TransferListener listener) {
        delegate.addTransferListener(listener);
    }

    @Override
    public long open(DataSpec dataSpec) throws IOException {
        String scheme = dataSpec.uri.getScheme();
        if (!isAllowedScheme(scheme)) {
            throw new IOException("Unsupported data source scheme while Xray is enabled");
        }
        opened = true;
        return delegate.open(dataSpec);
    }

    @Override
    public int read(byte[] buffer, int offset, int length) throws IOException {
        return delegate.read(buffer, offset, length);
    }

    @Override
    public Uri getUri() {
        return delegate.getUri();
    }

    @Override
    public Map<String, List<String>> getResponseHeaders() {
        return delegate.getResponseHeaders();
    }

    @Override
    public void close() throws IOException {
        if (!opened) return;
        opened = false;
        delegate.close();
    }

    private static boolean isAllowedScheme(String scheme) {
        if (isBlank(scheme)) return true;
        return "http".equalsIgnoreCase(scheme)
                || "https".equalsIgnoreCase(scheme)
                || "file".equalsIgnoreCase(scheme)
                || "asset".equalsIgnoreCase(scheme)
                || "content".equalsIgnoreCase(scheme)
                || "data".equalsIgnoreCase(scheme)
                || "rawresource".equalsIgnoreCase(scheme)
                || "android.resource".equalsIgnoreCase(scheme);
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
