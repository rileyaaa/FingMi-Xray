/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

/** Three exact descriptor candidates, not the complete 18-method class. */
final class LibassNative {
    public static native long nativeCreateLibrary(String fontConfig);
    public static native void nativeReleaseLibrary(long libraryPtr);
    public static native void nativeAddFont(long libraryPtr,String name,byte[] data);
}
