package androidx.media3.ui.danmaku;

import android.net.Uri;

import androidx.annotation.Nullable;
import androidx.media3.ui.PlayerView;

import okhttp3.OkHttpClient;

/**
 * Reconstructed upstream-missing adapter which keeps danmaku state across PlayerView rebinding.
 *
 * <p>The fixed FongMi Media3 PlayerView already owns the actual DanmakuController. This class only
 * retains the app-level source/config/client/enabled state and reapplies it when playback binds a
 * different PlayerView.
 */
public final class DanmakuPlayerViewController implements AutoCloseable {

    @Nullable private PlayerView playerView;
    @Nullable private OkHttpClient okHttpClient;
    @Nullable private Uri dataSource;
    private DanmakuConfig config = DanmakuConfig.DEFAULT;
    private boolean enabled = true;
    private boolean closed;

    public void bind(@Nullable PlayerView playerView) {
        if (closed || this.playerView == playerView) return;
        detachCurrentView();
        this.playerView = playerView;
        if (playerView == null) return;
        playerView.setDanmakuOkHttpClient(okHttpClient);
        playerView.setDanmakuConfig(config);
        playerView.setDanmakuEnabled(enabled);
        playerView.setDanmakuSource(dataSource);
    }

    public void setOkHttpClient(@Nullable OkHttpClient client) {
        if (closed) return;
        okHttpClient = client;
        if (playerView != null) playerView.setDanmakuOkHttpClient(client);
    }

    public void setDataSource(@Nullable Uri uri) {
        if (closed) return;
        dataSource = uri;
        if (playerView != null) playerView.setDanmakuSource(uri);
    }

    public void setConfig(DanmakuConfig config) {
        if (closed || config == null) return;
        this.config = config;
        if (playerView != null) playerView.setDanmakuConfig(config);
    }

    public void setEnabled(boolean enabled) {
        if (closed) return;
        this.enabled = enabled;
        if (playerView != null) playerView.setDanmakuEnabled(enabled);
    }

    public void sendNow(String text) {
        if (!closed && playerView != null) playerView.sendDanmaku(text);
    }

    @Override
    public void close() {
        if (closed) return;
        closed = true;
        detachCurrentView();
        playerView = null;
        okHttpClient = null;
        dataSource = null;
    }

    private void detachCurrentView() {
        if (playerView == null) return;
        playerView.setDanmakuSource(null);
        playerView.setDanmakuOkHttpClient(null);
    }
}
