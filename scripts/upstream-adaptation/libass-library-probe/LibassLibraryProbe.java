/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;
import java.nio.file.Files;
import java.nio.file.Paths;

public final class LibassLibraryProbe {
    private static native long openFixture(long lib,String text,long start,long duration);
    private static native long renderFixture(long track,long time);
    private static native void closeFixture(long track);
    private static native int liveLibraries();
    private static void check(boolean value,String what){if(!value)throw new AssertionError(what);}
    public static void main(String[] args)throws Exception{
        System.load(Paths.get(args[0]).toAbsolutePath().toString());
        check(liveLibraries()==0,"initial");
        byte[] font=Files.readAllBytes(Paths.get(args[1]));
        long library=LibassNative.nativeCreateLibrary(null);
        check(library>0&&liveLibraries()==1,"actual library");
        LibassNative.nativeAddFont(library,"DejaVuSans.ttf",font);
        java.util.Arrays.fill(font,(byte)0); // memory font must remain usable after Java buffer changes
        long a=openFixture(library,"Primary",1000,1000);
        long b=openFixture(library,"Secondary track",3000,1500);
        check(a!=0&&b!=0&&a!=b,"separate tracks");
        long first=renderFixture(a,1500),second=renderFixture(b,3500);
        check(first!=0&&second!=0&&first!=second,"real independent subtitle pixels");
        check(renderFixture(a,500)==0&&renderFixture(a,2500)==0,"primary time window");
        check(renderFixture(b,1500)==0&&renderFixture(b,5000)==0,"secondary time window");
        LibassNative.nativeReleaseLibrary(library);
        LibassNative.nativeReleaseLibrary(library);
        check(liveLibraries()==1,"tracks retain library after handle retirement");
        try{LibassNative.nativeAddFont(library,"stale",new byte[]{1});throw new AssertionError("stale font handle");}
        catch(IllegalStateException expected){}
        check(renderFixture(a,1500)==first&&renderFixture(b,3500)==second,"render after owner release");
        closeFixture(a);closeFixture(a);
        check(liveLibraries()==1&&renderFixture(b,3500)==second,"closing one track preserves other");
        try{renderFixture(a,1500);throw new AssertionError("stale track");}
        catch(IllegalStateException expected){}
        closeFixture(b);
        check(liveLibraries()==0,"last track destroys library");
        System.out.println("PASS_LIBASS_3_JNI_REAL_RENDER shared_library=1 tracks=2 distinct_bitmaps=2 time_windows=2 live_libraries=0");
    }
}
