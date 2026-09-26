package androidx.media3.exoplayer.trackselection;

import android.content.Context;
import androidx.annotation.Nullable;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.C;
import androidx.media3.common.Format;
import androidx.media3.common.Timeline;
import androidx.media3.common.TrackGroup;
import androidx.media3.common.TrackSelectionOverride;
import androidx.media3.common.TrackSelectionParameters;
import androidx.media3.common.Tracks;
import androidx.media3.exoplayer.ExoPlaybackException;
import androidx.media3.exoplayer.Renderer;
import androidx.media3.exoplayer.RendererCapabilities;
import androidx.media3.exoplayer.RendererConfiguration;
import androidx.media3.exoplayer.source.MediaSource.MediaPeriodId;
import androidx.media3.exoplayer.source.TrackGroupArray;
import androidx.media3.exoplayer.upstream.BandwidthMeter;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Reconstructed upstream-missing implementation for FongMi Media3 1.11.0.
 * The last text renderer is the dedicated secondary renderer. The delegate
 * retains every renderer index and all primary/audio/video selection policies.
 * Selection state is published only on activation, never while prebuffering.
 */
public final class SecondaryTextTrackSelector extends TrackSelector {
    public static final class Factory implements TrackSelector.Factory {
        private final TrackSelector.Factory delegate;
        private final List<SecondaryTextTrackSelector> selectors = new ArrayList<>();
        private Options options = new Options(null, false, 0);

        public Factory(TrackSelector.Factory delegate) { this.delegate = delegate; }

        @Override public TrackSelector createTrackSelector(Context context) {
            return new SecondaryTextTrackSelector(delegate.createTrackSelector(context), this);
        }

        public void setSecondaryTextTrackSelectionOverride(@Nullable TrackSelectionOverride override) {
            if (override != null && (override.getType() != C.TRACK_TYPE_TEXT || override.trackIndices.size() != 1))
                throw new IllegalArgumentException("Secondary text requires one text track");
            update(override, null);
        }

        public void setSecondaryTextTrackAutoSelectionEnabled(boolean enabled) { update(null, enabled); }

        public void reset() {
            List<SecondaryTextTrackSelector> targets;
            synchronized (this) {
                options = new Options(null, options.automatic, options.revision + 1);
                targets = new ArrayList<>(selectors);
            }
            for (SecondaryTextTrackSelector selector : targets) selector.invalidate(null);
        }

        private void update(@Nullable TrackSelectionOverride override, @Nullable Boolean automatic) {
            List<SecondaryTextTrackSelector> targets;
            synchronized (this) {
                TrackSelectionOverride next = automatic == null ? override : options.override;
                boolean auto = automatic == null ? options.automatic : automatic;
                if (Objects.equals(next, options.override) && auto == options.automatic) return;
                options = new Options(next, auto, options.revision + 1);
                targets = new ArrayList<>(selectors);
            }
            for (SecondaryTextTrackSelector selector : targets) selector.invalidate(null);
        }

        private synchronized Options snapshot() { return options; }
        private synchronized void attach(SecondaryTextTrackSelector selector) { if (!selectors.contains(selector)) selectors.add(selector); }
        private synchronized void detach(SecondaryTextTrackSelector selector) { selectors.remove(selector); }
    }

    private static final class Options {
        @Nullable final TrackSelectionOverride override;
        final boolean automatic;
        final long revision;
        Options(@Nullable TrackSelectionOverride override, boolean automatic, long revision) {
            this.override = override; this.automatic = automatic; this.revision = revision;
        }
    }

    private static final class Selection {
        @Nullable final Object delegateInfo;
        @Nullable final TrackSelectionOverride primary, secondary;
        final List<TrackSelectionOverride> available;
        final long revision, lifetime;
        final boolean suppressed;
        Selection(@Nullable Object info, @Nullable TrackSelectionOverride primary,
                @Nullable TrackSelectionOverride secondary, List<TrackSelectionOverride> available,
                Options options, long lifetime) {
            this.lifetime = lifetime;
            delegateInfo = info; this.primary = primary; this.secondary = secondary;
            this.available = java.util.Collections.unmodifiableList(new ArrayList<>(available));
            revision = options.revision;
            suppressed = options.override != null && secondary == null;
        }
    }

