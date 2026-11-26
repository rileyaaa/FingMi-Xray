/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

public final class LibassTrackProbe {
    // Test DTO with the reference LibassImage constructor descriptor.
    // Not the production Java class, texture renderer or complete frame contract.
    public static final class Image {
        final int x,y,w,h,color,textureId;
        final byte[] bitmap;
        public Image(int x,int y,int w,int h,int color,byte[] bitmap,int textureId) {
            this.x=x;this.y=y;this.w=w;this.h=h;this.color=color;this.bitmap=bitmap;this.textureId=textureId;
        }
    }
    private static native void setFixtureFrame(long track);
    private static native Image[] snapshot(long track,long time);
    private static void check(boolean value,String label){if(!value)throw new AssertionError(label);}
    private static void rejects(Class<? extends Throwable> type,Runnable action){
        try{action.run();}catch(Throwable error){if(type.isInstance(error))return;throw error;}
        throw new AssertionError("expected "+type.getName());
    }
    private static final String HEADER=
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n"
        +"[V4+ Styles]\n"
        +"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        +"Style: Default,DejaVu Sans,24,&H400000FF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n"
        +"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n";
    private static byte[] padded(String value){
        byte[] payload=value.getBytes(StandardCharsets.UTF_8);
        byte[] buf=new byte[payload.length+9];Arrays.fill(buf,(byte)0x7f);
        System.arraycopy(payload,0,buf,4,payload.length);return buf;
    }
    private static void packet(long track,String text,long start,long duration){
        byte[] bytes=padded("0,0,Default,,0,0,0,,"+text);
        LibassNative.nativeProcessChunk(track,bytes,4,bytes.length-9,start,duration);
        Arrays.fill(bytes,(byte)0);
    }
    private static long digest(Image[] images){
        check(images!=null&&images.length>0,"rendered image list");
        long hash=0xcbf29ce484222325L;boolean covered=false,red=false;
        for(Image im:images){
            check(im.w>0&&im.h>0&&im.bitmap.length==(long)im.w*im.h,"packed image dimensions");
            check(im.x>=0&&im.y>=0&&im.x+im.w<=320&&im.y+im.h<=180&&im.textureId==0,"CPU bounds/texture");
            red|=im.color==0xff000040;
            hash=(hash^im.color)*1099511628211L;hash=(hash^im.x)*1099511628211L;hash=(hash^im.y)*1099511628211L;
            for(byte b:im.bitmap){covered|=b!=0;hash=(hash^(b&255))*1099511628211L;}
        }
        check(covered&&red,"real alpha coverage and raw libass RRGGBBAA");
        return hash;
    }
    public static void main(String[] args)throws Exception{
        System.load(Paths.get(args[0]).toAbsolutePath().toString());
        byte[] font=Files.readAllBytes(Paths.get(args[1]));
        long lib=LibassNative.nativeCreateLibrary(null);
        LibassNative.nativeAddFont(lib,"DejaVuSans.ttf",font);Arrays.fill(font,(byte)0);
        rejects(UnsupportedOperationException.class,()->LibassNative.nativeCreate(lib,"/not-a-probe-font-dir","DejaVu Sans"));
        long a=LibassNative.nativeCreate(lib,null,"DejaVu Sans");
        long b=LibassNative.nativeCreate(lib,null,"DejaVu Sans");
        check(a>0&&b>0&&a!=b,"independent real tracks");
        for(long t:new long[]{a,b}){
            setFixtureFrame(t);
            byte[] hdr=padded(HEADER);
            LibassNative.nativeProcessCodecPrivate(t,hdr,4,hdr.length-9);
            Arrays.fill(hdr,(byte)0);
        }
        rejects(IndexOutOfBoundsException.class,()->LibassNative.nativeProcessCodecPrivate(a,new byte[2],Integer.MAX_VALUE,1));
        rejects(IndexOutOfBoundsException.class,()->LibassNative.nativeProcessChunk(a,new byte[2],1,2,1000,800));
        rejects(IllegalArgumentException.class,()->LibassNative.nativeProcessChunk(a,new byte[1],0,1,1000,-1));
        rejects(IllegalArgumentException.class,()->LibassNative.nativeProcessChunk(a,new byte[1],0,1,Long.MAX_VALUE,1));
        packet(a,"First subtitle",1000,800);packet(b,"Other subtitle text",3000,750);
        check(snapshot(a,999).length==0&&snapshot(a,1800).length==0,"duration endpoints");
        Image[] saved=snapshot(a,1000);long first=digest(saved);
        long second=digest(snapshot(b,3000));check(first!=second,"independent pixel payloads");
        check(snapshot(b,2999).length==0&&snapshot(b,3750).length==0,"secondary endpoints");
        check(digest(snapshot(a,1799))==first&&digest(snapshot(a,1000))==first,"backward time render");
        LibassNative.nativeReleaseLibrary(lib);
        rejects(IllegalStateException.class,()->LibassNative.nativeCreate(lib,null,"DejaVu Sans"));
        check(digest(snapshot(b,3200))==second,"track survives library owner retirement");
        LibassNative.nativeRelease(a);LibassNative.nativeRelease(a);
        rejects(IllegalStateException.class,()->snapshot(a,1200));
        rejects(IllegalStateException.class,()->packet(a,"retired",1000,800));
        LibassNative.nativeRelease(b);
        check(digest(saved)==first,"Java pixel data owns memory after next render/release");
        // Reuse the existing independently defined lifetime counter, not old test execution.
        check(LibassLibraryProbe.liveLibraryCountForTrackProbe()==0,"last track frees library");
        System.out.println("PASS_LIBASS_TRACK_SUBSET four_new_descriptors tracks=2 timed_windows=2 copied_pixels=2 stale_handles_rejected live_libraries=0");
    }
}
