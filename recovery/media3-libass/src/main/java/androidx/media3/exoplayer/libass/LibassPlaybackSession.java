package androidx.media3.exoplayer.libass;

import androidx.media3.common.*;
import androidx.media3.exoplayer.Renderer;
import androidx.media3.extractor.ExtractorsFactory;
import androidx.media3.extractor.text.SubtitleParser;
import java.util.*;

/**
 * Reconstructed upstream-missing public session, based on published5.6.5 sk1/rk1/qk1.
 * Media lifetime lives only in LibassMediaOwnership. Binding generations additionally reject
 * callbacks queued before detach/rebind, including rebinding the same Player instance.
 */
public final class LibassPlaybackSession implements AutoCloseable {
    public static final class MediaComponents {
        public final ExtractorsFactory extractorsFactory;
        public final SubtitleParser.Factory subtitleParserFactory;
        private MediaComponents(ExtractorsFactory extractors,SubtitleParser.Factory parsers){extractorsFactory=extractors;subtitleParserFactory=parsers;}
    }
    private static final class OwnedMedia implements LibassMediaOwnership.Resource {
        final LibassMediaState state;
        OwnedMedia(LibassMediaState state){this.state=state;}
        @Override public void close(){state.close();}
    }
    final LibassConfiguration configuration;
    private final boolean available;
    private final LibassMediaOwnership<MediaItem,OwnedMedia> ownership;
    private Player player;
    private Player.Listener playerListener;
    private long generation,positionUs,primaryOffsetUs,secondaryOffsetUs,renderVersion;
    private boolean closed,overrideScale;
    private float scale=1f,primaryPosition,secondaryPosition=1f;
    private LibassStyleOverride style;
    private String styleFamily;
    private Runnable renderInvalidation;

