package androidx.media3.exoplayer.libass;
import static org.junit.Assert.*;
import android.graphics.SurfaceTexture;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public final class LibassSurfaceLifecycleTest {
 static final class Texture extends SurfaceTexture {
  final AtomicInteger releases=new AtomicInteger();final CountDownLatch released=new CountDownLatch(1);
  Texture(){super(0);}
  @Override public void release(){releases.incrementAndGet();super.release();released.countDown();}
  void awaitReleased()throws Exception{assertTrue(released.await(5,TimeUnit.SECONDS));assertEquals(1,releases.get());}
 }
 @Test public void staleSurfaceCallbacksCannotCloseReplacementAndEachTextureReleasesOnce()throws Exception {
  new LibassSessionTest().reset();LibassPlaybackSession session=LibassSessionTest.session();LibassSubtitleView view=session.createSubtitleView(RuntimeEnvironment.getApplication());Texture a=new Texture(),b=new Texture();
  // Zero-sized surfaces exercise real HandlerThread cleanup without asking a fake EGL to render.
  view.onSurfaceTextureAvailable(a,0,0);view.onSurfaceTextureAvailable(b,0,0);a.awaitReleased();
  view.onSurfaceTextureSizeChanged(a,100,100);assertFalse(view.onSurfaceTextureDestroyed(a));assertEquals(0,b.releases.get());view.close();b.awaitReleased();assertFalse(view.onSurfaceTextureDestroyed(b));session.close();assertEquals(1,a.releases.get());assertEquals(1,b.releases.get());
 }
 @Test public void sessionCloseStopsAttachedSurfaceAndLateAvailabilityStaysUnowned()throws Exception {
  new LibassSessionTest().reset();LibassPlaybackSession session=LibassSessionTest.session();LibassSubtitleView view=session.createSubtitleView(RuntimeEnvironment.getApplication());Texture a=new Texture();view.onSurfaceTextureAvailable(a,0,0);session.close();a.awaitReleased();assertTrue(view.isClosed());
  Texture late=new Texture();view.onSurfaceTextureAvailable(late,0,0);assertTrue(view.onSurfaceTextureDestroyed(late));assertEquals(0,late.releases.get());late.release();
 }
}
