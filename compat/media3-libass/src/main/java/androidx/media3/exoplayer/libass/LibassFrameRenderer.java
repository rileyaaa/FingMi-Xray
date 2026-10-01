package androidx.media3.exoplayer.libass;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * Reconstructed upstream-missing implementation of published libass.e/f frame ownership.
 * All calls, including close and rejected-frame cleanup, belong to the current EGL thread.
 * The backend must be closed only after this owner. It must delete a failed CPU upload itself.
 * A fresh owner is required after EGL context loss; the caller must force native rendering.
 */
final class LibassFrameRenderer implements AutoCloseable {
    interface Textures {
        int upload(byte[] coverage, int width, int height);
        void delete(int textureId);
        void draw(Image image, int frameWidth, int frameHeight);
    }

    static final class Image {
        final int textureId, x, y, width, height;
        final float red, green, blue, alpha;

        Image(int textureId, LibassImage image) {
            this.textureId = textureId;
            x = image.x; y = image.y; width = image.width; height = image.height;
            // libass is RRGGBBTT (transparency), not Android ARGB.
            red = ((image.color >>> 24) & 255) / 255f;
            green = ((image.color >>> 16) & 255) / 255f;
            blue = ((image.color >>> 8) & 255) / 255f;
            alpha = 1f - (image.color & 255) / 255f;
        }
    }

    private static final class Layer {
        final List<Image> images;
        final int width, height;
        Layer(List<Image> images, int width, int height) {
            this.images = images; this.width = width; this.height = height;
        }
    }

    private static final Layer EMPTY = new Layer(Collections.emptyList(), 0, 0);
    private final Textures textures;
    private final Thread thread = Thread.currentThread();
    private Layer primary = EMPTY, secondary = EMPTY;
    private Object identity;
    private boolean closed;

    LibassFrameRenderer(Textures textures) { this.textures = Objects.requireNonNull(textures); }

    private void checkThread() {
        if (Thread.currentThread() != thread)
            throw new IllegalStateException("Libass textures belong to the EGL render thread");
    }

    /** Identity is an opaque per-media render generation, never equality of the media URL. */
    boolean bind(Object identity) {
        checkThread();
        if (closed) throw new IllegalStateException("LibassFrameRenderer is closed");
        if (this.identity == identity) return false;
        this.identity = identity;
        clear();
        return true;
    }

    /**
     * Consumes ownership of incoming native texture IDs even for stale or unchanged frames.
     * changed=false preserves that lane; null/changed-empty clears it. Both lanes publish
     * together after successful uploads (a reconstruction hardening over partial updates).
     */
    boolean update(Object identity, LibassFrameSet frames, int width, int height) {
        checkThread();
        Layer nextPrimary = primary, nextSecondary = secondary;
        boolean committed = false;
        try {
            if (closed || this.identity != identity || identity == null) return false;
            LibassFrame p = frames == null ? null : frames.primary;
            LibassFrame s = frames == null ? null : frames.secondary;
            if ((p != null && p.changed || s != null && s.changed) && (width <= 0 || height <= 0))
                throw new IllegalArgumentException("Frame size must be positive");
            nextSecondary = prepare(s, secondary, width, height);
            nextPrimary = prepare(p, primary, width, height);
            Layer oldPrimary = primary, oldSecondary = secondary;
            primary = nextPrimary; secondary = nextSecondary;
            committed = true;
            if (oldPrimary != primary) release(oldPrimary);
            if (oldSecondary != secondary) release(oldSecondary);
            return changed(p, oldPrimary) || changed(s, oldSecondary);
        } finally {
            try {
                if (!committed) {
                    if (nextPrimary != primary) release(nextPrimary);
                    if (nextSecondary != secondary) release(nextSecondary);
                }
            } finally {
                if (frames != null) {
                    try { releaseIncoming(frames.primary); }
                    finally { releaseIncoming(frames.secondary); }
                }
            }
        }
    }

    private static boolean changed(LibassFrame frame, Layer previous) {
        return frame == null ? !previous.images.isEmpty() : frame.changed;
    }

    private Layer prepare(LibassFrame frame, Layer previous, int width, int height) {
        if (frame == null) return EMPTY;
        if (!frame.changed) return previous;
        // Preallocate so a native texture is not lost if list allocation fails.
        ArrayList<Image> images = new ArrayList<>(frame.images.size());
        try {
            for (LibassImage image : frame.images) {
                if (image.width <= 0 || image.height <= 0)
                    throw new IllegalArgumentException("Invalid libass image size");
                int texture = image.textureId;
                boolean uploaded = texture == 0;
                if (uploaded) {
                    if (image.bitmap == null || (long) image.width * image.height != image.bitmap.length)
                        throw new IllegalArgumentException("Invalid libass coverage bitmap");
                    texture = textures.upload(image.bitmap, image.width, image.height);
                    if (texture == 0) throw new IllegalStateException("Texture upload returned zero");
                }
                try { images.add(new Image(texture, image)); }
                catch (RuntimeException | Error failure) {
                    if (uploaded) textures.delete(texture);
                    throw failure;
                }
                image.textureId = 0; // Native texture ownership transfers to this layer once.
            }
            return new Layer(images, width, height);
        } catch (RuntimeException | Error failure) {
            try { release(new Layer(images, width, height)); }
            catch (RuntimeException | Error cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        }
    }

    private void releaseIncoming(LibassFrame frame) {
        if (frame == null) return;
        for (LibassImage image : frame.images) {
            int texture = image.textureId;
            image.textureId = 0;
            if (texture != 0) textures.delete(texture);
        }
    }

    private void release(Layer layer) {
        for (Image image : layer.images) textures.delete(image.textureId);
    }

    private void clear() {
        Layer p = primary, s = secondary;
        primary = EMPTY; secondary = EMPTY;
        try { release(p); } finally { release(s); }
    }

    /** Draw primary then secondary over the same transparent surface. */
    void draw() {
        checkThread();
        if (closed) return;
        draw(primary); draw(secondary);
    }

    private void draw(Layer layer) {
        for (Image image : layer.images) textures.draw(image, layer.width, layer.height);
    }

    @Override public void close() {
        checkThread();
        if (closed) return;
        closed = true; identity = null;
        clear();
    }
}
