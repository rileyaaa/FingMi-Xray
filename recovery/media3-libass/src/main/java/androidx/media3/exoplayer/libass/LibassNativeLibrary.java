package androidx.media3.exoplayer.libass;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.Objects;
import java.util.function.Consumer;

/**
 * Reconstructed upstream-missing implementation from5.6.5 libass.c and libass.b.
 * One media library shares embedded fonts across isolated subtitle tracks.
 * One monitor also enforces the published media owner's track-before-library close order.
 * Native has no library reference count; letting a track outlive it is unsafe.
 */
final class LibassNativeLibrary implements AutoCloseable {
    static final int MAX_FONT_BYTES = 32 * 1024 * 1024;
    static final long MAX_TOTAL_FONT_BYTES = 128L * 1024 * 1024;
    private final LinkedHashSet<LibassTrack> tracks = new LinkedHashSet<>();
    private long handle;
    private long totalFontBytes;
    private boolean closing;

    LibassNativeLibrary(String fontsDirectory) {
        handle = LibassNative.nativeCreateLibrary(fontsDirectory);
        if (handle == 0) throw new IllegalStateException("Failed to create libass library");
    }

    synchronized LibassTrack createTrack(String fontConfig, String family,
                                        Consumer<LibassTrack> initialize) {
        checkOpen();
        Objects.requireNonNull(initialize);
        LibassTrack track = new LibassTrack(this, handle, fontConfig, family);
        tracks.add(track);
        try {
            initialize.accept(track);
            checkOpen();
            track.checkOpen();
            return track;
        } catch (RuntimeException | Error failure) {
            try { track.close(); } catch (RuntimeException | Error cleanup) {
                failure.addSuppressed(cleanup);
            }
            throw failure;
        }
    }

    synchronized void addFont(String name, byte[] data) {
        checkOpen();
        Objects.requireNonNull(name); Objects.requireNonNull(data);
        if (name.isEmpty()) throw new IllegalArgumentException("Font name must not be empty");
        if (data.length > MAX_FONT_BYTES) throw new IllegalArgumentException("Embedded font exceeds the per-font limit");
        if (totalFontBytes + data.length > MAX_TOTAL_FONT_BYTES)
            throw new IllegalArgumentException("Embedded fonts exceed the per-media limit");
        if (data.length == 0) return;
        LibassNative.nativeAddFont(handle, name, data);
        totalFontBytes += data.length;
    }

    void checkOpen() {
        if (handle == 0 || closing) throw new IllegalStateException("LibassNativeLibrary is closed");
    }
    void detached(LibassTrack track) { tracks.remove(track); }

    @Override public synchronized void close() {
        if (handle == 0 || closing) return;
        closing = true;
        Throwable failure = null;
        for (LibassTrack track : new ArrayList<>(tracks)) {
            try { track.close(); } catch (RuntimeException | Error error) {
                if (failure == null) failure = error; else failure.addSuppressed(error);
            }
        }
        long releasing = handle;
        handle = 0;
        totalFontBytes = 0;
        try { LibassNative.nativeReleaseLibrary(releasing); }
        catch (RuntimeException | Error error) {
            if (failure == null) failure = error; else failure.addSuppressed(error);
        }
        if (failure instanceof RuntimeException) throw (RuntimeException) failure;
        if (failure instanceof Error) throw (Error) failure;
    }
}
