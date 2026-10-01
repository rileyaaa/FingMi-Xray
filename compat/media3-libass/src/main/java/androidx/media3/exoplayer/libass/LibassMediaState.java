package androidx.media3.exoplayer.libass;

import androidx.media3.common.Format;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Reconstructed upstream-missing per-media state from published5.6.5 libass.a/b/g and ax0.
 * Parsers and renderers serialize against this media monitor; disposal invalidates callbacks
 * immediately, before asynchronous native release. No player/global state is retained here.
 */
final class LibassMediaState implements AutoCloseable {
    private static final byte[] EVENTS="[Events]\n".getBytes(StandardCharsets.UTF_8);
    private static final byte[] FORMAT="Format:".getBytes(StandardCharsets.UTF_8);
    private final LibassConfiguration configuration;
    private final boolean available;
    private final AtomicBoolean disposed=new AtomicBoolean();
    private final Map<String,LibassTrack> tracks=new LinkedHashMap<>();
    private final List<Font> fonts=new ArrayList<>();
    private LibassNativeLibrary library;
    private Format primary,secondary;
    private int frameWidth,frameHeight,storageWidth,storageHeight,left,top,right,bottom;
    private float scale=1f,primaryPosition,secondaryPosition=1f;
    private boolean overrideScale,closed;
    private long secondaryOffsetUs,totalFontBytes;
    private String family,styleFamily;
    private LibassStyleOverride style;

    LibassMediaState(LibassConfiguration configuration,boolean available) {
        this.configuration=Objects.requireNonNull(configuration);this.available=available;
        family=configuration.defaultFontFamily;
    }
    boolean isAvailable(){return available&&!disposed.get();}
    synchronized Format secondaryFormat(){return disposed.get()?null:secondary;}
    synchronized boolean hasActiveTrack(){return !disposed.get()&&(resolve(primary)!=null||resolve(secondary)!=null);}

    static String trackKey(Format format) {
        return format.id==null||format.id.isEmpty()?"external:"+Objects.toString(format.label,"")+":"+Objects.toString(format.language,""):format.id;
    }
    private String resolve(Format format) {
        if(format==null)return null;
        String key=trackKey(format);
        while(!tracks.containsKey(key)) {
            int colon=key.indexOf(':');if(colon<=0)return null;
            for(int i=0;i<colon;i++)if(key.charAt(i)<'0'||key.charAt(i)>'9')return null;
            key=key.substring(colon+1);
            if(key.isEmpty()) {
                key="external:"+Objects.toString(format.label,"")+":"+Objects.toString(format.language,"");
                return tracks.containsKey(key)?key:null;
            }
        }
        return key;
    }
    private boolean sameTrack(Format a,Format b) {
        if(a==null||b==null)return false;
        if(a.equals(b))return true;String key=resolve(a);return key!=null&&key.equals(resolve(b));
    }
    synchronized boolean setPrimaryFormat(Format value) {
        if(disposed.get())return false;
        Format nextSecondary=sameTrack(value,secondary)?null:secondary;
        if(Objects.equals(primary,value)&&Objects.equals(secondary,nextSecondary))return false;
        primary=value;secondary=nextSecondary;positionTracks();return true;
    }
    synchronized boolean setSecondaryFormat(Format value) {
        if(disposed.get())return false;
        if(sameTrack(primary,value))value=null;
        if(Objects.equals(secondary,value))return false;
        secondary=value;positionTracks();return true;
    }
    synchronized void setSecondaryOffsetUs(long value){if(!disposed.get())secondaryOffsetUs=value;}

