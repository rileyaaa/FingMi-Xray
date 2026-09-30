/*
 * Reconstructed from the immutable FongMi 5.6.8 Leanback release.
 */
package androidx.media3.decoder.ffmpeg;

import android.os.Build;
import android.view.Surface;
import androidx.annotation.Nullable;
import androidx.media3.common.util.Log;
import androidx.media3.common.util.Size;

/** JNI bridge for Dolby Vision profile 5 GPU mapping. */
final class FfmpegDolbyVisionP5Native {

  private static final String TAG = "FfmpegDoviP5Native";
  private static final int REQUIRED_CAPABILITIES = 0x7F;

  @Nullable private static Probe probe;

  private FfmpegDolbyVisionP5Native() {}

  public static final class NativeRenderer implements AutoCloseable {
    private final long[] statsBuffer = new long[11];
    private final Stats stats = new Stats();
    private long nativeContext;
    @Nullable private Surface inputSurface;

    NativeRenderer(long nativeContext, Surface inputSurface) {
      this.nativeContext = nativeContext;
      this.inputSurface = inputSurface;
    }

    public synchronized Stats getStats() {
      if (nativeContext != 0 && nativeGetStats(nativeContext, statsBuffer)) {
        stats.set(statsBuffer);
        return stats;
      }
      return Stats.EMPTY;
    }

    public synchronized Surface getInputSurface() {
      if (inputSurface == null) {
        throw new IllegalStateException("Renderer released");
      }
      return inputSurface;
    }

    public synchronized void setOutputSurface(@Nullable Surface surface, Size size) {
      if (nativeContext != 0) {
        nativeSetOutputSurface(nativeContext, surface, size.getWidth(), size.getHeight());
      }
    }

    public synchronized void clear() {
      if (nativeContext != 0) {
        nativeClear(nativeContext);
      }
    }

    public synchronized boolean queueFrame(long renderTimestampNs, long presentationTimeUs) {
      return nativeContext != 0
          && nativeQueueFrame(nativeContext, renderTimestampNs, presentationTimeUs);
    }

    public synchronized boolean queueRpu(long presentationTimeUs, byte[] rpu) {
      return nativeContext != 0
          && rpu.length >= 3
          && nativeQueueRpu(nativeContext, presentationTimeUs, rpu);
    }

    public synchronized void redraw() {
      if (nativeContext != 0) {
        nativeRedraw(nativeContext);
      }
    }

    @Override
    public synchronized void close() {
      if (nativeContext == 0) {
        return;
      }
      Surface surface = inputSurface;
      inputSurface = null;
      nativeRelease(nativeContext);
      nativeContext = 0;
      if (surface != null) {
        surface.release();
      }
    }
  }

  static final class Probe {
    public final boolean available;
    public final int capabilities;
    public final String reason;

    Probe(int capabilities, String reason, boolean available) {
      this.available = available;
      this.capabilities = capabilities;
      this.reason = reason;
    }

    @Override
    public String toString() {
      return "Probe(available="
          + available
          + ", capabilities="
          + capabilities
          + ", reason="
          + reason
          + ")";
    }
  }

  static final class Stats {
    static final Stats EMPTY = new Stats();

    long acquired;
    long matched;
    long unmatched;
    long frameDrops;
    long pendingFrames;
    long parsedRpus;
    long malformedRpus;
    long rpuDrops;
    long pendingRpus;
    long rendered;
    long failures;

    void set(long[] values) {
      acquired = values[0];
      matched = values[1];
      unmatched = values[2];
      frameDrops = values[3];
      pendingFrames = values[4];
      parsedRpus = values[5];
      malformedRpus = values[6];
      rpuDrops = values[7];
      pendingRpus = values[8];
      rendered = values[9];
      failures = values[10];
    }

    @Override
    public String toString() {
      return "Stats(acquired="
          + acquired
          + ", matched="
          + matched
          + ", unmatched="
          + unmatched
          + ", frameDrops="
          + frameDrops
          + ", pendingFrames="
          + pendingFrames
          + ", parsedRpus="
          + parsedRpus
          + ", malformedRpus="
          + malformedRpus
          + ", rpuDrops="
          + rpuDrops
          + ", pendingRpus="
          + pendingRpus
          + ", rendered="
          + rendered
          + ", failures="
          + failures
          + ")";
    }
  }

  public static NativeRenderer create(int width, int height) {
    if (width <= 0 || height <= 0 || !probe().available) {
      return null;
    }
    long nativeContext = nativeCreate(width, height);
    if (nativeContext == 0) {
      return null;
    }
    Surface inputSurface = nativeGetInputSurface(nativeContext);
    if (inputSurface != null) {
      return new NativeRenderer(nativeContext, inputSurface);
    }
    nativeRelease(nativeContext);
    return null;
  }

  public static synchronized Probe probe() {
    if (probe != null) {
      return probe;
    }
    if (Build.VERSION.SDK_INT < 26) {
      return setProbe(new Probe(0, "api-below-26", false));
    }
    if (!FfmpegLibrary.isAvailable()) {
      return setProbe(new Probe(0, "ffmpeg-unavailable", false));
    }
    try {
      System.loadLibrary("ffmpegDoviJNI");
      int capabilities = nativeProbeCapabilities();
      boolean available = (capabilities & REQUIRED_CAPABILITIES) == REQUIRED_CAPABILITIES;
      return setProbe(
          new Probe(
              capabilities,
              available ? "available" : "missing-capability",
              available));
    } catch (LinkageError | RuntimeException error) {
      return setProbe(
          new Probe(0, "probe-" + error.getClass().getSimpleName(), false));
    }
  }

  private static Probe setProbe(Probe value) {
    probe = value;
    Log.i(TAG, "GPU mapping " + value);
    return value;
  }

  private static native void nativeClear(long context);

  private static native long nativeCreate(int width, int height);

  private static native Surface nativeGetInputSurface(long context);

  private static native boolean nativeGetStats(long context, long[] stats);

  private static native int nativeProbeCapabilities();

  private static native boolean nativeQueueFrame(
      long context, long renderTimestampNs, long presentationTimeUs);

  private static native boolean nativeQueueRpu(long context, long presentationTimeUs, byte[] rpu);

  private static native void nativeRedraw(long context);

  private static native void nativeRelease(long context);

  private static native void nativeSetOutputSurface(
      long context, @Nullable Surface surface, int width, int height);
}
