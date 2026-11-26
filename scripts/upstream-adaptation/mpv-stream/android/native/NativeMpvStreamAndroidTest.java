/* SPDX-License-Identifier: Apache-2.0 */
package org.fingmi.mpvprobe;

import static org.junit.Assert.*;
import android.content.Context;
import android.util.Log;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.media3.datasource.DataSpec;
import androidx.media3.mpvplayer.media.Media3MpvInput;
import androidx.media3.mpvplayer.media.MpvNativeRequestGate;
import androidx.media3.mpvplayer.media.MpvStreamOwner;
import is.xyz.mpv.MPVLib;
import java.io.File;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import okhttp3.Call;
import okhttp3.Connection;
import okhttp3.EventListener;
import okhttp3.OkHttpClient;
import okhttp3.Credentials;
import okhttp3.mockwebserver.Dispatcher;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import okio.Buffer;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

/** Actual official libplayer -> libmpv stream callbacks -> unchanged Media3 adapter.
 * Synthetic loopback WAV only. No fake JNI, no TV app, no global event attribution. */
public final class NativeMpvStreamAndroidTest {
    private static final String TAG = "MpvNativeProbe";
    private static final String AUTH = Credentials.basic("fixture","synthetic");
    private static final byte[] WAV = wav(180);
    private static final byte[] SHORT_WAV = wav(2);
    private final Media3MpvInput input = new Media3MpvInput();
    private final MpvNativeRequestGate gate = new MpvNativeRequestGate();
    private final ConcurrentHashMap<Long, CompletableFuture<Reply>> pending = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Call, CallTrace> calls = new ConcurrentHashMap<>();
    private final CopyOnWriteArrayList<RecordedRequest> requests = new CopyOnWriteArrayList<>();
    private final CountDownLatch loaded = new CountDownLatch(1), shutdown = new CountDownLatch(1);
    private MockWebServer server;
    private OkHttpClient client;
    private MpvStreamOwner.Lease active;
    private Trace trace;
    private boolean created, initialized, slow;
    private Context context;

    static {
        System.loadLibrary("c++_shared");
        System.loadLibrary("ffmpeg");
        System.loadLibrary("mpv");
        System.loadLibrary("player");
    }

    private static byte[] wav(int seconds) {
        ByteBuffer b = ByteBuffer.allocate(44 + seconds * 16000).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(0x46464952).putInt(b.capacity()-8).putInt(0x45564157)
         .putInt(0x20746d66).putInt(16).putShort((short)1).putShort((short)1)
         .putInt(8000).putInt(16000).putShort((short)2).putShort((short)16)
         .putInt(0x61746164).putInt(b.capacity()-44);
        for (int i=0;b.hasRemaining();i++) b.putShort((short)(i*17));
        return b.array();
    }

    private static final class Reply {
        final long id, result; final int error;
        Reply(long id,int error,long result) { this.id=id; this.error=error; this.result=result; }
    }

    private final MPVLib.EventObserver observer = new MPVLib.EventObserver() {
        public void eventProperty(String p) {}
        public void eventProperty(String p,long v) {}
        public void eventProperty(String p,boolean v) {}
        public void eventProperty(String p,String v) {}
        public void eventProperty(String p,double v) {}
        public void event(int id) {
            // Global events are observed only as context lifecycle / single-file
            // synchronization. They never publish state into a playback lease.
            if (id==MPVLib.MpvEvent.MPV_EVENT_FILE_LOADED) loaded.countDown();
            if (id==MPVLib.MpvEvent.MPV_EVENT_SHUTDOWN) shutdown.countDown();
        }
        public void eventEndFile(int reason,int error,String msg) {
            Log.i(TAG,"UNATTRIBUTED_END_FILE reason="+reason+" error="+error);
        }
        public void eventCommandReply(long id,int error,long result) {
            CompletableFuture<Reply> f=pending.get(id);
            if (f!=null) f.complete(new Reply(id,error,result));
        }
    };

    private static final class CallTrace extends EventListener {
        final AtomicInteger acquired=new AtomicInteger(),released=new AtomicInteger();
        final CountDownLatch terminal=new CountDownLatch(1);
        @Override public void connectionAcquired(Call c,Connection v){acquired.incrementAndGet();}
        @Override public void connectionReleased(Call c,Connection v){released.incrementAndGet();}
        @Override public void callEnd(Call c){terminal.countDown();}
        @Override public void callFailed(Call c,IOException e){terminal.countDown();}
    }

