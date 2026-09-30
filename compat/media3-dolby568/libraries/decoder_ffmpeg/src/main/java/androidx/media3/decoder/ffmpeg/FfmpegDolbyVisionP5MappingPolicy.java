/*
 * Reconstructed from the immutable FongMi 5.6.8 Leanback release.
 */
package androidx.media3.decoder.ffmpeg;

import androidx.media3.common.Format;
import androidx.media3.common.MimeTypes;
import androidx.media3.common.util.CodecSpecificDataUtil;
import java.util.Locale;

/** Eligibility policy for the release-only Dolby Vision profile 5 GPU mapping renderer. */
final class FfmpegDolbyVisionP5MappingPolicy {

  private FfmpegDolbyVisionP5MappingPolicy() {}

  public static boolean isSupportedFormat(Format format) {
    if (!MimeTypes.VIDEO_DOLBY_VISION.equals(format.sampleMimeType)) {
      return false;
    }

    int codecProfile = codecProfile(format);
    byte[] dolbyVisionCsd = CodecSpecificDataUtil.getDolbyVisionCsd(format);
    if (dolbyVisionCsd != null) {
      int csdProfile = (dolbyVisionCsd[2] & 0xFE) >> 1;
      return csdProfile == 5
          && (codecProfile == -1 || codecProfile == csdProfile)
          && (dolbyVisionCsd[3] & 0x04) != 0;
    }

    return format.initializationData.size() <= 2 && codecProfile == 5;
  }

  private static int codecProfile(Format format) {
    if (!MimeTypes.VIDEO_DOLBY_VISION.equals(format.sampleMimeType)
        || format.codecs == null) {
      return -1;
    }
    for (String codec : format.codecs.split(",")) {
      String[] parts = codec.trim().toLowerCase(Locale.US).split("\\.");
      if (parts.length >= 3
          && ("dvhe".equals(parts[0]) || "dvh1".equals(parts[0]))
          && parts[1].length() == 2
          && Character.isDigit(parts[1].charAt(0))
          && Character.isDigit(parts[1].charAt(1))) {
        return Integer.parseInt(parts[1]);
      }
    }
    return -1;
  }
}
