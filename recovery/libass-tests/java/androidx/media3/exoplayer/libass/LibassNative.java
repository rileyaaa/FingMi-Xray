package androidx.media3.exoplayer.libass;
import java.util.*;
/** JVM-only instrumented native boundary. Never packaged in an AAR. */
final class LibassNative {
 static final List<String> log=Collections.synchronizedList(new ArrayList<>());
 static final Set<Long> libraries=new HashSet<>();
 static final Map<Long,Long> tracks=new HashMap<>();
 static long next=1;static String fail;static Runnable duringData;
 static void reset(){log.clear();libraries.clear();tracks.clear();next=1;fail=null;duringData=null;}
 static void call(String name,long handle){log.add(name+":"+handle);if(name.equals(fail)){fail=null;throw new IllegalStateException("injected "+name);}}
 static void track(long h){if(!tracks.containsKey(h)||!libraries.contains(tracks.get(h)))throw new AssertionError("native use after release");}
 static long nativeCreateLibrary(String dir){call("library",0);long h=next++;libraries.add(h);return h;}
 static long nativeCreate(long library,String config,String family){if(!libraries.contains(library))throw new AssertionError();call("create",library);long h=next++;tracks.put(h,library);return h;}
 static void nativeRelease(long h){track(h);tracks.remove(h);call("release",h);}
 static void nativeReleaseLibrary(long h){if(tracks.containsValue(h))throw new AssertionError("library freed before tracks");libraries.remove(h);call("releaseLibrary",h);}
 static void nativeAddFont(long h,String name,byte[] data){if(!libraries.contains(h))throw new AssertionError();call("font",h);}
 static void nativeSetFonts(long h,String config,String family){track(h);call("fonts",h);}
 static void nativeProcessCodecPrivate(long h,byte[] data,int off,int len){track(h);call("codec",h);}
 static void nativeProcessData(long h,byte[] data,int off,int len){track(h);call("dataBegin",h);if(duringData!=null)duringData.run();track(h);call("dataEnd",h);}
 static void nativeProcessTimedData(long h,byte[] data,int off,int len,long time){track(h);call("timed",h);log.add("timestamp:"+time);}
 static void nativeProcessChunk(long h,byte[] data,int off,int len,long time,long duration){track(h);call("chunk",h);}
 static void nativeSetFrameSize(long h,int w,int ht,int l,int t,int r,int b){track(h);call("frame",h);}
 static void nativeSetStorageSize(long h,int w,int ht){track(h);call("storage",h);}
 static void nativeSetFontScale(long h,float s,boolean o){track(h);call("scale",h);}
 static void nativeSetBottomPositionFraction(long h,float f){track(h);call("bottom",h);}
 static void nativeSetStyleOverride(long h,boolean enabled,String f,float s,int a,int b,int c,int d,float e,float g){track(h);call("style",h);}
 static void nativeSetCacheLimits(long h,int glyphs,int mb){track(h);call("cache",h);}
 static LibassFrame nativeRenderFrame(long h,long time,boolean a,boolean b){track(h);if(!b)throw new AssertionError();call("render",h);return new LibassFrame(0,null);}
}
