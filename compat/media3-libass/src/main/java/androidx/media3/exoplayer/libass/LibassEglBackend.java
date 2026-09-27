package androidx.media3.exoplayer.libass;

import android.graphics.SurfaceTexture;
import android.opengl.*;

/** Real GLES2 window context, exclusively owned by the subtitle HandlerThread. */
final class LibassEglBackend implements LibassRenderPipeline.Backend {
    private EGLDisplay display=EGL14.EGL_NO_DISPLAY;
    private EGLContext context=EGL14.EGL_NO_CONTEXT;
    private EGLSurface surface=EGL14.EGL_NO_SURFACE;
    private LibassGlTextures textures;
    LibassEglBackend(SurfaceTexture target){
        try{
            display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
            if(display==EGL14.EGL_NO_DISPLAY||!EGL14.eglInitialize(display,new int[2],0,new int[2],0))throw failure("initialize");
            int[] attrs={EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,EGL14.EGL_ALPHA_SIZE,8,EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_WINDOW_BIT,EGL14.EGL_NONE};
            EGLConfig[] configs=new EGLConfig[1];int[] count=new int[1];
            if(!EGL14.eglChooseConfig(display,attrs,0,configs,0,1,count,0)||count[0]==0)throw failure("choose config");
            context=EGL14.eglCreateContext(display,configs[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);
            if(context==EGL14.EGL_NO_CONTEXT)throw failure("create context");
            surface=EGL14.eglCreateWindowSurface(display,configs[0],target,new int[]{EGL14.EGL_NONE},0);
            if(surface==EGL14.EGL_NO_SURFACE||!EGL14.eglMakeCurrent(display,surface,surface,context))throw failure("make current");
            textures=new LibassGlTextures();
        }catch(RuntimeException|Error error){try{close();}catch(RuntimeException|Error cleanup){error.addSuppressed(cleanup);}throw error;}
    }
    private static IllegalStateException failure(String operation){return new IllegalStateException("Libass EGL "+operation+": "+EGL14.eglGetError());}
    @Override public LibassFrameRenderer.Textures textures(){return textures;}
    @Override public void begin(int width,int height){textures.beginFrame(width,height);}
    @Override public void present(){textures.endFrame();if(!EGL14.eglSwapBuffers(display,surface))throw failure("swap buffers/context lost");}
    @Override public void close(){
        try{if(textures!=null){LibassGlTextures old=textures;textures=null;old.close();}}
        finally{
            if(display!=EGL14.EGL_NO_DISPLAY){
                EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT);
                if(surface!=EGL14.EGL_NO_SURFACE)EGL14.eglDestroySurface(display,surface);
                if(context!=EGL14.EGL_NO_CONTEXT)EGL14.eglDestroyContext(display,context);
                EGL14.eglReleaseThread();EGL14.eglTerminate(display);
            }
            display=EGL14.EGL_NO_DISPLAY;surface=EGL14.EGL_NO_SURFACE;context=EGL14.EGL_NO_CONTEXT;
        }
    }
}
