/*
 * Reconstructed from the immutable FongMi 5.6.8 Leanback release.
 */
package androidx.media3.decoder.ffmpeg;

import android.content.Context;
import android.media.MediaCrypto;
import android.os.Handler;
import androidx.annotation.Nullable;
import androidx.media3.common.C;
import androidx.media3.common.DolbyVisionOutputPolicy;
import androidx.media3.common.Format;
import androidx.media3.common.MimeTypes;
import androidx.media3.common.PlaybackException;
import androidx.media3.common.util.CodecSpecificDataUtil;
import androidx.media3.decoder.DecoderInputBuffer;
import androidx.media3.exoplayer.ExoPlaybackException;
import androidx.media3.exoplayer.RendererCapabilities;
import androidx.media3.exoplayer.mediacodec.MediaCodecAdapter;
import androidx.media3.exoplayer.mediacodec.MediaCodecInfo;
import androidx.media3.exoplayer.mediacodec.MediaCodecSelector;
import androidx.media3.exoplayer.mediacodec.MediaCodecUtil.DecoderQueryException;
import androidx.media3.exoplayer.video.MediaCodecVideoRenderer;
import androidx.media3.exoplayer.video.VideoRendererEventListener;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;

/**
 * Release-only renderer for Dolby Vision profile 5.
 *
 * <p>The HEVC base layer is decoded by hardware MediaCodec into a native FFmpeg/libplacebo mapping
 * surface. RPU NAL units are extracted from the original access units and queued to the mapping
 * renderer by presentation timestamp.
 */
public final class FfmpegDolbyVisionP5Renderer extends MediaCodecVideoRenderer {

  private final Context context;
  private final @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy;
  private final FfmpegDolbyVisionP5VideoSink mappingSink;
  private volatile boolean mappingDisabled;

  public FfmpegDolbyVisionP5Renderer(
      Context context,
      MediaCodecAdapter.Factory codecAdapterFactory,
      MediaCodecSelector mediaCodecSelector,
      long allowedJoiningTimeMs,
      boolean enableDecoderFallback,
      @Nullable Handler eventHandler,
      @Nullable VideoRendererEventListener eventListener,
      @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy) {
    this(
        new FfmpegDolbyVisionP5VideoSink(),
        context,
        codecAdapterFactory,
        mediaCodecSelector,
        allowedJoiningTimeMs,
        enableDecoderFallback,
        eventHandler,
        eventListener,
        dolbyVisionOutputPolicy);
  }

  private FfmpegDolbyVisionP5Renderer(
      FfmpegDolbyVisionP5VideoSink mappingSink,
      Context context,
      MediaCodecAdapter.Factory codecAdapterFactory,
      MediaCodecSelector mediaCodecSelector,
      long allowedJoiningTimeMs,
      boolean enableDecoderFallback,
      @Nullable Handler eventHandler,
      @Nullable VideoRendererEventListener eventListener,
      @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy) {
    super(
        new MediaCodecVideoRenderer.Builder(context)
            .setCodecAdapterFactory(codecAdapterFactory)
            .setMediaCodecSelector(mediaCodecSelector)
            .setAllowedJoiningTimeMs(allowedJoiningTimeMs)
            .setEnableDecoderFallback(enableDecoderFallback)
            .setDolbyVisionOutputPolicy(dolbyVisionOutputPolicy)
            .setEventHandler(eventHandler)
            .setEventListener(eventListener)
            .setVideoSink(mappingSink));
    this.context = context.getApplicationContext();
    this.dolbyVisionOutputPolicy = dolbyVisionOutputPolicy;
    this.mappingSink = mappingSink;
    mappingSink.setFailureCallback(this::onMappingFailure);
  }

  @Override
  public String getName() {
    return "FfmpegDolbyVisionP5Renderer";
  }

  private static Format toBaseLayerFormat(Format format) {
    byte[] dolbyVisionCsd = CodecSpecificDataUtil.getDolbyVisionCsd(format);
    List<byte[]> initializationData = new ArrayList<>(format.initializationData);
    if (dolbyVisionCsd != null && initializationData.size() > 2) {
      initializationData.remove(2);
    }
    return format.buildUpon()
        .setSampleMimeType(MimeTypes.VIDEO_H265)
        .setCodecs(null)
        .setInitializationData(initializationData)
        .build();
  }

