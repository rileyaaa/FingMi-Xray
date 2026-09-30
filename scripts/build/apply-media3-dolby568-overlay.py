#!/usr/bin/env python3
"""Apply the reproducible FongMi 5.6.8 Dolby Vision release overlay to FongMi/media."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

OVERLAY_ID = "fongmi-tv-5.6.8-dolby-release-overlay-v1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_media_codec_video_renderer(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import static androidx.media3.exoplayer.DecoderReuseEvaluation.DISCARD_REASON_MAX_INPUT_SIZE_EXCEEDED;\n",
        "import static androidx.media3.exoplayer.DecoderReuseEvaluation.DISCARD_REASON_MAX_INPUT_SIZE_EXCEEDED;\n"
        "import static androidx.media3.exoplayer.DecoderReuseEvaluation.DISCARD_REASON_WORKAROUND;\n",
        "renderer workaround import",
    )
    text = replace_once(
        text,
        "import java.nio.ByteBuffer;\nimport java.util.List;\n",
        "import java.nio.ByteBuffer;\nimport java.util.ArrayList;\nimport java.util.List;\n",
        "renderer java imports",
    )
    text = replace_once(
        text,
        "  private final @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy;\n\n"
        "  private @MonotonicNonNull CodecMaxValues codecMaxValues;\n",
        "  private final @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy;\n"
        "  @Nullable private final DolbyVisionP7Converter.Factory dolbyVisionP7ConverterFactory;\n"
        "  @Nullable private DolbyVisionP7Converter dolbyVisionP7Converter;\n\n"
        "  private @MonotonicNonNull CodecMaxValues codecMaxValues;\n",
        "renderer P7 fields",
    )
    text = replace_once(
        text,
        "    private @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy;\n",
        "    private @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy;\n"
        "    @Nullable private DolbyVisionP7Converter.Factory dolbyVisionP7ConverterFactory;\n",
        "builder P7 field",
    )
    setter_anchor = """    public Builder setDolbyVisionOutputPolicy(
        @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy) {
      this.dolbyVisionOutputPolicy = dolbyVisionOutputPolicy;
      return this;
    }

"""
    setter = setter_anchor + """    /** Sets the optional FFmpeg-backed Dolby Vision profile 7 converter factory. */
    @CanIgnoreReturnValue
    public Builder setDolbyVisionP7ConverterFactory(
        @Nullable DolbyVisionP7Converter.Factory dolbyVisionP7ConverterFactory) {
      this.dolbyVisionP7ConverterFactory = dolbyVisionP7ConverterFactory;
      return this;
    }

