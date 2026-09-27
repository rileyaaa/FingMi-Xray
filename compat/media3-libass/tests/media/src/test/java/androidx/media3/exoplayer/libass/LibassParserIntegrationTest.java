package androidx.media3.exoplayer.libass;

import static org.junit.Assert.*;
import androidx.media3.common.*;
import androidx.media3.extractor.*;
import androidx.media3.extractor.mkv.MatroskaExtractor;
import androidx.media3.extractor.text.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.io.*;
import androidx.media3.common.util.ParsableByteArray;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassParserIntegrationTest {
 @Before public void reset(){LibassNative.reset();}
 static LibassMediaState media(){return new LibassMediaState(new LibassConfiguration.Builder().build(),true);}
 static Format format(String container){return new Format.Builder().setId("external").setSampleMimeType(MimeTypes.TEXT_SSA).setContainerMimeType(container).build();}
 static void parse(SubtitleParser p,byte[] b,long time){p.parse(b,1,b.length-2,time,SubtitleParser.OutputOptions.allCues(),c->{fail("Libass parser must not duplicate ordinary cues");});}
 static long count(String prefix){return LibassNative.log.stream().filter(s->s.startsWith(prefix+":")).count();}
 @Test public void nonAssDelegatesAndUnavailableAssFallsBack(){
  LibassMediaState m=media();DefaultSubtitleParserFactory delegate=new DefaultSubtitleParserFactory();LibassSubtitleParserFactory f=new LibassSubtitleParserFactory(m,delegate);
  Format vtt=new Format.Builder().setSampleMimeType(MimeTypes.TEXT_VTT).build();
  assertEquals(delegate.supportsFormat(vtt),f.supportsFormat(vtt));assertEquals(delegate.create(vtt).getClass(),f.create(vtt).getClass());
  m.close();assertEquals(delegate.create(format(null)).getClass(),f.create(format(null)).getClass());
 }
 @Test public void timedExternalSamplesPreserveRangeTimeAndResetDedup(){
  LibassMediaState m=media();SubtitleParser p=new LibassSubtitleParserFactory(m).create(format(MimeTypes.VIDEO_MP4));byte[] bytes={9,1,2,3,9};
  parse(p,bytes,1234000);p.reset();parse(p,bytes,1234000);
  assertEquals(1,count("timed"));assertArrayEquals(new byte[]{1,2,3},LibassNative.timedPayloads.get(0));assertTrue(LibassNative.log.contains("timestamp:1234"));m.close();
 }
 @Test public void genericMatroskaParserStillFeedsWithoutPairedExtractor(){
  LibassMediaState m=media();parse(new LibassSubtitleParserFactory(m).create(format(MimeTypes.VIDEO_MATROSKA)),new byte[]{9,1,9},2000);
  assertEquals(1,count("timed"));m.close();
 }
 @Test public void pairedMatroskaSuppressesDuplicateFeedAndRoutesOriginalSamples(){
  LibassMediaState m=media();LibassSubtitleParserFactory f=new LibassSubtitleParserFactory(m);SubtitleParser.Factory paired=f.forMatroska();
  LibassMatroskaExtractor e=new LibassMatroskaExtractor(new MatroskaExtractor(f,3),m,paired);
  e.onAssTrackInitialized(1,"name","en",new byte[]{1});e.onAssSubtitleSample(1,1000,2000,new byte[]{9,2,9},1,1);
  int calls=LibassNative.log.size();parse(paired.create(format(MimeTypes.VIDEO_MATROSKA)),new byte[]{9,2,9},1000);
  assertEquals(calls,LibassNative.log.size());e.seek(0,0);assertEquals(calls,LibassNative.log.size());m.close();
 }
 @Test public void attachmentAndLateCallbacksStayWithinMediaOwner(){
  LibassMediaState a=media(),b=media();LibassSubtitleParserFactory f=new LibassSubtitleParserFactory(a);
  LibassMatroskaExtractor e=new LibassMatroskaExtractor(new MatroskaExtractor(f,3),a,f.forMatroska());
  e.onAttachment("a.ttf","font/ttf",new byte[]{1});b.addTrack(1,new byte[]{2});assertEquals(0,count("font"));a.addTrack(1,new byte[]{2});assertEquals(1,count("font"));
  SubtitleParser p=f.create(format(MimeTypes.VIDEO_MP4));a.close();int before=LibassNative.log.size();
  parse(p,new byte[]{9,2,9},3000);e.onAttachment("late.ttf","font/ttf",new byte[]{2});e.onAssTrackInitialized(2,null,null,new byte[]{3});assertEquals(before,LibassNative.log.size());b.close();
 }
 @Test public void failedParserReplacementKeepsOldTrack(){
  LibassMediaState m=media();SubtitleParser p=new LibassSubtitleParserFactory(m).create(format(null));parse(p,new byte[]{9,65,9},0);
  LibassNative.fail="dataEnd";assertThrows(IllegalStateException.class,()->parse(p,new byte[]{9,66,9},0));
  assertTrue(LibassNative.tracks.containsKey(2L));assertFalse(LibassNative.tracks.containsKey(3L));m.close();
 }
 @Test public void wholeFileUtf16BomConvertedWithinRange(){
  LibassMediaState m=media();SubtitleParser p=new LibassSubtitleParserFactory(m).create(format(null));
  parse(p,new byte[]{9,(byte)255,(byte)254,65,0,9},0);assertArrayEquals("A".getBytes(StandardCharsets.UTF_8),LibassNative.payloads.get(0));assertEquals(0,count("timed"));m.close();
 }
 @Test public void factoryPreservesOrdinaryExtractorsAndCustomMatroskaSubclasses(){
  LibassMediaState m=media();LibassSubtitleParserFactory parser=new LibassSubtitleParserFactory(m);
  Extractor ordinary=new androidx.media3.extractor.mp3.Mp3Extractor();MatroskaExtractor custom=new MatroskaExtractor(parser,3){};
  ExtractorsFactory delegate=()->new Extractor[]{ordinary,new MatroskaExtractor(parser,3),custom};
  Extractor[] out=new LibassExtractorsFactory(delegate,m,parser).createExtractors();assertSame(ordinary,out[0]);assertTrue(out[1] instanceof LibassMatroskaExtractor);assertSame(custom,out[2]);m.close();
 }
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

 @Test public void publicMatroskaReadFeedsOriginalPacketOnce() throws Exception {
  LibassMediaState m=media();LibassSubtitleParserFactory p=new LibassSubtitleParserFactory(m);
  LibassExtractorsFactory f=new LibassExtractorsFactory(()->new Extractor[]{new MatroskaExtractor(p,1)},m,p);
  read(f.createExtractors()[0],mkv("S_TEXT/ASS",true,true,SAMPLE));
  assertEquals(1,count("codec"));assertEquals(1,count("chunk"));assertEquals(0,count("timed"));assertEquals(0,count("dataEnd"));assertEquals(1,count("font"));m.close();
 }
}
