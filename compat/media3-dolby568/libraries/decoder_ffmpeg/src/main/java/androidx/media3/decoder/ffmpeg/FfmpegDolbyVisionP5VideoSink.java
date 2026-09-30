/*
 * Reconstructed from the immutable FongMi 5.6.8 Leanback release.
 */
package androidx.media3.decoder.ffmpeg;

import static androidx.media3.exoplayer.video.VideoSink.RELEASE_FIRST_FRAME_IMMEDIATELY;
import static androidx.media3.exoplayer.video.VideoSink.RELEASE_FIRST_FRAME_WHEN_PREVIOUS_STREAM_PROCESSED;

import android.graphics.Bitmap;
import android.os.SystemClock;
import android.view.Surface;
import androidx.annotation.Nullable;
import androidx.media3.common.C;
import androidx.media3.common.Effect;
import androidx.media3.common.Format;
import androidx.media3.common.MimeTypes;
import androidx.media3.common.VideoSize;
import androidx.media3.common.util.Log;
import androidx.media3.common.util.Size;
import androidx.media3.common.util.TimestampIterator;
import androidx.media3.common.util.Util;
import androidx.media3.exoplayer.video.VideoFrameMetadataListener;
import androidx.media3.exoplayer.video.VideoSink;
import java.util.ArrayDeque;
import java.util.List;
import java.util.concurrent.Executor;

/** VideoSink used by the FongMi 5.6.8 Dolby Vision profile 5 GPU mapping renderer. */
final class FfmpegDolbyVisionP5VideoSink implements VideoSink {

  private static final String TAG = "FfmpegDoviP5Sink";
  private static final int MAX_PENDING_FRAMES = 8;
  private static final long STATS_INTERVAL_MS = 100;
  private static final long STALLED_PENDING_MS = 2_000;
  private static final long EARLY_RENDER_THRESHOLD_US = 50_000;
  private static final long LATE_DROP_THRESHOLD_US = -30_000;

  private enum FrameAction {
    WAIT,
    RENDER,
    DROP
  }

  private static final class PendingFrame {
    final long presentationTimeUs;
    final long adjustedPresentationTimeUs;
    final VideoFrameHandler handler;

    PendingFrame(
        long presentationTimeUs,
        long adjustedPresentationTimeUs,
        VideoFrameHandler handler) {
      this.presentationTimeUs = presentationTimeUs;
      this.adjustedPresentationTimeUs = adjustedPresentationTimeUs;
      this.handler = handler;
    }
  }

  private final ArrayDeque<PendingFrame> pendingFrames = new ArrayDeque<>();

  private Listener listener = Listener.NO_OP;
  private Executor listenerExecutor = Runnable::run;
  private Runnable failureCallback = () -> {};
  private VideoFrameMetadataListener metadataListener =
      (presentationTimeUs, releaseTimeNs, format, mediaFormat) -> {};
  private Format rawFormat = new Format.Builder().setSampleMimeType(MimeTypes.VIDEO_RAW).build();
  private Size outputResolution = Size.UNKNOWN;
  @Nullable private FfmpegDolbyVisionP5Native.NativeRenderer nativeRenderer;
  @Nullable private Surface outputSurface;

  private long bufferTimestampAdjustmentUs;
  private boolean initialized;
  private boolean started;
  private boolean releaseFirstFrameImmediately;
  private boolean releaseFirstFrameWhenPreviousStreamProcessed;
  private long streamStartPositionUs;
  private boolean ended;
  private boolean released;
  private boolean firstFrameRendered;
  private long lastRenderedCount;
  private long lastFailureCount;
  private long lastStatsCheckMs = C.TIME_UNSET;
  private long pendingSinceMs = C.TIME_UNSET;
  private int consecutiveFailures;
  private boolean nativeFailureReported;
  private float playbackSpeed = 1f;

  public void setFailureCallback(Runnable failureCallback) {
    this.failureCallback = failureCallback;
  }

  /** Queues a Dolby Vision RPU extracted by the renderer. */
  public void queueRpu(long presentationTimeUs, byte[] rpu) {
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (renderer != null) {
      renderer.queueRpu(presentationTimeUs, rpu);
    }
  }