    private final TrackSelector delegate;
    private final Factory owner;
    private TrackSelectionParameters activeParameters;
    @Nullable private volatile Selection active;
    private volatile boolean released;
    private long lifetime;

    public SecondaryTextTrackSelector(TrackSelector delegate, Factory owner) {
        this.delegate = delegate; this.owner = owner;
        activeParameters = delegate.getParameters();
    }

    @Override public void init(InvalidationListener listener, BandwidthMeter meter) {
        super.init(listener, meter);
        released = false; lifetime++;
        owner.attach(this);
        delegate.init(new InvalidationListener() {
            @Override public void onTrackSelectionsInvalidated(@Nullable TrackSelectionParameters parameters) { invalidate(parameters); }
            @Override public void onRendererCapabilitiesChanged(Renderer renderer) { invalidateForRendererCapabilitiesChange(renderer); }
        }, meter);
    }

    @Override public void release() {
        released = true; active = null; owner.detach(this);
        delegate.release(); super.release();
    }

    @Override public TrackSelectorResult selectTracks(RendererCapabilities[] renderers,
            TrackGroupArray groups, MediaPeriodId period, Timeline timeline) throws ExoPlaybackException {
        int secondaryIndex = -1, textCount = 0;
        for (int i = 0; i < renderers.length; i++) if (renderers[i].getTrackType() == C.TRACK_TYPE_TEXT) {
            secondaryIndex = i; textCount++;
        }
        if (textCount < 2) secondaryIndex = -1;
        RendererCapabilities[] primaryRenderers = renderers.clone();
        if (secondaryIndex >= 0) primaryRenderers[secondaryIndex] = RESERVED_TEXT;
        TrackSelectorResult result = delegate.selectTracks(primaryRenderers, groups, period, timeline);
        ExoTrackSelection[] selections = result.selections.clone();
        RendererConfiguration[] configs = result.rendererConfigurations.clone();
        TrackSelectionOverride primary = null;
        for (int i = 0; i < renderers.length; i++) {
            if (i != secondaryIndex && renderers[i].getTrackType() == C.TRACK_TYPE_TEXT && selections[i] != null) {
                ExoTrackSelection selection = selections[i];
                primary = new TrackSelectionOverride(selection.getTrackGroup(), selection.getIndexInTrackGroup(0));
                break;
            }
        }
        Options options = owner.snapshot();
        List<TrackSelectionOverride> available = new ArrayList<>();
        if (secondaryIndex >= 0) {
            selections[secondaryIndex] = null; configs[secondaryIndex] = null;
            for (int i = 0; i < groups.length; i++) {
                TrackGroup group = groups.get(i);
                if (group.type != C.TRACK_TYPE_TEXT) continue;
                for (int t = 0; t < group.length; t++) {
                    if (RendererCapabilities.getFormatSupport(renderers[secondaryIndex].supportsFormat(group.getFormat(t))) != C.FORMAT_HANDLED) continue;
                    TrackSelectionOverride candidate = new TrackSelectionOverride(group, t);
                    if (!candidate.equals(primary)) available.add(candidate);
                }
            }
        }
        TrackSelectionOverride secondary = null;
        if (options.override != null) {
            for (TrackSelectionOverride candidate : available) if (candidate.equals(options.override)) { secondary = candidate; break; }
        } else if (options.automatic && !activeParameters.disabledTrackTypes.contains(C.TRACK_TYPE_TEXT)) {
            int best = Integer.MIN_VALUE;
            String primaryLanguage = primary == null ? null : primary.mediaTrackGroup.getFormat(primary.trackIndices.get(0)).language;
            for (TrackSelectionOverride candidate : available) {
                Format format = candidate.mediaTrackGroup.getFormat(candidate.trackIndices.get(0));
                int score = Objects.equals(format.language, primaryLanguage) ? 0 : 100;
                for (int i = 0; i < activeParameters.preferredTextLanguages.size(); i++) {
                    if (languageMatches(format.language, activeParameters.preferredTextLanguages.get(i))) {
                        score += 1000 - i; break;
                    }
                }
                if ((format.selectionFlags & C.SELECTION_FLAG_FORCED) == 0) score += 10;
                if (score > best) { best = score; secondary = candidate; }
            }
        }
        if (secondary != null) {
            selections[secondaryIndex] = new FixedTrackSelection(secondary.mediaTrackGroup, secondary.trackIndices.get(0));
            configs[secondaryIndex] = RendererConfiguration.DEFAULT;
        }
        List<Tracks.Group> tracks = new ArrayList<>();
        for (Tracks.Group group : result.tracks.getGroups()) {
            boolean[] selected = new boolean[group.length]; int[] support = new int[group.length];
            for (int t = 0; t < group.length; t++) {
                support[t] = group.getTrackSupport(t);
                boolean secondarySelected = secondary != null && secondary.mediaTrackGroup.equals(group.getMediaTrackGroup()) && secondary.trackIndices.contains(t);
                selected[t] = group.isTrackSelected(t) || secondarySelected;
                if (secondarySelected) support[t] = C.FORMAT_HANDLED;
            }
            tracks.add(new Tracks.Group(group.getMediaTrackGroup(), group.isAdaptiveSupported(), support, selected));
        }
        return new TrackSelectorResult(configs, selections, new Tracks(tracks),
                new Selection(result.info, primary, secondary, available, options, lifetime));
    }

