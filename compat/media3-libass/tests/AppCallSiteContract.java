/* Compile-only call-site witness against real production dependencies.
 * Mirrors Libass/Media3 calls in current5.6.3 ExoPlayerSession,
 * ExoMediaSourceFactory, ExoSubtitleController and ExoUtil.
 * No replacement application or Media3 classes. Not an Android app build.
 */
package com.fongmi.android.tv.player.exo;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import androidx.media3.common.MediaItem;
import androidx.media3.common.TrackSelectionOverride;
import androidx.media3.datasource.DataSource;
import androidx.media3.exoplayer.DefaultLoadControl;
import androidx.media3.exoplayer.DefaultRenderersFactory;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.Renderer;
import androidx.media3.exoplayer.libass.LibassConfiguration;
import androidx.media3.exoplayer.libass.LibassPlaybackSession;
import androidx.media3.exoplayer.libass.LibassSubtitleController;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import androidx.media3.exoplayer.source.MediaSource;
import androidx.media3.exoplayer.source.preload.DefaultPreloadManager;
import androidx.media3.exoplayer.source.preload.MediaSourceFactorySupplier;
import androidx.media3.exoplayer.text.SecondaryTextOutput;
import androidx.media3.exoplayer.text.TextOutput;
import androidx.media3.exoplayer.text.TextRenderer;
import androidx.media3.exoplayer.trackselection.DecodeTrackSelector;
import androidx.media3.exoplayer.trackselection.SecondaryTextTrackSelector;
import androidx.media3.extractor.DefaultExtractorsFactory;
import androidx.media3.ui.CaptionStyleCompat;
import androidx.media3.ui.PlayerView;
import androidx.media3.ui.libass.LibassPlayerViewController;
import java.util.ArrayList;
import java.util.List;

final class AppCallSiteContract {
  static void check(Context context, ExoPlayer player, PlayerView playerView,
      MediaItem mediaItem, DataSource.Factory dataSources, MediaSourceFactorySupplier supplier,
      CaptionStyleCompat style, TrackSelectionOverride selection) {
    LibassConfiguration configuration = new LibassConfiguration.Builder()
        .setFontConfig(null).setFontsDirectory(null).setDefaultFontFamily(null)
        .setMaximumRenderPixels(1920 * 1080).setMaximumGlyphCount(4096)
        .setMaximumBitmapCacheSizeMb(48).build();
    LibassPlaybackSession session = new LibassPlaybackSession(configuration, true);
    SecondaryTextTrackSelector.Factory selectors =
        new SecondaryTextTrackSelector.Factory(DecodeTrackSelector::new);
    SecondaryTextOutput output = new SecondaryTextOutput();
    DefaultPreloadManager.Builder preload = new DefaultPreloadManager.Builder(context,
        ignored -> DefaultPreloadManager.PreloadStatus.specifiedRangeLoaded(0, 10_000))
        .setMediaSourceFactorySupplier(supplier)
        .setRenderersFactory(new Renderers(context, session, output))
        .setTrackSelectorFactory(selectors)
        .setLoadControl(new DefaultLoadControl.Builder().build());
    LibassSubtitleController subtitles = new LibassSubtitleController(player, session, selectors, output);
    LibassPlayerViewController view = new LibassPlayerViewController(player, session, subtitles);
    view.bind(playerView);
    session.setPreloadMediaItem(mediaItem);
    if (session.isAvailable()) {
      LibassPlaybackSession.MediaComponents components =
          session.createMediaComponents(mediaItem, new DefaultExtractorsFactory());
      MediaSource source = new DefaultMediaSourceFactory(dataSources, components.extractorsFactory)
          .setSubtitleParserFactory(components.subtitleParserFactory).createMediaSource(mediaItem);
    }
    session.setBottomPositionFraction(0.1f);
    session.setSecondaryBottomPositionFraction(0.8f);
    session.setFontScale(1.0f, true);
    view.setStyleOverride(style, null);
    view.setSecondarySubtitleViewConfigurator(subtitleView -> {
      subtitleView.setBottomPosition(0.0f);
      subtitleView.setBottomPaddingFraction(0.8f);
    });
    TrackSelectionOverride primary = subtitles.getPrimaryTextTrackSelectionOverride();
    TrackSelectionOverride secondary = subtitles.getSecondaryTextTrackSelectionOverride();
    List<TrackSelectionOverride> overrides = subtitles.getSecondaryTextTrackSelectionOverrides();
    boolean suppressed = subtitles.isSecondaryTextTrackSuppressed();
    subtitles.setSecondaryTextTrackAutoSelectionEnabled(true);
    subtitles.setSecondaryTextTrackSelectionOverride(selection);
    session.setPreloadMediaItem(null);
    view.close();
    subtitles.close();
    session.close();
  }

  private static final class Renderers extends DefaultRenderersFactory {
    private final LibassPlaybackSession session;
    private final TextOutput secondary;
    Renderers(Context context, LibassPlaybackSession session, TextOutput secondary) {
      super(context);
      this.session = session;
      this.secondary = secondary;
    }
    @Override protected void buildMiscellaneousRenderers(Context context, Handler handler,
        int extensionMode, ArrayList<Renderer> out) {
      super.buildMiscellaneousRenderers(context, handler, extensionMode, out);
      if (session.isAvailable()) out.add(session.createClockRenderer());
    }
    @Override protected void buildTextRenderers(Context context, TextOutput output, Looper looper,
        int extensionMode, ArrayList<Renderer> out) {
      super.buildTextRenderers(context, output, looper, extensionMode, out);
      out.add(new TextRenderer(secondary, looper));
    }
  }
}
