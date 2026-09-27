package androidx.media3.exoplayer.libass;
import static org.junit.Assert.*;
import androidx.media3.common.*;
import androidx.media3.common.text.*;
import androidx.media3.exoplayer.*;
import androidx.media3.exoplayer.source.*;
import androidx.media3.exoplayer.trackselection.*;
import androidx.media3.exoplayer.text.*;
import androidx.media3.exoplayer.upstream.DefaultBandwidthMeter;
import java.lang.reflect.Proxy;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassControllerTest {
 public TrackGroup p=group("p","zh"),s=group("s","en"),other=group("other","fr");
 SecondaryTextTrackSelector.Factory factory;SecondaryTextTrackSelector selector;public LibassPlaybackSession session;public LibassSubtitleController controller;public SecondaryTextOutput output;
 MediaItem item=MediaItem.fromUri("https://example.invalid/active");Tracks tracks=Tracks.EMPTY;List<Player.Listener> listeners=new ArrayList<>();public ExoPlayer player;
 static TrackGroup group(String id,String language){return new TrackGroup(id,new Format.Builder().setId(id).setLanguage(language).setSampleMimeType(MimeTypes.TEXT_SSA).setContainerMimeType(MimeTypes.VIDEO_MP4).build());}
 static RendererCapabilities renderer(){return new RendererCapabilities(){public String getName(){return "Text";}public int getTrackType(){return C.TRACK_TYPE_TEXT;}public int supportsFormat(Format f){return RendererCapabilities.create(C.FORMAT_HANDLED);}public int supportsMixedMimeTypeAdaptation(){return ADAPTIVE_NOT_SUPPORTED;}};}
 @Before public void setup(){
  new LibassSessionTest().reset();
  factory=new SecondaryTextTrackSelector.Factory(context->{DefaultTrackSelector d=new DefaultTrackSelector(context);d.setParameters(d.buildUponParameters().setOverrideForType(new TrackSelectionOverride(p,0)).build());return d;});
  selector=createSelector();session=LibassSessionTest.session();output=new SecondaryTextOutput();
  player=(ExoPlayer)Proxy.newProxyInstance(ExoPlayer.class.getClassLoader(),new Class<?>[]{ExoPlayer.class},(obj,method,args)->{
   switch(method.getName()){
    case "getTrackSelector":return selector;case "getCurrentMediaItem":return item;case "getCurrentTracks":return tracks;
    case "getCurrentTimeline":return new SinglePeriodTimeline(1000000,true,false,false,null,item);
    case "getVideoSize":return new VideoSize(1920,1080);case "getPlaybackState":return Player.STATE_READY;case "addListener":listeners.add((Player.Listener)args[0]);return null;
    case "removeListener":listeners.remove(args[0]);return null;case "equals":return obj==args[0];case "hashCode":return System.identityHashCode(obj);case "toString":return "Controller test player";
    default:throw new AssertionError(method.getName());
   }
  });
  controller=new LibassSubtitleController(player,session,factory,output);
 }
 SecondaryTextTrackSelector createSelector(){SecondaryTextTrackSelector selected=(SecondaryTextTrackSelector)factory.createTrackSelector(RuntimeEnvironment.getApplication());selected.init(parameters->{},new DefaultBandwidthMeter.Builder(RuntimeEnvironment.getApplication()).build());selected.onParametersActivated(selected.getParameters());return selected;}
 public void activate(TrackGroup... groups)throws Exception {TrackSelectorResult r=selector.selectTracks(new RendererCapabilities[]{renderer(),renderer()},new TrackGroupArray(groups),new MediaSource.MediaPeriodId("p"),Timeline.EMPTY);selector.onSelectionActivated(r.info);tracks=r.tracks;event(Player.EVENT_TRACKS_CHANGED);}
 void event(int flag){Player.Events events=new Player.Events(new FlagSet.Builder().add(flag).build());for(Player.Listener listener:new ArrayList<>(listeners))listener.onEvents(player,events);}
 @After public void close(){controller.close();session.close();selector.release();}
 @Test public void primaryOnly(){try{activate(p,s);}catch(Exception e){throw new AssertionError(e);}assertEquals(p,controller.getPrimaryTextTrackSelectionOverride().mediaTrackGroup);assertNull(controller.getSecondaryTextTrackSelectionOverride());}
 @Test public void manualSecondaryAndPrimaryBothReachMedia()throws Exception {
  controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(s,0));activate(p,s);
  assertEquals(s,controller.getSecondaryTextTrackSelectionOverride().mediaTrackGroup);assertEquals(s.getFormat(0),session.activeMedia().secondaryFormat());
  LibassMediaState media=session.activeMedia();media.processTimedData(p.getFormat(0),new byte[]{1},0,1,0);media.processTimedData(s.getFormat(0),new byte[]{1},0,1,0);media.setFrameSize(100,100,100,100,0,0,100,100);LibassFrameSet frames=media.renderFrames(0,true);assertNotNull(frames.primary);assertNotNull(frames.secondary);
 }
 @Test public void autoSecondaryUsesExistingFactoryPolicy()throws Exception {controller.setSecondaryTextTrackAutoSelectionEnabled(true);activate(p,s);assertEquals(s,controller.getSecondaryTextTrackSelectionOverride().mediaTrackGroup);}
 @Test public void duplicateTrackGroupAndUnavailableManualAreSuppressed()throws Exception {
  controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(p,0));activate(p,s);assertNull(controller.getSecondaryTextTrackSelectionOverride());assertTrue(controller.isSecondaryTextTrackSuppressed());
  controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(other,0));activate(p,s);assertTrue(controller.isSecondaryTextTrackSuppressed());assertNull(session.activeMedia().secondaryFormat());
 }
 @Test public void mediaChangeResetsManualAndClearsCues()throws Exception {
  controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(s,0));activate(p,s);List<CueGroup> received=new ArrayList<>();controller.setSecondaryTextOutput(received::add);output.onCues(new CueGroup(Collections.singletonList(new Cue.Builder().setText("old").build()),0));
  item=MediaItem.fromUri("https://example.invalid/new");tracks=Tracks.EMPTY;event(Player.EVENT_MEDIA_ITEM_TRANSITION);assertNull(controller.getSecondaryTextTrackSelectionOverride());assertTrue(received.get(received.size()-1).cues.isEmpty());assertNull(session.activeMedia().secondaryFormat());
 }
 @Test public void preloadActivationDoesNotReplaceActiveSelection()throws Exception {
  controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(s,0));activate(p,s);SecondaryTextTrackSelector preload=createSelector();
  TrackSelectorResult result=preload.selectTracks(new RendererCapabilities[]{renderer(),renderer()},new TrackGroupArray(p,other),new MediaSource.MediaPeriodId("preload"),Timeline.EMPTY);preload.onSelectionActivated(result.info);event(Player.EVENT_TRACKS_CHANGED);assertEquals(s,controller.getSecondaryTextTrackSelectionOverride().mediaTrackGroup);preload.release();
 }
 @Test public void closeRejectsOldTracksAndOldCues()throws Exception {
  controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(s,0));activate(p,s);List<CueGroup> cues=new ArrayList<>();controller.setSecondaryTextOutput(cues::add);List<Player.Listener> old=new ArrayList<>(listeners);controller.close();int count=cues.size();
  for(Player.Listener listener:old)listener.onEvents(player,new Player.Events(new FlagSet.Builder().add(Player.EVENT_TRACKS_CHANGED).build()));output.onCues(new CueGroup(Collections.singletonList(new Cue.Builder().setText("late").build()),0));assertEquals(count,cues.size());assertNull(controller.getSecondaryTextTrackSelectionOverride());assertTrue(controller.getSecondaryTextTrackSelectionOverrides().isEmpty());assertTrue(listeners.isEmpty());
 }
 @Test public void factoryOwnershipMustMatch(){SecondaryTextTrackSelector.Factory foreign=new SecondaryTextTrackSelector.Factory(DefaultTrackSelector::new);assertThrows(IllegalArgumentException.class,()->new LibassSubtitleController(player,session,foreign,new SecondaryTextOutput()));}
 @Test public void nonAssSecondaryStaysOnOrdinaryOutput()throws Exception {
  TrackGroup vtt=new TrackGroup("vtt",new Format.Builder().setId("vtt").setSampleMimeType(MimeTypes.TEXT_VTT).build());controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(vtt,0));activate(p,vtt);assertNull(session.activeMedia().secondaryFormat());List<CueGroup> cues=new ArrayList<>();controller.setSecondaryTextOutput(cues::add);CueGroup cue=new CueGroup(Collections.singletonList(new Cue.Builder().setText("ordinary").build()),0);output.onCues(cue);assertSame(cue,cues.get(cues.size()-1));
 }
}