    private LibassNativeLibrary library() {
        if(library!=null)return library;
        LibassNativeLibrary created=new LibassNativeLibrary(configuration.fontsDirectory);
        try {for(Font font:fonts)created.addFont(font.name,font.data);}
        catch(RuntimeException|Error failure){try{created.close();}catch(RuntimeException|Error cleanup){failure.addSuppressed(cleanup);}throw failure;}
        library=created;for(Font font:fonts)font.data=null;return created;
    }
    private LibassTrack create(java.util.function.Consumer<LibassTrack> initialize) {
        return library().createTrack(configuration.fontConfig,family,track->{
            track.setFontScale(scale,overrideScale);track.setBottomPositionFraction(primaryPosition);applyStyle(track);
            if(configuration.maximumGlyphCount!=0||configuration.maximumBitmapCacheSizeMb!=0)
                track.setCacheLimits(configuration.maximumGlyphCount,configuration.maximumBitmapCacheSizeMb);
            if(frameWidth!=0)size(track);
            initialize.accept(track);
        });
    }
    private void replace(String key,LibassTrack next) {
        LibassTrack previous=tracks.put(key,next);
        try {if(previous!=null)previous.close();}
        finally {
            // Keys may become resolvable after track discovery, not only at selection time.
            if(sameTrack(primary,secondary))secondary=null;
            positionTracks();
        }
    }
    synchronized void addTrack(int number,byte[] codecPrivate) {
        if(!isAvailable())return;
        LibassTrack next=create(track->track.processCodecPrivate(codecPrivate,0,codecPrivate.length));
        replace(Integer.toString(number),next);
    }
    synchronized void addExternalTrack(Format format,byte[] data,int offset,int length) {
        if(!isAvailable())return;
        LibassTrack next=create(track->track.processData(data,offset,length));replace(trackKey(format),next);
    }
    synchronized void processTimedData(Format format,byte[] data,int offset,int length,long sampleTimeUs) {
        if(!isAvailable())return;
        // Format.OFFSET_SAMPLE_RELATIVE is Long.MAX_VALUE; TIME_UNSET means offset zero.
        long timeUs=format.subsampleOffsetUs!=Long.MAX_VALUE?format.subsampleOffsetUs:
                sampleTimeUs==Long.MIN_VALUE+1?0:sampleTimeUs;
        String key=trackKey(format);LibassTrack track=tracks.get(key);
        if(track!=null){track.processTimedData(data,offset,length,timeUs);return;}
        LibassTrack next=create(t->{initialize(t,format.initializationData);t.processTimedData(data,offset,length,timeUs);});
        replace(key,next);
    }
    private static boolean startsWith(byte[] data,byte[] prefix) {
        if(data.length<prefix.length)return false;
        for(int i=0;i<prefix.length;i++)if(data[i]!=prefix[i])return false;
        return true;
    }
    private static void initialize(LibassTrack track,List<byte[]> data) {
        if(data.size()==2&&startsWith(data.get(0),FORMAT)) {
            byte[] header=data.get(1);track.processCodecPrivate(header,0,header.length);
            byte[] format=data.get(0),events=Arrays.copyOf(EVENTS,EVENTS.length+format.length);
            System.arraycopy(format,0,events,EVENTS.length,format.length);track.processData(events,0,events.length);
        }else for(byte[] bytes:data)track.processData(bytes,0,bytes.length);
    }
    synchronized void processSample(int number,long timeUs,long durationUs,byte[] data,int offset,int length) {
        if(disposed.get())return;LibassTrack track=tracks.get(Integer.toString(number));
        if(track!=null)track.processChunk(data,offset,length,timeUs,durationUs);
    }

