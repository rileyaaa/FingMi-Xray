package androidx.media3.exoplayer.libass;

import android.opengl.GLES20;
import java.util.*;

public final class GlTexturesTest {
    static void check(boolean b){if(!b)throw new AssertionError();}
    static void failure(Runnable r){try{r.run();throw new AssertionError();}catch(IllegalStateException expected){}}
    static void noLeaks(){check(GLES20.shaders.isEmpty()&&GLES20.programs.isEmpty()&&GLES20.textures.isEmpty());}
    static LibassFrame frame(int color){return new LibassFrame(1,new LibassImage[]{new LibassImage(160,90,2,2,color,new byte[]{0,64,(byte)128,(byte)255},0)});}
    public static void main(String[]args){
        for(int fail=1;fail<=2;fail++){
            GLES20.reset();GLES20.failShader=fail;failure(LibassGlTextures::new);noLeaks();
        }
        GLES20.reset();GLES20.failLink=1;failure(LibassGlTextures::new);noLeaks();
        System.out.println("PASS shader compile/link failure cleanup");

        GLES20.reset();LibassGlTextures gl=new LibassGlTextures();check(GLES20.shaders.isEmpty());
        check(GLES20.sources.values().stream().anyMatch(s->s.contains("texture2D(uTexture, vTexCoord).a")&&s.contains("uColor.a * coverage")));
        LibassGlTextures failedUploadBackend=gl;
        GLES20.uploadError=1285;failure(()->failedUploadBackend.upload(new byte[4],2,2));check(GLES20.textures.isEmpty()&&GLES20.bound==0);
        gl.close();gl.close();noLeaks();System.out.println("PASS failed GL upload deletes created texture");

        GLES20.reset();gl=new LibassGlTextures();LibassFrameRenderer renderer=new LibassFrameRenderer(gl);Object media=new Object();renderer.bind(media);
        renderer.update(media,new LibassFrameSet(frame(0xff000000),frame(0x00ff0080)),640,360);
        check(Arrays.equals(GLES20.uploaded,new byte[]{0,64,(byte)128,(byte)255})&&GLES20.alignment==1);
        check(GLES20.parameters.equals(Map.of(10241,9729,10240,9729,10242,33071,10243,33071)));
        gl.beginFrame(1920,1080);renderer.draw();gl.endFrame();
        check(Arrays.equals(GLES20.viewport,new int[]{0,0,1920,1080}));
        check(Arrays.equals(GLES20.blend,new int[]{770,771,1,771}));
        check(Arrays.equals(GLES20.clearColor,new float[]{0,0,0,0})&&GLES20.draws.size()==2);
        check(Arrays.equals(GLES20.colors.get(0),new float[]{1,0,0,1}));
        check(Arrays.equals(GLES20.colors.get(1),new float[]{0,1,0,1-128/255f}));
        float[] positions=GLES20.positions.get(0);check(positions[0]==-0.5f&&positions[1]==0.5f);
        check(positions[2]==162*2f/640-1&&positions[5]==1-92*2f/360);
        check(GLES20.bound==0);System.out.println("PASS coverage upload, geometry, dual draw order and alpha composition calls");
        renderer.update(media,new LibassFrameSet(new LibassFrame(1,null),new LibassFrame(1,null)),640,360);
        gl.beginFrame(1920,1080);renderer.draw();gl.endFrame();check(GLES20.clears==2&&GLES20.draws.size()==2&&GLES20.textures.isEmpty());
        renderer.close();gl.close();noLeaks();System.out.println("PASS disappearance clears the surface without redrawing old glyphs");
        System.out.println("PASS GLES backend API tests (recording API; no EGL/display claim)");
    }
}
