/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

import android.os.Build;
import android.util.Log;
import androidx.test.platform.app.InstrumentationRegistry;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;

/** Real pinned reference Java caller/DTOs on Android; not the full player. */
public final class LibassReferenceAndroidTest {
    private static final String TAG="AssReferenceProbe";
    private static final String HEADER=
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n"
        +"[V4+ Styles]\n"
        +"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        +"Style: Default,DejaVu Sans,24,&H400000FF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n"
        +"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n";

    private static byte[] font() throws Exception {
        try(InputStream in=InstrumentationRegistry.getInstrumentation().getTargetContext().getAssets().open("DejaVuSans.ttf");
            ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);return out.toByteArray();
        }
    }
    private static void data(LibassTrackSession t,String text){
        byte[] bytes=text.getBytes(StandardCharsets.UTF_8),pad=new byte[bytes.length+7];
        Arrays.fill(pad,(byte)0x7f);System.arraycopy(bytes,0,pad,3,bytes.length);
        t.processData(pad,3,bytes.length);Arrays.fill(pad,(byte)0);
    }
    private static long digest(LibassFrame frame){
        assertNotNull(frame);assertFalse(frame.isEmpty());
        long h=0xcbf29ce484222325L;boolean red=false,covered=false;
        for(LibassImage i:frame.images){
            assertTrue(i.width>0&&i.height>0&&i.x>=0&&i.y>=0&&i.x+i.width<=320&&i.y+i.height<=180);
            assertEquals(0,i.textureId);assertNotNull(i.bitmap);assertEquals(i.width*i.height,i.bitmap.length);
            // Actual unchanged reference GL image color consumer. This is a
            // CPU color/vertex-buffer object; no GPU texture is claimed.
            LibassGlImage gl=new LibassGlImage(0,i);
            assertEquals(i.x,gl.x);assertEquals(i.y,gl.y);assertEquals(i.width,gl.width);assertEquals(i.height,gl.height);
            assertEquals(((i.color>>>24)&255)/255f,gl.red,0f);
            assertEquals(1f-(i.color&255)/255f,gl.alpha,0f);
            if(i.color==0xff000040){red=true;assertEquals(1f,gl.red,0f);assertEquals(0f,gl.green,0f);assertEquals(0f,gl.blue,0f);assertEquals(191f/255f,gl.alpha,0.00001f);}
            for(int n:new int[]{i.x,i.y,i.width,i.height,i.color})h=(h^n)*1099511628211L;
            for(byte b:i.bitmap){covered|=b!=0;h=(h^(b&255))*1099511628211L;}
        }
        assertTrue(red);assertTrue(covered);return h;
    }
    private static int width(LibassFrame f){
        int lo=320,hi=0;for(LibassImage i:f.images){lo=Math.min(lo,i.x);hi=Math.max(hi,i.x+i.width);}return hi-lo;
    }
    private static int bottom(LibassFrame f){
        int b=0;for(LibassImage i:f.images)b=Math.max(b,i.y+i.height);return b;
    }
    private static void reject(Class<? extends Throwable> type,Runnable r){
        try{r.run();}catch(Throwable e){if(type.isInstance(e))return;throw e;}
        fail("expected "+type.getName());
    }
    @Test public void actualCallerCompleteFramesGeometryAndOwnership() throws Exception {
        assertEquals(34,Build.VERSION.SDK_INT);assertEquals("x86_64",Build.SUPPORTED_ABIS[0]);
        assertTrue(LibassLibrary.isAvailable());
        LibassNativeLibrary lib=new LibassNativeLibrary(null);
        byte[] font=font();lib.addFont("DejaVuSans.ttf",font);Arrays.fill(font,(byte)0);
        LibassTrackSession a=new LibassTrackSession(lib,"","primary","DejaVu Sans");
        LibassTrackSession b=new LibassTrackSession(lib,"","secondary","DejaVu Sans");
        try {
            reject(IllegalStateException.class,()->a.renderFrame(1000,true));
            for(LibassTrackSession t:new LibassTrackSession[]{a,b}){
                t.setStorageSize(320,180);t.setFrameSize(320,180,0,0,320,180,1);
            }
            data(a,HEADER+"Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,First real frame\n");
            data(b,HEADER+"Dialogue: 0,0:00:03.00,0:00:04.00,Default,,0,0,0,,Other subtitle\n");
            LibassFrame before=a.renderFrame(999,true);assertTrue(before.changed);assertTrue(before.isEmpty());
            LibassFrame saved=a.renderFrame(1000,true);assertTrue(saved.changed);long first=digest(saved);
            LibassFrame same=a.renderFrame(1100,false);assertFalse(same.changed);assertEquals(first,digest(same));
            assertNotSame(saved.images.get(0).bitmap,same.images.get(0).bitmap);
            LibassFrame other=b.renderFrame(3000,true);assertTrue(other.changed);long second=digest(other);assertNotEquals(first,second);
            int w=width(saved),bot=bottom(saved);
            a.setFrameSize(320,180,0,0,320,180,1.5);
            LibassFrame par=a.renderFrame(1100,true);assertTrue(par.changed);assertNotEquals(w,width(par));assertNotEquals(first,digest(par));
            a.setFrameSize(320,180,20,20,300,145,1);
            LibassFrame inset=a.renderFrame(1100,true);assertTrue(inset.changed);assertTrue(bottom(inset)<bot);assertNotEquals(first,digest(inset));
            a.setFrameSize(320,180,0,0,320,180,1);
            assertEquals(first,digest(a.renderFrame(1100,true)));
            LibassFrame end=a.renderFrame(2000,true);assertTrue(end.changed);assertTrue(end.isEmpty());
            LibassFrame empty=a.renderFrame(2100,true);assertFalse(empty.changed);assertTrue(empty.isEmpty());
            LibassFrame backwards=a.renderFrame(1000,true);assertTrue(backwards.changed);assertEquals(first,digest(backwards));
            reject(UnsupportedOperationException.class,()->LibassNative.nativeRenderFrame(a.trackPtr,1100,true,false));
            reject(UnsupportedOperationException.class,()->a.setFrameSize(320,180,-5,0,320,180,1));
            reject(UnsupportedOperationException.class,()->a.setFrameSize(640,360,0,0,640,360,1));
            reject(IllegalArgumentException.class,()->LibassNative.nativeSetFrameSize(a.trackPtr,320,180,0,0,0,180,1));
            // Existing reference owner close while real native track lives.
            lib.close();
            assertEquals(second,digest(b.renderFrame(3100,true)));
            a.close();reject(IllegalStateException.class,()->a.renderFrame(1000,true));
            b.close();assertEquals(first,digest(saved));assertEquals(second,digest(other));
            Log.i(TAG,"PASS_REFERENCE_FRAME_OWNERSHIP changed_empty_backward=1 copied_arrays=1 tracks=2 saved_after_close=1");
            Log.i(TAG,"PASS_REFERENCE_DISPLAY_GEOMETRY base_width="+w+" par_width="+width(par)+" bottom="+bot+" inset_bottom="+bottom(inset));
            Log.i(TAG,"PASS_REFERENCE_REAL_JAVA_CALLER_CPU_FRAME Android34 x86_64 synchronous_only");
        } finally {a.close();b.close();lib.close();}
    }
}
