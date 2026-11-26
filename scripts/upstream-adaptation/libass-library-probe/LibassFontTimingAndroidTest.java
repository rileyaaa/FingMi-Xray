/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

import android.content.Context;
import android.os.Build;
import android.util.Log;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Collections;
import org.junit.Test;
import static org.junit.Assert.*;

/** Actual reference fontconfig writer and actual TrackSession, no substitute DTO. */
public final class LibassFontTimingAndroidTest {
    static final String TAG="AssFontTimingProbe";
    static void copy(Context ctx,String name,File dir)throws Exception{
        try(InputStream in=ctx.getAssets().open(name);FileOutputStream out=new FileOutputStream(new File(dir,name))){
            byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
        }
    }
    @Test public void actualConfiguredFontTimingAndScale() throws Exception {
        assertEquals(34,Build.VERSION.SDK_INT);assertEquals("x86_64",Build.SUPPORTED_ABIS[0]);
        assertTrue(LibassLibrary.isAvailable());
        Context ctx=InstrumentationRegistry.getInstrumentation().getTargetContext();
        File root=Files.createTempDirectory(ctx.getCacheDir().toPath(),"ass-config-").toFile();
        File dir=new File(root,"字幕 fonts"),cache=new File(root,"字幕 cache"),config=new File(root,"字型 config.xml");
        assertTrue(dir.mkdir());assertTrue(cache.mkdir());
        try{
            copy(ctx,"DejaVuSans.ttf",dir);copy(ctx,"DejaVuSerif.ttf",dir);
            LibassFontConfig.write(config,cache,Collections.singletonList(dir));
            String xml=new String(Files.readAllBytes(config.toPath()),StandardCharsets.UTF_8);
            assertTrue(xml.contains(dir.getAbsolutePath()));assertTrue(xml.contains(cache.getAbsolutePath()));
            assertTrue(xml.contains("/system/fonts/")&&xml.contains("/product/fonts/"));
            final String path=dir.getAbsolutePath();
            try(LibassNativeLibrary lib=new LibassNativeLibrary(config.getAbsolutePath())){
                LibassFontTimingChecks.run(family->new T(lib,path,family),path,s->Log.i(TAG,s));
                // No embedded font, system directory from the actual config.
                // Verify ordinary Roboto glyph coverage is distinct from
                // an external fixture font with the same text and timing.
                try(T system=new T(lib,path,"Roboto");T external=new T(lib,path,"DejaVu Sans")){
                    LibassFontTimingChecks.init(system,"Roboto");LibassFontTimingChecks.init(external,"DejaVu Sans");
                    LibassFontTimingChecks.chunk(system,1,LibassFontTimingChecks.TEXT,1000000,500000);
                    LibassFontTimingChecks.chunk(external,1,LibassFontTimingChecks.TEXT,1000000,500000);
                    long sys=LibassFontTimingChecks.hash(system.render(1000));
                    long ext=LibassFontTimingChecks.hash(external.render(1000));
                    assertNotEquals(ext,sys);
                    Log.i(TAG,"PASS_REFERENCE_FONTCONFIG_WRITER_SYSTEM_AND_EXTERNAL system="+Long.toHexString(sys)+" external="+Long.toHexString(ext));
                }
            }
            try(LibassNativeLibrary bad=new LibassNativeLibrary(config.getAbsolutePath()+".absent")){
                LibassFontTimingChecks.reject(IllegalArgumentException.class,()->new T(bad,path,"DejaVu Sans"));
            }
            assertEquals(0,LibassLibraryProbe.liveLibraryCountForTrackProbe());
            Log.i(TAG,"PASS_REFERENCE_ANDROID_FONT_TIMING_ONLY live_libraries=0");
        }finally{delete(root);}
        assertFalse(root.exists());
        Log.i(TAG,"PASS_REFERENCE_FONT_FIXTURE_CLEANED");
    }
    static void delete(File f){
        if(f.isDirectory()){File[] children=f.listFiles();if(children!=null)for(File child:children)delete(child);}
        assertTrue(!f.exists()||f.delete());
    }
    static final class T implements LibassFontTimingChecks.Track {
        final LibassTrackSession t;
        T(LibassNativeLibrary lib,String dir,String family){
            t=new LibassTrackSession(lib,dir,"reference",family);
            try{t.setStorageSize(640,360);t.setFrameSize(640,360,0,0,640,360,1);}
            catch(RuntimeException|Error e){t.close();throw e;}
        }
        public void codec(byte[] b,int o,int n){t.processCodecPrivate(b,o,n);}
        public void chunk(byte[] b,int o,int n,long s,long d){t.processChunk(b,o,n,s,d);}
        public LibassFrame render(long ms){return t.renderFrame(ms,true);}
        public void fonts(String d,String f){t.setFonts(d,f);}
        public void scale(boolean a,float s){t.setFontScale(a,s);}
        public long handle(){return t.trackPtr;}
        public void close(){t.close();}
    }
}
