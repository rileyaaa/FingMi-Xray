/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package androidx.media3.exoplayer.libass;

import androidx.annotation.Nullable;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.extractor.mkv.MatroskaExtractor;
import androidx.media3.extractor.text.SubtitleParser;

/** Reconstructed published5.6.5 libass.a (no historical flush-on-seek native call). Matroska extractor that forwards original ASS/SSA samples and attachment fonts to libass. */
@UnstableApi
/* package */ final class LibassMatroskaExtractor extends MatroskaExtractor {

  private final LibassMediaState mediaState;

  /** Creates an extractor whose libass state is owned by the caller. */
  public LibassMatroskaExtractor(
      MatroskaExtractor source,
      LibassMediaState mediaState,
      SubtitleParser.Factory subtitleParserFactory) {
    super(source, subtitleParserFactory);
    this.mediaState = mediaState;
  }

  @Override
  protected boolean shouldReadAttachment(
      @Nullable String fileName, @Nullable String mimeType, int contentSize) {
    return mediaState.shouldReadAttachment(fileName, mimeType, contentSize);
  }

  @Override
  protected void onAttachment(
      @Nullable String fileName, @Nullable String mimeType, byte[] attachmentData) {
    mediaState.addAttachment(fileName, mimeType, attachmentData);
  }

  @Override
  protected void onAssTrackInitialized(
      int trackNumber,
      @Nullable String name,
      @Nullable String language,
      byte[] codecPrivate) {
    mediaState.addTrack(trackNumber, codecPrivate);
  }

  @Override
  protected void onAssSubtitleSample(
      int trackNumber,
      long timeUs,
      long durationUs,
      byte[] sampleData,
      int sampleOffset,
      int sampleLength) {
    mediaState.processSample(
        trackNumber, timeUs, durationUs, sampleData, sampleOffset, sampleLength);
  }
}

