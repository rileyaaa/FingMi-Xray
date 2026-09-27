package androidx.media3.ui.libass;

import android.graphics.Rect;
import android.view.*;
import android.widget.FrameLayout;
import androidx.media3.common.*;
import androidx.media3.exoplayer.libass.*;
import androidx.media3.ui.*;
import java.util.Objects;
import java.util.function.Consumer;

/** Reconstructed public PlayerView coordinator; ordinary primary SubtitleView stays player-owned. */
public final class LibassPlayerViewController implements AutoCloseable,View.OnAttachStateChangeListener,ViewTreeObserver.OnPreDrawListener {
    interface Host {
        View root();FrameLayout overlay();Player player();View video();
    }
    interface Overlay extends AutoCloseable { View view();void geometry(int width,int height,Rect viewport);void close(); }
    interface OverlayFactory { Overlay create(android.content.Context context); }
    private final Player player;
    private final LibassPlaybackSession session;
    private final LibassSubtitleController controller;
    private final OverlayFactory createOverlay;
    private Host host;
    private Overlay ass;
    private SubtitleView secondary;
    private Consumer<SubtitleView> configurator;
    private boolean closed;
    private long generation;

    public LibassPlayerViewController(Player player,LibassPlaybackSession session,LibassSubtitleController controller){
        this(player,session,controller,context->{LibassSubtitleView view=session.createSubtitleView(context);return new Overlay(){
            public View view(){return view;}public void geometry(int w,int h,Rect r){view.setVideoGeometry(w,h,r);}public void close(){view.close();}
        };});
    }
    LibassPlayerViewController(Player player,LibassPlaybackSession session,LibassSubtitleController controller,OverlayFactory factory){
        this.player=Objects.requireNonNull(player);this.session=Objects.requireNonNull(session);this.controller=Objects.requireNonNull(controller);createOverlay=factory;
        controller.setOnChangedListener(this::update);
    }
    public void bind(PlayerView view){
        if(host!=null&&host.root()==view)return;
        bindHost(view==null?null:new Host(){public View root(){return view;}public FrameLayout overlay(){return view.getOverlayFrameLayout();}public Player player(){return view.getPlayer();}public View video(){return view.getVideoSurfaceView();}});
    }
    void bindHost(Host next){
        if(closed)throw new IllegalStateException("Libass PlayerView controller is closed");
        detachHost();host=next;++generation;
        if(next!=null){next.root().addOnAttachStateChangeListener(this);next.root().getViewTreeObserver().addOnPreDrawListener(this);update();}
    }
    private static void remove(View view){if(view!=null&&view.getParent() instanceof ViewGroup)((ViewGroup)view.getParent()).removeView(view);}
    private void clearOverlays(){
        ++generation;controller.setSecondaryTextOutput(null);
        if(secondary!=null){secondary.setCues(null);remove(secondary);secondary=null;}
        if(ass!=null){Overlay old=ass;ass=null;try{old.close();}finally{remove(old.view());}}
    }
    private void detachHost(){
        if(host!=null){host.root().removeOnAttachStateChangeListener(this);if(host.root().getViewTreeObserver().isAlive())host.root().getViewTreeObserver().removeOnPreDrawListener(this);}
        clearOverlays();host=null;
    }
    private static boolean isAss(TrackSelectionOverride selection){return selection!=null&&MimeTypes.TEXT_SSA.equals(selection.mediaTrackGroup.getFormat(selection.trackIndices.get(0)).sampleMimeType);}
    private void update(){
        if(closed||host==null)return;
        FrameLayout container=host.overlay();
        if(container==null||host.player()!=player||!host.root().isAttachedToWindow()){clearOverlays();return;}
        boolean running=player.getPlaybackState()==Player.STATE_READY||player.getPlaybackState()==Player.STATE_BUFFERING;
        TrackSelectionOverride primary=controller.getPrimaryTextTrackSelectionOverride(),second=controller.getSecondaryTextTrackSelectionOverride();
        boolean nativeAss=running&&session.isAvailable()&&(isAss(primary)||isAss(second));
        if(nativeAss&&ass==null){ass=createOverlay.create(container.getContext());container.addView(ass.view(),new FrameLayout.LayoutParams(-1,-1));}
        if(!nativeAss&&ass!=null){Overlay old=ass;ass=null;try{old.close();}finally{remove(old.view());}}
        boolean ordinary=running&&second!=null&&(!session.isAvailable()||!isAss(second));
        if(ordinary&&secondary==null){
            SubtitleView view=new SubtitleView(container.getContext());secondary=view;if(configurator!=null)configurator.accept(view);
            container.addView(view,new FrameLayout.LayoutParams(-1,-1));long binding=generation;
            controller.setSecondaryTextOutput(cues->{if(!closed&&binding==generation&&secondary==view)view.setCues(cues.cues);});
        }else if(!ordinary&&secondary!=null){controller.setSecondaryTextOutput(null);secondary.setCues(null);remove(secondary);secondary=null;}
        updateGeometry();
    }
    private void updateGeometry(){
        if(ass==null||host==null)return;
        View surface=host.video();Rect viewport=new Rect();
        if(surface!=null&&surface.getWidth()>0&&surface.getHeight()>0){
            int[] video=new int[2],overlay=new int[2];surface.getLocationInWindow(video);host.overlay().getLocationInWindow(overlay);
            viewport.set(video[0]-overlay[0],video[1]-overlay[1],video[0]-overlay[0]+surface.getWidth(),video[1]-overlay[1]+surface.getHeight());
        }
        VideoSize size=player.getVideoSize();ass.geometry(size.width,size.height,viewport);
    }
    public void setStyleOverride(CaptionStyleCompat style,String family){if(closed)throw new IllegalStateException("Controller closed");session.setCaptionStyle(style,family);}
    public void setSecondarySubtitleViewConfigurator(Consumer<SubtitleView> configurator){
        if(closed)throw new IllegalStateException("Controller closed");this.configurator=configurator;if(secondary!=null&&configurator!=null)configurator.accept(secondary);
    }
    @Override public void onViewAttachedToWindow(View view){if(host!=null&&host.root()==view)update();}
    @Override public void onViewDetachedFromWindow(View view){if(host!=null&&host.root()==view)clearOverlays();}
    @Override public boolean onPreDraw(){update();return true;}
    @Override public void close(){if(closed)return;closed=true;controller.setOnChangedListener(null);detachHost();configurator=null;}
}
