package androidx.media3.exoplayer.libass;

/** Reconstructed published libass.d: independent primary and secondary native frames. */
final class LibassFrameSet {
    final LibassFrame primary;
    final LibassFrame secondary;

    LibassFrameSet(LibassFrame primary, LibassFrame secondary) {
        this.primary = primary;
        this.secondary = secondary;
    }
}
