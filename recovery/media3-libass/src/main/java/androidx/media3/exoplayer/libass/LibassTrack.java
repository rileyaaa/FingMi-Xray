package androidx.media3.exoplayer.libass;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;

/** Reconstructed5.6.5 libass.g/bl1 contract; uses the new JNI, never the historical ABI. */
final class LibassTrack implements AutoCloseable {
    private final LibassNativeLibrary owner;
    private final String fontConfig;
    private final MessageDigest digest;
    private final HashSet<TimedKey> timedData = new HashSet<>();
    private String family;
    private long handle;
    private boolean frameSizeSet;

    LibassTrack(LibassNativeLibrary owner, long libraryHandle, String fontConfig, String family) {
        this.owner=owner; this.fontConfig=fontConfig; this.family=family;
        try { digest=MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        handle=LibassNative.nativeCreate(libraryHandle,fontConfig,family);
        if(handle==0) throw new IllegalStateException("Failed to create libass track");
    }
    void checkOpen() {
        if(handle==0) throw new IllegalStateException("LibassTrack is closed");
        owner.checkOpen();
    }
    private static void range(byte[] data,int offset,int length) {
        Objects.requireNonNull(data);
        if(offset<0||length<0||offset>data.length-length)throw new IndexOutOfBoundsException("invalid data range");
    }
    private static long ms(long us) { return us==Long.MIN_VALUE||us==Long.MIN_VALUE+1 ? us : us/1000; }
    void processCodecPrivate(byte[] data,int offset,int length) { synchronized(owner) {
        checkOpen();range(data,offset,length);LibassNative.nativeProcessCodecPrivate(handle,data,offset,length);
    }}
    void processData(byte[] data,int offset,int length) { synchronized(owner) {
        checkOpen();range(data,offset,length);LibassNative.nativeProcessData(handle,data,offset,length);
    }}
    void processTimedData(byte[] data,int offset,int length,long timeUs) { synchronized(owner) {
        checkOpen();range(data,offset,length);digest.reset();digest.update(data,offset,length);
        TimedKey key=new TimedKey(digest.digest(),length,timeUs);
        if(timedData.contains(key))return;
        LibassNative.nativeProcessTimedData(handle,data,offset,length,ms(timeUs));
        timedData.add(key);
    }}
    void processChunk(byte[] data,int offset,int length,long startUs,long durationUs) { synchronized(owner) {
        checkOpen();range(data,offset,length);
        if(durationUs<0)throw new IllegalArgumentException("Duration must be non-negative");
        LibassNative.nativeProcessChunk(handle,data,offset,length,ms(startUs),ms(durationUs));
    }}
    void setFonts(String family) { synchronized(owner) {
        checkOpen();if(Objects.equals(this.family,family))return;
        LibassNative.nativeSetFonts(handle,fontConfig,family);this.family=family;
    }}
    /** Newly added shared-library fonts require reloading even when the family is unchanged. */
    void reloadFonts() { synchronized(owner) {
        checkOpen();LibassNative.nativeSetFonts(handle,fontConfig,family);
    }}
    void setFrameSize(int width,int height,int left,int top,int right,int bottom) { synchronized(owner) {
        checkOpen();if(width<=0||height<=0||right<=left||bottom<=top)throw new IllegalArgumentException("Frame size and viewport must be positive");
        LibassNative.nativeSetFrameSize(handle,width,height,left,top,right,bottom);frameSizeSet=true;
    }}
    void setStorageSize(int width,int height) { synchronized(owner) {
        checkOpen();if(width<=0||height<=0)throw new IllegalArgumentException("Storage size must be positive");
        LibassNative.nativeSetStorageSize(handle,width,height);
    }}
    void setFontScale(float scale,boolean override) { synchronized(owner) {
        checkOpen();if(!Float.isFinite(scale)||scale<=0)throw new IllegalArgumentException("Font scale must be finite and positive");
        LibassNative.nativeSetFontScale(handle,scale,override);
    }}
    void setBottomPositionFraction(float fraction) { synchronized(owner) {
        checkOpen();if(!Float.isFinite(fraction))throw new IllegalArgumentException("Bottom position must be finite");
        LibassNative.nativeSetBottomPositionFraction(handle,fraction);
    }}
    void setCacheLimits(int glyphs,int bitmapMb) { synchronized(owner) {
        checkOpen();if(glyphs<0||bitmapMb<0)throw new IllegalArgumentException("Cache limits must be non-negative");
        LibassNative.nativeSetCacheLimits(handle,glyphs,bitmapMb);
    }}
    void setStyleOverride(boolean enabled,String family,float size,int field1,int field2,
                          int field3,int field4,float metric1,float metric2) { synchronized(owner) {
        checkOpen();LibassNative.nativeSetStyleOverride(handle,enabled,family,size,field1,field2,field3,field4,metric1,metric2);
    }}
    LibassFrame renderFrame(long positionUs,boolean forceUpdate) { synchronized(owner) {
        checkOpen();if(!frameSizeSet)throw new IllegalStateException("Frame size must be set before rendering");
        return LibassNative.nativeRenderFrame(handle,ms(positionUs),forceUpdate,true);
    }}
    @Override public void close() { synchronized(owner) {
        if(handle==0)return;
        long releasing=handle;handle=0;frameSizeSet=false;timedData.clear();owner.detached(this);
        LibassNative.nativeRelease(releasing);
    }}
    private static final class TimedKey {
        final byte[] hash;final int length;final long timeUs;
        TimedKey(byte[] hash,int length,long timeUs){this.hash=hash;this.length=length;this.timeUs=timeUs;}
        @Override public boolean equals(Object other){if(!(other instanceof TimedKey))return false;TimedKey k=(TimedKey)other;return length==k.length&&timeUs==k.timeUs&&Arrays.equals(hash,k.hash);}
        @Override public int hashCode(){return Arrays.hashCode(hash)+((Long.hashCode(timeUs)*31+length)*31);}
    }
}
