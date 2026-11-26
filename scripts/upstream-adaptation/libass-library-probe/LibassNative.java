/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

/** Seven descriptor candidates in an isolated embedded-font profile, not the complete 18-method class. */
final class LibassNative {
    public static native long nativeCreateLibrary(String fontConfig);
    public static native void nativeReleaseLibrary(long libraryPtr);
    public static native void nativeAddFont(long libraryPtr,String name,byte[] data);
    public static native long nativeCreate(long libraryPtr,String fontsDirectory,String defaultFontFamily);
    public static native void nativeRelease(long trackPtr);
    public static native void nativeProcessCodecPrivate(long trackPtr,byte[] data,int offset,int length);
    public static native void nativeProcessChunk(long trackPtr,byte[] data,int offset,int length,long startTimeMs,long durationMs);
}
