package androidx.media3.exoplayer.libass;

/** Reconstructed upstream-missing implementation: 5.6.5 DEX + both ELF method tables.
 * Not compatible with the historical9dae39e9 SO. Runtime loading must pass the ABI gate.
 * Flag names remain neutral until their native rendering semantics are established.
 */
final class LibassNative {
    private LibassNative() {
    }

    public static native void nativeAddFont(long j, String str, byte[] bArr);

    public static native long nativeCreate(long j, String str, String str2);

    public static native long nativeCreateLibrary(String str);

    public static native void nativeProcessChunk(long j, byte[] bArr, int i, int i2, long j2, long j3);

    public static native void nativeProcessCodecPrivate(long j, byte[] bArr, int i, int i2);

    public static native void nativeProcessData(long j, byte[] bArr, int i, int i2);

    public static native void nativeProcessTimedData(long j, byte[] bArr, int i, int i2, long j2);

    public static native void nativeRelease(long j);

    public static native void nativeReleaseLibrary(long j);

    public static native LibassFrame nativeRenderFrame(long j, long j2, boolean z, boolean z2);

    public static native void nativeSetBottomPositionFraction(long j, float f);

    public static native void nativeSetCacheLimits(long j, int i, int i2);

    public static native void nativeSetFontScale(long j, float f, boolean z);

    public static native void nativeSetFonts(long j, String str, String str2);

    public static native void nativeSetFrameSize(long j, int i, int i2, int i3, int i4, int i5, int i6);

    public static native void nativeSetStorageSize(long j, int i, int i2);

    public static native void nativeSetStyleOverride(long j, boolean z, String str, float f, int i, int i2, int i3, int i4, float f2, float f3);
}
