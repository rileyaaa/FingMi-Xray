package androidx.media3.exoplayer.libass;

import android.content.Context;
import android.graphics.Rect;
import android.graphics.SurfaceTexture;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Log;
import android.view.TextureView;
import java.util.IdentityHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

/** Reconstructed al1/zk1 view ownership. Surface callbacks are fenced by object identity. */
public final class LibassSubtitleView extends TextureView implements AutoCloseable,TextureView.SurfaceTextureListener {
    private final LibassPlaybackSession session;
    private final IdentityHashMap<SurfaceTexture,Boolean> known=new IdentityHashMap<>();
    private volatile Worker current;
    private volatile Geometry geometry=new Geometry(0,0,0,0,new Rect());
    private volatile boolean closed;
    LibassSubtitleView(Context context,LibassPlaybackSession session){super(context);this.session=session;setOpaque(false);setSurfaceTextureListener(this);}
    public void setVideoGeometry(int storageWidth,int storageHeight,Rect viewport){
        geometry=new Geometry(getWidth(),getHeight(),storageWidth,storageHeight,viewport);requestRender();
    }
    void requestRender(){Worker worker=current;if(!closed&&worker!=null)worker.request();}
    public boolean isClosed(){return closed;}
    @Override public void onSurfaceTextureAvailable(SurfaceTexture texture,int width,int height){
        if(closed){return;}
        Worker old=current;if(old!=null){if(old.texture==texture)return;old.stop();}
        known.put(texture,Boolean.TRUE);Worker worker=new Worker(texture,width,height);current=worker;worker.request();
    }
    @Override public void onSurfaceTextureSizeChanged(SurfaceTexture texture,int width,int height){Worker worker=current;if(worker!=null&&worker.texture==texture&&!closed){worker.width=width;worker.height=height;worker.request();}}
    @Override public boolean onSurfaceTextureDestroyed(SurfaceTexture texture){
        Worker worker=current;if(worker!=null&&worker.texture==texture){current=null;worker.stop();}
        // Known textures are released by their owning render thread exactly once, even after rebind.
        return known.remove(texture)==null;
    }
    @Override public void onSurfaceTextureUpdated(SurfaceTexture texture){}
    @Override public void close(){
        if(closed)return;closed=true;Worker worker=current;current=null;
        if(worker!=null)worker.stop();session.detachSubtitleView(this);
    }
    static final class Geometry {
        final int width,height,storageWidth,storageHeight;final Rect viewport;
        Geometry(int w,int h,int sw,int sh,Rect viewport){width=w;height=h;storageWidth=sw;storageHeight=sh;this.viewport=new Rect(viewport);}
    }
    private final class Worker {
        final SurfaceTexture texture;
        final LibassRenderGate gate=new LibassRenderGate();
        final AtomicBoolean queued=new AtomicBoolean();
        final LibassRenderPipeline pipeline;
        final HandlerThread thread;
        final Handler handler;
        volatile int width,height;
        Worker(SurfaceTexture texture,int width,int height){
            this.texture=texture;this.width=width;this.height=height;
            pipeline=new LibassRenderPipeline(()->new LibassEglBackend(texture));
            thread=new HandlerThread("LibassSubtitleRenderThread"){
                @Override public void run(){try{super.run();}finally{try{pipeline.close();}finally{texture.release();}}}
            };
            thread.start();handler=new Handler(thread.getLooper());
        }
        void request(){if(queued.compareAndSet(false,true)&&!handler.post(this::render))queued.set(false);}
        void render(){
            queued.set(false);
            gate.run(()->{
                if(closed||current!=this||width<=0||height<=0)return;
                try{synchronized(session){
                    if(closed||current!=this)return;
                    Geometry g=geometry;
                    LibassMediaState media=session.isRendering()?session.activeMedia():null;
                    int sw=g.storageWidth>0?g.storageWidth:width,sh=g.storageHeight>0?g.storageHeight:height;
                    int[] size=renderSize(width,height,session.configuration.maximumRenderPixels);
                    Rect viewport=scaleViewport(g.viewport,g.width,g.height,size[0],size[1]);
                    if(media!=null)media.setFrameSize(size[0],size[1],sw,sh,viewport.left,viewport.top,viewport.right,viewport.bottom);
                    long time=session.positionUs();
                    pipeline.draw(media,force->media.renderFrames(time,force),session.renderVersion(),size[0],size[1],width,height);
                }}catch(RuntimeException failure){Log.w("LibassSubtitleView","Subtitle render failed; next frame recreates the context",failure);}
            });
        }
        void stop(){
            // Wait only for an in-flight render, and invalidate before returning to session release.
            if(!gate.close())return;
            if(!handler.post(thread::quitSafely))thread.quitSafely();
        }
    }
    static int[] renderSize(int width,int height,int maximum){
        long pixels=(long)width*height;if(maximum<=0||pixels<=maximum)return new int[]{width,height};
        double scale=Math.sqrt((double)maximum/pixels);return new int[]{Math.max(1,(int)Math.floor(width*scale)),Math.max(1,(int)Math.floor(height*scale))};
    }
    static Rect scaleViewport(Rect source,int width,int height,int targetWidth,int targetHeight){
        if(source.isEmpty()||width<=0||height<=0)return new Rect(0,0,targetWidth,targetHeight);
        int l=Math.round((float)source.left*targetWidth/width),t=Math.round((float)source.top*targetHeight/height);
        return new Rect(l,t,Math.max(l+1,Math.round((float)source.right*targetWidth/width)),Math.max(t+1,Math.round((float)source.bottom*targetHeight/height)));
    }
}