    static boolean isFont(String name,String mime) {
        String m=mime==null?"":mime.toLowerCase(Locale.US);
        if(m.startsWith("font/")&&!m.equals("font/woff2")||m.equals("application/font-woff")||m.equals("application/font-sfnt")
                ||m.equals("application/vnd.ms-opentype")||m.equals("application/x-font-ttf")||m.equals("application/x-font-otf")||m.equals("application/x-truetype-font"))return true;
        String n=name==null?"":name.toLowerCase(Locale.US);
        return n.endsWith(".ttf")||n.endsWith(".otf")||n.endsWith(".ttc")||n.endsWith(".otc")||n.endsWith(".woff");
    }
    synchronized boolean shouldReadAttachment(String name,String mime,int size) {
        return isAvailable()&&size>0&&size<=LibassNativeLibrary.MAX_FONT_BYTES&&totalFontBytes+size<=LibassNativeLibrary.MAX_TOTAL_FONT_BYTES
                &&(name==null||mime==null||isFont(name,mime));
    }
    synchronized void addAttachment(String name,String mime,byte[] data) {
        if(!shouldReadAttachment(name,mime,data.length)||!isFont(name,mime))return;
        String resolved=name==null||name.isEmpty()?"attachment-"+fonts.size():name;
        Font font=new Font(resolved,data);
        for(Font old:fonts)if(old.name.equals(font.name)&&old.length==font.length&&MessageDigest.isEqual(old.hash,font.hash))return;
        if(library!=null){library.addFont(font.name,font.data);font.data=null;}
        fonts.add(font);totalFontBytes+=data.length;
        if(library!=null)for(LibassTrack track:tracks.values())track.reloadFonts();
    }
    private static final class Font {
        final String name;final int length;final byte[] hash;byte[] data;
        Font(String name,byte[] data){this.name=name;this.length=data.length;this.data=data.clone();
            try{hash=MessageDigest.getInstance("SHA-256").digest(data);}
            catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    }
    private void size(LibassTrack track) {
        track.setStorageSize(storageWidth,storageHeight);track.setFrameSize(frameWidth,frameHeight,left,top,right,bottom);
    }
    synchronized void setFrameSize(int width,int height,int storageWidth,int storageHeight,int left,int top,int right,int bottom) {
        if(disposed.get())return;
        if(width<=0||height<=0||storageWidth<=0||storageHeight<=0||right<=left||bottom<=top)throw new IllegalArgumentException("Invalid frame, storage or viewport size");
        if(frameWidth==width&&frameHeight==height&&this.storageWidth==storageWidth&&this.storageHeight==storageHeight&&this.left==left&&this.top==top&&this.right==right&&this.bottom==bottom)return;
        frameWidth=width;frameHeight=height;this.storageWidth=storageWidth;this.storageHeight=storageHeight;this.left=left;this.top=top;this.right=right;this.bottom=bottom;
        for(LibassTrack track:tracks.values())size(track);
    }
    synchronized void setFontScale(float scale,boolean override) {
        if(disposed.get())return;
        if(!Float.isFinite(scale)||scale<=0)throw new IllegalArgumentException("Invalid font scale");
        if(this.scale==scale&&overrideScale==override)return;this.scale=scale;overrideScale=override;
        for(LibassTrack track:tracks.values())track.setFontScale(scale,override);
    }
    private void positionTracks() {
        String second=resolve(secondary);
        for(Map.Entry<String,LibassTrack> track:tracks.entrySet())track.getValue().setBottomPositionFraction(track.getKey().equals(second)?secondaryPosition:primaryPosition);
    }
    synchronized void setBottomPositionFraction(float value) {
        if(disposed.get())return;if(!Float.isFinite(value))throw new IllegalArgumentException("Invalid bottom position");
        if(primaryPosition==value)return;primaryPosition=value;positionTracks();
    }
    synchronized void setSecondaryBottomPositionFraction(float value) {
        if(disposed.get())return;if(!Float.isFinite(value))throw new IllegalArgumentException("Invalid secondary bottom position");
        if(secondaryPosition==value)return;secondaryPosition=value;positionTracks();
    }
    synchronized void setDefaultFontFamily(String family) {
        if(disposed.get())return;LibassConfiguration.family(family);if(Objects.equals(this.family,family))return;
        for(LibassTrack track:tracks.values())track.setFonts(family);this.family=family;
    }
    private void applyStyle(LibassTrack track) {
        if(style==null)track.setStyleOverride(false,styleFamily,0,0,0,0,0,0,0);else style.apply(track,styleFamily);
    }
    synchronized void setStyleOverride(LibassStyleOverride style,String family) {
        if(disposed.get())return;LibassConfiguration.family(family);
        if(Objects.equals(this.style,style)&&Objects.equals(styleFamily,family))return;
        this.style=style;styleFamily=family;for(LibassTrack track:tracks.values())applyStyle(track);
    }
    private LibassFrame render(Format format,long timeUs,boolean force) {
        String key=resolve(format);return key==null||frameWidth==0?null:tracks.get(key).renderFrame(timeUs,force);
    }
    synchronized LibassFrameSet renderFrames(long positionUs,boolean force) {
        if(disposed.get()||primary==null&&secondary==null)return null;
        LibassFrame p=render(primary,positionUs,force),s=render(secondary,positionUs-secondaryOffsetUs,force);
        return p==null&&s==null?null:new LibassFrameSet(p,s);
    }
    void dispose(Executor releaseExecutor) {
        if(!disposed.compareAndSet(false,true))return;
        try{releaseExecutor.execute(this::closeNative);}
        catch(RejectedExecutionException rejected){closeNative();}
    }
    private synchronized void closeNative() {
        if(closed)return;closed=true;primary=null;secondary=null;tracks.clear();fonts.clear();totalFontBytes=0;
        LibassNativeLibrary old=library;library=null;if(old!=null)old.close();
    }
    @Override public void close(){disposed.set(true);closeNative();}
}
