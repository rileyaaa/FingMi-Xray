package androidx.media3.extractor.text;

import static org.junit.Assert.*;
import androidx.media3.common.*;
import androidx.media3.common.util.Consumer;
import androidx.media3.common.util.ParsableByteArray;
import androidx.media3.extractor.*;
import androidx.media3.extractor.text.ssa.SsaParser;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class SubtitleSampleTimeTest {
    static final class Sink implements TrackOutput {
        final List<Long> timestamps=new ArrayList<>();
        public void format(Format f){}
        public int sampleData(DataReader r,int length,boolean end,int part)throws IOException{return r.read(new byte[length],0,length);}
        public void sampleData(ParsableByteArray b,int length,int part){b.skipBytes(length);}
        public void sampleMetadata(long time,int flags,int size,int offset,CryptoData crypto){timestamps.add(time);}
    }
    static class Timed implements SubtitleParser {
        final List<Long> times=new ArrayList<>();final List<byte[]> samples=new ArrayList<>();boolean emit;
        public void parse(byte[] b,int offset,int length,OutputOptions options,Consumer<CuesWithTiming> out){throw new AssertionError("Timestamp was discarded");}
        public void parse(byte[] b,int offset,int length,long time,OutputOptions options,Consumer<CuesWithTiming> out){times.add(time);samples.add(Arrays.copyOfRange(b,offset,offset+length));if(emit)out.accept(new CuesWithTiming(Collections.emptyList(),70,80));}
        public int getCueReplacementBehavior(){return Format.CUE_REPLACEMENT_BEHAVIOR_REPLACE;}
    }
    static SubtitleTranscodingTrackOutput output(Sink sink,SubtitleParser parser,Format format){
        SubtitleTranscodingTrackOutput output=new SubtitleTranscodingTrackOutput(sink,new SubtitleParser.Factory(){
            public boolean supportsFormat(Format f){return true;}
            public int getCueReplacementBehavior(Format f){return parser.getCueReplacementBehavior();}
            public SubtitleParser create(Format f){return parser;}
        });output.format(format);return output;
    }
    static Format format(){return new Format.Builder().setSampleMimeType("text/x-ssa").build();}
    @Test public void metadataTimestampAndBufferedSampleRangeReachParser(){
        Timed parser=new Timed();SubtitleTranscodingTrackOutput output=output(new Sink(),parser,format());
        output.sampleData(new ParsableByteArray(new byte[]{1,2,3,4,5,6}),6);
        output.sampleMetadata(1234567,0,2,2,null);output.sampleMetadata(2345678,0,2,0,null);
        assertEquals(Arrays.asList(1234567L,2345678L),parser.times);assertArrayEquals(new byte[]{3,4},parser.samples.get(0));assertArrayEquals(new byte[]{5,6},parser.samples.get(1));
    }
    @Test public void oldParserMethodRemainsDefaultTarget(){
        final List<byte[]> calls=new ArrayList<>();SubtitleParser old=new SubtitleParser(){
            public void parse(byte[] b,int o,int n,OutputOptions opts,Consumer<CuesWithTiming> out){calls.add(Arrays.copyOfRange(b,o,o+n));}
            public int getCueReplacementBehavior(){return Format.CUE_REPLACEMENT_BEHAVIOR_REPLACE;}
        };
        old.parse(new byte[]{1,2,3},1,2,7654321,SubtitleParser.OutputOptions.allCues(),c->{fail();});
        assertEquals(1,calls.size());assertArrayEquals(new byte[]{2,3},calls.get(0));
    }
    @Test public void prebuiltSsaParserUsesNewDefaultWithoutChangingCueTimes(){
        byte[] bytes=("[Script Info]\nScriptType: v4.00+\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,Synthetic\n").getBytes(StandardCharsets.UTF_8);
        List<CuesWithTiming> original=new ArrayList<>(),timed=new ArrayList<>();
        new SsaParser().parse(bytes,0,bytes.length,SubtitleParser.OutputOptions.allCues(),original::add);
        SubtitleParser prebuilt=new SsaParser();prebuilt.parse(bytes,0,bytes.length,9876543,SubtitleParser.OutputOptions.allCues(),timed::add);
        assertFalse(original.isEmpty());assertEquals(original.size(),timed.size());
        for(int i=0;i<original.size();i++){assertEquals(original.get(i).startTimeUs,timed.get(i).startTimeUs);assertEquals(original.get(i).durationUs,timed.get(i).durationUs);assertEquals(original.get(i).cues,timed.get(i).cues);}
    }
    @Test public void cueOutputOffsetsStillAppliedExactlyOnce(){
        for(boolean absolute:new boolean[]{false,true}){
            Timed parser=new Timed();parser.emit=true;Sink sink=new Sink();Format f=absolute?format().buildUpon().setSubsampleOffsetUs(9000).build():format();
            SubtitleTranscodingTrackOutput output=output(sink,parser,f);output.sampleData(new ParsableByteArray(new byte[]{1}),1);output.sampleMetadata(1000,0,1,0,null);
            assertEquals(Collections.singletonList(1000L),parser.times);assertEquals(Collections.singletonList(absolute?9070L:1070L),sink.timestamps);
        }
    }
}
