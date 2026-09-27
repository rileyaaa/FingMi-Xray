package androidx.media3.extractor.mkv;

import static org.junit.Assert.*;
import androidx.media3.common.*;
import androidx.media3.common.util.ParsableByteArray;
import androidx.media3.extractor.*;
import androidx.media3.extractor.text.DefaultSubtitleParserFactory;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/** Real public extractor read path, synthetic EBML only; no reflection-driven expected values. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassMatroskaHooksTest {
    static final byte[] HEADER=text("[Script Info]\nScriptType: v4.00+\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n");
    static final byte[] SAMPLE=text("0,0,Default,,0,0,0,,Synthetic subtitle");
    static byte[] text(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static byte[] join(byte[]...parts){ByteArrayOutputStream o=new ByteArrayOutputStream();for(byte[] b:parts)o.write(b,0,b.length);return o.toByteArray();}
    static byte[] number(long value){int size=1;while(size<8&&(value>>>(size*8))!=0)size++;byte[] b=new byte[size];for(int i=size-1;i>=0;i--){b[i]=(byte)value;value>>>=8;}return b;}
    static byte[] element(int id,byte[]...payload){byte[] b=join(payload);int count=1;while(b.length>=(1L<<(7*count))-1)count++;return join(number(id),number((1L<<(7*count))|b.length),b);}
    static byte[] integer(int id,long value){return element(id,number(value));}
    static byte[] attachment(boolean metadataFirst){
        byte[] meta=join(element(0x466e,text("synthetic.ttf")),element(0x4660,text("font/ttf")));
        byte[] data=element(0x465c,new byte[]{1,2,3,4});
        return element(0x1941a469,element(0x61a7,metadataFirst?join(meta,data):join(data,meta)));
    }
    static byte[] mkv(String codec,boolean metadataFirst,boolean duration,byte[] sample){
        byte[] ebml=element(0x1a45dfa3,integer(0x4286,1),integer(0x42f7,1),integer(0x42f2,4),integer(0x42f3,8),element(0x4282,text("matroska")),integer(0x4287,4),integer(0x4285,2));
        byte[] info=element(0x1549a966,integer(0x2ad7b1,1000000));
        byte[] tracks=element(0x1654ae6b,element(0xae,integer(0xd7,1),integer(0x73c5,1),integer(0x83,17),element(0x86,text(codec)),element(0x63a2,HEADER),element(0x536e,text("synthetic")),element(0x22b59c,text("eng"))));
        byte[] block=element(0xa1,new byte[]{(byte)0x81,0,20,0},sample);
        byte[] cluster=element(0x1f43b675,integer(0xe7,100),element(0xa0,duration?join(block,integer(0x9b,50)):block));
        return join(ebml,element(0x18538067,info,tracks,attachment(metadataFirst),cluster));
    }
    static final class Capture extends MatroskaExtractor {
        final boolean accept;
        final List<String> events=new ArrayList<>();
        byte[] codec,raw,font;String name,mime;long time,duration;int initialized,samples,decisions;
        Capture(boolean accept){super(new DefaultSubtitleParserFactory(),FLAG_DISABLE_SEEK_FOR_CUES|FLAG_EMIT_RAW_SUBTITLE_DATA);this.accept=accept;}
        @Override protected boolean shouldReadAttachment(String name,String mime,int size){decisions++;events.add("attachment-decision:"+name+":"+mime);assertEquals(4,size);return accept;}
        @Override protected void onAttachment(String name,String mime,byte[] font){this.name=name;this.mime=mime;this.font=font.clone();events.add("font");}
        @Override protected void onAssTrackInitialized(int track,String name,String language,byte[] codec){assertEquals(1,track);assertEquals("synthetic",name);assertEquals("eng",language);this.codec=codec.clone();initialized++;events.add("track");}
        @Override protected void onAssSubtitleSample(int track,long time,long duration,byte[] bytes,int offset,int length){assertEquals(1,track);assertTrue(offset>0);this.time=time;this.duration=duration;raw=Arrays.copyOfRange(bytes,offset,offset+length);samples++;events.add("sample");}
    }
    static final class Output implements ExtractorOutput,TrackOutput {
        byte[] data;long time;int samples;Format format;
        public TrackOutput track(int id,int type){assertEquals(1,id);assertEquals(C.TRACK_TYPE_TEXT,type);return this;}
        public void endTracks(){}
        public void seekMap(SeekMap map){}
        public void format(Format format){this.format=format;}
        public int sampleData(DataReader reader,int length,boolean end,int part)throws IOException {byte[] b=new byte[length];return reader.read(b,0,length);}
        public void sampleData(ParsableByteArray bytes,int length,int part){data=new byte[length];bytes.readBytes(data,0,length);}
        public void sampleMetadata(long time,int flags,int size,int offset,CryptoData crypto){this.time=time;samples++;}
    }
    static Output read(Extractor extractor,byte[] bytes)throws Exception{
        ByteArrayInputStream stream=new ByteArrayInputStream(bytes);DefaultExtractorInput input=new DefaultExtractorInput(stream::read,0,bytes.length);
        assertTrue(extractor.sniff(input));input.resetPeekPosition();Output output=new Output();extractor.init(output);PositionHolder seek=new PositionHolder();
        for(int i=0;i<20;i++){int result=extractor.read(input,seek);if(result==Extractor.RESULT_END_OF_INPUT){extractor.release();return output;}assertEquals(Extractor.RESULT_CONTINUE,result);}
        throw new AssertionError("Extractor did not finish");
    }
    @Test public void assRawSampleAndNormalOutputBothPreserved()throws Exception{
        Capture c=new Capture(true);Output o=read(c,mkv("S_TEXT/ASS",true,true,SAMPLE));
        assertEquals(1,c.initialized);assertArrayEquals(HEADER,c.codec);assertArrayEquals(SAMPLE,c.raw);
        assertEquals(120000,c.time);assertEquals(50000,c.duration);assertEquals(1,c.samples);
        assertEquals(1,o.samples);assertEquals(c.time,o.time);assertEquals("text/x-ssa",o.format.sampleMimeType);
        // Independent unmodified pinned AAR defines the ordinary Media3 output.
        try(URLClassLoader baseline=new URLClassLoader(new URL[]{new File(System.getProperty("libass.baseline")).toURI().toURL()},getClass().getClassLoader()){
            @Override protected synchronized Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException{
                if(!name.startsWith("androidx.media3.extractor.mkv."))return super.loadClass(name,resolve);
                Class<?> cls=findLoadedClass(name);if(cls==null)cls=findClass(name);if(resolve)resolveClass(cls);return cls;
            }
        }){
            Class<?> cls=baseline.loadClass("androidx.media3.extractor.mkv.MatroskaExtractor");
            Extractor reference=(Extractor)cls.getConstructor(androidx.media3.extractor.text.SubtitleParser.Factory.class,int.class).newInstance(new DefaultSubtitleParserFactory(),3);
            Output original=read(reference,mkv("S_TEXT/ASS",true,true,SAMPLE));
            assertArrayEquals(original.data,o.data);assertEquals(original.time,o.time);assertEquals(original.format,o.format);
        }
        assertArrayEquals(new byte[]{1,2,3,4},c.font);assertEquals(Arrays.asList("track","attachment-decision:synthetic.ttf:font/ttf","font","sample"),c.events);
    }
    @Test public void ssaNullTerminationExcludesTrailingGarbage()throws Exception{
        Capture c=new Capture(false);Output o=read(c,mkv("S_TEXT/SSA",true,true,join(SAMPLE,new byte[]{0},text("trailing"))));
        assertArrayEquals(SAMPLE,c.raw);assertFalse(new String(o.data,StandardCharsets.UTF_8).contains("trailing"));assertNull(c.font);assertEquals(1,c.decisions);
    }
    @Test public void attachmentMetadataMayFollowPayload()throws Exception{
        Capture c=new Capture(true);read(c,mkv("S_TEXT/ASS",false,true,SAMPLE));
        assertTrue(c.events.contains("attachment-decision:null:null"));assertEquals("synthetic.ttf",c.name);assertEquals("font/ttf",c.mime);assertArrayEquals(new byte[]{1,2,3,4},c.font);
    }
    @Test public void absentDurationDoesNotInventNativeEvent()throws Exception{
        Capture c=new Capture(true);read(c,mkv("S_TEXT/ASS",true,false,SAMPLE));assertEquals(0,c.samples);assertNull(c.raw);
    }
    @Test public void plainExtractorStillDeliversSubtitleWithoutReadingAttachment()throws Exception{
        MatroskaExtractor c=new MatroskaExtractor(new DefaultSubtitleParserFactory(),MatroskaExtractor.FLAG_DISABLE_SEEK_FOR_CUES|MatroskaExtractor.FLAG_EMIT_RAW_SUBTITLE_DATA);
        Output output=read(c,mkv("S_TEXT/ASS",true,true,SAMPLE));assertEquals(1,output.samples);assertNotNull(output.data);
    }
}
