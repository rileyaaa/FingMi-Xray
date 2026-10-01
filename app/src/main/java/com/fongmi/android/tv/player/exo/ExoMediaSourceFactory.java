package com.fongmi.android.tv.player.exo;

import androidx.annotation.NonNull;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.database.StandaloneDatabaseProvider;
import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.TransferListener;
import androidx.media3.datasource.DefaultDataSource;
import androidx.media3.datasource.HttpDataSource;
import androidx.media3.datasource.cache.Cache;
import androidx.media3.datasource.cache.CacheDataSource;
import androidx.media3.datasource.cache.LeastRecentlyUsedCacheEvictor;
import androidx.media3.datasource.cache.SimpleCache;
import androidx.media3.datasource.okhttp.OkHttpDataSource;
import androidx.media3.exoplayer.drm.DrmSessionManagerProvider;
import androidx.media3.exoplayer.drm.DefaultDrmSessionManagerProvider;
import androidx.media3.exoplayer.rtsp.RtspMediaSource;
import androidx.media3.exoplayer.libass.LibassPlaybackSession;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import androidx.media3.exoplayer.source.MediaSource;
import androidx.media3.exoplayer.source.preload.MediaSourceFactorySupplier;
import androidx.media3.exoplayer.upstream.LoadErrorHandlingPolicy;
import androidx.media3.extractor.DefaultExtractorsFactory;
import androidx.media3.extractor.ExtractorsFactory;
import androidx.media3.extractor.ts.TsExtractor;

import com.fongmi.android.tv.App;
import com.fingmi.xray.network.XrayHttpClient;
import android.net.Uri;
import java.io.IOException;
import java.util.List;
import com.fongmi.android.tv.setting.PreloadSetting;
import com.github.catvod.net.OkHttp;
import com.github.catvod.utils.Path;

import java.io.File;
import java.util.Map;

public class ExoMediaSourceFactory implements MediaSource.Factory {

    private static final int CACHE_SPACE_PERCENT = 80;

    private static StandaloneDatabaseProvider databaseProvider;
    private static Cache cache;

    private final DefaultMediaSourceFactory defaultMediaSourceFactory;
    private final XrayHttpClient proxy;
    private final LibassPlaybackSession libassPlaybackSession;

    private HttpDataSource.Factory httpDataSourceFactory;
    private DataSource.Factory dataSourceFactory;

    private ExoMediaSourceFactory(LibassPlaybackSession libassPlaybackSession, XrayHttpClient proxy) {
        this.libassPlaybackSession = libassPlaybackSession;
        this.proxy = proxy;
        this.defaultMediaSourceFactory = configuredFactory(createDefaultExtractorsFactory());
    }

    static MediaSourceFactorySupplier supplier(LibassPlaybackSession libassPlaybackSession, XrayHttpClient proxy) {
        return new MediaSourceFactorySupplier() {
            @NonNull
            @Override
            public MediaSourceFactorySupplier setCache(Cache cache) {
                return this;
            }

            @NonNull
            @Override
            public MediaSourceFactorySupplier setDataSourceFactory(DataSource.Factory dataSourceFactory) {
                return this;
            }

            @Override
            public MediaSource.Factory get() {
                return new ExoMediaSourceFactory(libassPlaybackSession, proxy);
            }
        };
    }

    static DataSource.Factory createUpstreamDataSourceFactory(Map<String, String> headers) {
        HttpDataSource.Factory factory = new OkHttpDataSource.Factory(OkHttp.player());
        factory.setDefaultRequestProperties(headers);
        return new DefaultDataSource.Factory(App.get(), factory);
    }

    static synchronized Cache getCache() {
        if (cache != null) return cache;
        File dir = Path.exoCache();
        return cache = new SimpleCache(dir, new LeastRecentlyUsedCacheEvictor(getMaxCacheSize(dir)), getDatabaseProvider());
    }

    private static StandaloneDatabaseProvider getDatabaseProvider() {
        if (databaseProvider == null) databaseProvider = new StandaloneDatabaseProvider(App.get());
        return databaseProvider;
    }

    private static long getMaxCacheSize(File dir) {
        long usedBytes = Path.size(dir);
        long availableBytes = Math.max(0, Path.available(dir));
        long storageBudget = (usedBytes + availableBytes) * CACHE_SPACE_PERCENT / 100;
        return Math.min(PreloadSetting.getSizeBytes(), storageBudget);
    }

    @NonNull
    @Override
    public MediaSource.Factory setDrmSessionManagerProvider(@NonNull DrmSessionManagerProvider drmSessionManagerProvider) {
        return this;
    }

    @NonNull
    @Override
    public MediaSource.Factory setLoadErrorHandlingPolicy(@NonNull LoadErrorHandlingPolicy loadErrorHandlingPolicy) {
        return this;
    }

