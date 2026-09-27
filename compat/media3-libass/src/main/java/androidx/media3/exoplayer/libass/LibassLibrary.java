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

import androidx.media3.common.MediaLibraryInfo;
import androidx.media3.common.util.LibraryLoader;
import androidx.media3.common.util.UnstableApi;

/**
 * Configures and queries the underlying libass JNI library.
 * Historical upstream API retained; published 5.6.5 ok1/nk1 confirms the Media3
 * LibraryLoader, media3ass name and module registration. Enablement setters are
 * retained compatibility API, not claimed as surviving public methods in that DEX.
 */
@UnstableApi
public final class LibassLibrary {

  private static volatile boolean enabled = true;

  private static final LibraryLoader LOADER =
      new LibraryLoader("media3ass") {
        @Override
        protected void loadLibrary(String name) {
          System.loadLibrary(name);
        }
      };

  static {
    MediaLibraryInfo.registerModule("media3.exoplayer.libass");
  }

  /**
   * Overrides the names of the native libraries.
   *
   * <p>This method must be called before any other method in this class or before creating a {@link
   * LibassTrack}.
   */
  public static void setLibraries(String... libraries) {
    LOADER.setLibraries(libraries);
  }

  /**
   * Enables or disables libass for subsequently created playback sessions.
   *
   * <p>Disabling libass prevents the native library from being loaded. Existing tracks and media
   * states keep the setting that was captured when their playback session was created.
   */
  public static void setEnabled(boolean enabled) {
    LibassLibrary.enabled = enabled;
  }

  /** Returns whether libass is enabled for subsequently created playback sessions. */
  public static boolean isEnabled() {
    return enabled;
  }

  /** Returns whether libass is enabled and its native library is available. */
  public static boolean isAvailable() {
    return enabled && isNativeAvailable();
  }

  static boolean isNativeAvailable() {
    return LOADER.isAvailable();
  }

  private LibassLibrary() {}
}
