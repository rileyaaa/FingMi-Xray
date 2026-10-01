package androidx.media3.exoplayer.libass;

import java.util.Arrays;
import java.util.List;

/** Reconstructed5.6.5 JNI value object; constructor descriptor is a native ABI. */
final class LibassFrame {
    public final boolean changed;
    public final List<LibassImage> images;
    public LibassFrame(int change, LibassImage[] images) {
        this.changed = change != 0;
        this.images = images == null ? List.of() : List.copyOf(Arrays.asList(images));
    }
}
