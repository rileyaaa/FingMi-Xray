/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

/** Actual full-line ASS parser, storage geometry and cache limit calls.
 * Host-only CPU snapshot, no invented nativeRenderFrame or texture contract.
 */
public final class LibassDataGeometryProbe {
    private static void check(boolean b,String label){if(!b)throw new AssertionError(label);}
    private static void rejects(Class<? extends Throwable> type,Runnable action){
        try{action.run();}catch(Throwable t){if(type.isInstance(t))return;throw t;}
        throw new AssertionError("expected "+type.getName());
    }
    private static void data(long track,String content){
        byte[] payload=content.getBytes(StandardCharsets.UTF_8), padded=new byte[payload.length+17];
        Arrays.fill(padded,(byte)0x7f);System.arraycopy(payload,0,padded,8,payload.length);
        LibassNative.nativeProcessData(track,padded,8,payload.length);
        Arrays.fill(padded,(byte)0);
    }
    private static long digest(LibassTrackProbe.Image[] images){
        check(images!=null&&images.length>0,"actual images");
        long h=0xcbf29ce484222325L;boolean coverage=false;
        for(LibassTrackProbe.Image i:images){
            check(i.w>0&&i.h>0&&i.bitmap.length==(long)i.w*i.h&&i.textureId==0,"packed real CPU image");
            check(i.x>=0&&i.y>=0&&i.x+i.w<=320&&i.y+i.h<=180,"image bounds");
            for(int n:new int[]{i.x,i.y,i.w,i.h,i.color})h=(h^n)*1099511628211L;
            for(byte b:i.bitmap){coverage|=b!=0;h=(h^(b&255))*1099511628211L;}
        }
        check(coverage,"nonempty actual pixel coverage");return h;
    }
    private static LibassTrackProbe.Image[] snap(long t,long ms){return LibassTrackProbe.snapshot(t,ms);}
    private static long render(long t,long ms){return digest(snap(t,ms));}
    private static int extent(LibassTrackProbe.Image[] images){
        int lo=320,hi=0;
        for(LibassTrackProbe.Image i:images){lo=Math.min(lo,i.x);hi=Math.max(hi,i.x+i.w);}
        return hi-lo;
    }
    public static void main(String[] args)throws Exception{
        System.load(Paths.get(args[0]).toAbsolutePath().toString());
        long lib=LibassNative.nativeCreateLibrary(null);
        byte[] font=Files.readAllBytes(Paths.get(args[1]));
        LibassNative.nativeAddFont(lib,"DejaVuSans.ttf",font);Arrays.fill(font,(byte)0);
        long t=LibassNative.nativeCreate(lib,null,"DejaVu Sans");
        LibassTrackProbe.setFixtureFrame(t);
        // Self-timed ASS, not Matroska processChunk. Separate ingestion mode.
        data(t,LibassTrackProbe.HEADER+
            "Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,MMMM wide text\n"+
            "Dialogue: 0,0:00:03.00,0:00:04.50,Default,,0,0,0,,Different glyphs 012345\n");
        check(snap(t,999).length==0&&snap(t,2000).length==0&&snap(t,2999).length==0&&snap(t,4500).length==0,"ASS embedded timestamps");
        long first=render(t,1000),second=render(t,3000);
        check(first!=second&&render(t,1999)==first&&render(t,4499)==second,"two self-timed images and boundaries");
        int normal=extent(snap(t,1100));
        LibassNative.nativeSetStorageSize(t,160,180);
        LibassTrackProbe.Image[] changed=snap(t,1100);
        int anamorphic=extent(changed);
        check(normal!=anamorphic&&digest(changed)!=first,"actual storage aspect changes rendered geometry");
        LibassNative.nativeSetStorageSize(t,320,180);
        check(render(t,1100)==first,"restore real source aspect");
        // Exercise very small cache and its reset. Verify real render correctness
        // across changing glyph sets; do not claim measured memory/eviction counts.
        LibassNative.nativeSetCacheLimits(t,1,1);
        for(int i=0;i<20;i++){
            check(render(t,1000)==first&&render(t,3000)==second,"cache-limited rerender "+i);
        }
        LibassNative.nativeSetCacheLimits(t,0,0);
        check(render(t,1000)==first&&render(t,3000)==second,"default cache reset");
        rejects(IndexOutOfBoundsException.class,()->LibassNative.nativeProcessData(t,new byte[2],1,2));
        rejects(IllegalArgumentException.class,()->LibassNative.nativeSetStorageSize(t,0,180));
        rejects(IllegalArgumentException.class,()->LibassNative.nativeSetStorageSize(t,Integer.MAX_VALUE,180));
        rejects(IllegalArgumentException.class,()->LibassNative.nativeSetCacheLimits(t,-1,1));
        rejects(IllegalArgumentException.class,()->LibassNative.nativeSetCacheLimits(t,1,-1));
        LibassNative.nativeRelease(t);
        rejects(IllegalStateException.class,()->LibassNative.nativeProcessData(t,new byte[0],0,0));
        rejects(IllegalStateException.class,()->LibassNative.nativeSetStorageSize(t,320,180));
        rejects(IllegalStateException.class,()->LibassNative.nativeSetCacheLimits(t,0,0));
        LibassNative.nativeReleaseLibrary(lib);
        check(LibassLibraryProbe.liveLibraryCountForTrackProbe()==0,"library closed");
        System.out.println("PASS_LIBASS_DATA_GEOMETRY_CACHE three_new_descriptors self_timed_windows=2 storage_widths="+normal+","+anamorphic+" cache_limited_renders=40 live_libraries=0");
    }
}