"""
    text = replace_once(text, setter_anchor, setter, "builder P7 setter")
    text = replace_once(
        text,
        "    dolbyVisionOutputPolicy = builder.dolbyVisionOutputPolicy;\n"
        "    nextOutputBufferToProcessPresentationTimeUs = C.TIME_UNSET;\n",
        "    dolbyVisionOutputPolicy = builder.dolbyVisionOutputPolicy;\n"
        "    dolbyVisionP7ConverterFactory = builder.dolbyVisionP7ConverterFactory;\n"
        "    dolbyVisionP7Converter = null;\n"
        "    nextOutputBufferToProcessPresentationTimeUs = C.TIME_UNSET;\n",
        "renderer P7 constructor",
    )
    text = replace_once(
        text,
        "    return supportsFormatInternal(\n"
        "        context, mediaCodecSelector, format, DolbyVisionOutputPolicy.AUTO);\n",
        "    return supportsFormatInternal(\n"
        "        context,\n"
        "        mediaCodecSelector,\n"
        "        format,\n"
        "        DolbyVisionOutputPolicy.AUTO,\n"
        "        /* dolbyVisionP7ConverterFactory= */ null);\n",
        "static supports P7",
    )
    text = replace_once(
        text,
        "    return supportsFormatInternal(context, mediaCodecSelector, format, dolbyVisionOutputPolicy);\n",
        "    return supportsFormatInternal(\n"
        "        context,\n"
        "        mediaCodecSelector,\n"
        "        format,\n"
        "        dolbyVisionOutputPolicy,\n"
        "        dolbyVisionP7ConverterFactory);\n",
        "instance supports P7",
    )
    text = replace_once(
        text,
        "      Format format,\n"
        "      @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy)\n"
        "      throws DecoderQueryException {\n",
        "      Format format,\n"
        "      @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy,\n"
        "      @Nullable DolbyVisionP7Converter.Factory dolbyVisionP7ConverterFactory)\n"
        "      throws DecoderQueryException {\n",
        "supports internal signature",
    )
    text = replace_once(
        text,
        "    boolean requiresSecureDecryption = drmInitData != null;\n"
        "    List<MediaCodecInfo> decoderInfos =\n"
        "        getDecoderInfos(\n"
        "            context,\n"
        "            mediaCodecSelector,\n"
        "            format,\n"
        "            requiresSecureDecryption,\n"
        "            /* requiresTunnelingDecoder= */ false,\n"
        "            dolbyVisionOutputPolicy);\n",
        "    boolean requiresSecureDecryption = drmInitData != null;\n"
        "    @Nullable\n"
        "    Format dolbyVisionP7Format =\n"
        "        selectDolbyVisionP7Format(\n"
        "            context,\n"
        "            mediaCodecSelector,\n"
        "            format,\n"
        "            requiresSecureDecryption,\n"
        "            /* requiresTunnelingDecoder= */ false,\n"
        "            dolbyVisionOutputPolicy,\n"
        "            dolbyVisionP7ConverterFactory);\n"
        "    Format decoderFormat = dolbyVisionP7Format != null ? dolbyVisionP7Format : format;\n"
        "    List<MediaCodecInfo> decoderInfos =\n"
        "        getDecoderInfos(\n"
        "            context,\n"
        "            mediaCodecSelector,\n"
        "            decoderFormat,\n"
        "            requiresSecureDecryption,\n"
        "            /* requiresTunnelingDecoder= */ false,\n"
        "            dolbyVisionOutputPolicy);\n",
        "supports P7 selection",
    )
    text = replace_once(
        text,
        "              format,\n"
        "              /* requiresSecureDecoder= */ false,\n",
        "              decoderFormat,\n"
        "              /* requiresSecureDecoder= */ false,\n",
        "supports fallback P7 format",
    )
    text = replace_once(
        text,
        "    boolean isFormatSupported = decoderInfo.isFormatSupported(context, format);\n",
        "    boolean isFormatSupported = decoderInfo.isFormatSupported(context, decoderFormat);\n",
        "supports first decoder format",
    )
    text = replace_once(
        text,
        "        if (otherDecoderInfo.isFormatSupported(context, format)) {\n",
        "        if (otherDecoderInfo.isFormatSupported(context, decoderFormat)) {\n",
        "supports other decoder format",
    )
    text = replace_once(
        text,
        "    boolean requiresDolbyVisionToneMapping =\n"
        "        shouldUseDolbyVisionToneMappingDecoder(context, format, dolbyVisionOutputPolicy);\n",
        "    boolean requiresDolbyVisionToneMapping =\n"
        "        dolbyVisionP7Format == null\n"
        "            && shouldUseDolbyVisionToneMappingDecoder(\n"
        "                context, format, dolbyVisionOutputPolicy);\n",
        "supports tone map P7",
    )
    text = replace_once(
        text,
        "        decoderInfo.isSeamlessAdaptationSupported(format)\n",
        "        decoderInfo.isSeamlessAdaptationSupported(decoderFormat)\n",
        "supports adaptive P7",
    )
    text = replace_once(
        text,
        "    if (shouldUseDolbyVisionFallbackDecoder(context, format, dolbyVisionOutputPolicy)\n"
        "        && !requiresDolbyVisionToneMapping) {\n"
        "      decoderSupport = DECODER_SUPPORT_FALLBACK_MIMETYPE;\n"
        "    }\n",
        "    if (dolbyVisionP7Format != null\n"
        "        || (shouldUseDolbyVisionFallbackDecoder(context, format, dolbyVisionOutputPolicy)\n"
        "            && !requiresDolbyVisionToneMapping)) {\n"
        "      decoderSupport = DECODER_SUPPORT_FALLBACK_MIMETYPE;\n"
        "    }\n",
        "supports decoder support P7",
    )

    text = replace_once(
        text,
        "    return MediaCodecUtil.getDecoderInfosSortedByFormatSupport(\n"
        "        context,\n"
        "        getDecoderInfos(\n"
        "            context,\n"
        "            mediaCodecSelector,\n"
        "            format,\n"
        "            requiresSecureDecoder,\n"
        "            tunneling,\n"
        "            dolbyVisionOutputPolicy),\n"
        "        format);\n",
        "    @Nullable\n"
        "    Format dolbyVisionP7Format =\n"
        "        selectDolbyVisionP7Format(\n"
        "            context,\n"
        "            mediaCodecSelector,\n"
        "            format,\n"
        "            requiresSecureDecoder,\n"
        "            tunneling,\n"
        "            dolbyVisionOutputPolicy,\n"
        "            dolbyVisionP7ConverterFactory);\n"
        "    Format decoderFormat = dolbyVisionP7Format != null ? dolbyVisionP7Format : format;\n"
        "    return MediaCodecUtil.getDecoderInfosSortedByFormatSupport(\n"
        "        context,\n"
        "        getDecoderInfos(\n"
        "            context,\n"
        "            mediaCodecSelector,\n"
        "            decoderFormat,\n"
        "            requiresSecureDecoder,\n"
        "            tunneling,\n"
        "            dolbyVisionOutputPolicy),\n"
        "        decoderFormat);\n",
        "decoder infos P7",
    )

    tone_anchor = """  private static boolean shouldUseDolbyVisionToneMappingDecoder(
      Context context, Format format, @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy) {
    return SDK_INT >= 31
        && shouldUseDolbyVisionFallbackDecoder(context, format, dolbyVisionOutputPolicy)
        && CodecSpecificDataUtil.getDolbyVisionCompatibleBaseLayerMimeType(format) == null;
  }