  /** Releases the native renderer while keeping the sink instance reusable. */
  public void resetNativeRenderer() {
    releaseNativeState();
  }

  @Override
  public void startRendering() {
    started = true;
    resetFailureWindow(/* resetRendered= */ false);
  }

  @Override
  public void stopRendering() {
    started = false;
    resetFailureWindow(/* resetRendered= */ false);
  }

  @Override
  public void setListener(Listener listener, Executor executor) {
    this.listener = listener;
    this.listenerExecutor = executor;
  }

  @Override
  public boolean initialize(Format sourceFormat) throws VideoSinkException {
    if (initialized) {
      return true;
    }
    if (released || nativeFailureReported) {
      return false;
    }
    if (sourceFormat.width <= 0
        || sourceFormat.height <= 0
        || sourceFormat.cryptoType != C.CRYPTO_TYPE_NONE
        || !FfmpegDolbyVisionP5MappingPolicy.isSupportedFormat(sourceFormat)) {
      throw new VideoSinkException(
          new IllegalArgumentException("Unsupported Dolby Vision profile 5 format"),
          sourceFormat);
    }

    try {
      FfmpegDolbyVisionP5Native.NativeRenderer renderer =
          FfmpegDolbyVisionP5Native.create(sourceFormat.width, sourceFormat.height);
      if (renderer == null) {
        markNativeFailure();
        return false;
      }
      nativeRenderer = renderer;
      if (outputSurface != null) {
        renderer.setOutputSurface(outputSurface, outputResolution);
      }
      rawFormat =
          sourceFormat.buildUpon().setSampleMimeType(MimeTypes.VIDEO_RAW).setCodecs(null).build();
      initialized = true;
      ended = false;
      nativeFailureReported = false;
      resetFailureWindow(/* resetRendered= */ true);
      return true;
    } catch (LinkageError | RuntimeException error) {
      Log.e(TAG, "Failed to initialize Dolby Vision profile 5 GPU mapping", error);
      FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
      nativeRenderer = null;
      if (renderer != null) {
        renderer.close();
      }
      markNativeFailure();
      return false;
    }
  }

  @Override
  public boolean isInitialized() {
    return initialized;
  }

  @Override
  public void redraw() {
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (renderer != null) {
      renderer.redraw();
    }
  }

  @Override
  public void flush(boolean resetPosition) {
    while (!pendingFrames.isEmpty()) {
      pendingFrames.remove().handler.skip();
    }
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (renderer != null) {
      renderer.clear();
    }
    ended = false;
    if (resetPosition) {
      releaseFirstFrameImmediately = false;
      releaseFirstFrameWhenPreviousStreamProcessed = false;
      firstFrameRendered = false;
    }
    resetFailureWindow(/* resetRendered= */ true);
  }

  @Override
  public boolean isReady(boolean otherwiseReady) {
    return initialized && otherwiseReady;
  }

  @Override
  public void signalEndOfCurrentInputStream() {
    ended = true;
  }

  @Override
  public void signalEndOfInput() {
    ended = true;
  }

  @Override
  public boolean isEnded() {
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    return ended
        && pendingFrames.isEmpty()
        && (renderer == null || renderer.getStats().pendingFrames == 0);
  }

  @Override
  public Surface getInputSurface() {
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (!initialized || renderer == null) {
      throw new IllegalStateException("Dolby Vision profile 5 sink is not initialized");
    }
    return renderer.getInputSurface();
  }

  @Override
  public void setVideoFrameMetadataListener(
      VideoFrameMetadataListener videoFrameMetadataListener) {
    metadataListener = videoFrameMetadataListener;
  }

  @Override
  public void setPlaybackSpeed(float speed) {
    if (speed > 0f) {
      playbackSpeed = speed;
    } else {
      Log.w(TAG, "Playback speed must be positive");
    }
  }

  @Override
  public void setVideoEffects(List<Effect> videoEffects) {
    // The released GPU mapping path does not apply Media3 video effects.
  }

  @Override
  public void setBufferTimestampAdjustmentUs(long bufferTimestampAdjustmentUs) {
    this.bufferTimestampAdjustmentUs = bufferTimestampAdjustmentUs;
  }

