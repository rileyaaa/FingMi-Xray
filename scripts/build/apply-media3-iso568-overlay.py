#!/usr/bin/env python3
"""Apply the FongMi 5.6.7/5.6.8 native ISO UDF and navigation compatibility overlay."""

from __future__ import annotations

import argparse
from pathlib import Path


OVERLAY_ID = "fongmi-tv-5.6.8-iso-navigation-stream-overlay-v4"


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

  public synchronized int read(byte[] buffer, int offset, int length, int expectedDiscontinuityId)
      throws IOException {
    ensureOpenLocked();
    if (offset < 0 || length < 0 || offset > buffer.length - length) {
      throw new IndexOutOfBoundsException();
    }
    if (length == 0) {
      return 0;
    }
    throwFailureLocked();
    int result = nativeRead(nativeHandle, buffer, offset, length, expectedDiscontinuityId);
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
    signalStateChangeLocked();
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
    signalStateChangeLocked();
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
          signalStateChangeLocked();
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
      signalStateChangeLocked();
    }
  }

  private void signalStateChangeLocked() {
    stateGeneration++;
    notifyAll();
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



def write_navigation_data_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.exoplayer.source.iso;

import android.net.Uri;
import androidx.annotation.Nullable;
import androidx.media3.common.C;
import androidx.media3.common.PlaybackException;
import androidx.media3.datasource.BaseDataSource;
import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DataSourceException;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.IsoDataReader;
import androidx.media3.exoplayer.iso.IsoNavigationSession;
import java.io.ByteArrayOutputStream;
import java.io.Closeable;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * DataSource backed by the 5.6.8 disc-navigation JNI stream.
 *
 * <p>The native reader uses -2 for "wait for navigation state", -4 for "the expected
 * discontinuity was replaced", and -5 for end of the current navigation segment. The final
 * nativeRead argument is the expected discontinuity id, or -1 until the first segment is
 * established.
 */
public final class IsoNavigationDataSource extends BaseDataSource {

  private static final int RESULT_WAIT_FOR_STATE = -2;
  private static final int RESULT_SEGMENT_REPLACED = -4;
  private static final int RESULT_SEGMENT_END = -5;

  private final Factory factory;

  @Nullable private IsoNavigationSession session;
  @Nullable private Uri uri;
  @Nullable private byte[] replay;
  private int replayPosition;
  private long bytesRemaining;
  private int segmentId;
  private boolean opened;

  private IsoNavigationDataSource(Factory factory) {
    super(false);
    this.factory = factory;
  }

  @Override
  public long open(DataSpec dataSpec) throws IOException {
    transferInitializing(dataSpec);
    Factory.Binding binding = factory.bind(dataSpec.uri);
    session = binding.session;
    segmentId = binding.segmentId;
    uri = dataSpec.uri;
    replay = binding.replay;

    if (replay != null) {
      if (dataSpec.position > replay.length) {
        throw new DataSourceException(PlaybackException.ERROR_CODE_IO_READ_POSITION_OUT_OF_RANGE);
      }
      replayPosition = (int) dataSpec.position;
      long available = replay.length - replayPosition;
      bytesRemaining =
          dataSpec.length == C.LENGTH_UNSET ? available : Math.min(dataSpec.length, available);
    } else {
      if (dataSpec.position != 0) {
        throw new DataSourceException(PlaybackException.ERROR_CODE_IO_READ_POSITION_OUT_OF_RANGE);
      }
      replayPosition = 0;
      bytesRemaining = dataSpec.length;
    }

    opened = true;
    transferStarted(dataSpec);
    return bytesRemaining;
  }

  @Override
  public int read(byte[] buffer, int offset, int length) throws IOException {
    if (length == 0) {
      return 0;
    }
    if (bytesRemaining == 0) {
      return C.RESULT_END_OF_INPUT;
    }

    byte[] completedReplay = replay;
    if (completedReplay != null) {
      int available = completedReplay.length - replayPosition;
      int toRead =
          (int)
              Math.min(
                  Math.min((long) length, available),
                  bytesRemaining == C.LENGTH_UNSET ? Long.MAX_VALUE : bytesRemaining);
      if (toRead <= 0) {
        return C.RESULT_END_OF_INPUT;
      }
      System.arraycopy(completedReplay, replayPosition, buffer, offset, toRead);
      replayPosition += toRead;
      if (bytesRemaining != C.LENGTH_UNSET) {
        bytesRemaining -= toRead;
      }
      bytesTransferred(toRead);
      return toRead;
    }

    IsoNavigationSession active = session;
    if (active == null) {
      throw new IOException("Disc navigation data source is closed");
    }

    int requested =
        (int)
            Math.min(
                (long) length,
                bytesRemaining == C.LENGTH_UNSET ? (long) length : bytesRemaining);
    while (true) {
      boolean established = factory.isSegmentEstablished();
      if (established && active.getDiscontinuityId() != segmentId) {
        throw new SegmentChangedException(segmentId, active.getDiscontinuityId());
      }

      long observedGeneration = active.getStateGeneration();
      int expectedDiscontinuityId = established ? segmentId : C.INDEX_UNSET;
      int result =
          active.read(buffer, offset, requested, expectedDiscontinuityId);
      int currentSegmentId = active.getDiscontinuityId();
      boolean menuActive = active.isMenuActive();

      if (!established) {
        segmentId = currentSegmentId;
        if (result > 0 || menuActive || result == RESULT_SEGMENT_END) {
          factory.establishSegment(currentSegmentId);
          established = true;
        }
      }

      if (result == RESULT_WAIT_FOR_STATE) {
        active.waitForStateChange(observedGeneration);
        continue;
      }
      if (result == RESULT_SEGMENT_REPLACED) {
        throw new SegmentChangedException(segmentId, currentSegmentId);
      }
      if (result == RESULT_SEGMENT_END || result == C.RESULT_END_OF_INPUT) {
        factory.finishSegment(segmentId, menuActive);
        return C.RESULT_END_OF_INPUT;
      }
      if (result < 0) {
        throw new IOException("Unexpected disc navigation read result: " + result);
      }
      if (result == 0) {
        throw new IOException("Disc navigation native reader made no progress");
      }

      factory.capture(segmentId, menuActive, buffer, offset, result);
      if (bytesRemaining != C.LENGTH_UNSET) {
        bytesRemaining -= result;
      }
      bytesTransferred(result);
      return result;
    }
  }

  @Nullable
  @Override
  public Uri getUri() {
    return uri;
  }

  @Override
  public Map<String, List<String>> getResponseHeaders() {
    return Collections.emptyMap();
  }

  @Override
  public void close() {
    session = null;
    uri = null;
    replay = null;
    replayPosition = 0;
    bytesRemaining = 0;
    if (opened) {
      opened = false;
      transferEnded();
    }
  }

  public static final class SegmentChangedException extends InterruptedIOException {
    public final int expectedDiscontinuityId;
    public final int actualDiscontinuityId;

    SegmentChangedException(int expectedDiscontinuityId, int actualDiscontinuityId) {
      super(
          "Disc navigation segment replaced: expected "
              + expectedDiscontinuityId
              + ", actual "
              + actualDiscontinuityId);
      this.expectedDiscontinuityId = expectedDiscontinuityId;
      this.actualDiscontinuityId = actualDiscontinuityId;
    }
  }

  /** Shared owner for all DataSource instances of one navigation MediaSource. */
  public static final class Factory implements DataSource.Factory, Closeable {

    private static final int MAX_MENU_REPLAY_BYTES = 64 * 1024 * 1024;

    private final DataSource.Factory upstreamFactory;
    private final int initialMenuAction;

    @Nullable private IsoDataReader reader;
    @Nullable private IsoNavigationSession session;
    @Nullable private Uri isoUri;
    @Nullable private ByteArrayOutputStream capture;
    @Nullable private byte[] replay;
    private int captureSegmentId = C.INDEX_UNSET;
    private int replaySegmentId = C.INDEX_UNSET;
    private int segmentId = C.INDEX_UNSET;
    private boolean captureDisabled;
    private boolean segmentEstablished;
    private boolean closed;

    public Factory(DataSource.Factory upstreamFactory, int initialMenuAction) {
      if (initialMenuAction != IsoNavigationSession.ACTION_MENU
          && initialMenuAction != IsoNavigationSession.ACTION_POPUP_MENU
          && initialMenuAction != IsoNavigationSession.ACTION_TITLE_MENU) {
        throw new IllegalArgumentException("Unsupported initial disc menu action");
      }
      this.upstreamFactory = upstreamFactory;
      this.initialMenuAction = initialMenuAction;
    }

    @Override
    public DataSource createDataSource() {
      return new IsoNavigationDataSource(this);
    }

    @Nullable
    public synchronized IsoNavigationSession getSession() {
      return session;
    }

    public synchronized boolean isSegmentEstablished() {
      return segmentEstablished;
    }

    private synchronized Binding bind(Uri requestedUri) throws IOException {
      if (closed) {
        throw new IOException("Disc navigation source is closed");
      }
      Uri normalized =
          requestedUri.getFragment() == null
              ? requestedUri
              : requestedUri.buildUpon().fragment(null).build();
      if (session == null) {
        IsoDataReader newReader = new IsoDataReader(upstreamFactory, normalized);
        IsoNavigationSession newSession = null;
        try {
          newSession = IsoNavigationSession.open(newReader);
          if (newSession == null) {
            throw new IOException("Disc navigation native library is unavailable");
          }
          // Force the title table to be readable before exposing the shared session.
          newSession.getTitleCount();
          reader = newReader;
          session = newSession;
          isoUri = normalized;
          segmentId = newSession.getDiscontinuityId();
          if (newSession.hasMenu()) {
            newSession.dispatchAction(initialMenuAction);
          }
        } catch (IOException | RuntimeException error) {
          newReader.close();
          if (newSession != null) {
            newSession.close();
          }
          throw error;
        }
      } else if (!normalized.equals(isoUri)) {
        throw new IOException("Disc navigation session cannot switch ISO files");
      }

      IsoNavigationSession active = session;
      if (active == null) {
        throw new IOException("Disc navigation source is closed");
      }
      int current = active.getDiscontinuityId();
      if (segmentEstablished && current != segmentId) {
        resetForSegment(current);
      } else if (!segmentEstablished) {
        segmentId = current;
      }
      byte[] completedReplay =
          replay != null && replaySegmentId == segmentId
              ? Arrays.copyOf(replay, replay.length)
              : null;
      return new Binding(active, segmentId, completedReplay);
    }

    private synchronized void establishSegment(int id) {
      if (!segmentEstablished || segmentId != id) {
        resetForSegment(id);
      }
      segmentEstablished = true;
    }

    private synchronized void capture(
        int id, boolean menuActive, byte[] buffer, int offset, int length) {
      if (!menuActive || length <= 0) {
        return;
      }
      if (captureSegmentId != id) {
        captureSegmentId = id;
        capture = null;
        captureDisabled = false;
      }
      if (captureDisabled) {
        return;
      }
      if (capture == null) {
        capture = new ByteArrayOutputStream(Math.min(length, 65536));
      }
      if (capture.size() > MAX_MENU_REPLAY_BYTES - length) {
        capture = null;
        captureDisabled = true;
        return;
      }
      capture.write(buffer, offset, length);
    }

    private synchronized void finishSegment(int id, boolean menuActive) {
      if (menuActive
          && id == captureSegmentId
          && !captureDisabled
          && capture != null
          && capture.size() > 0) {
        replay = capture.toByteArray();
        replaySegmentId = id;
      }
      capture = null;
      captureDisabled = false;
    }

    private void resetForSegment(int id) {
      segmentId = id;
      segmentEstablished = false;
      captureSegmentId = C.INDEX_UNSET;
      replaySegmentId = C.INDEX_UNSET;
      capture = null;
      replay = null;
      captureDisabled = false;
    }

    @Override
    public synchronized void close() {
      closed = true;
      IsoNavigationSession oldSession = session;
      IsoDataReader oldReader = reader;
      session = null;
      reader = null;
      isoUri = null;
      resetForSegment(C.INDEX_UNSET);
      if (oldSession != null) {
        oldSession.close();
      }
      if (oldReader != null) {
        oldReader.close();
      }
    }

    private static final class Binding {
      public final IsoNavigationSession session;
      public final int segmentId;
      @Nullable public final byte[] replay;

      Binding(IsoNavigationSession session, int segmentId, @Nullable byte[] replay) {
        this.session = session;
        this.segmentId = segmentId;
        this.replay = replay;
      }
    }
  }
}
""",
        encoding="utf-8",
    )


def write_navigation_media_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.exoplayer.source.iso;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.Timeline;
import androidx.media3.datasource.DataSource;
import androidx.media3.exoplayer.drm.DrmSessionManagerProvider;
import androidx.media3.exoplayer.iso.IsoNavigationSession;
import androidx.media3.exoplayer.source.CompositeMediaSource;
import androidx.media3.exoplayer.source.MediaPeriod;
import androidx.media3.exoplayer.source.MediaSource;
import androidx.media3.exoplayer.source.ProgressiveMediaSource;
import androidx.media3.exoplayer.upstream.Allocator;
import androidx.media3.exoplayer.upstream.DefaultLoadErrorHandlingPolicy;
import androidx.media3.exoplayer.upstream.LoadErrorHandlingPolicy;
import androidx.media3.extractor.Extractor;
import androidx.media3.extractor.ExtractorsFactory;
import androidx.media3.extractor.iso.bdmv.BdmvTsExtractor;
import androidx.media3.extractor.ts.PsExtractor;
import java.io.IOException;

/**
 * One navigation segment backed by {@link IsoNavigationDataSource}.
 *
 * <p>The controller is intentionally separate: when the shared session advances its
 * discontinuity id, the controller replaces this source with a new instance while keeping the
 * same {@link IsoNavigationDataSource.Factory}. That matches the 5.6.8 segmented navigation
 * model without folding player policy into the JNI transport.
 */
public final class IsoNavigationMediaSource extends CompositeMediaSource<Void> {

  private final MediaItem mediaItem;
  private final IsoNavigationDataSource.Factory navigationFactory;
  private final MediaSource childSource;

  private IsoNavigationMediaSource(
      MediaItem mediaItem,
      DataSource.Factory upstreamFactory,
      int initialMenuAction,
      LoadErrorHandlingPolicy loadErrorHandlingPolicy) {
    this.mediaItem = mediaItem;
    navigationFactory = new IsoNavigationDataSource.Factory(upstreamFactory, initialMenuAction);
    ExtractorsFactory extractorsFactory =
        () -> {
          IsoNavigationSession session = navigationFactory.getSession();
          if (session != null) {
            if (session.getDiscType() == IsoNavigationSession.DISC_TYPE_DVD) {
              return new Extractor[] {new PsExtractor()};
            }
            if (session.getDiscType() == IsoNavigationSession.DISC_TYPE_BLURAY) {
              return new Extractor[] {
                new BdmvTsExtractor(
                    /* clipInfo= */ null,
                    /* startM2ts= */ 0L,
                    /* inTimeTicks= */ 0L,
                    C.TIME_UNSET)
              };
            }
          }
          return new Extractor[] {
            new PsExtractor(),
            new BdmvTsExtractor(
                /* clipInfo= */ null,
                /* startM2ts= */ 0L,
                /* inTimeTicks= */ 0L,
                C.TIME_UNSET)
          };
        };
    ProgressiveMediaSource.Factory progressiveFactory =
        new ProgressiveMediaSource.Factory(navigationFactory, extractorsFactory);
    progressiveFactory.setLoadErrorHandlingPolicy(loadErrorHandlingPolicy);
    childSource = progressiveFactory.createMediaSource(mediaItem);
  }

  @Nullable
  public IsoNavigationSession getNavigationSession() {
    return navigationFactory.getSession();
  }

  public boolean dispatchMenuAction(int action) {
    IsoNavigationSession session = navigationFactory.getSession();
    return session != null && session.dispatchAction(action);
  }

  @NonNull
  @Override
  public MediaItem getMediaItem() {
    return mediaItem;
  }

  @Override
  protected void prepareSourceInternal(@Nullable androidx.media3.datasource.TransferListener listener) {
    super.prepareSourceInternal(listener);
    prepareChildSource(null, childSource);
  }

  @Override
  protected void onChildSourceInfoRefreshed(
      Void id, @NonNull MediaSource mediaSource, @NonNull Timeline timeline) {
    refreshSourceInfo(timeline);
  }

  @NonNull
  @Override
  public MediaPeriod createPeriod(
      @NonNull MediaPeriodId id, @NonNull Allocator allocator, long startPositionUs) {
    return childSource.createPeriod(id, allocator, startPositionUs);
  }

  @Override
  public void releasePeriod(@NonNull MediaPeriod mediaPeriod) {
    childSource.releasePeriod(mediaPeriod);
  }

  @Override
  protected void releaseSourceInternal() {
    super.releaseSourceInternal();
    navigationFactory.close();
  }

  public static final class Factory implements MediaSource.Factory {

    private final DataSource.Factory upstreamFactory;
    private final int initialMenuAction;
    private LoadErrorHandlingPolicy loadErrorHandlingPolicy;

    public Factory(DataSource.Factory upstreamFactory, int initialMenuAction) {
      this.upstreamFactory = upstreamFactory;
      this.initialMenuAction = initialMenuAction;
      loadErrorHandlingPolicy = new DefaultLoadErrorHandlingPolicy();
    }

    @NonNull
    @Override
    public MediaSource createMediaSource(@NonNull MediaItem mediaItem) {
      return new IsoNavigationMediaSource(
          mediaItem, upstreamFactory, initialMenuAction, loadErrorHandlingPolicy);
    }

    @NonNull
    @Override
    public MediaSource.Factory setDrmSessionManagerProvider(
        @NonNull DrmSessionManagerProvider drmSessionManagerProvider) {
      return this;
    }

    @NonNull
    @Override
    public MediaSource.Factory setLoadErrorHandlingPolicy(
        @NonNull LoadErrorHandlingPolicy loadErrorHandlingPolicy) {
      this.loadErrorHandlingPolicy = loadErrorHandlingPolicy;
      return this;
    }

    @NonNull
    @Override
    public @C.ContentType int[] getSupportedTypes() {
      return new int[] {C.CONTENT_TYPE_OTHER};
    }
  }
}
""",
        encoding="utf-8",
    )