"""
    helpers = tone_anchor + """  @Nullable
  private static Format getDolbyVisionP7Hdr10Format(Format format) {
    byte[] dolbyVisionCsd = CodecSpecificDataUtil.getDolbyVisionCsd(format);
    if (dolbyVisionCsd == null
        || ((dolbyVisionCsd[2] & 0xFE) >> 1) != 7
        || (dolbyVisionCsd[3] & 0x01) == 0) {
      return null;
    }
    List<byte[]> initializationData = new ArrayList<>(format.initializationData);
    if (initializationData.size() > 2) {
      initializationData.remove(2);
    }
    return format.buildUpon()
        .setSampleMimeType(MimeTypes.VIDEO_H265)
        .setCodecs(null)
        .setInitializationData(initializationData)
        .build();
  }

  @Nullable
  private static Format getDolbyVisionP7Profile81Format(Format format) {
    if (!MimeTypes.VIDEO_DOLBY_VISION.equals(format.sampleMimeType)) {
      return null;
    }
    byte[] dolbyVisionCsd = CodecSpecificDataUtil.getDolbyVisionCsd(format);
    if (dolbyVisionCsd == null || ((dolbyVisionCsd[2] & 0xFE) >> 1) != 7) {
      return null;
    }
    int flags = dolbyVisionCsd[3] & 0xFF;
    if ((flags & 0x05) != 0x05) {
      return null;
    }
    int level = ((dolbyVisionCsd[2] & 0x01) << 5) | ((flags & 0xF8) >> 3);
    String prefix = "dvhe";
    if (format.codecs != null) {
      for (String codec : format.codecs.split(",")) {
        String candidate = codec.trim();
        if (candidate.startsWith("dvhe.07.") || candidate.startsWith("dvh1.07.")) {
          prefix = candidate.substring(0, 4);
          break;
        }
      }
    }
    byte[] profile81Csd =
        CodecSpecificDataUtil.buildDolbyVisionInitializationData(
            /* profile= */ 8, level, /* blSignalCompatibilityId= */ 1, /* mdCompression= */ 0);
    return format.buildUpon()
        .setCodecs(Util.formatInvariant("%s.08.%02d", prefix, level))
        .setInitializationData(
            CodecSpecificDataUtil.setDolbyVisionCsd(format.initializationData, profile81Csd))
        .build();
  }

  @Nullable
  private static Format selectDolbyVisionP7Format(
      Context context,
      MediaCodecSelector mediaCodecSelector,
      Format format,
      boolean requiresSecureDecoder,
      boolean requiresTunnelingDecoder,
      @DolbyVisionOutputPolicy.Mode int dolbyVisionOutputPolicy,
      @Nullable DolbyVisionP7Converter.Factory converterFactory)
      throws DecoderQueryException {
    if (requiresSecureDecoder
        || requiresTunnelingDecoder
        || format.drmInitData != null
        || format.cryptoType != C.CRYPTO_TYPE_NONE
        || converterFactory == null
        || !MimeTypes.VIDEO_DOLBY_VISION.equals(format.sampleMimeType)) {
      return null;
    }

    Format hdr10Format = getDolbyVisionP7Hdr10Format(format);
    if (!DolbyVisionOutputPolicy.isNativeOutputAllowed(context, dolbyVisionOutputPolicy)) {
      return hdr10Format != null
              && converterFactory.isConversionAvailable(DolbyVisionP7Converter.OUTPUT_MODE_HDR10)
          ? hdr10Format
          : null;
    }

    Format profile81Format = getDolbyVisionP7Profile81Format(format);
    if (profile81Format == null && hdr10Format == null) {
      return null;
    }

    boolean originalSoftwareSupported = false;
    List<MediaCodecInfo> dolbyVisionDecoders =
        mediaCodecSelector.getDecoderInfos(
            MimeTypes.VIDEO_DOLBY_VISION,
            /* requiresSecureDecoder= */ false,
            /* requiresTunnelingDecoder= */ false);
    for (MediaCodecInfo decoderInfo : dolbyVisionDecoders) {
      if (decoderInfo.isFormatSupported(context, format)) {
        if (decoderInfo.hardwareAccelerated) {
          return null;
        }
        originalSoftwareSupported = true;
      }
    }

    boolean profile81SoftwareSupported = false;
    if (profile81Format != null
        && converterFactory.isConversionAvailable(
            DolbyVisionP7Converter.OUTPUT_MODE_PROFILE_8_1)) {
      for (MediaCodecInfo decoderInfo : dolbyVisionDecoders) {
        if (decoderInfo.isFormatSupported(context, profile81Format)) {
          if (decoderInfo.hardwareAccelerated) {
            return profile81Format;
          }
          profile81SoftwareSupported = true;
        }
      }
    }

    boolean hdr10SoftwareSupported = false;
    if (hdr10Format != null
        && converterFactory.isConversionAvailable(DolbyVisionP7Converter.OUTPUT_MODE_HDR10)) {
      List<MediaCodecInfo> hevcDecoders =
          mediaCodecSelector.getDecoderInfos(
              MimeTypes.VIDEO_H265,
              /* requiresSecureDecoder= */ false,
              /* requiresTunnelingDecoder= */ false);
      for (MediaCodecInfo decoderInfo : hevcDecoders) {
        if (decoderInfo.isFormatSupported(context, hdr10Format)) {
          if (decoderInfo.hardwareAccelerated) {
            return hdr10Format;
          }
          hdr10SoftwareSupported = true;
        }
      }
    }

    if (originalSoftwareSupported) {
      return null;
    }
    if (profile81SoftwareSupported) {
      return profile81Format;
    }
    return hdr10SoftwareSupported ? hdr10Format : null;
  }

  @Nullable
  private Format selectDolbyVisionP7FormatForCodec(MediaCodecInfo codecInfo, Format format) {
    DolbyVisionP7Converter.Factory converterFactory = dolbyVisionP7ConverterFactory;
    if (tunneling
        || format.drmInitData != null
        || format.cryptoType != C.CRYPTO_TYPE_NONE
        || converterFactory == null) {
      return null;
    }
    boolean nativeOutputAllowed =
        DolbyVisionOutputPolicy.isNativeOutputAllowed(context, dolbyVisionOutputPolicy);
    if (!nativeOutputAllowed || MimeTypes.VIDEO_H265.equals(codecInfo.mimeType)) {
      Format hdr10Format = getDolbyVisionP7Hdr10Format(format);
      if (hdr10Format != null
          && MimeTypes.VIDEO_H265.equals(codecInfo.mimeType)
          && converterFactory.isConversionAvailable(DolbyVisionP7Converter.OUTPUT_MODE_HDR10)
          && codecInfo.isFormatSupported(context, hdr10Format)) {
        return hdr10Format;
      }
      return null;
    }
    if (MimeTypes.VIDEO_DOLBY_VISION.equals(codecInfo.mimeType)
        && !codecInfo.isFormatSupported(context, format)) {
      Format profile81Format = getDolbyVisionP7Profile81Format(format);
      if (profile81Format != null
          && converterFactory.isConversionAvailable(
              DolbyVisionP7Converter.OUTPUT_MODE_PROFILE_8_1)
          && codecInfo.isFormatSupported(context, profile81Format)) {
        return profile81Format;
      }
    }
    return null;
  }

  private void releaseDolbyVisionP7Converter() {
    if (dolbyVisionP7Converter != null) {
      dolbyVisionP7Converter.release();
      dolbyVisionP7Converter = null;
    }
  }