    public LibassPlaybackSession(LibassConfiguration configuration,boolean enabled){
        this.configuration=Objects.requireNonNull(configuration);
        available=enabled&&LibassLibrary.isAvailable();
        ownership=new LibassMediaOwnership<>(item->{
            LibassMediaState state=new LibassMediaState(configuration,available);
            applySettings(state);return new OwnedMedia(state);
        });
    }
    public synchronized boolean isAvailable(){return available&&!closed;}
    private void checkAvailable(){if(closed)throw new IllegalStateException("Libass playback session is closed");if(!available)throw new IllegalStateException("libmedia3ass is unavailable");}
    public synchronized MediaComponents createMediaComponents(MediaItem item,ExtractorsFactory extractors){
        checkAvailable();Objects.requireNonNull(extractors);
        LibassMediaState state=ownership.createComponents(item).state;
        LibassSubtitleParserFactory parser=new LibassSubtitleParserFactory(state);
        return new MediaComponents(new LibassExtractorsFactory(extractors,state,parser),parser);
    }
    public synchronized void setPreloadMediaItem(MediaItem item){if(isAvailable())ownership.setPreload(item);}
    synchronized void bindPlayer(Player next){
        if(!isAvailable()||player==next)return;
        Player old=player;Player.Listener oldListener=playerListener;
        player=next;playerListener=null;long binding=++generation;
        if(old!=null)old.removeListener(oldListener);
        ownership.bindPlayer(next);
        if(next!=null){
            playerListener=new Player.Listener(){
                @Override public void onEvents(Player sender,Player.Events events){refresh(sender,binding,events.contains(Player.EVENT_TIMELINE_CHANGED));}
            };
            next.addListener(playerListener);refresh(next,binding,true);
        }
        invalidate();
    }
    synchronized void detachPlayer(Player sender){if(player==sender)bindPlayer(null);}
    private synchronized void refresh(Player sender,long binding,boolean timelineChanged){
        if(!accepts(sender,binding))return;
        if(timelineChanged){
            Timeline timeline=sender.getCurrentTimeline();Timeline.Window window=new Timeline.Window();List<MediaItem> items=new ArrayList<>();
            for(int i=0;i<timeline.getWindowCount();i++)items.add(timeline.getWindow(i,window).mediaItem);
            ownership.updateTimeline(sender,items);
        }
        ownership.updateCurrent(sender,sender.getCurrentMediaItem());
        updateFormats(sender,null,false);invalidate();
    }
    private boolean accepts(Player sender,long binding){return isAvailable()&&sender!=null&&sender==player&&binding==generation;}
    synchronized void setSecondaryFormat(Player sender,Format secondary){
        if(sender!=player||!isAvailable())return;updateFormats(sender,secondary,true);invalidate();
    }
    private void updateFormats(Player sender,Format requested,boolean replaceSecondary){
        LibassMediaState media=activeMedia();if(media==null)return;
        Format secondary=replaceSecondary?requested:media.secondaryFormat();
        Format canonical=null,primary=null;
        Tracks tracks=sender.getCurrentTracks();
        for(Tracks.Group group:tracks.getGroups())if(group.getType()==C.TRACK_TYPE_TEXT)
            for(int i=0;i<group.length;i++){
                Format format=group.getTrackFormat(i);
                if(Objects.equals(format,secondary)&&LibassSubtitleParserFactory.isAss(format))canonical=format;
            }
        primarySearch: for(Tracks.Group group:tracks.getGroups())if(group.getType()==C.TRACK_TYPE_TEXT)
            for(int i=0;i<group.length;i++)if(group.isTrackSelected(i)){
                Format format=group.getTrackFormat(i);
                if(LibassSubtitleParserFactory.isAss(format)&&!Objects.equals(format,canonical)){primary=format;break primarySearch;}
            }
        media.setPrimaryFormat(primary);media.setSecondaryFormat(canonical);
    }
    synchronized LibassMediaState activeMedia(){OwnedMedia owned=ownership.active();return owned==null?null:owned.state;}
    synchronized long positionUs(){return positionUs-primaryOffsetUs;}
    synchronized boolean isRendering(){return isAvailable()&&player!=null&&(player.getPlaybackState()==Player.STATE_READY||player.getPlaybackState()==Player.STATE_BUFFERING);}
    synchronized void setRenderInvalidation(Runnable callback){renderInvalidation=closed?null:callback;}
    synchronized long renderVersion(){return renderVersion;}
    private void invalidate(){++renderVersion;if(renderInvalidation!=null)renderInvalidation.run();}
    public synchronized Renderer createClockRenderer(){
        checkAvailable();
        return new LibassClockRenderer(new LibassClockRenderer.Listener(){
            private long binding=-1;
            @Override public void enabled(){synchronized(LibassPlaybackSession.this){binding=generation;}}
            @Override public void disabled(){synchronized(LibassPlaybackSession.this){binding=-1;}}
            @Override public void position(long timeUs,boolean force){synchronized(LibassPlaybackSession.this){
                if(binding!=generation||!isAvailable())return;positionUs=timeUs;if(force)invalidate();else if(renderInvalidation!=null)renderInvalidation.run();
            }}
            @Override public void offset(long offsetMs){synchronized(LibassPlaybackSession.this){
                if(binding!=generation||!isAvailable())return;setTextOffsetsUs(offsetMs*1000,offsetMs*1000);
            }}
        });
    }
    synchronized void setTextOffsetsUs(long primary,long secondary){
        if(closed)return;primaryOffsetUs=primary;secondaryOffsetUs=secondary;
        ownership.forEach(value->value.state.setSecondaryOffsetUs(secondary-primary));invalidate();
    }
    private void applySettings(LibassMediaState media){
        media.setFontScale(scale,overrideScale);media.setBottomPositionFraction(primaryPosition);
        media.setSecondaryBottomPositionFraction(secondaryPosition);media.setStyleOverride(style,styleFamily);
        media.setSecondaryOffsetUs(secondaryOffsetUs-primaryOffsetUs);
    }
    public synchronized void setFontScale(float scale,boolean override){
        if(!Float.isFinite(scale)||scale<=0)throw new IllegalArgumentException("Invalid font scale");
        if(closed)return;this.scale=scale;overrideScale=override;ownership.forEach(value->value.state.setFontScale(scale,override));invalidate();
    }
    public synchronized void setBottomPositionFraction(float value){
        if(!Float.isFinite(value))throw new IllegalArgumentException("Invalid bottom position");
        if(closed)return;primaryPosition=value;ownership.forEach(media->media.state.setBottomPositionFraction(value));invalidate();
    }
    public synchronized void setSecondaryBottomPositionFraction(float value){
        if(!Float.isFinite(value))throw new IllegalArgumentException("Invalid secondary bottom position");
        if(closed)return;secondaryPosition=value;ownership.forEach(media->media.state.setSecondaryBottomPositionFraction(value));invalidate();
    }
    synchronized void setStyleOverride(LibassStyleOverride value,String family){
        LibassConfiguration.family(family);if(closed)return;style=value;styleFamily=family;ownership.forEach(media->media.state.setStyleOverride(value,family));invalidate();
    }
    @Override public synchronized void close(){
        if(closed)return;closed=true;++generation;renderInvalidation=null;
        Player old=player;Player.Listener listener=playerListener;player=null;playerListener=null;
        try{if(old!=null)old.removeListener(listener);}finally{ownership.close();}
    }
}
