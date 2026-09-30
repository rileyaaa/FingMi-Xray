/*
 * Reconstructed from the immutable FongMi 5.6.8 Leanback release.
 */
package androidx.media3.decoder.ffmpeg;

import androidx.media3.common.Format;
import androidx.media3.common.util.CodecSpecificDataUtil;
import androidx.media3.common.util.Log;
import androidx.media3.exoplayer.video.DolbyVisionP7Converter;
import java.nio.ByteBuffer;

/** FFmpeg-backed Dolby Vision profile 7 converter used by MediaCodec video decoding. */
public final class FfmpegDolbyVisionP7Converter implements DolbyVisionP7Converter {

  private static final String TAG = "FfmpegDoviP7";
  private static Boolean profile81Available;
  private static Boolean hdr10Available;

  private final int outputMode;
  private long nativeContext;

  /** Factory loaded reflectively by DefaultRenderersFactory. */
  public static final class Factory implements DolbyVisionP7Converter.Factory {
    @Override
    public boolean isConversionAvailable(int outputMode) {
      if (outputMode != OUTPUT_MODE_PROFILE_8_1 && outputMode != OUTPUT_MODE_HDR10) {
        Log.w(TAG, "Unknown Dolby Vision output mode: " + outputMode);
        return false;
      }
      return FfmpegLibrary.isAvailable() && isNativeConversionAvailable(outputMode);
    }

    @Override
    public DolbyVisionP7Converter create(Format format, int outputMode) {
      return new FfmpegDolbyVisionP7Converter(format, outputMode);
    }
  }

  public FfmpegDolbyVisionP7Converter(Format format, int outputMode) {
    byte[] dolbyVisionCsd = CodecSpecificDataUtil.getDolbyVisionCsd(format);
    if (dolbyVisionCsd == null) {
      throw new IllegalArgumentException("A Dolby Vision configuration record is required.");
    }
    int profile = (dolbyVisionCsd[2] & 0xFE) >> 1;
    int flags = dolbyVisionCsd[3] & 0xFF;
    if (profile != 7 || (flags & 0x01) == 0) {
      throw new IllegalArgumentException("Profile 7 with a base layer is required.");
    }
    if (outputMode == OUTPUT_MODE_PROFILE_8_1 && (flags & 0x04) == 0) {
      throw new IllegalArgumentException("Profile 8.1 conversion requires RPU metadata.");
    }
    if (outputMode != OUTPUT_MODE_PROFILE_8_1 && outputMode != OUTPUT_MODE_HDR10) {
      throw new IllegalArgumentException("Unknown Dolby Vision output mode: " + outputMode);
    }

    int level = ((dolbyVisionCsd[2] & 0x01) << 5) | ((flags & 0xF8) >> 3);
    boolean enhancementLayerPresent = (flags & 0x02) != 0;
    byte[] extraData = FfmpegInitializationData.forVideo(format).extraData;
    nativeContext =
        ffmpegCreateDolbyVisionP7Converter(
            outputMode, level, enhancementLayerPresent, extraData);
    if (nativeContext == 0) {
      throw new IllegalStateException("Failed to initialize Dolby Vision profile 7 conversion.");
    }
    this.outputMode = outputMode;
  }

  private static synchronized boolean isNativeConversionAvailable(int outputMode) {
    Boolean cached =
        outputMode == OUTPUT_MODE_PROFILE_8_1 ? profile81Available : hdr10Available;
    if (cached == null) {
      cached = ffmpegIsDolbyVisionP7ConversionAvailable(outputMode);
      if (outputMode == OUTPUT_MODE_PROFILE_8_1) {
        profile81Available = cached;
      } else {
        hdr10Available = cached;
      }
    }
    return cached;
  }

  @Override
  public void convert(ByteBuffer buffer) {
    if (!buffer.isDirect() || buffer.isReadOnly() || buffer.position() != 0) {
      throw new IllegalArgumentException(
          "A writable direct buffer at position zero is required.");
    }
    if (nativeContext == 0) {
      throw new IllegalStateException("The converter has been released.");
    }
    int size =
        ffmpegConvertDolbyVisionP7(
            nativeContext, buffer, buffer.limit(), buffer.capacity());
    if (size < 0) {
      String target =
          outputMode == OUTPUT_MODE_PROFILE_8_1 ? "profile 8.1" : "HDR10";
      throw new IllegalStateException(
          "Dolby Vision profile 7 to " + target + " failed: " + size);
    }
    buffer.limit(size);
  }

  @Override
  public void flush() {
    if (nativeContext != 0) {
      ffmpegFlushDolbyVisionP7Converter(nativeContext);
    } else {
      Log.w(TAG, "The converter has been released.");
    }
  }

  @Override
  public void release() {
    if (nativeContext != 0) {
      ffmpegReleaseDolbyVisionP7Converter(nativeContext);
      nativeContext = 0;
    }
  }

  private static native int ffmpegConvertDolbyVisionP7(
      long context, ByteBuffer buffer, int limit, int capacity);

  private static native long ffmpegCreateDolbyVisionP7Converter(
      int outputMode, int level, boolean enhancementLayerPresent, byte[] extraData);

  private static native void ffmpegFlushDolbyVisionP7Converter(long context);

  private static native boolean ffmpegIsDolbyVisionP7ConversionAvailable(int outputMode);

  private static native void ffmpegReleaseDolbyVisionP7Converter(long context);
}
