package androidx.media3.exoplayer.libass;
import static org.junit.Assert.*;
import android.graphics.Rect;
import java.util.*;
import java.util.concurrent.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassRenderPipelineTest {
 static final class Backend implements LibassRenderPipeline.Backend,LibassFrameRenderer.Textures {
  int next=100,clears,presents,closes;boolean uploadFailure,contextLost;
  List<Integer> drawn=new ArrayList<>(),deleted=new ArrayList<>();Set<Integer> owned=new HashSet<>();
  public LibassFrameRenderer.Textures textures(){return this;}public int upload(byte[] data,int w,int h){if(uploadFailure)throw new IllegalStateException("upload");int id=next++;owned.add(id);return id;}
  public void delete(int id){assertTrue("double delete "+id,owned.remove(id));deleted.add(id);}public void draw(LibassFrameRenderer.Image image,int w,int h){drawn.add(image.textureId);}
  public void begin(int w,int h){clears++;drawn.clear();}public void present(){if(contextLost)throw new IllegalStateException("lost");presents++;}public void close(){closes++;assertTrue(owned.isEmpty());}
 }
 static LibassFrame frame(int id){return new LibassFrame(1,new LibassImage[]{new LibassImage(0,0,1,1,0xffffff00,id==0?new byte[]{127}:null,id)});}
 static void draw(LibassRenderPipeline p,Object id,LibassFrameSet frames,long version){p.draw(id,force->frames,version,100,100,200,200);}
 @Test public void primaryAndSecondaryCompositionOrder(){Backend b=new Backend();b.owned.addAll(Arrays.asList(1,2));LibassRenderPipeline p=new LibassRenderPipeline(()->b);draw(p,this,new LibassFrameSet(frame(1),frame(2)),0);assertEquals(Arrays.asList(1,2),b.drawn);p.close();assertEquals(2,b.deleted.size());}
 @Test public void primaryOnlyAndSecondaryOnly(){Backend b=new Backend();b.owned.addAll(Arrays.asList(1,2));LibassRenderPipeline p=new LibassRenderPipeline(()->b);draw(p,this,new LibassFrameSet(frame(1),null),0);assertEquals(Arrays.asList(1),b.drawn);draw(p,this,new LibassFrameSet(null,frame(2)),0);assertEquals(Arrays.asList(2),b.drawn);assertEquals(Arrays.asList(1),b.deleted);p.close();}
 @Test public void unchangedRetainsBothLanes(){Backend b=new Backend();b.owned.addAll(Arrays.asList(1,2));LibassRenderPipeline p=new LibassRenderPipeline(()->b);draw(p,this,new LibassFrameSet(frame(1),frame(2)),0);draw(p,this,new LibassFrameSet(new LibassFrame(0,null),new LibassFrame(0,null)),0);assertEquals(Arrays.asList(1,2),b.drawn);assertTrue(b.deleted.isEmpty());p.close();}
 @Test public void changedEmptyClearsTransparentSurface(){Backend b=new Backend();b.owned.add(1);LibassRenderPipeline p=new LibassRenderPipeline(()->b);draw(p,this,new LibassFrameSet(frame(1),null),0);draw(p,this,new LibassFrameSet(new LibassFrame(1,null),null),0);assertTrue(b.drawn.isEmpty());assertEquals(2,b.clears);assertEquals(2,b.presents);p.close();}
 @Test public void mediaIdentityChangeClearsOldTexturesAndForcesNewFrame(){Backend b=new Backend();b.owned.add(1);LibassRenderPipeline p=new LibassRenderPipeline(()->b);draw(p,this,new LibassFrameSet(frame(1),null),0);p.draw(new Object(),force->{assertTrue(force);return null;},0,100,100,200,200);assertEquals(Arrays.asList(1),b.deleted);p.close();}
 @Test public void cpuUploadAndTextureOwnershipTransferOnce(){Backend b=new Backend();LibassRenderPipeline p=new LibassRenderPipeline(()->b);LibassFrame f=frame(0);draw(p,this,new LibassFrameSet(f,null),0);assertEquals(Arrays.asList(100),b.drawn);p.close();p.close();assertEquals(Arrays.asList(100),b.deleted);assertEquals(1,b.closes);}
 @Test public void uploadFailureReleasesIncomingNativeTexture(){Backend b=new Backend();b.uploadFailure=true;b.owned.add(9);LibassRenderPipeline p=new LibassRenderPipeline(()->b);assertThrows(IllegalStateException.class,()->draw(p,this,new LibassFrameSet(frame(0),frame(9)),0));assertEquals(Arrays.asList(9),b.deleted);assertEquals(1,b.closes);p.close();}
 @Test public void contextLossRecreatesBackendAndForcesNewFrame(){Backend a=new Backend(),b=new Backend();a.owned.add(1);a.contextLost=true;List<Backend> backends=new ArrayList<>(Arrays.asList(a,b));LibassRenderPipeline p=new LibassRenderPipeline(()->backends.remove(0));assertThrows(IllegalStateException.class,()->draw(p,this,new LibassFrameSet(frame(1),null),0));p.draw(this,force->{assertTrue(force);return new LibassFrameSet(frame(0),null);},0,100,100,200,200);assertEquals(1,a.closes);assertEquals(1,b.presents);p.close();}
 @Test public void unchangedVersionDoesNotForceButSeekVersionDoes(){Backend b=new Backend();LibassRenderPipeline p=new LibassRenderPipeline(()->b);List<Boolean> force=new ArrayList<>();LibassRenderPipeline.Source source=f->{force.add(f);return null;};p.draw(this,source,1,100,100,200,200);p.draw(this,source,1,100,100,200,200);p.draw(this,source,2,100,100,200,200);assertEquals(Arrays.asList(true,false,true),force);p.close();}
 @Test public void closeRejectsQueuedNativeRenderAndStaleSurfaceTask(){Backend b=new Backend();LibassRenderPipeline p=new LibassRenderPipeline(()->b);LibassRenderGate gate=new LibassRenderGate();Runnable queued=()->gate.run(()->p.draw(this,force->{fail("late native render");return null;},0,1,1,1,1));gate.close();queued.run();p.close();assertEquals(0,b.closes);}
 @Test public void closeWaitsForInflightOperation()throws Exception {
  LibassRenderGate gate=new LibassRenderGate();CountDownLatch entered=new CountDownLatch(1),resume=new CountDownLatch(1);List<String> events=Collections.synchronizedList(new ArrayList<>());
  Thread render=new Thread(()->gate.run(()->{entered.countDown();try{if(!resume.await(5,TimeUnit.SECONDS))throw new AssertionError("watchdog");}catch(InterruptedException e){throw new AssertionError(e);}events.add("native-end");}));render.start();assertTrue(entered.await(5,TimeUnit.SECONDS));
  Thread close=new Thread(()->{gate.close();events.add("closed");});close.start();resume.countDown();render.join(5000);close.join(5000);assertFalse(render.isAlive());assertFalse(close.isAlive());assertEquals(Arrays.asList("native-end","closed"),events);
 }
 @Test public void framePixelLimitAndViewportScale(){assertArrayEquals(new int[]{1920,1080},LibassSubtitleView.renderSize(3840,2160,1920*1080));assertEquals(new Rect(0,100,1920,980),LibassSubtitleView.scaleViewport(new Rect(0,200,3840,1960),3840,2160,1920,1080));}
}