  @Override
  protected void onQueueInputBuffer(DecoderInputBuffer buffer) throws ExoPlaybackException {
    super.onQueueInputBuffer(buffer);
    if (buffer.data == null || buffer.isEndOfStream()) {
      return;
    }
    for (byte[] rpu : extractRpuNalUnits(buffer.data)) {
      mappingSink.queueRpu(buffer.timeUs, rpu);
    }
  }

  @Override
  protected @Capabilities int supportsFormat(
      MediaCodecSelector mediaCodecSelector, Format format) throws DecoderQueryException {
    if (!isEligible(mediaCodecSelector, format)) {
      return RendererCapabilities.create(C.FORMAT_UNSUPPORTED_TYPE);
    }
    List<MediaCodecInfo> decoderInfos = getHardwareDecoderInfos(mediaCodecSelector, format);
    if (decoderInfos.isEmpty() || !FfmpegDolbyVisionP5Native.probe().available) {
      return RendererCapabilities.create(C.FORMAT_UNSUPPORTED_SUBTYPE);
    }

    Format baseLayerFormat = toBaseLayerFormat(format);
    boolean formatHandled = false;
    for (MediaCodecInfo decoderInfo : decoderInfos) {
      if (decoderInfo.isFormatSupported(context, baseLayerFormat)) {
        formatHandled = true;
        break;
      }
    }
    return RendererCapabilities.create(
        formatHandled ? C.FORMAT_HANDLED : C.FORMAT_EXCEEDS_CAPABILITIES,
        RendererCapabilities.ADAPTIVE_NOT_SUPPORTED,
        RendererCapabilities.TUNNELING_NOT_SUPPORTED,
        RendererCapabilities.HARDWARE_ACCELERATION_SUPPORTED,
        RendererCapabilities.DECODER_SUPPORT_FALLBACK_MIMETYPE);
  }

  @Override
  protected List<MediaCodecInfo> getDecoderInfos(
      MediaCodecSelector mediaCodecSelector, Format format, boolean requiresSecureDecoder)
      throws DecoderQueryException {
    if (requiresSecureDecoder || !isEligible(mediaCodecSelector, format)) {
      return new ArrayList<>();
    }
    List<MediaCodecInfo> decoderInfos = getHardwareDecoderInfos(mediaCodecSelector, format);
    return decoderInfos.isEmpty() || !FfmpegDolbyVisionP5Native.probe().available
        ? new ArrayList<>()
        : decoderInfos;
  }

  @Override
  protected MediaCodecAdapter.Configuration getMediaCodecConfiguration(
      MediaCodecInfo codecInfo,
      Format format,
      @Nullable MediaCrypto crypto,
      float codecOperatingRate) {
    return super.getMediaCodecConfiguration(
        codecInfo, toBaseLayerFormat(format), crypto, codecOperatingRate);
  }

  @Override
  protected void onDisabled() {
    try {
      super.onDisabled();
    } finally {
      try {
        releaseCodec();
      } finally {
        mappingSink.resetNativeRenderer();
      }
    }
  }

  @Override
  protected void onRelease() {
    try {
      super.onRelease();
    } finally {
      mappingSink.release();
    }
  }

  private boolean isEligible(MediaCodecSelector mediaCodecSelector, Format format)
      throws DecoderQueryException {
    if (mappingDisabled
        || format.cryptoType != C.CRYPTO_TYPE_NONE
        || !FfmpegDolbyVisionP5MappingPolicy.isSupportedFormat(format)
        || dolbyVisionOutputPolicy == DolbyVisionOutputPolicy.ASSUME_SUPPORTED) {
      return false;
    }

    if (dolbyVisionOutputPolicy != DolbyVisionOutputPolicy.ASSUME_UNSUPPORTED
        && DolbyVisionOutputPolicy.isNativeOutputAllowed(context, dolbyVisionOutputPolicy)) {
      List<MediaCodecInfo> nativeDolbyVisionDecoders =
          mediaCodecSelector.getDecoderInfos(
              MimeTypes.VIDEO_DOLBY_VISION,
              /* requiresSecureDecoder= */ false,
              /* requiresTunnelingDecoder= */ false);
      for (MediaCodecInfo decoderInfo : nativeDolbyVisionDecoders) {
        if (decoderInfo.hardwareAccelerated && decoderInfo.isFormatSupported(context, format)) {
          return false;
        }
      }
    }
    return true;
  }