    /** Wrap the actual Stream returned by Media3MpvInput's existing registry.
     * No native calls are synthesized. Each operation below is invoked by stream.cpp. */
    private static final class Trace implements MPVLib.Stream {
        final MPVLib.Stream delegate; final byte[] expected;
        final AtomicInteger opens=new AtomicInteger(), reads=new AtomicInteger(), sizes=new AtomicInteger();
        final AtomicInteger eof=new AtomicInteger(), cancels=new AtomicInteger(), closes=new AtomicInteger();
        final AtomicLong bytes=new AtomicLong();
        final AtomicReference<Throwable> bad=new AtomicReference<>();
        final CopyOnWriteArrayList<Long> seeks=new CopyOnWriteArrayList<>();
        final CountDownLatch reading=new CountDownLatch(1), cancelled=new CountDownLatch(1),closed=new CountDownLatch(1);
        long position;
        Trace(MPVLib.Stream s,byte[] expected){this.delegate=s;this.expected=expected;}
        public int read(ByteBuffer b) {
            reading.countDown();
            int before=b.position();
            int n=delegate.read(b);
            reads.incrementAndGet();
            if(n==0)eof.incrementAndGet();
            if(n>0){
                try {
                    if(!b.isDirect() || b.position()!=before+n || position+n>expected.length)
                        throw new AssertionError("native buffer/count");
                    ByteBuffer copy=b.duplicate(); copy.position(before);
                    for(int i=0;i<n;i++)if(copy.get()!=expected[(int)position+i])
                        throw new AssertionError("native byte mismatch "+(position+i));
                    position+=n;bytes.addAndGet(n);
                } catch(Throwable t){bad.compareAndSet(null,t);return -1;}
            }
            return n;
        }
        public long seek(long p){long result=delegate.seek(p);if(result>=0){position=result;seeks.add(result);}return result;}
        public long size(){sizes.incrementAndGet();return delegate.size();}
        public void cancel(){cancels.incrementAndGet();delegate.cancel();cancelled.countDown();}
        public void close(){closes.incrementAndGet();try{delegate.close();}finally{closed.countDown();}}
    }

    @Before public void setup() throws Exception {
        context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        server=new MockWebServer();server.start(InetAddress.getByName("127.0.0.1"),0);
        server.setDispatcher(new Dispatcher(){
            @Override public MockResponse dispatch(RecordedRequest request){
                requests.add(request);
                if(!AUTH.equals(request.getHeader("Authorization")) || request.getHeader("X-Playback")==null)
                    return new MockResponse().setResponseCode(401);
                String path=request.getRequestUrl().encodedPath();
                byte[] data="/dump".equals(path)?SHORT_WAV:WAV;
                String range=request.getHeader("Range");
                long start=0;
                if(range!=null){
                    if(!range.matches("bytes=[0-9]+-"))return new MockResponse().setResponseCode(400);
                    start=Long.parseLong(range.substring(6,range.length()-1));
                }
                if(start>=data.length)return new MockResponse().setResponseCode(416).setHeader("Content-Range","bytes */"+data.length);
                int p=(int)start;
                MockResponse response=new MockResponse().setBody(new Buffer().write(data,p,data.length-p));
                if(range!=null)response.setResponseCode(206).setHeader("Content-Range","bytes "+p+"-"+(data.length-1)+"/"+data.length);
                if("/slow".equals(path))response.setBodyDelay(20,TimeUnit.SECONDS);
                return response;
            }
        });
        client=new OkHttpClient.Builder().connectTimeout(5,TimeUnit.SECONDS).readTimeout(45,TimeUnit.SECONDS)
            .callTimeout(60,TimeUnit.SECONDS).eventListenerFactory(c->{CallTrace t=new CallTrace();calls.put(c,t);return t;}).build();
        MPVLib.addObserver(observer);
    }

    private void option(String k,String v){assertEquals("option "+k,0,MPVLib.setOptionString(k,v));}
    private void start(String dump) {
        MPVLib.create(context);created=true;
        option("config","no");option("idle","yes");option("vo","null");option("ao","null");
        option("audio-display","no");option("cache","no");option("pause",dump==null?"yes":"no");
        option("demuxer-max-bytes","131072");option("demuxer-max-back-bytes","0");
        if(dump!=null)option("stream-dump",dump);
        MPVLib.init();initialized=true;
        String version=MPVLib.getPropertyString("mpv-version");
        assertNotNull(version);Log.i(TAG,"REAL_MPV_VERSION "+version);
    }

