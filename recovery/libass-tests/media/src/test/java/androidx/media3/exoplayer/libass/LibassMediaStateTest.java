package androidx.media3.exoplayer.libass;

import static org.junit.Assert.*;
import androidx.media3.common.Format;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassMediaStateTest {
    @Before public void reset(){LibassNative.reset();}
    static byte[] data(String s){return s.getBytes(StandardCharsets.UTF_8);}
    static Format format(String id){return new Format.Builder().setId(id).setSampleMimeType("text/x-ssa").build();}
    static LibassMediaState media(){return new LibassMediaState(new LibassConfiguration.Builder().setMaximumGlyphCount(4096).setMaximumBitmapCacheSizeMb(48).build(),true);}
    static long count(String name){return LibassNative.log.stream().filter(s->s.startsWith(name+":")).count();}
    static void size(LibassMediaState m){m.setFrameSize(640,360,1920,1080,0,0,640,360);}
    static void close(LibassMediaState m){m.close();m.close();assertTrue(LibassNative.tracks.isEmpty());assertTrue(LibassNative.libraries.isEmpty());}

    @Test public void sharedLibraryAndIndependentSecondaryClock(){
        LibassMediaState m=media();m.addTrack(1,data("header1"));m.addTrack(2,data("header2"));size(m);
        m.setPrimaryFormat(format("0:1"));m.setSecondaryFormat(format("0:2"));m.setSecondaryOffsetUs(300000);
        LibassFrameSet result=m.renderFrames(1000000,true);assertNotNull(result.primary);assertNotNull(result.secondary);
        assertEquals(1,count("library"));assertEquals(2,count("create"));
        assertTrue(LibassNative.log.contains("renderArgs:2:1000:true"));assertTrue(LibassNative.log.contains("renderArgs:3:700:true"));
        assertTrue(LibassNative.log.contains("position:2:0.0"));assertTrue(LibassNative.log.contains("position:3:1.0"));close(m);
    }
    @Test public void canonicalTrackCollisionAndNonnumericPrefix(){
        LibassMediaState m=media();m.setPrimaryFormat(format("0:2:7"));m.setSecondaryFormat(format("7"));
        m.addTrack(7,data("header"));size(m);LibassFrameSet frames=m.renderFrames(0,false);
        assertNotNull(frames.primary);assertNull(frames.secondary);assertEquals(1,count("render"));
        m.setPrimaryFormat(format("bad:7"));assertNull(m.renderFrames(0,true));close(m);
    }
    @Test public void externalFallbackAndNumericEmptySuffix(){
        LibassMediaState m=media();Format external=new Format.Builder().setLabel("English").setLanguage("en").setSampleMimeType("text/x-ssa").build();
        m.addExternalTrack(external,data("full ASS"),0,8);size(m);m.setPrimaryFormat(external.buildUpon().setId("2:").build());
        assertNotNull(m.renderFrames(0,true).primary);close(m);
    }
    @Test public void failedReplacementPreservesOldTrack(){
        LibassMediaState m=media();Format f=format("external");m.addExternalTrack(f,data("old"),0,3);size(m);m.setPrimaryFormat(f);
        LibassNative.fail="dataEnd";
        try{m.addExternalTrack(f,data("new"),0,3);fail();}catch(IllegalStateException expected){}
        assertTrue(LibassNative.tracks.containsKey(2L));assertFalse(LibassNative.tracks.containsKey(3L));
        m.renderFrames(1000,true);assertTrue(LibassNative.log.contains("renderArgs:2:1:true"));
        m.addExternalTrack(f,data("replacement"),0,11);assertFalse(LibassNative.tracks.containsKey(2L));assertEquals(1,LibassNative.tracks.size());close(m);
    }
    @Test public void timedSamplesUseFormatOffsetAndDeduplicate(){
        LibassMediaState m=media();Format relative=format("relative");byte[] bytes=data("sample");
        m.processTimedData(relative,bytes,0,bytes.length,2000);m.processTimedData(relative,bytes,0,bytes.length,2000);
        assertEquals(1,count("timed"));assertTrue(LibassNative.log.contains("timestamp:2"));
        m.processTimedData(relative,bytes,0,bytes.length,2001);assertEquals(2,count("timed"));
        Format absolute=relative.buildUpon().setId("absolute").setSubsampleOffsetUs(9000).build();m.processTimedData(absolute,bytes,0,bytes.length,2000);
        assertTrue(LibassNative.log.contains("timestamp:9"));
        m.processTimedData(format("unset"),bytes,0,bytes.length,Long.MIN_VALUE+1);assertTrue(LibassNative.log.contains("timestamp:0"));close(m);
    }
    @Test public void initializationDataPrefixMustActuallyMatch(){
        LibassMediaState m=media();byte[] format=data("Format: Layer, Text\n"),header=data("[Script Info]\n");
        Format f=format("init").buildUpon().setInitializationData(Arrays.asList(format,header)).build();m.processTimedData(f,data("a"),0,1,0);
        assertEquals(1,count("codec"));assertArrayEquals(header,LibassNative.payloads.get(0));assertArrayEquals(data("[Events]\nFormat: Layer, Text\n"),LibassNative.payloads.get(1));
        long codecs=count("codec");Format ordinary=f.buildUpon().setId("ordinary").setInitializationData(Arrays.asList(data("FormaX: ignored"),header)).build();
        m.processTimedData(ordinary,data("a"),0,1,0);assertEquals(codecs,count("codec"));close(m);
    }
    @Test public void fontsAreCopiedDeduplicatedAndReloadExistingTracks(){
        LibassMediaState m=media();byte[] bytes={1,2,3};m.addAttachment("synthetic.ttf","font/ttf",bytes);bytes[0]=9;
        m.addAttachment("synthetic.ttf","font/ttf",new byte[]{1,2,3});m.addTrack(1,data("h"));m.addTrack(2,data("h"));
        assertEquals(1,count("font"));assertArrayEquals(new byte[]{1,2,3},LibassNative.payloads.get(0));
        m.addAttachment("next.ttf","font/ttf",new byte[]{4,5,6});assertEquals(2,count("font"));assertEquals(2,count("fonts"));
        m.addAttachment("next.ttf","font/ttf",new byte[]{4,5,6});assertEquals(2,count("font"));assertEquals(2,count("fonts"));close(m);
    }
    @Test public void attachmentAdmissionMatchesMetadataAndBounds(){
        LibassMediaState m=media();assertFalse(m.shouldReadAttachment(null,null,0));assertFalse(m.shouldReadAttachment(null,null,33554433));
        assertTrue(m.shouldReadAttachment(null,null,4));assertTrue(m.shouldReadAttachment("x.ttf","unknown",4));assertFalse(m.shouldReadAttachment("x.woff2","font/woff2",4));
        m.addAttachment("x.woff2","font/woff2",new byte[]{1});m.addTrack(1,data("h"));assertEquals(0,count("font"));close(m);
    }
    @Test public void disposalImmediatelyFencesLateParserAndRenderBeforeQueuedCleanup(){
        LibassMediaState m=media();m.addTrack(1,data("h"));size(m);m.setPrimaryFormat(format("1"));List<Runnable> queue=new ArrayList<>();
        m.dispose(queue::add);m.dispose(queue::add);int before=LibassNative.log.size();
        m.addTrack(2,data("late"));m.addExternalTrack(format("late"),data("late"),0,4);m.processSample(1,0,0,data("late"),0,4);
        m.processTimedData(format("late"),data("late"),0,4,0);m.addAttachment("late.ttf","font/ttf",data("late"));
        m.setFontScale(2,true);assertFalse(m.isAvailable());assertNull(m.renderFrames(0,true));assertEquals(before,LibassNative.log.size());
        assertEquals(1,queue.size());assertFalse(LibassNative.tracks.isEmpty());queue.get(0).run();close(m);
    }
    @Test public void rejectedReleaseQueueStillFreesNative(){
        LibassMediaState m=media();m.addTrack(1,data("h"));m.dispose(r->{throw new RejectedExecutionException("closed queue");});close(m);
    }
    @Test public void inFlightParserCompletesBeforeNativeRelease()throws Exception{
        LibassMediaState m=media();CountDownLatch entered=new CountDownLatch(1),finish=new CountDownLatch(1);AtomicReference<Throwable> failure=new AtomicReference<>();
        LibassNative.duringData=()->{entered.countDown();try{if(!finish.await(10,TimeUnit.SECONDS))throw new AssertionError("watchdog");}catch(InterruptedException e){throw new AssertionError(e);}};
        Thread parser=new Thread(()->{try{m.addExternalTrack(format("flight"),data("ASS"),0,3);}catch(Throwable e){failure.set(e);}});parser.start();assertTrue(entered.await(10,TimeUnit.SECONDS));
        List<Runnable> queue=new ArrayList<>();m.dispose(queue::add);assertFalse(m.isAvailable());finish.countDown();parser.join(10000);assertFalse(parser.isAlive());assertNull(failure.get());
        queue.get(0).run();assertTrue(LibassNative.log.indexOf("dataEnd:2")<LibassNative.log.indexOf("release:2"));close(m);
    }
    @Test public void captionStyleMappingAndSettingsApplyToNewTracks(){
        LibassMediaState m=media();m.setStyleOverride(new LibassStyleOverride(null,1,2,3,4,5,6),"Synthetic Family");m.setBottomPositionFraction(0.25f);m.setFontScale(1.5f,true);
        m.addTrack(1,data("h"));assertTrue(LibassNative.log.contains("styleArgs:true:Synthetic Family:38.0:1:2:1:4:5.0:6.0"));assertTrue(LibassNative.log.contains("position:2:0.25"));
        m.setStyleOverride(null,null);assertTrue(LibassNative.log.contains("styleArgs:false:null:0.0:0:0:0:0:0.0:0.0"));
        assertEquals(2,new LibassStyleOverride(null,1,2,2,4,5,6).edgeType);assertEquals(0,new LibassStyleOverride(null,1,2,0,4,5,6).edgeType);close(m);
    }
}