    private static boolean languageMatches(@Nullable String language, String preferred) {
        return language != null && (language.equalsIgnoreCase(preferred)
                || language.split("-")[0].equalsIgnoreCase(preferred.split("-")[0]));
    }

    @Override public void onSelectionActivated(@Nullable Object info) {
        if (released) return;
        if (!(info instanceof Selection)) { active = null; delegate.onSelectionActivated(info); return; }
        Selection selection = (Selection) info;
        if (selection.lifetime != lifetime) return;
        delegate.onSelectionActivated(selection.delegateInfo);
        active = selection.revision == owner.snapshot().revision ? selection : null;
    }

    @Nullable private Selection current() {
        Selection value = active;
        return value != null && value.revision == owner.snapshot().revision ? value : null;
    }
    @Nullable public TrackSelectionOverride getPrimaryTextTrackSelectionOverride() { Selection value = current(); return value == null ? null : value.primary; }
    @Nullable public TrackSelectionOverride getSecondaryTextTrackSelectionOverride() { Selection value = current(); return value == null ? null : value.secondary; }
    public List<TrackSelectionOverride> getSecondaryTextTrackSelectionOverrides() { Selection value = current(); return value == null ? java.util.Collections.emptyList() : value.available; }
    public boolean isSecondaryTextTrackSuppressed() { Selection value = current(); return value != null && value.suppressed; }
    @Override public TrackSelectionParameters getParameters() { return delegate.getParameters(); }
    @Override public void setParameters(TrackSelectionParameters parameters) { delegate.setParameters(parameters); }
    @Override public void onParametersActivated(@Nullable TrackSelectionParameters parameters) {
        delegate.onParametersActivated(parameters);
        if (parameters != null) activeParameters = parameters;
    }
    @Override public boolean isSetParametersSupported() { return delegate.isSetParametersSupported(); }
    @Override public void setAudioAttributes(AudioAttributes attributes) { delegate.setAudioAttributes(attributes); }
    @Nullable @Override public RendererCapabilities.Listener getRendererCapabilitiesListener() { return delegate.getRendererCapabilitiesListener(); }

    private static final RendererCapabilities RESERVED_TEXT = new RendererCapabilities() {
        @Override public String getName() { return "ReservedSecondaryText"; }
        @Override public int getTrackType() { return C.TRACK_TYPE_TEXT; }
        @Override public int supportsFormat(Format format) { return RendererCapabilities.create(C.FORMAT_UNSUPPORTED_TYPE); }
        @Override public int supportsMixedMimeTypeAdaptation() { return ADAPTIVE_NOT_SUPPORTED; }
    };
}
