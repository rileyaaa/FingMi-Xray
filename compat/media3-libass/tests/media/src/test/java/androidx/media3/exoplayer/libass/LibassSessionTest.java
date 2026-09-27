package androidx.media3.exoplayer.libass;

import static org.junit.Assert.*;
import androidx.media3.common.*;
import androidx.media3.exoplayer.source.SinglePeriodTimeline;
import androidx.media3.extractor.*;
import androidx.media3.extractor.text.SubtitleParser;
import java.lang.reflect.Proxy;
import java.util.*;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassSessionTest {
 static boolean initialized;
 @Before public void reset(){LibassNative.reset();if(!initialized){LibassLibrary.setLibraries();initialized=true;}LibassLibrary.setEnabled(true);}
 static LibassPlaybackSession session(){return new LibassPlaybackSession(new LibassConfiguration.Builder().build(),true);}
 static MediaItem item(String id){return MediaItem.fromUri("https://example.invalid/"+id);}
 static Format format(String id){return new Format.Builder().setId(id).setSampleMimeType(MimeTypes.TEXT_SSA).setContainerMimeType(MimeTypes.VIDEO_MP4).build();}
 static SubtitleParser parser(LibassPlaybackSession s,MediaItem item,String id){return s.createMediaComponents(item,()->new Extractor[0]).subtitleParserFactory.create(format(id));}
 static void feed(SubtitleParser parser){parser.parse(new byte[]{1,2},0,2,2000,SubtitleParser.OutputOptions.allCues(),c->fail());}
 static final class Host {
  MediaItem current;Timeline timeline=Timeline.EMPTY;Tracks tracks=Tracks.EMPTY;final List<Player.Listener> listeners=new ArrayList<>();
  final Player player=(Player)Proxy.newProxyInstance(Player.class.getClassLoader(),new Class<?>[]{Player.class},(p,m,args)->{
   switch(m.getName()) {
    case "addListener":listeners.add((Player.Listener)args[0]);return null;
    case "removeListener":listeners.remove(args[0]);return null;
    case "getCurrentMediaItem":return current;
    case "getCurrentTimeline":return timeline;
    case "getCurrentTracks":return tracks;
    case "getPlaybackState":return Player.STATE_READY;
    case "equals":return p==args[0];case "hashCode":return System.identityHashCode(p);case "toString":return "Synthetic Player";
    default:throw new AssertionError("Unexpected Player call "+m.getName());
   }
  });
  void set(MediaItem item){current=item;timeline=item==null?Timeline.EMPTY:new SinglePeriodTimeline(1000000,true,false,false,null,item);}
  void event(int flag){for(Player.Listener l:new ArrayList<>(listeners))l.onEvents(player,new Player.Events(new FlagSet.Builder().add(flag).build()));}
 }
 @Test public void enablementCapturedAtConstructionAndDisabledSkipsAvailability(){
  LibassLibrary.setEnabled(false);LibassPlaybackSession off=session();assertFalse(off.isAvailable());LibassLibrary.setEnabled(true);assertFalse(off.isAvailable());
  LibassPlaybackSession on=session();LibassLibrary.setEnabled(false);assertTrue(on.isAvailable());assertThrows(IllegalStateException.class,()->off.createMediaComponents(item("off"),()->new Extractor[0]));off.close();on.close();
 }
 @Test public void preloadPromotionReusesParserMediaAndNativeLibrary(){
  LibassPlaybackSession s=session();MediaItem a=item("a");s.setPreloadMediaItem(a);feed(parser(s,a,"p"));Host host=new Host();host.set(a);s.bindPlayer(host.player);
  LibassMediaState active=s.activeMedia();s.setPreloadMediaItem(null);feed(parser(s,a,"p"));assertSame(active,s.activeMedia());assertEquals(1,LibassNative.libraries.size());assertEquals(1,LibassNative.tracks.size());s.close();
 }
 @Test public void emptyTimelineRetainsPreparingUntilConfirmedTimeline(){
  LibassPlaybackSession s=session();SubtitleParser preparing=parser(s,item("preparing"),"p");feed(preparing);Host host=new Host();s.bindPlayer(host.player);
  assertEquals(1,LibassNative.tracks.size());host.set(item("confirmed"));host.event(Player.EVENT_TIMELINE_CHANGED);assertTrue(LibassNative.tracks.isEmpty());int before=LibassNative.log.size();feed(preparing);assertEquals(before,LibassNative.log.size());s.close();
 }
 @Test public void priorPlayerAndSamePlayerOldGenerationCannotChangeActiveMedia(){
  LibassPlaybackSession s=session();Host a=new Host(),b=new Host();a.set(item("a"));b.set(item("b"));s.bindPlayer(a.player);Player.Listener stale=a.listeners.get(0);s.bindPlayer(b.player);LibassMediaState active=s.activeMedia();
  stale.onEvents(a.player,new Player.Events(new FlagSet.Builder().add(Player.EVENT_TIMELINE_CHANGED).build()));assertSame(active,s.activeMedia());
  Player.Listener staleSame=b.listeners.get(0);s.bindPlayer(null);s.bindPlayer(b.player);active=s.activeMedia();b.set(item("late"));staleSame.onEvents(b.player,new Player.Events(new FlagSet.Builder().add(Player.EVENT_TIMELINE_CHANGED).build()));assertSame(active,s.activeMedia());s.close();
 }
 @Test public void selectedPrimaryAndSecondaryReachActiveStateAndClearOnSwitch(){
  LibassPlaybackSession s=session();Host h=new Host();MediaItem a=item("a");feed(parser(s,a,"p"));feed(parser(s,a,"s"));Format p=format("p"),q=format("s");
  h.set(a);h.tracks=new Tracks(Arrays.asList(new Tracks.Group(new TrackGroup(p),false,new int[]{C.FORMAT_HANDLED},new boolean[]{true}),new Tracks.Group(new TrackGroup(q),false,new int[]{C.FORMAT_HANDLED},new boolean[]{true})));
  s.bindPlayer(h.player);s.setSecondaryFormat(h.player,q);LibassMediaState active=s.activeMedia();active.setFrameSize(100,100,100,100,0,0,100,100);LibassFrameSet frames=active.renderFrames(0,true);assertNotNull(frames.primary);assertNotNull(frames.secondary);
  h.set(item("b"));h.tracks=Tracks.EMPTY;h.event(Player.EVENT_MEDIA_ITEM_TRANSITION);assertNull(s.activeMedia().renderFrames(0,true));s.close();
 }
 @Test public void settingsPropagateToExistingAndFutureMedia(){
  LibassPlaybackSession s=session();MediaItem a=item("a"),b=item("b");feed(parser(s,a,"p"));s.setFontScale(1.5f,true);s.setBottomPositionFraction(.3f);s.setSecondaryBottomPositionFraction(.7f);feed(parser(s,b,"p"));
  assertTrue(LibassNative.log.contains("position:2:0.3"));assertTrue(LibassNative.log.contains("position:4:0.3"));s.close();
 }
 @Test public void closeFencesParsersPlayersAndReleasesTracksBeforeLibraries(){
  LibassPlaybackSession s=session();MediaItem a=item("a");SubtitleParser parser=parser(s,a,"p");feed(parser);Host h=new Host();h.set(a);s.bindPlayer(h.player);Player.Listener stale=h.listeners.get(0);s.close();int after=LibassNative.log.size();
  feed(parser);stale.onEvents(h.player,new Player.Events(new FlagSet.Builder().add(Player.EVENT_TRACKS_CHANGED).build()));s.close();assertEquals(after,LibassNative.log.size());assertTrue(LibassNative.tracks.isEmpty());assertTrue(LibassNative.libraries.isEmpty());assertTrue(h.listeners.isEmpty());assertFalse(s.isAvailable());
  assertThrows(IllegalStateException.class,()->s.createMediaComponents(a,()->new Extractor[0]));assertThrows(IllegalStateException.class,s::createClockRenderer);
 }
 @Test public void clockOffsetThrottleSeekAndElapsedClockRollback(){
  List<String> events=new ArrayList<>();LibassClockRenderer r=new LibassClockRenderer(new LibassClockRenderer.Listener(){public void enabled(){}public void disabled(){}public void offset(long value){}public void position(long p,boolean force){events.add(p+":"+force);}});
  r.onRendererOffsetChanged(1000000);r.onPositionReset(1000100,false,false);r.render(1000200,10);r.render(1000300,20);r.render(1000400,16676);r.render(1000500,1);r.onPositionReset(999999,false,false);
  assertEquals(Arrays.asList("100:true","200:false","400:false","500:false","-1:true"),events);
 }

 @Test public void obsoleteClockCannotMoveReplacementPlayerClock() throws Exception {
  LibassPlaybackSession s=session();Host a=new Host(),b=new Host();a.set(item("a"));b.set(item("b"));s.bindPlayer(a.player);
  LibassClockRenderer old=(LibassClockRenderer)s.createClockRenderer();old.onEnabled(false);old.onRendererOffsetChanged(1000);old.onPositionReset(4000,false,false);assertEquals(3000,s.positionUs());
  s.bindPlayer(b.player);old.onPositionReset(9000,false,false);old.handleMessage(24,99L);assertEquals(3000,s.positionUs());s.close();old.onPositionReset(9999,false,false);assertEquals(3000,s.positionUs());
 }
}
