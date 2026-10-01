package androidx.media3.exoplayer.libass;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;

public final class NativeOwnershipTest {
 static int passed;
 static void check(boolean b){if(!b)throw new AssertionError(LibassNative.log);}
 static void rejects(Runnable r){try{r.run();throw new AssertionError("Expected failure");}catch(IllegalArgumentException|IllegalStateException|IndexOutOfBoundsException expected){}}
 static LibassTrack track(LibassNativeLibrary l){return l.createTrack(null,null,t->{});}
 static long count(String prefix){return LibassNative.log.stream().filter(s->s.startsWith(prefix+":")).count();}
 static void test(String name,Runnable r){LibassNative.reset();r.run();check(LibassNative.libraries.isEmpty()&&LibassNative.tracks.isEmpty());passed++;System.out.println("PASS "+name);}
 public static void main(String[] args)throws Exception {
  test("shared library and ordered idempotent close",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);LibassTrack a=track(l),b=track(l);
   l.addFont("synthetic",new byte[]{1});l.close();a.close();b.close();l.close();
   check(count("release")==2&&count("releaseLibrary")==1&&count("font")==1);
   check(LibassNative.log.indexOf("release:3")<LibassNative.log.indexOf("releaseLibrary:1"));
   rejects(()->a.processData(new byte[0],0,0));rejects(()->track(l));
  });
  test("native create and initializer failures roll back",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);LibassNative.fail="create";rejects(()->track(l));
   LibassNative.fail="cache";rejects(()->l.createTrack(null,null,t->t.setCacheLimits(4096,48)));
   check(LibassNative.tracks.isEmpty());track(l);l.close();
  });
  test("reentrant initializer cannot return released track",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);rejects(()->l.createTrack(null,null,t->l.close()));
   check(count("release")==1&&count("releaseLibrary")==1);
  });
  test("cleanup failure still releases siblings and parent once",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);LibassTrack a=track(l);track(l);
   LibassNative.fail="release";rejects(l::close);l.close();a.close();check(count("release")==2&&count("releaseLibrary")==1);
  });
  test("timed sample digest/time dedup and failed-native retry",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);LibassTrack t=track(l);byte[] d={0,1,2,3};
   t.processTimedData(d,1,2,1001);t.processTimedData(new byte[]{1,2},0,2,1001);check(count("timed")==1);
   t.processTimedData(d,1,2,1002);check(count("timed")==2);
   LibassNative.fail="timed";rejects(()->t.processTimedData(d,0,2,2000));t.processTimedData(d,0,2,2000);check(count("timed")==4);
   rejects(()->t.processTimedData(d,Integer.MAX_VALUE,2,1));l.close();
  });
  test("font budget is shared per media",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);byte[] font=new byte[LibassNativeLibrary.MAX_FONT_BYTES];
   l.addFont("empty",new byte[0]);for(int i=0;i<4;i++)l.addFont("font"+i,font);
   rejects(()->l.addFont("over",new byte[]{1}));check(count("font")==4);l.close();
  });
  test("render prerequisites and finite settings",()->{
   LibassNativeLibrary l=new LibassNativeLibrary(null);LibassTrack t=track(l);
   rejects(()->t.renderFrame(0,false));rejects(()->t.setFontScale(Float.NaN,true));rejects(()->t.setBottomPositionFraction(Float.POSITIVE_INFINITY));
   t.setFrameSize(1920,1080,0,0,1920,1080);t.setStorageSize(1920,1080);t.setFontScale(1,true);
   check(t.renderFrame(1000,true).images.isEmpty());l.close();
  });
  LibassNative.reset();LibassNativeLibrary l=new LibassNativeLibrary(null);LibassTrack t=track(l);
  CountDownLatch entered=new CountDownLatch(1),finish=new CountDownLatch(1);AtomicReference<Throwable> failure=new AtomicReference<>();
  LibassNative.duringData=()->{check(Thread.holdsLock(l));entered.countDown();try{if(!finish.await(5,TimeUnit.SECONDS))throw new AssertionError("watchdog");}catch(InterruptedException e){throw new AssertionError(e);}};
  Thread parse=new Thread(()->{try{t.processData(new byte[]{1},0,1);}catch(Throwable e){failure.set(e);}});
  Thread close=new Thread(()->{try{l.close();}catch(Throwable e){failure.set(e);}});
  parse.start();check(entered.await(5,TimeUnit.SECONDS));close.start();
  // Wait for a specific monitor state, never a guessed sleep duration.
  long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);
  try{while(close.getState()!=Thread.State.BLOCKED&&close.isAlive()&&System.nanoTime()<end)Thread.yield();check(close.getState()==Thread.State.BLOCKED);}
  finally{finish.countDown();parse.join(5000);close.join(5000);}
  check(!parse.isAlive()&&!close.isAlive()&&failure.get()==null);
  check(LibassNative.log.indexOf("dataEnd:2")<LibassNative.log.indexOf("release:2"));
  check(LibassNative.libraries.isEmpty()&&LibassNative.tracks.isEmpty());passed++;
  System.out.println("PASS in-flight parser vs close monitor fence");System.out.println("PASS "+passed+" native ownership cases");
 }
}