def patch_ts_extractor_navigation_timestamp_hook(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  private final TsDurationReader durationReader;\n\n"
        "  // Accessed only by the loading thread.\n",
        "  private final TsDurationReader durationReader;\n"
        "  @Nullable private TimestampDiscontinuityProvider timestampDiscontinuityProvider;\n\n"
        "  /** Supplies timestamp offsets for native disc-navigation play-item boundaries. */\n"
        "  public interface TimestampDiscontinuityProvider {\n"
        "    long pollTimestampOffsetUs(long packetPosition);\n"
        "  }\n\n"
        "  /** Installs the optional disc-navigation timestamp discontinuity provider. */\n"
        "  public void setTimestampDiscontinuityProvider(\n"
        "      @Nullable TimestampDiscontinuityProvider timestampDiscontinuityProvider) {\n"
        "    this.timestampDiscontinuityProvider = timestampDiscontinuityProvider;\n"
        "  }\n\n"
        "  // Accessed only by the loading thread.\n",
        "TsExtractor navigation timestamp provider",
    )
    text = replace_once(
        text,
        "    int endOfPacket = findEndOfFirstTsPacketInBuffer();\n"
        "    int limit = tsPacketBuffer.limit();\n"
        "    if (endOfPacket > limit) {\n"
        "      return RESULT_CONTINUE;\n"
        "    }\n\n"
        "    @TsPayloadReader.Flags int packetHeaderFlags = 0;\n",
        "    int endOfPacket = findEndOfFirstTsPacketInBuffer();\n"
        "    int limit = tsPacketBuffer.limit();\n"
        "    if (endOfPacket > limit) {\n"
        "      return RESULT_CONTINUE;\n"
        "    }\n\n"
        "    TimestampDiscontinuityProvider discontinuityProvider = timestampDiscontinuityProvider;\n"
        "    if (discontinuityProvider != null) {\n"
        "      long packetPosition = input.getPosition() - tsPacketBuffer.bytesLeft();\n"
        "      long timestampOffsetUs = discontinuityProvider.pollTimestampOffsetUs(packetPosition);\n"
        "      if (timestampOffsetUs != C.TIME_UNSET) {\n"
        "        for (int i = 0; i < timestampAdjusters.size(); i++) {\n"
        "          timestampAdjusters.get(i).reset(timestampOffsetUs);\n"
        "        }\n"
        "        for (int i = 0; i < tsPayloadReaders.size(); i++) {\n"
        "          tsPayloadReaders.valueAt(i).seek();\n"
        "        }\n"
        "        continuityCounters.clear();\n"
        "      }\n"
        "    }\n\n"
        "    @TsPayloadReader.Flags int packetHeaderFlags = 0;\n",
        "TsExtractor packet-position navigation timestamp hook",
    )
    path.write_text(text, encoding="utf-8")