    private MpvStreamOwner.Lease register(String path,String owner,byte[] expected) {
        DataSpec spec=new DataSpec.Builder().setUri(server.url(path).toString())
            .setHttpRequestHeaders(new java.util.HashMap<String,String>(){{
                put("Authorization",AUTH);put("X-Playback",owner);
            }}).build();
        active=input.replace(client,spec);
        MPVLib.Stream real=MPVLib.openStream(active.uri);
        assertNotNull(real);
        Trace t=new Trace(real,expected);trace=t;
        // One native open per synthetic fixture. Creating this cursor does not
        // open HTTP; only subsequent real native callbacks perform network I/O.
        MPVLib.unregisterStream(active.uri);
        MPVLib.registerStream(active.uri,()->t.opens.incrementAndGet()==1?t:null);
        return active;
    }

    private Reply submit(MpvStreamOwner.Lease owner,boolean result,String... cmd)throws Exception{
        long id=gate.reserve(owner);
        CompletableFuture<Reply> f=new CompletableFuture<>();pending.put(id,f);
        try{
            int status=result?MPVLib.enqueueCommandLongResult(id,"playlist_entry_id",cmd):MPVLib.enqueueCommand(id,cmd);
            assertEquals("native submit "+cmd[0],0,status);
            Reply reply=f.get(20,TimeUnit.SECONDS);
            assertEquals(id,reply.id);assertEquals("native reply "+cmd[0],0,reply.error);
            if(result)assertTrue("playlist entry ID",reply.result>0);
            Log.i(TAG,"NATIVE_TAGGED_REPLY id="+id+" result="+reply.result+" command="+cmd[0]);
            return reply;
        }catch(Exception|AssertionError e){gate.forget(id);throw e;}
        finally{pending.remove(id);}
    }

