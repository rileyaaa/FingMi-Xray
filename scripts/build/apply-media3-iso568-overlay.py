#!/usr/bin/env python3
"""Apply the FongMi 5.6.7/5.6.8 native ISO UDF and navigation compatibility overlay."""

from __future__ import annotations

import argparse
from pathlib import Path


OVERLAY_ID = "fongmi-tv-5.6.8-iso-native-navigation-overlay-v2"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one source match, found {text.count(old)}")
    return text.replace(old, new, 1)


def write_native_udf(path: Path) -> None:
    path.write_text(
        """/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.extractor.iso.udf;

import androidx.media3.common.CacheDataReader;
import androidx.media3.extractor.iso.IsoFileEntry;
import java.io.Closeable;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

/** JNI-backed UDF reader carried by FongMi 5.6.7+ release builds. */
final class NativeUdfFileSystem implements Closeable {

  static final class UnsupportedImageException extends IOException {
    UnsupportedImageException(String message) {
      super(message);
    }
  }

  private static final boolean AVAILABLE;

  static {
    boolean available;
    try {
      System.loadLibrary("isoJNI");
      available = true;
    } catch (UnsatisfiedLinkError error) {
      available = false;
    }
    AVAILABLE = available;
  }

  private long nativeHandle;

  NativeUdfFileSystem(CacheDataReader reader) throws IOException {
    if (!AVAILABLE) {
      throw new UnsupportedImageException("ISO native library is unavailable");
    }
    nativeHandle = nativeOpen(reader);
    if (nativeHandle == 0L) {
      throw new IOException("Could not open UDF image");
    }
  }

  IsoFileEntry findFile(String path) throws IOException {
    ensureOpen();
    return nativeFindFile(nativeHandle, path);
  }

  List<String> listFiles(String path) throws IOException {
    ensureOpen();
    return Arrays.asList(nativeListFiles(nativeHandle, path));
  }

  @Override
  public synchronized void close() {
    if (nativeHandle != 0L) {
      nativeClose(nativeHandle);
      nativeHandle = 0L;
    }
  }

  private void ensureOpen() throws IOException {
    if (nativeHandle == 0L) {
      throw new IOException("UDF image is closed");
    }
  }

  private static native long nativeOpen(CacheDataReader reader);

  private static native void nativeClose(long handle);

  private static native IsoFileEntry nativeFindFile(long handle, String path);

  private static native String[] nativeListFiles(long handle, String path);
}
""",
        encoding="utf-8",
    )



