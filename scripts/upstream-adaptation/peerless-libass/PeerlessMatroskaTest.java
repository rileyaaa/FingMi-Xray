/* SPDX-License-Identifier: Apache-2.0 */
package org.fingmi.peerlessprobe;

import android.graphics.Bitmap;
import android.os.Build;
import android.util.Log;
import androidx.media3.common.C;
import androidx.media3.common.DataReader;
import androidx.media3.common.Format;
import androidx.media3.common.MimeTypes;
import androidx.media3.common.TrackGroup;
import androidx.media3.common.Tracks;
import androidx.media3.common.util.ParsableByteArray;
import androidx.media3.extractor.*;
import androidx.test.platform.app.InstrumentationRegistry;
import io.github.peerless2012.ass.*;
import io.github.peerless2012.ass.media.*;
import io.github.peerless2012.ass.media.extractor.AssMatroskaExtractor;
import io.github.peerless2012.ass.media.parser.AssSubtitleParserFactory;
import io.github.peerless2012.ass.media.type.AssRenderType;
import java.io.*;
import java.util.*;
import org.junit.Test;
import static org.junit.Assert.*;

/** Actual upstream Kotlin/JNI, actual pinned Media3 extractor. No full-player claim. */
public final class PeerlessMatroskaTest {
    static final String TAG="PeerlessAssProbe";
    static final class Sink implements TrackOutput {
        Format format; int committed; long lastTime;
        public void format(Format value){format=value;}
        public int sampleData(DataReader in,int len,boolean allow,int part)throws IOException{
            byte[] b=new byte[Math.min(4096,len)];int n=in.read(b,0,b.length);
            if(n<0&&!allow)throw new EOFException();return n;
        }
        public void sampleData(ParsableByteArray in,int len,int part){in.skipBytes(len);}
        public void sampleMetadata(long time,int flags,int size,int offset,CryptoData crypto){
            if(size>0){committed++;lastTime=time;}
        }
    }
    static final class Output implements ExtractorOutput {
        final Map<Integer,Sink> sinks=new HashMap<>();
        public TrackOutput track(int id,int type){return sinks.computeIfAbsent(id,k->new Sink());}
        public void endTracks(){}
        public void seekMap(SeekMap map){}
    }
    static DefaultExtractorInput input(byte[] bytes,int start){
        ByteArrayInputStream in=new ByteArrayInputStream(bytes,start,bytes.length-start);
        return new DefaultExtractorInput((b,o,n)->in.read(b,o,n),start,bytes.length);
    }
    static byte[] fixture()throws Exception{
        try(InputStream in=InstrumentationRegistry.getInstrumentation().getTargetContext().getAssets().open("timed.mkv");
            ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();
        }
    }
    static AssTrack select(AssHandler h,Format f){
        assertNotNull(f);assertEquals(MimeTypes.TEXT_SSA,f.codecs);
        h.onTracksChanged(new Tracks(Collections.singletonList(new Tracks.Group(
            new TrackGroup("test-"+f.id,f),false,new int[]{C.FORMAT_HANDLED},new boolean[]{true}))));
        assertNotNull(h.getTrack());return h.getTrack();
    }
    static long pixels(AssFrame f){
        assertNotNull(f);assertNotNull(f.getImages());assertTrue(f.getImages().length>0);
        long hash=0xcbf29ce484222325L;boolean ink=false;
        for(AssTex tex:f.getImages()){
            Bitmap b=tex.getBitmap();if(b==null)continue;
            assertEquals(0,tex.getTex());assertEquals(tex.getW(),b.getWidth());assertEquals(tex.getH(),b.getHeight());
            int[] data=new int[b.getWidth()*b.getHeight()];b.getPixels(data,0,b.getWidth(),0,0,b.getWidth(),b.getHeight());
            for(int v:data){ink|=(v>>>24)!=0;hash=(hash^v)*1099511628211L;}
        }
        assertTrue("actual bitmap coverage",ink);return hash;
    }
    static void empty(AssRender r,long ms){assertNull(r.renderFrame(ms,AssTexType.BITMAP_RGBA));}
    @Test public void actualSourceExtractsAndRendersIndependentTracks()throws Exception{
        assertEquals(34,Build.VERSION.SDK_INT);assertEquals("x86_64",Build.SUPPORTED_ABIS[0]);
        AssHandler h=new AssHandler(AssRenderType.OVERLAY_CANVAS,new AssHandlerConfig(10000,128,0));
        h.setVideoSize(320,180);h.onSurfaceSizeChanged(320,180);
        AssMatroskaExtractor ex=new AssMatroskaExtractor(new AssSubtitleParserFactory(h),h,0);
        byte[] bytes=fixture();DefaultExtractorInput in=input(bytes,0);
        assertTrue(ex.sniff(in));in.resetPeekPosition();
        Output out=new Output();ex.init(out);PositionHolder seek=new PositionHolder();
        AssTrack a=null,b=null;AssRender render=null;AssFrame saved=null;long digest=0;
        try{
            boolean eof=false;
            for(int i=0;i<200;i++){
                int r=ex.read(in,seek);
                if(r==Extractor.RESULT_END_OF_INPUT){eof=true;break;}
                if(r==Extractor.RESULT_SEEK)in=input(bytes,Math.toIntExact(seek.position));
            }
            assertTrue("actual extractor EOF",eof);assertEquals(3,out.sinks.size());
            a=select(h,out.sinks.get(1).format);render=h.getRender();assertNotNull(render);
            AssEvent[] ae=a.getEvents();assertNotNull(ae);assertEquals("no duplicate or stale no-duration event",2,ae.length);
            assertEquals(1230,ae[0].getStart());assertEquals(570,ae[0].getDuration());
            assertEquals(3000,ae[1].getStart());assertEquals(500,ae[1].getDuration());
            empty(render,1229);saved=render.renderFrame(1230,AssTexType.BITMAP_RGBA);digest=pixels(saved);
            empty(render,1800);long second=pixels(render.renderFrame(3000,AssTexType.BITMAP_RGBA));assertNotEquals(digest,second);
            empty(render,3500);empty(render,4500);
            b=select(h,out.sinks.get(2).format);assertNotSame(a,b);
            AssEvent[] be=b.getEvents();assertNotNull(be);assertEquals(1,be.length);assertEquals(2000,be[0].getStart());assertEquals(600,be[0].getDuration());
            empty(render,1999);long other=pixels(render.renderFrame(2000,AssTexType.BITMAP_RGBA));assertNotEquals(other,digest);
            empty(render,2600);assertSame(a,select(h,out.sinks.get(1).format));
            assertEquals(digest,pixels(render.renderFrame(1230,AssTexType.BITMAP_RGBA)));
            Sink ordinary=out.sinks.get(3);
            assertEquals(MimeTypes.TEXT_SUBRIP,ordinary.format.codecs);assertTrue("ordinary parser emitted cues",ordinary.committed>0);
            assertEquals(4000000L,ordinary.lastTime);
            Log.i(TAG,"PASS_PEERLESS_REAL_MATROSKA packets=3 tracks=2 no_duration_rejected=1 ordinary_cues="+ordinary.committed);
            Log.i(TAG,"PASS_PEERLESS_NATIVE_RGBA_TIMING first="+Long.toHexString(digest)+" second="+Long.toHexString(second)+" other="+Long.toHexString(other));
        }finally{ex.release();h.release();}
        assertNotNull(a);assertNotNull(b);assertNotNull(render);assertTrue(a.getReleased());assertTrue(b.getReleased());
        assertTrue(render.getReleased());assertTrue(h.getAss().getReleased());assertEquals(digest,pixels(saved));
        Log.i(TAG,"PASS_PEERLESS_OWNER_RELEASE_SAVED_BITMAPS");
    }
}