    private void accept(Reply reply){assertTrue(gate.deliver(reply.id,reply.error,reply.result,(id,e,v)->{
        assertEquals(reply.id,id);assertEquals(reply.result,v);
    }));}
    private static void await(CountDownLatch latch,String what)throws Exception{assertTrue(what,latch.await(20,TimeUnit.SECONDS));}
    private static void until(java.util.function.BooleanSupplier condition,String what)throws Exception{
        long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(20);
        while(!condition.getAsBoolean()&&System.nanoTime()<deadline)Thread.sleep(50);
        assertTrue(what,condition.getAsBoolean());
    }
    private void verify(Trace t){
        assertEquals("native open",1,t.opens.get());assertTrue("native read",t.reads.get()>0);
        assertEquals("native close",1,t.closes.get());assertNull("native bytes",t.bad.get());
        Log.i(TAG,"NATIVE_CALLBACK_COUNTS open="+t.opens+" read="+t.reads+" bytes="+t.bytes
            +" seek="+t.seeks.size()+" size="+t.sizes+" eof="+t.eof+" cancel="+t.cancels+" close="+t.closes);
    }
    private void releases()throws Exception{
        assertFalse(calls.isEmpty());int n=0,released=0;
        for(Map.Entry<Call,CallTrace> e:calls.entrySet()){
            CallTrace t=e.getValue();await(t.terminal,"actual OkHttp terminal");
            assertEquals(t.acquired.get(),t.released.get());n++;released+=t.released.get();
        }
        until(()->client.dispatcher().runningCallsCount()==0,"dispatcher");
        assertEquals(0,client.dispatcher().queuedCallsCount());
        client.connectionPool().evictAll();assertEquals(0,client.connectionPool().connectionCount());
        Log.i(TAG,"PASS_NATIVE_OKHTTP_RELEASE calls="+n+" connectionReleases="+released);
    }
    private void retire(){if(active!=null){input.retire(active);active=null;}}
    private static byte[] contents(File file)throws IOException{
        try(FileInputStream in=new FileInputStream(file);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];for(int n;(n=in.read(b))!=-1;)out.write(b,0,n);return out.toByteArray();
        }
    }

    @Test public void nativeProtocolDumpReadsRealBytesAndEof()throws Exception{
        File dump=new File(context.getCacheDir(),"native-probe.wav");if(dump.exists())assertTrue(dump.delete());
        start(dump.getAbsolutePath());
        MpvStreamOwner.Lease owner=register("/dump","dump",SHORT_WAV);
        Reply load=submit(owner,true,"loadfile",owner.uri,"replace");accept(load);
        Trace t=trace;await(t.closed,"native stream close");
        assertTrue("native EOF",t.eof.get()>0);assertEquals(SHORT_WAV.length,t.bytes.get());
        assertArrayEquals(SHORT_WAV,contents(dump));assertTrue(dump.delete());
        verify(t);retire();releases();
        Log.i(TAG,"PASS_NATIVE_MEDIA3ISO_DUMP_EOF");
    }

    @Test public void nativeSeekAndActualRequestIdDeliveryIsolation()throws Exception{
        start(null);
        MpvStreamOwner.Lease old=register("/media","old",WAV);Trace t=trace;
        Reply delayed=submit(old,true,"loadfile",old.uri,"replace");
        await(loaded,"single-file loaded (not owner-attributed)");
        int before=t.seeks.size();accept(submit(old,false,"seek","120","absolute+exact"));
        until(()->t.seeks.size()>before&&t.seeks.subList(before,t.seeks.size()).stream().anyMatch(p->p>1000000),"forward native seek");
        int after=t.seeks.size();accept(submit(old,false,"seek","4","absolute+exact"));
        until(()->t.seeks.size()>after&&t.seeks.subList(after,t.seeks.size()).stream().anyMatch(p->p<1000000),"backward native seek");
        assertTrue("actual HTTP range",requests.stream().anyMatch(q->q.getHeader("Range")!=null&&!q.getHeader("Range").equals("bytes=0-")));
        accept(submit(old,false,"stop"));await(t.closed,"old native close");verify(t);
        MpvStreamOwner.Lease next=register("/media","new",WAV);Trace n=trace;
        Reply current=submit(next,true,"loadfile",next.uri,"replace");
        AtomicInteger delivered=new AtomicInteger();
        // These are actual native replies, with the old one intentionally
        // held before owner delivery. No claim of native late-arrival timing.
        assertFalse(gate.deliver(delayed.id,delayed.error,delayed.result,(id,e,v)->delivered.incrementAndGet()));
        assertTrue(gate.deliver(current.id,current.error,current.result,(id,e,v)->delivered.incrementAndGet()));
        assertEquals(1,delivered.get());assertFalse(gate.deliver(current.id,0,current.result,(id,e,v)->delivered.incrementAndGet()));
        assertNull(MPVLib.openStream(old.uri));
        await(n.reading,"new native read");accept(submit(next,false,"stop"));await(n.closed,"new native close");
        verify(n);retire();releases();
        Log.i(TAG,"PASS_NATIVE_SEEK_TAGGED_REQUEST_ISOLATION old="+delayed.id+" new="+current.id);
    }

    @Test public void nativeStopCallsCancelAndReleasesRealHttp()throws Exception{
        start(null);slow=true;
        MpvStreamOwner.Lease owner=register("/slow","slow",WAV);Trace t=trace;
        accept(submit(owner,true,"loadfile",owner.uri,"replace"));
        await(t.reading,"native read entered");Thread.sleep(150);
        assertEquals(0,t.bytes.get());assertEquals(0,t.cancels.get());
        long start=System.nanoTime();accept(submit(owner,false,"stop"));
        assertTrue("native cancel while HTTP blocked",t.cancelled.await(10,TimeUnit.SECONDS));
        assertTrue("native close",t.closed.await(10,TimeUnit.SECONDS));
        assertTrue("cancel before delayed body",TimeUnit.NANOSECONDS.toMillis(System.nanoTime()-start)<15000);
        assertTrue(calls.keySet().stream().anyMatch(Call::isCanceled));
        verify(t);retire();releases();Log.i(TAG,"PASS_NATIVE_STOP_CANCEL_CLOSE");
    }

    @After public void cleanup()throws Exception{
        try{
            retire();
            if(created){assertEquals(0,MPVLib.destroy());if(initialized)await(shutdown,"native context shutdown");}
        }finally{
            MPVLib.removeObserver(observer);gate.clear();
            if(client!=null){client.dispatcher().cancelAll();client.connectionPool().evictAll();client.dispatcher().executorService().shutdownNow();}
            if(slow)Thread.sleep(21000); // let intentionally delayed fixture writer finish
            if(server!=null)server.shutdown();
        }
    }
}