  @Override
  public void setOutputSurfaceInfo(Surface outputSurface, Size outputResolution) {
    this.outputSurface = outputSurface;
    this.outputResolution = outputResolution;
    firstFrameRendered = false;
    resetFailureWindow(/* resetRendered= */ true);
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (renderer != null) {
      renderer.setOutputSurface(outputSurface, outputResolution);
    }
  }

  @Override
  public void clearOutputSurfaceInfo() {
    outputSurface = null;
    outputResolution = Size.UNKNOWN;
    firstFrameRendered = false;
    resetFailureWindow(/* resetRendered= */ true);
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (renderer != null) {
      renderer.setOutputSurface(null, Size.UNKNOWN);
    }
  }

  @Override
  public void setChangeFrameRateStrategy(@C.VideoChangeFrameRateStrategy int changeFrameRateStrategy) {
    // The released mapping renderer leaves frame-rate strategy to the output surface owner.
  }

  @Override
  public void onInputStreamChanged(
      @InputType int inputType,
      Format format,
      long startPositionUs,
      @FirstFrameReleaseInstruction int firstFrameReleaseInstruction,
      List<Effect> videoEffects) {
    rawFormat = format.buildUpon().setSampleMimeType(MimeTypes.VIDEO_RAW).setCodecs(null).build();
    streamStartPositionUs = startPositionUs;
    releaseFirstFrameImmediately =
        firstFrameReleaseInstruction == RELEASE_FIRST_FRAME_IMMEDIATELY;
    releaseFirstFrameWhenPreviousStreamProcessed =
        firstFrameReleaseInstruction == RELEASE_FIRST_FRAME_WHEN_PREVIOUS_STREAM_PROCESSED;
    ended = false;
    listenerExecutor.execute(
        () -> listener.onVideoSizeChanged(new VideoSize(format.width, format.height)));
  }

  @Override
  public void allowReleaseFirstFrameBeforeStarted() {
    releaseFirstFrameImmediately = true;
  }

  @Override
  public boolean handleInputFrame(
      long bufferPresentationTimeUs, VideoFrameHandler videoFrameHandler) {
    if (!initialized || released || pendingFrames.size() >= MAX_PENDING_FRAMES) {
      return false;
    }
    pendingFrames.add(
        new PendingFrame(
            bufferPresentationTimeUs,
            bufferPresentationTimeUs + bufferTimestampAdjustmentUs,
            videoFrameHandler));
    listenerExecutor.execute(listener::onFrameAvailableForRendering);
    return true;
  }

  @Override
  public boolean handleInputBitmap(
      Bitmap inputBitmap, TimestampIterator bufferTimestampIterator) {
    return false;
  }

  @Override
  public void render(long positionUs, long elapsedRealtimeUs) {
    inspectNativeHealth();

    PendingFrame pending = pendingFrames.peek();
    if (pending == null) {
      return;
    }

    long earlyUs =
        (long)
            ((pending.adjustedPresentationTimeUs
                    - (positionUs + bufferTimestampAdjustmentUs))
                / (double) playbackSpeed);
    if (started) {
      earlyUs -= Util.msToUs(SystemClock.elapsedRealtime()) - elapsedRealtimeUs;
    }

    boolean mayRelease =
        started
            || releaseFirstFrameImmediately
            || (releaseFirstFrameWhenPreviousStreamProcessed
                && positionUs >= streamStartPositionUs);
    FrameAction action = FrameAction.WAIT;
    if (mayRelease && earlyUs <= EARLY_RENDER_THRESHOLD_US) {
      action = earlyUs < LATE_DROP_THRESHOLD_US ? FrameAction.DROP : FrameAction.RENDER;
    }
    if (action == FrameAction.WAIT) {
      return;
    }

    pendingFrames.remove();
    if (action == FrameAction.DROP) {
      pending.handler.skip();
      listenerExecutor.execute(listener::onFrameDropped);
      return;
    }

    long renderTimestampNs = Math.max(0L, earlyUs) * 1_000L + System.nanoTime();
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    if (renderer != null
        && renderer.queueFrame(renderTimestampNs, pending.presentationTimeUs)) {
      metadataListener.onVideoFrameAboutToBeRendered(
          pending.adjustedPresentationTimeUs, renderTimestampNs, rawFormat, null);
      pending.handler.render(renderTimestampNs);
      releaseFirstFrameImmediately = false;
      releaseFirstFrameWhenPreviousStreamProcessed = false;
      return;
    }

    pending.handler.skip();
    listenerExecutor.execute(listener::onFrameDropped);
  }

