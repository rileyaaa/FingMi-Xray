package androidx.media3.exoplayer.libass;

import java.util.function.Supplier;

/** Render-thread context ownership around the frozen frame/texture implementations. */
final class LibassRenderPipeline implements AutoCloseable {
    interface Backend extends AutoCloseable {
        LibassFrameRenderer.Textures textures();
        void begin(int width,int height);
        void present();
        void close();
    }
    interface Source { LibassFrameSet render(boolean force); }
    private final Supplier<Backend> create;
    private Backend backend;
    private LibassFrameRenderer frames;
    private long version=Long.MIN_VALUE;
    private int width,height;
    private boolean closed;
    LibassRenderPipeline(Supplier<Backend> create){this.create=create;}
    void draw(Object identity,Source source,long nextVersion,int width,int height,int surfaceWidth,int surfaceHeight){
        if(closed)return;
        try {
            boolean force=backend==null;
            if(backend==null){backend=create.get();frames=new LibassFrameRenderer(backend.textures());}
            force|=frames.bind(identity)||version!=nextVersion||this.width!=width||this.height!=height;
            // EGL is current before native render, which may transfer native-created texture IDs.
            LibassFrameSet result=identity==null?null:source.render(force);
            frames.update(identity,result,width,height);
            backend.begin(surfaceWidth,surfaceHeight);frames.draw();backend.present();
            version=nextVersion;this.width=width;this.height=height;
        }catch(RuntimeException|Error failure){
            try{releaseContext();}catch(RuntimeException|Error cleanup){failure.addSuppressed(cleanup);}throw failure;
        }
    }
    private void releaseContext(){
        LibassFrameRenderer oldFrames=frames;Backend oldBackend=backend;frames=null;backend=null;version=Long.MIN_VALUE;
        try{if(oldFrames!=null)oldFrames.close();}finally{if(oldBackend!=null)oldBackend.close();}
    }
    @Override public void close(){if(closed)return;closed=true;releaseContext();}
}