  private List<MediaCodecInfo> getHardwareDecoderInfos(
      MediaCodecSelector mediaCodecSelector, Format format) throws DecoderQueryException {
    List<MediaCodecInfo> decoderInfos =
        super.getDecoderInfos(
            mediaCodecSelector,
            toBaseLayerFormat(format),
            /* requiresSecureDecoder= */ false);
    ArrayList<MediaCodecInfo> hardwareDecoders = new ArrayList<>(decoderInfos.size());
    for (MediaCodecInfo decoderInfo : decoderInfos) {
      if (decoderInfo.hardwareAccelerated) {
        hardwareDecoders.add(decoderInfo);
      }
    }
    return hardwareDecoders;
  }

  private void onMappingFailure() {
    if (mappingDisabled) {
      return;
    }
    mappingDisabled = true;
    Format[] formats = getStreamFormats();
    @Nullable Format format = formats.length == 0 ? null : formats[0];
    setPendingPlaybackException(
        createRendererException(
            new FfmpegDecoderException("Dolby Vision profile 5 GPU mapping failed"),
            format,
            /* isRecoverable= */ true,
            PlaybackException.ERROR_CODE_VIDEO_FRAME_PROCESSING_FAILED));
  }

  private static List<byte[]> extractRpuNalUnits(ByteBuffer source) {
    ByteBuffer buffer = source.duplicate();
    int start = buffer.position();
    int limit = buffer.limit();

    for (int lengthSize = 4; lengthSize >= 1; lengthSize--) {
      @Nullable List<byte[]> lengthPrefixed = parseLengthPrefixedRpus(buffer, start, limit, lengthSize);
      if (lengthPrefixed != null) {
        return lengthPrefixed;
      }
    }
    return parseAnnexBRpus(buffer, start, limit);
  }

  @Nullable
  private static List<byte[]> parseLengthPrefixedRpus(
      ByteBuffer buffer, int start, int limit, int lengthSize) {
    int offset = start;
    ArrayList<byte[]> rpus = null;
    while (offset < limit) {
      if (limit - offset < lengthSize) {
        return null;
      }
      long nalLength = 0;
      for (int i = 0; i < lengthSize; i++) {
        nalLength = (nalLength << 8) | (buffer.get(offset + i) & 0xFFL);
      }
      int nalStart = offset + lengthSize;
      if (nalLength < 2 || nalLength > limit - nalStart) {
        return null;
      }
      int nalEnd = nalStart + (int) nalLength;
      if (nalEnd - nalStart >= 3 && ((buffer.get(nalStart) & 0x7E) >> 1) == 62) {
        if (rpus == null) {
          rpus = new ArrayList<>();
        }
        rpus.add(copy(buffer, nalStart, nalEnd));
      }
      offset = nalEnd;
    }
    return rpus == null ? new ArrayList<>() : rpus;
  }

  private static List<byte[]> parseAnnexBRpus(ByteBuffer buffer, int start, int limit) {
    int firstStartCode = findStartCode(buffer, start, limit);
    if (firstStartCode < 0) {
      return new ArrayList<>();
    }
    ArrayList<byte[]> rpus = new ArrayList<>();
    int search = firstStartCode;
    while (true) {
      int startCode = findStartCode(buffer, search, limit);
      if (startCode < 0) {
        break;
      }
      int nalStart =
          startCode + (buffer.get(startCode + 2) == 1 ? 3 : 4);
      int nextStartCode = findStartCode(buffer, nalStart, limit);
      int nalEnd = nextStartCode < 0 ? limit : nextStartCode;
      if (nalEnd - nalStart >= 3 && ((buffer.get(nalStart) & 0x7E) >> 1) == 62) {
        rpus.add(copy(buffer, nalStart, nalEnd));
      }
      if (nextStartCode < 0) {
        break;
      }
      search = nextStartCode;
    }
    return rpus;
  }

  private static int findStartCode(ByteBuffer buffer, int start, int limit) {
    for (int offset = start; offset + 3 <= limit; offset++) {
      if (buffer.get(offset) == 0 && buffer.get(offset + 1) == 0) {
        if (buffer.get(offset + 2) == 1
            || (offset + 4 <= limit
                && buffer.get(offset + 2) == 0
                && buffer.get(offset + 3) == 1)) {
          return offset;
        }
      }
    }
    return -1;
  }

  private static byte[] copy(ByteBuffer buffer, int start, int end) {
    byte[] bytes = new byte[end - start];
    ByteBuffer duplicate = buffer.duplicate();
    duplicate.position(start);
    duplicate.limit(end);
    duplicate.get(bytes);
    return bytes;
  }
}
