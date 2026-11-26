/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;
import java.nio.file.Paths;
public final class LibassFontTimingHostProbe {
    public static void main(String[] args){
        System.load(Paths.get(args[0]).toAbsolutePath().toString());
        String config=args[1],dir=args[2];
        long lib=LibassNative.nativeCreateLibrary(config);
        try {
            LibassFontTimingChecks.run(family->new T(lib,dir,family),dir,System.out::println);
            long invalid=LibassNative.nativeCreateLibrary(config+".absent");
            try{LibassFontTimingChecks.reject(IllegalArgumentException.class,()->new T(invalid,dir,"DejaVu Sans"));}
            finally{LibassNative.nativeReleaseLibrary(invalid);}
        }finally{LibassNative.nativeReleaseLibrary(lib);}
        LibassFontTimingChecks.check(LibassLibraryProbe.liveLibraryCountForTrackProbe()==0,"last library released");
        System.out.println("PASS_REFERENCE_FONT_TIMING_HOST_ONLY live_libraries=0");
    }
    static final class T implements LibassFontTimingChecks.Track {
        long id;
        T(long lib,String dir,String family){
            id=LibassNative.nativeCreate(lib,dir,family);
            LibassNative.nativeSetStorageSize(id,640,360);
            LibassNative.nativeSetFrameSize(id,640,360,0,0,640,360,1);
        }
        public void codec(byte[] b,int o,int n){LibassNative.nativeProcessCodecPrivate(id,b,o,n);}
        public void chunk(byte[] b,int o,int n,long s,long d){LibassNative.nativeProcessChunk(id,b,o,n,s/1000,d/1000);}
        public LibassFrame render(long ms){return LibassNative.nativeRenderFrame(id,ms,true,true);}
        public void fonts(String d,String f){LibassNative.nativeSetFonts(id,d,f);}
        public void scale(boolean a,float s){LibassNative.nativeSetFontScale(id,s,a);}
        public long handle(){return id;}
        public void close(){if(id!=0){LibassNative.nativeRelease(id);id=0;}}
    }
}
