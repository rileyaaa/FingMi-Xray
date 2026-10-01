#!/usr/bin/env python3
"""Apply the FongMi 5.6.7/5.6.8 native ISO UDF compatibility overlay."""

from __future__ import annotations

import argparse
from pathlib import Path


OVERLAY_ID = "fongmi-tv-5.6.8-iso-native-udf-overlay-v1"


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
      throw new UnsupportedImageException("Could not open UDF image");
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

    for required in (udf_path, parsed_path):
      if not required.is_file():
        raise SystemExit(f"missing pinned media source file: {required}")

    write_native_udf(native_path)
    patch_udf(udf_path)
    patch_iso_parsed_media(parsed_path)
    print(f"Applied {OVERLAY_ID}")


if __name__ == "__main__":
    main()