    @NonNull
    @Override
    public @C.ContentType int[] getSupportedTypes() {
        return defaultMediaSourceFactory.getSupportedTypes();
    }

    @NonNull
    @Override
    public MediaSource createMediaSource(@NonNull MediaItem mediaItem) {
        Map<String, String> headers = ExoUtil.extractHeaders(mediaItem);
        getHttpDataSourceFactory().setDefaultRequestProperties(headers);
        if (proxy != null && mediaItem.localConfiguration != null) {
            Uri uri = mediaItem.localConfiguration.uri;
            String scheme = uri.getScheme();
            if ("rtsp".equalsIgnoreCase(scheme) || "rtspt".equalsIgnoreCase(scheme)) {
                RtspMediaSource.Factory factory = new RtspMediaSource.Factory()
                        .setForceUseRtpTcp(true)
                        .setSocketFactory(proxy.rtspSocketFactory());
                String userAgent = headers.get("User-Agent");
                if (userAgent != null && userAgent.codePoints()
                        .anyMatch(codePoint -> !Character.isWhitespace(codePoint))) {
                    factory.setUserAgent(userAgent);
                }
                return factory.createMediaSource(mediaItem);
            }
        }
        if (!libassPlaybackSession.isAvailable()) return defaultMediaSourceFactory.createMediaSource(mediaItem);
        LibassPlaybackSession.MediaComponents components = libassPlaybackSession.createMediaComponents(mediaItem, createDefaultExtractorsFactory());
        return configuredFactory(components.extractorsFactory).setSubtitleParserFactory(components.subtitleParserFactory).createMediaSource(mediaItem);
    }

    private DefaultMediaSourceFactory configuredFactory(ExtractorsFactory extractorsFactory) {
        DefaultMediaSourceFactory factory = new DefaultMediaSourceFactory(getDataSourceFactory(), extractorsFactory);
        if (proxy != null) {
            DefaultDrmSessionManagerProvider drm = new DefaultDrmSessionManagerProvider();
            drm.setDrmHttpDataSourceFactory(getDataSourceFactory());
            factory.setDrmSessionManagerProvider(drm);
        }
        return factory;
    }

    private static ExtractorsFactory createDefaultExtractorsFactory() {
        return new DefaultExtractorsFactory().setTsExtractorTimestampSearchBytes(TsExtractor.DEFAULT_TIMESTAMP_SEARCH_BYTES * 10);
    }

    private DataSource.Factory getDataSourceFactory() {
        if (dataSourceFactory == null) {
            DataSource.Factory upstream = new DefaultDataSource.Factory(App.get(), getHttpDataSourceFactory());
            dataSourceFactory = proxy == null
                    ? () -> getCacheDataSource(upstream).createDataSource()
                    : () -> new GuardedPlaybackDataSource(upstream.createDataSource());
        }
        return dataSourceFactory;
    }

    private CacheDataSource.Factory getCacheDataSource(DataSource.Factory upstreamFactory) {
        return new CacheDataSource.Factory().setCache(getCache()).setUpstreamDataSourceFactory(upstreamFactory).setCacheWriteDataSinkFactory(null).setFlags(CacheDataSource.FLAG_IGNORE_CACHE_ON_ERROR);
    }

    private HttpDataSource.Factory getHttpDataSourceFactory() {
        if (httpDataSourceFactory == null) httpDataSourceFactory = new OkHttpDataSource.Factory(proxy == null ? OkHttp.player() : proxy.client());
        return httpDataSourceFactory;
    }

    /**
     * HTTP(S) uses the session proxy; Android/local resource schemes stay
     * local. Other generic schemes are rejected. RTSP/RTSPT are handled by
     * the dedicated Xray RTSP factory above.
     */
    private static final class GuardedPlaybackDataSource implements DataSource {
        private final DataSource delegate;
        private boolean opened;

        GuardedPlaybackDataSource(DataSource delegate) {
            this.delegate = delegate;
        }

        @Override
        public void addTransferListener(TransferListener listener) {
            delegate.addTransferListener(listener);
        }

        @Override
        public long open(DataSpec dataSpec) throws IOException {
            String scheme = dataSpec.uri.getScheme();
            if (!isAllowed(scheme)) {
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

        private static boolean isAllowed(String scheme) {
            if (scheme == null || scheme.trim().isEmpty()) return true;
            return "http".equalsIgnoreCase(scheme)
                    || "https".equalsIgnoreCase(scheme)
                    || "file".equalsIgnoreCase(scheme)
                    || "asset".equalsIgnoreCase(scheme)
                    || "content".equalsIgnoreCase(scheme)
                    || "data".equalsIgnoreCase(scheme)
                    || "rawresource".equalsIgnoreCase(scheme)
                    || "android.resource".equalsIgnoreCase(scheme);
        }
    }
}