def write_navigation_session(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.exoplayer.iso;

import androidx.media3.common.CacheDataReader;
import java.io.Closeable;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/** JNI-compatible disc navigation session used by FongMi 5.6.7+ release builds. */
public final class IsoNavigationSession implements Closeable {

  public static final int DISC_TYPE_DVD = 1;
  public static final int DISC_TYPE_BLURAY = 2;

  public static final int ACTION_UP = 1;
  public static final int ACTION_DOWN = 2;
  public static final int ACTION_LEFT = 3;
  public static final int ACTION_RIGHT = 4;
  public static final int ACTION_SELECT = 5;
  public static final int ACTION_MENU = 6;
  public static final int ACTION_POPUP_MENU = 7;
  public static final int ACTION_PREVIOUS = 8;
  public static final int ACTION_TITLE_MENU = 11;

  private static final int MAX_PUMP_ITERATIONS = 16;
  private static final boolean NATIVE_AVAILABLE;

  static {
    boolean available;
    try {
      System.loadLibrary("isoJNI");
      available = true;
    } catch (UnsatisfiedLinkError error) {
      available = false;
    }
    NATIVE_AVAILABLE = available;
  }

  // These names and primitive types are part of the libisoJNI reverse JNI ABI.
  // Native code mutates them directly, so R8 must keep the complete class unchanged.
  private volatile int discontinuityId;
  private long finiteStillDurationMs;
  private long finiteStillId;
  private volatile boolean infiniteStill;
  private volatile boolean menuActive;
  private volatile int menuDomain;
  private volatile long stateVersion;
  private volatile boolean titleEnded;
  private volatile boolean waitingForDrain;

  private final int discType;
  private final boolean bdj;
  private final boolean hasMenu;
  private final ArrayBlockingQueue<PendingAction> actions = new ArrayBlockingQueue<>(16);
  private final ExecutorService executor;
  private final AtomicBoolean pumpScheduled = new AtomicBoolean();
  private final AtomicLong directAction = new AtomicLong();

  private volatile IOException failure;
  private long nativeHandle;
  private long observedStateVersion = Long.MIN_VALUE;
  private long stateGeneration;
  private PendingAction activeAction;

  public interface ActionCallback {
    void onComplete(boolean handled);
  }

  private static final class PendingAction {
    public final long action;
    public final ActionCallback callback;

    public PendingAction(long action, ActionCallback callback) {
      this.action = action;
      this.callback = callback;
    }
  }

  public static boolean isNativeAvailable() {
    return NATIVE_AVAILABLE;
  }

  public static IsoNavigationSession open(CacheDataReader reader) throws IOException {
    if (!NATIVE_AVAILABLE) {
      return null;
    }
    return new IsoNavigationSession(reader);
  }

  public IsoNavigationSession(CacheDataReader reader) throws IOException {
    if (!NATIVE_AVAILABLE) {
      throw new IOException("Disc navigation native library is unavailable");
    }
    executor =
        Executors.newSingleThreadExecutor(
            new ThreadFactory() {
              @Override
              public Thread newThread(Runnable runnable) {
                Thread thread = new Thread(runnable, "Media3-IsoNavigation");
                thread.setDaemon(true);
                return thread;
              }
            });
    nativeHandle = nativeOpen(reader, this, 0);
    if (nativeHandle == 0L) {
      executor.shutdownNow();
      throw new IOException("Could not open disc navigation session");
    }
    discType = nativeGetDiscType(nativeHandle);
    bdj = nativeIsBdj(nativeHandle);
    hasMenu = nativeHasMenu(nativeHandle);
    refreshStateLocked();
  }

  private static native void nativeClose(long handle);

  private static native boolean nativeCopyHdmvMenuOverlay(
      long handle, int overlayId, int[] pixels);

  public static native boolean nativeDisableSubtitles(long handle);

  private static native long[] nativeGetChapterTimesUs(long handle, int titleIndex);

  private static native long[][] nativeGetClipInfo(long handle, int clipIndex);

  private static native String[] nativeGetClipNames(long handle, int titleIndex);

  private static native long[] nativeGetClipTimesUs(long handle, int titleIndex);

  private static native int nativeGetCurrentClipIndex(long handle);

  private static native int nativeGetCurrentTitleIndex(long handle);

  private static native int nativeGetDiscType(long handle);

  private static native int[] nativeGetDvdMenuHighlight(long handle);

  private static native int[] nativeGetHdmvMenuOverlayInfo(long handle, int lastOverlayId);

  private static native int nativeGetReadPlayItemIndex(long handle);

  private static native long nativeGetReadPlayItemStartTimeUs(long handle);

  private static native long nativeGetSegmentStartTimeUs(long handle);

  private static native int nativeGetSelectedTrackIndex(long handle, boolean subtitle);

  private static native int nativeGetTitleCount(long handle);

  private static native long[] nativeGetTitleInfo(long handle, int titleIndex);

  private static native String[] nativeGetTrackInfo(
      long handle, int titleIndex, boolean subtitle, int clipIndex);

  private static native long nativeGetWaitTimeoutMs(long handle);

  private static native boolean nativeHasMenu(long handle);

  private static native boolean nativeIsBdj(long handle);

  private static native long nativeOpen(
      CacheDataReader reader, IsoNavigationSession session, int navigationFlags);

  private static native int nativePump(long handle);

  private static native int nativeRead(
      long handle, byte[] buffer, int offset, int length, int readFlags);

  private static native boolean nativeResumeBlurayPlaylist(
      long handle, int discontinuityId);

  private static native boolean nativeResumeDvdWait(long handle, int discontinuityId);

  public static native boolean nativeSeekToChapter(long handle, int chapterIndex);

  public static native boolean nativeSeekToTimeUs(long handle, long timeUs);

  public static native boolean nativeSelectTitle(long handle, int titleIndex);

  private static native boolean nativeSelectTrack(
      long handle, boolean subtitle, int trackIndex);

  private static native boolean nativeSkipFiniteStill(
      long handle, int discontinuityId, long stillId);

  // libisoJNI looks this up by exact name/signature and calls it from nativePump().
  private long pollAction() {
    PendingAction action = actions.poll();
    activeAction = action;
    return action != null ? action.action : directAction.getAndSet(0L);
  }

  public int getDiscType() {
    return discType;
  }

  public boolean isBdj() {
    return bdj;
  }

  public boolean hasMenu() {
    return hasMenu;
  }

  public boolean isMenuActive() {
    return menuActive;
  }

  public int getMenuDomain() {
    return menuDomain;
  }

  public boolean isInfiniteStill() {
    return infiniteStill;
  }

  public boolean isTitleEnded() {
    return titleEnded;
  }

  public boolean isWaitingForDrain() {
    return waitingForDrain;
  }

  public int getDiscontinuityId() {
    return discontinuityId;
  }

  public long getStateVersion() {
    return stateVersion;
  }

  public long getStateGeneration() {
    synchronized (this) {
      return stateGeneration;
    }
  }

  public long getFiniteStillId() {
    synchronized (this) {
      return finiteStillId;
    }
  }

  public long getFiniteStillDurationMs() {
    synchronized (this) {
      return finiteStillDurationMs;
    }
  }

  public boolean dispatchAction(int action) {
    return dispatchAction(action, null);
  }

  public boolean dispatchAction(int action, ActionCallback callback) {
    if (!isSupportedAction(action) || !hasMenu || nativeHandle == 0L) {
      return false;
    }
    if (!actions.offer(new PendingAction(action, callback))) {
      return false;
    }
    schedulePump();
    return true;
  }

  public synchronized int read(byte[] buffer, int offset, int length, int readFlags)
      throws IOException {
    ensureOpenLocked();
    if (offset < 0 || length < 0 || offset > buffer.length - length) {
      throw new IndexOutOfBoundsException();
    }
    if (length == 0) {
      return 0;
    }
    throwFailureLocked();
    int result = nativeRead(nativeHandle, buffer, offset, length, readFlags);
    refreshStateLocked();
    if (hasPendingActions()) {
      schedulePump();
    }
    return result;
  }

  public synchronized int getCurrentTitleIndex() throws IOException {
    ensureHealthyLocked();
    return nativeGetCurrentTitleIndex(nativeHandle);
  }

  public synchronized int getCurrentClipIndex() throws IOException {
    ensureHealthyLocked();
    return nativeGetCurrentClipIndex(nativeHandle);
  }

  public synchronized long getSegmentStartTimeUs() throws IOException {
    ensureHealthyLocked();
    return nativeGetSegmentStartTimeUs(nativeHandle);
  }

  public synchronized int getReadPlayItemIndex() throws IOException {
    ensureHealthyLocked();
    return nativeGetReadPlayItemIndex(nativeHandle);
  }

  public synchronized long getReadPlayItemStartTimeUs() throws IOException {
    ensureHealthyLocked();
    return nativeGetReadPlayItemStartTimeUs(nativeHandle);
  }

  public synchronized int getTitleCount() throws IOException {
    ensureHealthyLocked();
    return nativeGetTitleCount(nativeHandle);
  }

  public synchronized long[] getTitleInfo(int titleIndex) throws IOException {
    ensureHealthyLocked();
    return nativeGetTitleInfo(nativeHandle, titleIndex);
  }

  public synchronized long[] getChapterTimesUs(int titleIndex) throws IOException {
    ensureHealthyLocked();
    return nativeGetChapterTimesUs(nativeHandle, titleIndex);
  }

  public synchronized String[] getClipNames(int titleIndex) throws IOException {
    ensureHealthyLocked();
    return nativeGetClipNames(nativeHandle, titleIndex);
  }

  public synchronized long[] getClipTimesUs(int titleIndex) throws IOException {
    ensureHealthyLocked();
    return nativeGetClipTimesUs(nativeHandle, titleIndex);
  }

  public synchronized long[][] getClipInfo(int clipIndex) throws IOException {
    ensureHealthyLocked();
    return nativeGetClipInfo(nativeHandle, clipIndex);
  }

  public synchronized String[] getTrackInfo(
      int titleIndex, boolean subtitle, int clipIndex) throws IOException {
    ensureHealthyLocked();
    return nativeGetTrackInfo(nativeHandle, titleIndex, subtitle, clipIndex);
  }

  public synchronized int getSelectedTrackIndex(boolean subtitle) throws IOException {
    ensureHealthyLocked();
    return nativeGetSelectedTrackIndex(nativeHandle, subtitle);
  }

  public synchronized int[] getDvdMenuHighlight() throws IOException {
    ensureHealthyLocked();
    return nativeGetDvdMenuHighlight(nativeHandle);
  }

  public synchronized int[] getHdmvMenuOverlayInfo(int lastOverlayId) throws IOException {
    ensureHealthyLocked();
    return nativeGetHdmvMenuOverlayInfo(nativeHandle, lastOverlayId);
  }

  public synchronized boolean copyHdmvMenuOverlay(int overlayId, int[] pixels)
      throws IOException {
    ensureHealthyLocked();
    return nativeCopyHdmvMenuOverlay(nativeHandle, overlayId, pixels);
  }

  public synchronized boolean selectTitle(int titleIndex) throws IOException {
    ensureHealthyLocked();
    boolean changed = nativeSelectTitle(nativeHandle, titleIndex);
    refreshStateLocked();
    return changed;
  }

  public synchronized boolean seekToChapter(int chapterIndex) throws IOException {
    ensureHealthyLocked();
    boolean changed = nativeSeekToChapter(nativeHandle, chapterIndex);
    refreshStateLocked();
    return changed;
  }

  public synchronized boolean seekToTimeUs(long timeUs) throws IOException {
    ensureHealthyLocked();
    boolean changed = nativeSeekToTimeUs(nativeHandle, timeUs);
    refreshStateLocked();
    return changed;
  }

  public synchronized boolean selectTrack(boolean subtitle, int trackIndex) throws IOException {
    ensureHealthyLocked();
    boolean changed = nativeSelectTrack(nativeHandle, subtitle, trackIndex);
    refreshStateLocked();
    return changed;
  }

  public synchronized boolean disableSubtitles() throws IOException {
    ensureHealthyLocked();
    boolean changed = nativeDisableSubtitles(nativeHandle);
    refreshStateLocked();
    return changed;
  }

  public synchronized boolean resumeNavigation(int expectedDiscontinuityId) throws IOException {
    ensureHealthyLocked();
    boolean resumed =
        discType == DISC_TYPE_DVD
            ? nativeResumeDvdWait(nativeHandle, expectedDiscontinuityId)
            : nativeResumeBlurayPlaylist(nativeHandle, expectedDiscontinuityId);
    refreshStateLocked();
    if (resumed && hasPendingActions()) {
      schedulePump();
    }
    return resumed;
  }

  public synchronized boolean skipFiniteStill() throws IOException {
    ensureHealthyLocked();
    if (finiteStillDurationMs <= 0L) {
      return false;
    }
    boolean skipped = nativeSkipFiniteStill(nativeHandle, discontinuityId, finiteStillId);
    refreshStateLocked();
    return skipped;
  }

  public synchronized void waitForStateChange(long observedGeneration) throws IOException {
    if (stateGeneration != observedGeneration) {
      return;
    }
    ensureHealthyLocked();
    long timeoutMs = nativeGetWaitTimeoutMs(nativeHandle);
    try {
      if (timeoutMs < 0L) {
        wait();
      } else {
        wait(Math.max(1L, timeoutMs));
      }
    } catch (InterruptedException error) {
      Thread.currentThread().interrupt();
      throw new InterruptedIOException("Disc navigation read interrupted");
    }
    ensureHealthyLocked();
  }

  @Override
  public synchronized void close() {
    executor.shutdownNow();
    if (nativeHandle != 0L) {
      nativeClose(nativeHandle);
      nativeHandle = 0L;
    }
    actions.clear();
    directAction.set(0L);
    activeAction = null;
    waitingForDrain = false;
    titleEnded = false;
    menuActive = false;
    menuDomain = 0;
    stateGeneration++;
    notifyAll();
  }

  private void schedulePump() {
    if (failure != null || nativeHandle == 0L || !pumpScheduled.compareAndSet(false, true)) {
      return;
    }
    try {
      executor.execute(
          new Runnable() {
            @Override
            public void run() {
              pumpLoop();
            }
          });
    } catch (RejectedExecutionException error) {
      pumpScheduled.set(false);
    }
  }

  private void pumpLoop() {
    try {
      for (int i = 0; i < MAX_PUMP_ITERATIONS; i++) {
        PendingAction completed;
        int result;
        synchronized (this) {
          if (nativeHandle == 0L || failure != null || (i > 0 && !hasPendingActions())) {
            break;
          }
          activeAction = null;
          result = pumpNativeLocked();
          refreshStateLocked();
          completed = activeAction;
          activeAction = null;
        }
        if (completed != null && completed.callback != null) {
          completed.callback.onComplete(result > 0);
        }
      }
    } catch (IOException error) {
      synchronized (this) {
        failure = error;
        stateGeneration++;
        notifyAll();
      }
    } finally {
      pumpScheduled.set(false);
      if (nativeHandle != 0L && failure == null && hasPendingActions()) {
        schedulePump();
      }
    }
  }

  private int pumpNativeLocked() throws IOException {
    return nativePump(nativeHandle);
  }

  private boolean hasPendingActions() {
    return !actions.isEmpty() || directAction.get() != 0L;
  }

  private static boolean isSupportedAction(int action) {
    return (action >= ACTION_UP && action <= ACTION_PREVIOUS) || action == ACTION_TITLE_MENU;
  }

  private void refreshStateLocked() {
    long currentVersion = stateVersion;
    if (observedStateVersion != currentVersion) {
      observedStateVersion = currentVersion;
      stateGeneration++;
      notifyAll();
    }
  }

  private void ensureOpenLocked() throws IOException {
    if (nativeHandle == 0L) {
      throw new IOException("Disc navigation session is closed");
    }
  }

  private void throwFailureLocked() throws IOException {
    if (failure != null) {
      throw failure;
    }
  }

  private void ensureHealthyLocked() throws IOException {
    ensureOpenLocked();
    throwFailureLocked();
  }
}
""",
        encoding="utf-8",
    )


def patch_navigation_keep_rules(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    marker = "-keep class androidx.media3.exoplayer.iso.IsoNavigationSession { *; }"
    if marker in text:
        raise SystemExit("IsoNavigationSession keep rule unexpectedly already exists in pinned source")
    text = (
        text.rstrip()
        + """

# libisoJNI performs reverse JNI lookups against exact IsoNavigationSession
# field/method names. Keep the complete class, not only native declarations.
-keep class androidx.media3.exoplayer.iso.IsoNavigationSession { *; }
"""
    )
    path.write_text(text, encoding="utf-8")


def patch_udf(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import java.io.IOException;\n",
        "import java.io.Closeable;\nimport java.io.IOException;\n",
        "UdfFileSystem Closeable import",
    )
    text = replace_once(
        text,
        "public final class UdfFileSystem {\n",
        "public final class UdfFileSystem implements Closeable {\n",
        "UdfFileSystem Closeable declaration",
    )
    text = replace_once(
        text,
        "  private CacheDataReader reader;\n",
        "  private CacheDataReader reader;\n"
        "  @Nullable private NativeUdfFileSystem nativeFileSystem;\n"
        "  private boolean javaFallbackOpened;\n",
        "UdfFileSystem native state",
    )
    text = replace_once(
        text,
        "  public void open(CacheDataReader reader) throws IOException {\n"
        "    this.reader = reader;\n"
        "    findFsdAndPartitionBase();\n"
        "  }\n",
        "  public void open(CacheDataReader reader) throws IOException {\n"
        "    close();\n"
        "    this.reader = reader;\n"
        "    javaFallbackOpened = false;\n"
        "    try {\n"
        "      nativeFileSystem = new NativeUdfFileSystem(reader);\n"
        "    } catch (NativeUdfFileSystem.UnsupportedImageException error) {\n"
        "      nativeFileSystem = null;\n"
        "      openJavaFallback();\n"
        "    }\n"
        "  }\n",
        "UdfFileSystem native-first open",
    )
    text = replace_once(
        text,
        "  public IsoFileEntry findFile(String path) throws IOException {\n",
        "  public IsoFileEntry findFile(String path) throws IOException {\n"
        "    if (nativeFileSystem != null) {\n"
        "      try {\n"
        "        return nativeFileSystem.findFile(path);\n"
        "      } catch (NativeUdfFileSystem.UnsupportedImageException error) {\n"
        "        disableNativeAndOpenJava();\n"
        "      }\n"
        "    }\n"
        "    openJavaFallback();\n",
        "UdfFileSystem native find",
    )
    text = replace_once(
        text,
        "  public List<String> listFiles(String dirPath) throws IOException {\n",
        "  public List<String> listFiles(String dirPath) throws IOException {\n"
        "    if (nativeFileSystem != null) {\n"
        "      try {\n"
        "        return nativeFileSystem.listFiles(dirPath);\n"
        "      } catch (NativeUdfFileSystem.UnsupportedImageException error) {\n"
        "        disableNativeAndOpenJava();\n"
        "      }\n"
        "    }\n"
        "    openJavaFallback();\n",
        "UdfFileSystem native list",
    )
    anchor = "  private void findFsdAndPartitionBase() throws IOException {\n"
    helpers = """  @Override
  public void close() {
    if (nativeFileSystem != null) {
      nativeFileSystem.close();
      nativeFileSystem = null;
    }
    javaFallbackOpened = false;
  }

  private void disableNativeAndOpenJava() throws IOException {
    if (nativeFileSystem != null) {
      nativeFileSystem.close();
      nativeFileSystem = null;
    }
    openJavaFallback();
  }

  private void openJavaFallback() throws IOException {
    if (!javaFallbackOpened) {
      findFsdAndPartitionBase();
      javaFallbackOpened = true;
    }
  }

"""
    text = replace_once(text, anchor, helpers + anchor, "UdfFileSystem fallback helpers")
    path.write_text(text, encoding="utf-8")


def patch_iso_parsed_media(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  public void close() {\n"
        "    isoReader.close();\n"
        "  }\n",
        "  public void close() {\n"
        "    if (udf != null) {\n"
        "      udf.close();\n"
        "    }\n"
        "    isoReader.close();\n"
        "  }\n",
        "IsoParsedMedia native UDF close",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    root = args.source.resolve()

    udf_dir = root / "libraries/extractor/src/main/java/androidx/media3/extractor/iso/udf"
    native_path = udf_dir / "NativeUdfFileSystem.java"
    udf_path = udf_dir / "UdfFileSystem.java"
    parsed_path = (
        root
        / "libraries/exoplayer/src/main/java/androidx/media3/exoplayer/source/iso/IsoParsedMedia.java"
    )
    navigation_path = (
        root
        / "libraries/exoplayer/src/main/java/androidx/media3/exoplayer/iso/IsoNavigationSession.java"
    )
    exoplayer_proguard = root / "libraries/exoplayer/proguard-rules.txt"

    for required in (udf_path, parsed_path, exoplayer_proguard):
      if not required.is_file():
        raise SystemExit(f"missing pinned media source file: {required}")

    write_native_udf(native_path)
    write_navigation_session(navigation_path)
    patch_udf(udf_path)
    patch_iso_parsed_media(parsed_path)
    patch_navigation_keep_rules(exoplayer_proguard)
    print(f"Applied {OVERLAY_ID}")


if __name__ == "__main__":
    main()