"""
    text = replace_once(text, tone_anchor, helpers, "P7 helpers")

    config_old = """    String codecMimeType = codecInfo.codecMimeType;
    codecMaxValues = getCodecMaxValues(codecInfo, format, getStreamFormats());
    MediaFormat mediaFormat =
        getMediaFormat(
            format,
            codecMimeType,
            codecMaxValues,
            codecOperatingRate,
            deviceNeedsNoPostProcessWorkaround,
            tunneling ? tunnelingAudioSessionId : C.AUDIO_SESSION_ID_UNSET);
    Surface codecSurface = getSurfaceForCodec(codecInfo);
    maybeSetKeyAllowFrameDrop(mediaFormat);
    return MediaCodecAdapter.Configuration.createForVideoDecoding(
        codecInfo, mediaFormat, format, codecSurface, crypto);
"""
    config_new = """    @Nullable Format dolbyVisionP7Format = selectDolbyVisionP7FormatForCodec(codecInfo, format);
    Format codecFormat = dolbyVisionP7Format != null ? dolbyVisionP7Format : format;
    releaseDolbyVisionP7Converter();
    String codecMimeType = codecInfo.codecMimeType;
    Format[] streamFormats =
        dolbyVisionP7Format != null ? new Format[] {codecFormat} : getStreamFormats();
    codecMaxValues = getCodecMaxValues(codecInfo, codecFormat, streamFormats);
    MediaFormat mediaFormat =
        getMediaFormat(
            codecFormat,
            codecMimeType,
            codecMaxValues,
            codecOperatingRate,
            deviceNeedsNoPostProcessWorkaround,
            tunneling ? tunnelingAudioSessionId : C.AUDIO_SESSION_ID_UNSET);
    Surface codecSurface = getSurfaceForCodec(codecInfo);
    maybeSetKeyAllowFrameDrop(mediaFormat);
    MediaCodecAdapter.Configuration configuration =
        MediaCodecAdapter.Configuration.createForVideoDecoding(
            codecInfo, mediaFormat, codecFormat, codecSurface, crypto);
    if (dolbyVisionP7Format != null) {
      DolbyVisionP7Converter.Factory converterFactory =
          checkNotNull(dolbyVisionP7ConverterFactory);
      int outputMode =
          MimeTypes.VIDEO_H265.equals(dolbyVisionP7Format.sampleMimeType)
              ? DolbyVisionP7Converter.OUTPUT_MODE_HDR10
              : DolbyVisionP7Converter.OUTPUT_MODE_PROFILE_8_1;
      dolbyVisionP7Converter = converterFactory.create(format, outputMode);
      Log.i(
          TAG,
          outputMode == DolbyVisionP7Converter.OUTPUT_MODE_HDR10
              ? "Using the Dolby Vision profile 7 HDR10 base layer."
              : "Converting Dolby Vision profile 7 input to profile 8.1.");
    }
    return configuration;