def patch_bdmv_navigation_timestamp_hook(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = """  public BdmvTsExtractor(
      @Nullable ClpiInfo clipInfo, long startM2ts, long inTimeTicks, long durationUs) {
    payloadReaderFactory = new BdmvTsPayloadReaderFactory(clipInfo);
    delegate =
        new TsExtractor(
            TsExtractor.MODE_SINGLE_PMT,
            TsExtractor.FLAG_EMIT_RAW_SUBTITLE_DATA | TsExtractor.FLAG_IGNORE_SECTION_CRC,
            SubtitleParser.Factory.UNSUPPORTED,
            new TimestampAdjuster(0),
            payloadReaderFactory,
            TsExtractor.DEFAULT_TIMESTAMP_SEARCH_BYTES);
    epSeekMap = buildEpSeekMap(clipInfo, startM2ts, inTimeTicks, durationUs);
"""
    new = """  public BdmvTsExtractor(
      @Nullable ClpiInfo clipInfo, long startM2ts, long inTimeTicks, long durationUs) {
    this(
        clipInfo,
        startM2ts,
        inTimeTicks,
        durationUs,
        /* timestampDiscontinuityProvider= */ null);
  }

  public BdmvTsExtractor(
      @Nullable ClpiInfo clipInfo,
      long startM2ts,
      long inTimeTicks,
      long durationUs,
      @Nullable TsExtractor.TimestampDiscontinuityProvider timestampDiscontinuityProvider) {
    payloadReaderFactory = new BdmvTsPayloadReaderFactory(clipInfo);
    delegate =
        new TsExtractor(
            TsExtractor.MODE_SINGLE_PMT,
            TsExtractor.FLAG_EMIT_RAW_SUBTITLE_DATA | TsExtractor.FLAG_IGNORE_SECTION_CRC,
            SubtitleParser.Factory.UNSUPPORTED,
            new TimestampAdjuster(0),
            payloadReaderFactory,
            TsExtractor.DEFAULT_TIMESTAMP_SEARCH_BYTES);
    delegate.setTimestampDiscontinuityProvider(timestampDiscontinuityProvider);
    epSeekMap = buildEpSeekMap(clipInfo, startM2ts, inTimeTicks, durationUs);
"""
    text = replace_once(text, old, new, "BdmvTsExtractor navigation timestamp hook")
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
    navigation_data_source_path = (
        root
        / "libraries/exoplayer/src/main/java/androidx/media3/exoplayer/source/iso/IsoNavigationDataSource.java"
    )
    navigation_media_source_path = (
        root
        / "libraries/exoplayer/src/main/java/androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource.java"
    )
    ts_extractor_path = (
        root
        / "libraries/extractor/src/main/java/androidx/media3/extractor/ts/TsExtractor.java"
    )
    bdmv_ts_extractor_path = (
        root
        / "libraries/extractor/src/main/java/androidx/media3/extractor/iso/bdmv/BdmvTsExtractor.java"
    )
    exoplayer_proguard = root / "libraries/exoplayer/proguard-rules.txt"

    for required in (
        udf_path,
        parsed_path,
        ts_extractor_path,
        bdmv_ts_extractor_path,
        exoplayer_proguard,
    ):
      if not required.is_file():
        raise SystemExit(f"missing pinned media source file: {required}")

    write_native_udf(native_path)
    write_navigation_session(navigation_path)
    write_navigation_data_source(navigation_data_source_path)
    write_navigation_media_source(navigation_media_source_path)
    patch_ts_extractor_navigation_timestamp_hook(ts_extractor_path)
    patch_bdmv_navigation_timestamp_hook(bdmv_ts_extractor_path)
    patch_udf(udf_path)
    patch_iso_parsed_media(parsed_path)
    patch_navigation_keep_rules(exoplayer_proguard)
    print(f"Applied {OVERLAY_ID}")


if __name__ == "__main__":
    main()
