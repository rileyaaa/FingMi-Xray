/*
 * Reconstructed from the immutable FongMi 5.6.8 Leanback release.
 */
package androidx.media3.exoplayer.video;

import androidx.media3.common.Format;
import java.nio.ByteBuffer;

/** Converts Dolby Vision profile 7 access units before MediaCodec input. */
public interface DolbyVisionP7Converter {

  int OUTPUT_MODE_PROFILE_8_1 = 0;
  int OUTPUT_MODE_HDR10 = 1;

  /** Factory injected by the optional FFmpeg extension. */
  interface Factory {
    boolean isConversionAvailable(int outputMode);

    DolbyVisionP7Converter create(Format format, int outputMode);
  }

  void convert(ByteBuffer buffer);

  void flush();

  void release();
}