"""
    text = replace_once(text, config_old, config_new, "P7 codec configuration")

    text = replace_once(
        text,
        "    DecoderReuseEvaluation evaluation = codecInfo.canReuseCodec(oldFormat, newFormat);\n",
        "    if (dolbyVisionP7Converter != null) {\n"
        "      return new DecoderReuseEvaluation(\n"
        "          codecInfo.name, oldFormat, newFormat, REUSE_RESULT_NO, DISCARD_REASON_WORKAROUND);\n"
        "    }\n"
        "    DecoderReuseEvaluation evaluation = codecInfo.canReuseCodec(oldFormat, newFormat);\n",
        "P7 codec reuse",
    )
    text = replace_once(
        text,
        "    if (av1SampleDependencyParser != null) {\n"
        "      av1SampleDependencyParser.reset();\n"
        "    }\n"
        "  }\n\n"
        "  @Override\n"
        "  public void setPlaybackSpeed",
        "    if (av1SampleDependencyParser != null) {\n"
        "      av1SampleDependencyParser.reset();\n"
        "    }\n"
        "    if (dolbyVisionP7Converter != null) {\n"
        "      dolbyVisionP7Converter.flush();\n"
        "    }\n"
        "  }\n\n"
        "  @Override\n"
        "  public void setPlaybackSpeed",
        "P7 flush",
    )
    text = replace_once(
        text,
        "  protected void onCodecReleased(String name) {\n"
        "    eventDispatcher.decoderReleased(name);\n"
        "  }\n",
        "  protected void onCodecReleased(String name) {\n"
        "    eventDispatcher.decoderReleased(name);\n"
        "    releaseDolbyVisionP7Converter();\n"
        "  }\n",
        "P7 codec release",
    )
    text = replace_once(
        text,
        "  protected void onQueueInputBuffer(DecoderInputBuffer buffer) throws ExoPlaybackException {\n"
        "    String mimeType = checkNotNull(getCodecInfo()).mimeType;\n",
        "  protected void onQueueInputBuffer(DecoderInputBuffer buffer) throws ExoPlaybackException {\n"
        "    if (dolbyVisionP7Converter != null && buffer.data != null) {\n"
        "      try {\n"
        "        dolbyVisionP7Converter.convert(buffer.data);\n"
        "      } catch (RuntimeException error) {\n"
        "        throw createRendererException(\n"
        "            error, getCodecInputFormat(), PlaybackException.ERROR_CODE_DECODING_FAILED);\n"
        "      }\n"
        "    }\n"
        "    String mimeType = checkNotNull(getCodecInfo()).mimeType;\n",
        "P7 queue conversion",
    )
    text = replace_once(
        text,
        "    try {\n"
        "      super.onDisabled();\n"
        "    } finally {\n"
        "      eventDispatcher.disabled(decoderCounters);\n",
        "    try {\n"
        "      super.onDisabled();\n"
        "    } finally {\n"
        "      releaseDolbyVisionP7Converter();\n"
        "      eventDispatcher.disabled(decoderCounters);\n",
        "P7 disabled release",
    )

    path.write_text(text, encoding="utf-8")


def patch_default_renderers_factory(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import androidx.media3.exoplayer.video.MediaCodecVideoRenderer;\n",
        "import androidx.media3.exoplayer.video.DolbyVisionP7Converter;\n"
        "import androidx.media3.exoplayer.video.MediaCodecVideoRenderer;\n",
        "factory P7 import",
    )
    text = replace_once(
        text,
        "            .setDolbyVisionOutputPolicy(dolbyVisionOutputPolicy)\n"
        "            .setEventHandler(eventHandler)\n",
        "            .setDolbyVisionOutputPolicy(dolbyVisionOutputPolicy)\n"
        "            .setDolbyVisionP7ConverterFactory(createDolbyVisionP7ConverterFactory())\n"
        "            .setEventHandler(eventHandler)\n",
        "factory P7 injection",
    )
    anchor = """  /**
   * Builds video renderers for use by the player.
"""
    helper = """  @Nullable
  private DolbyVisionP7Converter.Factory createDolbyVisionP7ConverterFactory() {
    try {
      Class<?> clazz =
          Class.forName("androidx.media3.decoder.ffmpeg.FfmpegDolbyVisionP7Converter$Factory");
      return (DolbyVisionP7Converter.Factory) clazz.getConstructor().newInstance();
    } catch (ClassNotFoundException e) {
      return null;
    } catch (Exception e) {
      throw new IllegalStateException(
          "Error instantiating Dolby Vision profile 7 converter factory", e);
    }
  }

"""
    text = replace_once(text, anchor, helper + anchor, "factory P7 loader")
    path.write_text(text, encoding="utf-8")


def patch_proguard(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    anchor = """-dontnote androidx.media3.decoder.ffmpeg.FfmpegVideoRenderer
-keepclassmembers class androidx.media3.decoder.ffmpeg.FfmpegVideoRenderer {
  <init>(android.content.Context, long, android.os.Handler, androidx.media3.exoplayer.video.VideoRendererEventListener, int);
}
"""
    addition = anchor + """
-dontnote androidx.media3.decoder.ffmpeg.FfmpegDolbyVisionP7Converter$Factory
-keep class androidx.media3.decoder.ffmpeg.FfmpegDolbyVisionP7Converter$Factory {
  public <init>();
}
"""
    text = replace_once(text, anchor, addition, "factory P7 proguard")
    path.write_text(text, encoding="utf-8")


def copy_overlay(root: Path, overlay_root: Path) -> None:
    source = overlay_root / "libraries"
    if not source.is_dir():
        raise ValueError(f"missing overlay libraries directory: {source}")
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(overlay_root)
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--overlay",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "compat/media3-dolby568",
    )
    args = parser.parse_args()

    root = args.source.resolve()
    overlay_root = args.overlay.resolve()
    try:
        copy_overlay(root, overlay_root)
        patch_media_codec_video_renderer(
            root
            / "libraries/exoplayer/src/main/java/androidx/media3/exoplayer/video/MediaCodecVideoRenderer.java"
        )
        patch_default_renderers_factory(
            root / "libraries/exoplayer/src/main/java/androidx/media3/exoplayer/DefaultRenderersFactory.java"
        )
        patch_proguard(root / "libraries/exoplayer/proguard-rules.txt")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"PASS: applied {OVERLAY_ID}")


if __name__ == "__main__":
    main()
