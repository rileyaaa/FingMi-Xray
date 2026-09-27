package androidx.media3.ui.libass;
import static org.junit.Assert.*;
import android.app.Activity;
import android.graphics.Rect;
import android.view.View;
import android.widget.FrameLayout;
import androidx.media3.common.*;
import androidx.media3.exoplayer.libass.LibassControllerTest;
import androidx.media3.ui.CaptionStyleCompat;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.Config;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassViewControllerTest {
 LibassControllerTest fixture;LibassPlayerViewController controller;Activity activity;List<Overlay> created=new ArrayList<>();
 final class Host implements LibassPlayerViewController.Host {
  final FrameLayout root,overlay;Player player;
  Host(){root=new FrameLayout(activity);overlay=new FrameLayout(activity);root.addView(overlay);player=fixture.player;((FrameLayout)activity.findViewById(android.R.id.content)).addView(root);}
  public View root(){return root;}public FrameLayout overlay(){return overlay;}public Player player(){return player;}public View video(){return null;}
 }
 final class Overlay implements LibassPlayerViewController.Overlay {
  final View view=new View(activity);int closes,geometry;
  public View view(){return view;}public void geometry(int w,int h,Rect r){assertEquals(1920,w);assertEquals(1080,h);geometry++;}public void close(){closes++;}
 }
 @Before public void setup()throws Exception {
  fixture=new LibassControllerTest();fixture.setup();fixture.activate(fixture.p,fixture.s);
  activity=Robolectric.buildActivity(Activity.class).setup().visible().get();
  controller=new LibassPlayerViewController(fixture.player,fixture.session,fixture.controller,context->{Overlay view=new Overlay();created.add(view);return view;});
 }
 @After public void close(){controller.close();fixture.close();activity.finish();}
 @Test public void bindARebindBAndCloseRemoveOnlyOwnedOverlays(){Host a=new Host(),b=new Host();View ordinary=new View(activity);a.overlay.addView(ordinary);controller.bindHost(a);assertEquals(2,a.overlay.getChildCount());controller.bindHost(b);assertEquals(1,a.overlay.getChildCount());assertSame(ordinary,a.overlay.getChildAt(0));assertEquals(1,created.get(0).closes);assertEquals(1,b.overlay.getChildCount());controller.close();assertEquals(0,b.overlay.getChildCount());assertEquals(1,created.get(1).closes);}
 @Test public void oldHostDetachCannotCloseReplacement(){Host a=new Host(),b=new Host();controller.bindHost(a);controller.bindHost(b);controller.onViewDetachedFromWindow(a.root);assertEquals(0,created.get(1).closes);controller.onPreDraw();assertTrue(created.get(1).geometry>0);}
 @Test public void playerReplacementOnBoundViewClearsOverlay(){Host a=new Host();controller.bindHost(a);a.player=null;controller.onPreDraw();assertEquals(0,a.overlay.getChildCount());assertEquals(1,created.get(0).closes);a.player=fixture.player;controller.onPreDraw();assertEquals(2,created.size());}
 @Test public void unbindAndRepeatedCloseAreIdempotent(){Host a=new Host();controller.bindHost(a);controller.bindHost(null);controller.close();controller.close();assertEquals(1,created.get(0).closes);assertEquals(0,a.overlay.getChildCount());}
 @Test public void detachReattachAndLateCallbackAfterClose(){Host a=new Host();controller.bindHost(a);controller.onViewDetachedFromWindow(a.root);assertEquals(1,created.get(0).closes);controller.onViewAttachedToWindow(a.root);assertEquals(2,created.size());controller.close();controller.onViewAttachedToWindow(a.root);controller.onPreDraw();assertEquals(2,created.size());}
 @Test public void secondaryConfiguratorFollowsViewLifetime()throws Exception {
  TrackGroup vtt=new TrackGroup("vtt",new Format.Builder().setId("vtt").setSampleMimeType(MimeTypes.TEXT_VTT).build());fixture.controller.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(vtt,0));fixture.activate(fixture.p,vtt);List<androidx.media3.ui.SubtitleView> configured=new ArrayList<>();controller.setSecondarySubtitleViewConfigurator(configured::add);
  Host a=new Host(),b=new Host();controller.bindHost(a);assertEquals(1,configured.size());controller.bindHost(b);assertEquals(2,configured.size());assertNotSame(configured.get(0),configured.get(1));controller.close();assertNull(configured.get(1).getParent());
 }
 @Test public void styleAndClosedMutations(){controller.setStyleOverride(CaptionStyleCompat.DEFAULT,"sans-serif");controller.close();assertThrows(IllegalStateException.class,()->controller.setStyleOverride(null,null));}
}
