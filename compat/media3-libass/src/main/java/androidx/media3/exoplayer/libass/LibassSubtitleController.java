package androidx.media3.exoplayer.libass;

import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.trackselection.*;
import androidx.media3.exoplayer.text.*;
import java.util.*;

/** Reconstructed public coordinator; selection policy remains in the existing SecondaryText selector. */
public final class LibassSubtitleController implements AutoCloseable,Player.Listener {
    private final ExoPlayer player;
    private final LibassPlaybackSession session;
    private final SecondaryTextTrackSelector.Factory factory;
    private final SecondaryTextTrackSelector selector;
    private final SecondaryTextOutput output;
    private MediaItem mediaItem;
    private Runnable changed;
    private boolean closed;

    public LibassSubtitleController(ExoPlayer player,LibassPlaybackSession session,
            SecondaryTextTrackSelector.Factory factory,SecondaryTextOutput output){
        this.player=Objects.requireNonNull(player);this.session=Objects.requireNonNull(session);
        this.factory=Objects.requireNonNull(factory);this.output=Objects.requireNonNull(output);
        TrackSelector active=player.getTrackSelector();
        if(!factory.owns(active))throw new IllegalArgumentException("Player must use a SecondaryTextTrackSelector created by this factory");
        selector=(SecondaryTextTrackSelector)active;mediaItem=player.getCurrentMediaItem();
        session.bindPlayer(player);player.addListener(this);update();
    }
    @Override public void onEvents(Player sender,Player.Events events){
        if(closed||sender!=player)return;
        MediaItem current=player.getCurrentMediaItem();
        if(!Objects.equals(current,mediaItem)){
            mediaItem=current;factory.reset();output.reset();
        }
        if(player.getPlaybackState()==Player.STATE_IDLE||player.getPlaybackState()==Player.STATE_ENDED)output.reset();
        update();
    }
    private void update(){
        if(closed)return;
        TrackSelectionOverride selected=getSecondaryTextTrackSelectionOverride();
        Format format=selected==null?null:selected.mediaTrackGroup.getFormat(selected.trackIndices.get(0));
        session.setSecondaryFormat(player,format!=null&&LibassSubtitleParserFactory.isAss(format)?format:null);
        if(changed!=null)changed.run();
    }
    public TrackSelectionOverride getPrimaryTextTrackSelectionOverride(){return closed?null:selector.getPrimaryTextTrackSelectionOverride();}
    public TrackSelectionOverride getSecondaryTextTrackSelectionOverride(){return closed?null:selector.getSecondaryTextTrackSelectionOverride();}
    public List<TrackSelectionOverride> getSecondaryTextTrackSelectionOverrides(){return closed?Collections.emptyList():selector.getSecondaryTextTrackSelectionOverrides();}
    public boolean isSecondaryTextTrackSuppressed(){return !closed&&selector.isSecondaryTextTrackSuppressed();}
    public void setSecondaryTextTrackSelectionOverride(TrackSelectionOverride selection){
        if(closed)return;factory.setSecondaryTextTrackSelectionOverride(selection);output.reset();update();
    }
    public void setSecondaryTextTrackAutoSelectionEnabled(boolean enabled){
        if(closed)return;factory.setSecondaryTextTrackAutoSelectionEnabled(enabled);update();
    }
    public void setSecondaryTextOutput(TextOutput target){if(!closed)output.setOutput(target);}
    public void setOnChangedListener(Runnable listener){if(closed)return;changed=listener;if(listener!=null)listener.run();}
    @Override public void close(){
        if(closed)return;closed=true;changed=null;player.removeListener(this);
        try{factory.reset();output.close();}finally{session.setSecondaryFormat(player,null);session.detachPlayer(player);}
    }
}
