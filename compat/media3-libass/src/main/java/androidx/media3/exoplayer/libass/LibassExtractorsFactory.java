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

import android.net.Uri;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.extractor.Extractor;
import androidx.media3.extractor.ExtractorsFactory;
import androidx.media3.extractor.mkv.MatroskaExtractor;
import androidx.media3.extractor.text.SubtitleParser;
import java.util.List;
import java.util.Map;

/** Reconstructed published5.6.5 lk1 using historical upstream structure. Replaces only Matroska extractors while preserving every other configured extractor. */
@UnstableApi
/* package */ final class LibassExtractorsFactory implements ExtractorsFactory {

  private ExtractorsFactory delegate;
  private final LibassMediaState mediaState;
  private SubtitleParser.Factory subtitleParserFactory;

  public LibassExtractorsFactory(
      ExtractorsFactory delegate,
      LibassMediaState mediaState,
      SubtitleParser.Factory subtitleParserFactory) {
    this.delegate = delegate.setSubtitleParserFactory(subtitleParserFactory);
    this.mediaState = mediaState;
    this.subtitleParserFactory = subtitleParserFactory;
  }

  @Override
  public ExtractorsFactory setSubtitleParserFactory(
      SubtitleParser.Factory subtitleParserFactory) {
    this.subtitleParserFactory = subtitleParserFactory;
    delegate = delegate.setSubtitleParserFactory(subtitleParserFactory);
    return this;
  }

  @Override
  public Extractor[] createExtractors() {
    return replaceMatroskaExtractors(delegate.createExtractors());
  }

  @Override
  public Extractor[] createExtractors(
      Uri uri, Map<String, List<String>> responseHeaders) {
    return replaceMatroskaExtractors(delegate.createExtractors(uri, responseHeaders));
  }

  private Extractor[] replaceMatroskaExtractors(Extractor[] extractors) {
    for (int i = 0; i < extractors.length; i++) {
      if (extractors[i].getClass() == MatroskaExtractor.class) {
        extractors[i] =
            new LibassMatroskaExtractor(
                (MatroskaExtractor) extractors[i], mediaState,
                subtitleParserFactory instanceof LibassSubtitleParserFactory
                    ? ((LibassSubtitleParserFactory) subtitleParserFactory).forMatroska()
                    : subtitleParserFactory);
      }
    }
    return extractors;
  }
}