  @Override
  public void join(boolean renderNextFrameImmediately) {
    if (renderNextFrameImmediately) {
      releaseFirstFrameImmediately = true;
    }
  }

  @Override
  public void release() {
    if (released) {
      return;
    }
    released = true;
    releaseNativeState();
    outputSurface = null;
    outputResolution = Size.UNKNOWN;
  }

  private void inspectNativeHealth() {
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    Surface surface = outputSurface;
    if (renderer == null || surface == null || !surface.isValid()) {
      lastStatsCheckMs = C.TIME_UNSET;
      pendingSinceMs = C.TIME_UNSET;
      return;
    }

    long nowMs = SystemClock.elapsedRealtime();
    if (lastStatsCheckMs != C.TIME_UNSET
        && nowMs - lastStatsCheckMs < STATS_INTERVAL_MS) {
      return;
    }
    lastStatsCheckMs = nowMs;
    FfmpegDolbyVisionP5Native.Stats stats = renderer.getStats();
    long renderedDelta = Math.max(0L, stats.rendered - lastRenderedCount);
    long failureDelta = Math.max(0L, stats.failures - lastFailureCount);
    lastRenderedCount = stats.rendered;
    lastFailureCount = stats.failures;

    if (renderedDelta > 0) {
      consecutiveFailures = 0;
      pendingSinceMs = stats.pendingFrames > 0 ? nowMs : C.TIME_UNSET;
      if (!firstFrameRendered) {
        firstFrameRendered = true;
        listenerExecutor.execute(listener::onFirstFrameRendered);
      }
    } else {
      consecutiveFailures = (int) Math.min(3L, consecutiveFailures + failureDelta);
      if (stats.pendingFrames == 0) {
        pendingSinceMs = C.TIME_UNSET;
      } else if (pendingSinceMs == C.TIME_UNSET) {
        pendingSinceMs = nowMs;
      }
    }

    boolean stalled =
        stats.pendingFrames > 0
            && pendingSinceMs != C.TIME_UNSET
            && nowMs - pendingSinceMs >= STALLED_PENDING_MS;
    if ((consecutiveFailures >= 3 || stalled) && !nativeFailureReported) {
      Log.e(TAG, "Disabling failed Dolby Vision profile 5 GPU mapping: " + stats);
      markNativeFailure();
    }
  }

  private void markNativeFailure() {
    if (nativeFailureReported) {
      return;
    }
    nativeFailureReported = true;
    failureCallback.run();
  }

  private void resetFailureWindow(boolean resetRendered) {
    consecutiveFailures = 0;
    lastStatsCheckMs = C.TIME_UNSET;
    pendingSinceMs = C.TIME_UNSET;
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    FfmpegDolbyVisionP5Native.Stats stats =
        renderer == null ? FfmpegDolbyVisionP5Native.Stats.EMPTY : renderer.getStats();
    if (resetRendered) {
      lastRenderedCount = stats.rendered;
    }
    lastFailureCount = stats.failures;
  }

  private void releaseNativeState() {
    while (!pendingFrames.isEmpty()) {
      try {
        pendingFrames.remove().handler.skip();
      } catch (RuntimeException error) {
        pendingFrames.clear();
        closeNativeRenderer();
        resetStateAfterNativeRelease();
        throw error;
      }
    }
    pendingFrames.clear();
    closeNativeRenderer();
    resetStateAfterNativeRelease();
  }

  private void closeNativeRenderer() {
    FfmpegDolbyVisionP5Native.NativeRenderer renderer = nativeRenderer;
    nativeRenderer = null;
    if (renderer != null) {
      renderer.close();
    }
  }

  private void resetStateAfterNativeRelease() {
    initialized = false;
    started = false;
    releaseFirstFrameImmediately = false;
    releaseFirstFrameWhenPreviousStreamProcessed = false;
    ended = false;
    nativeFailureReported = false;
    firstFrameRendered = false;
    resetFailureWindow(/* resetRendered= */ true);
  }
}
