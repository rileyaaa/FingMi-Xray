package androidx.media3.exoplayer.libass;

/** Reconstructed5.6.5 JNI value object, including the new textureId argument. */
final class LibassImage {
    public final int x, y, width, height, color;
    public final byte[] bitmap;
    int textureId;
    public LibassImage(int x, int y, int width, int height, int color, byte[] bitmap, int textureId) {
        this.x=x; this.y=y; this.width=width; this.height=height;
        this.color=color; this.bitmap=bitmap; this.textureId=textureId;
    }
}
