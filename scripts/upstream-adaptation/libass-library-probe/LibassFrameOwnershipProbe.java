/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Real libass JNI + unchanged reference frame behavior (host annotations
 * removed for javac only). Test two concurrent owners, not the Android
 * geometry or previous single-thread fixtures.
 */
public final class LibassFrameOwnershipProbe {
    private static void check(boolean b,String label){if(!b)throw new AssertionError(label);}
    private static final String HEADER=
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n"
        +"[V4+ Styles]\n"
        +"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        +"Style: Default,DejaVu Sans,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n"
        +"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n";
    private static long create(long lib,String text){
        long track=LibassNative.nativeCreate(lib,null,"DejaVu Sans");
        LibassNative.nativeSetStorageSize(track,320,180);
        LibassNative.nativeSetFrameSize(track,320,180,0,0,320,180,1);
        byte[] bytes=(HEADER+"Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,"+text+"\n").getBytes(StandardCharsets.UTF_8);
        LibassNative.nativeProcessData(track,bytes,0,bytes.length);
        return track;
    }
    private static long digest(LibassFrame f){
        check(f!=null&&!f.isEmpty(),"nonempty actual frame");
        long h=0xcbf29ce484222325L;boolean ink=false;
        for(LibassImage i:f.images){
            check(i.bitmap!=null&&i.bitmap.length==i.width*i.height&&i.textureId==0,"actual CPU bitmap");
            for(int v:new int[]{i.x,i.y,i.width,i.height,i.color})h=(h^v)*1099511628211L;
            for(byte b:i.bitmap){ink|=b!=0;h=(h^(b&255))*1099511628211L;}
        }
        check(ink,"real pixel coverage");return h;
    }
    private static LibassFrame render(long track,long ms){
        return LibassNative.nativeRenderFrame(track,ms,true,true);
    }
    private static void stale(long t){
        try{render(t,1000);throw new AssertionError("retired track accepted");}
        catch(IllegalStateException expected){}
    }
    private static Callable<Integer> worker(long track,long expected,LibassFrame saved,
        CyclicBarrier ready,CyclicBarrier race,CountDownLatch closed){
        return ()->{
            ready.await(20,TimeUnit.SECONDS);
            int actual=0;
            for(int i=0;i<60;i++){
                LibassFrame next=render(track,1100);
                check(digest(next)==expected,"cross-track pixels changed");
                check(next.images.get(0).bitmap!=saved.images.get(0).bitmap,"native frame aliases Java buffer");
                Arrays.fill(next.images.get(0).bitmap,(byte)0);
                check(digest(saved)==expected,"saved image overwritten by another Java array");
                check(render(track,2100).isEmpty(),"empty interval");
                actual+=2;
            }
            race.await(20,TimeUnit.SECONDS);
            // Release can win or this render can win; neither may read freed
            // memory. Do not assert an artificial exact native interleaving.
            try{check(digest(render(track,1200))==expected,"render in retirement race");actual++;}
            catch(IllegalStateException expectedRace){}
            check(closed.await(20,TimeUnit.SECONDS),"close completion");
            stale(track);check(digest(saved)==expected,"saved data survives native close");
            return actual;
        };
    }
    public static void main(String[] args)throws Exception{
        System.load(Paths.get(args[0]).toAbsolutePath().toString());
        byte[] font=Files.readAllBytes(Paths.get(args[1]));
        long lib=LibassNative.nativeCreateLibrary(null);
        LibassNative.nativeAddFont(lib,"DejaVuSans.ttf",font);
        long a=create(lib,"First owner"),b=create(lib,"Independent other owner");
        LibassFrame savedA=render(a,1000),savedB=render(b,1000);
        long da=digest(savedA),db=digest(savedB);check(da!=db,"independent data");
        ExecutorService pool=Executors.newFixedThreadPool(2);
        CyclicBarrier ready=new CyclicBarrier(3),race=new CyclicBarrier(3);
        CountDownLatch closed=new CountDownLatch(1);
        try{
            Future<Integer> fa=pool.submit(worker(a,da,savedA,ready,race,closed));
            Future<Integer> fb=pool.submit(worker(b,db,savedB,ready,race,closed));
            ready.await(20,TimeUnit.SECONDS);
            // The active tracks retain the library even after Java owner retires.
            LibassNative.nativeReleaseLibrary(lib);
            race.await(30,TimeUnit.SECONDS);
            LibassNative.nativeRelease(a);LibassNative.nativeRelease(b);closed.countDown();
            int rendered=fa.get(30,TimeUnit.SECONDS)+fb.get(30,TimeUnit.SECONDS);
            check(rendered>=240,"render count");
            check(digest(savedA)==da&&digest(savedB)==db,"retained frame bytes");
            check(LibassLibraryProbe.liveLibraryCountForTrackProbe()==0,"last native owner released");
            System.out.println("PASS_REFERENCE_CONCURRENT_FRAME_OWNERSHIP renders="+rendered+" tracks=2 retired_handles=2 saved_arrays=2 live_libraries=0");
        }finally{
            closed.countDown();pool.shutdownNow();
            LibassNative.nativeRelease(a);LibassNative.nativeRelease(b);LibassNative.nativeReleaseLibrary(lib);
        }
    }
}
