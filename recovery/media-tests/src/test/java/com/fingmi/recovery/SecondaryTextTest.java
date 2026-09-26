package com.fingmi.recovery;

import static org.junit.Assert.*;
import androidx.media3.common.*;
import androidx.media3.common.text.*;
import androidx.media3.exoplayer.*;
import androidx.media3.exoplayer.source.*;
import androidx.media3.exoplayer.source.MediaSource.MediaPeriodId;
import androidx.media3.exoplayer.trackselection.*;
import androidx.media3.exoplayer.text.*;
import androidx.media3.exoplayer.upstream.DefaultBandwidthMeter;
import java.util.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE, sdk=28)
public class SecondaryTextTest {
    private final TrackGroup zh = group("zh", "zh"), en = group("en", "en"), fr = group("fr", "fr");
    private SecondaryTextTrackSelector.Factory factory;
    private SecondaryTextTrackSelector selector;
    private DefaultTrackSelector primary;
    private int invalidations;
    private RendererCapabilities[] renderers;

    static TrackGroup group(String id, String language) {
        return new TrackGroup(id, new Format.Builder().setId(id).setSampleMimeType(MimeTypes.TEXT_VTT).setLanguage(language).build());
    }
    static RendererCapabilities text(boolean supported) {
        return new RendererCapabilities() {
            public String getName() { return "TextRenderer"; }
            public int getTrackType() { return C.TRACK_TYPE_TEXT; }
            public int supportsFormat(Format format) { return RendererCapabilities.create(supported && MimeTypes.getTrackType(format.sampleMimeType)==C.TRACK_TYPE_TEXT ? C.FORMAT_HANDLED : C.FORMAT_UNSUPPORTED_TYPE); }
            public int supportsMixedMimeTypeAdaptation() { return ADAPTIVE_NOT_SUPPORTED; }
        };
    }
    @Before public void setup() {
        factory = new SecondaryTextTrackSelector.Factory(context -> {
            primary = new DefaultTrackSelector(context);
            primary.setParameters(primary.buildUponParameters().setOverrideForType(new TrackSelectionOverride(zh,0)).build());
            return primary;
        });
        selector = (SecondaryTextTrackSelector)factory.createTrackSelector(RuntimeEnvironment.getApplication());
        selector.init(p -> invalidations++, new DefaultBandwidthMeter.Builder(RuntimeEnvironment.getApplication()).build());
        selector.onParametersActivated(primary.getParameters());
        renderers = new RendererCapabilities[]{text(true),text(true)};
    }
    @After public void cleanup() { selector.release(); }
    TrackSelectorResult select(TrackGroup... groups) throws Exception {
        return selector.selectTracks(renderers,new TrackGroupArray(groups),new MediaPeriodId("period"),Timeline.EMPTY);
    }
    @Test public void twoIndependentStreamsAndPrimaryUnchanged() throws Exception {
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(en,0));
        TrackSelectorResult result = select(zh,en);
        assertEquals(zh,result.selections[0].getTrackGroup());
        assertEquals(en,result.selections[1].getTrackGroup());
        assertTrue(result.isRendererEnabled(0));assertTrue(result.isRendererEnabled(1));
        assertEquals(2,result.tracks.getGroups().stream().filter(Tracks.Group::isSelected).count());
        assertNull(selector.getSecondaryTextTrackSelectionOverride());
        selector.onSelectionActivated(result.info);
        assertEquals(en,selector.getSecondaryTextTrackSelectionOverride().mediaTrackGroup);
        assertEquals(zh,selector.getPrimaryTextTrackSelectionOverride().mediaTrackGroup);
    }
    @Test public void primaryDuplicateSuppressedAndUnsupportedDoesNotFallback() throws Exception {
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(zh,0));
        TrackSelectorResult result=select(zh,en);assertNull(result.selections[1]);selector.onSelectionActivated(result.info);
        assertTrue(selector.isSecondaryTextTrackSuppressed());
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(en,0));
        renderers[1]=text(false);result=select(zh,en);assertNull(result.selections[1]);assertNotNull(result.selections[0]);
    }
    @Test public void sameTrackGroupCannotBindSampleQueueTwice() throws Exception {
        TrackGroup multi=new TrackGroup("multi",zh.getFormat(0),en.getFormat(0));
        primary.setParameters(primary.buildUponParameters().setOverrideForType(new TrackSelectionOverride(multi,0)).build());
        selector.onParametersActivated(primary.getParameters());
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(multi,1));
        TrackSelectorResult result=select(multi);
        assertEquals(0,result.selections[0].getIndexInTrackGroup(0));assertNull(result.selections[1]);
    }
    @Test public void autoLanguageAndDisable() throws Exception {
        primary.setParameters(primary.buildUponParameters().setPreferredTextLanguages("fr","en").build());
        selector.onParametersActivated(primary.getParameters());factory.setSecondaryTextTrackAutoSelectionEnabled(true);
        assertEquals(fr,select(zh,en,fr).selections[1].getTrackGroup());
        factory.setSecondaryTextTrackAutoSelectionEnabled(false);assertNull(select(zh,en,fr).selections[1]);
    }
    @Test public void absentOverrideNeverSubstitutesAnotherTrack() throws Exception {
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(en,0));
        factory.setSecondaryTextTrackAutoSelectionEnabled(true);
        assertNull(select(zh,fr).selections[1]);
    }
    @Test public void oldActivationCannotPublishAfterResetOrRelease() throws Exception {
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(en,0));
        TrackSelectorResult old=select(zh,en);factory.reset();selector.onSelectionActivated(old.info);
        assertNull(selector.getSecondaryTextTrackSelectionOverride());
        int before=invalidations;selector.release();factory.setSecondaryTextTrackAutoSelectionEnabled(true);
        assertEquals(before,invalidations);selector.onSelectionActivated(old.info);assertNull(selector.getPrimaryTextTrackSelectionOverride());
    }
    @Test public void preloaderActivationCannotPublishIntoPlayerSelector() throws Exception {
        factory.setSecondaryTextTrackSelectionOverride(new TrackSelectionOverride(en,0));
        TrackSelectorResult foreign=select(zh,en);
        SecondaryTextTrackSelector other=(SecondaryTextTrackSelector)factory.createTrackSelector(RuntimeEnvironment.getApplication());
        other.init(p -> {},new DefaultBandwidthMeter.Builder(RuntimeEnvironment.getApplication()).build());
        other.onSelectionActivated(foreign.info);
        assertNull(other.getSecondaryTextTrackSelectionOverride());other.release();
    }
    @Test public void outputRebindResetAndLateCallbacks() {
        SecondaryTextOutput output = new SecondaryTextOutput();
        List<CueGroup> first=new ArrayList<>(), second=new ArrayList<>();output.setOutput(first::add);
        TextOutput old=output.createRendererOutput();
        CueGroup cue=new CueGroup(Collections.singletonList(new Cue.Builder().setText("second").build()),42);
        old.onCues(cue);assertSame(cue,first.get(first.size()-1));
        output.setOutput(second::add);assertTrue(first.get(first.size()-1).cues.isEmpty());assertSame(cue,second.get(0));
        output.reset();old.onCues(cue);assertTrue(second.get(second.size()-1).cues.isEmpty());
        TextOutput fresh=output.createRendererOutput();fresh.onCues(cue);assertSame(cue,second.get(second.size()-1));
        output.close();fresh.onCues(cue);assertTrue(second.get(second.size()-1).cues.isEmpty());
    }
}
