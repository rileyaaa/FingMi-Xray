package androidx.media3.exoplayer.text;

import androidx.annotation.Nullable;
import androidx.media3.common.text.CueGroup;

/** Reconstructed upstream-missing secondary cue channel; never feeds primary Player.onCues. */
public final class SecondaryTextOutput implements TextOutput, AutoCloseable {
    @Nullable private TextOutput output;
    private CueGroup cues = CueGroup.EMPTY_TIME_ZERO;
    private boolean closed;
    private long generation;

    public synchronized void setOutput(@Nullable TextOutput output) {
        if (closed) return;
        TextOutput previous = this.output;
        this.output = output;
        if (previous != null && previous != output) previous.onCues(CueGroup.EMPTY_TIME_ZERO);
        if (!closed && this.output == output && output != null) output.onCues(cues);
    }

    @Override public synchronized void onCues(CueGroup cues) {
        if (closed) return;
        this.cues = cues;
        if (output != null) output.onCues(cues);
    }

    /** Use for a renderer lifetime; reset/close reject callbacks queued by older renderers. */
    public synchronized TextOutput createRendererOutput() {
        long token = generation;
        return cues -> {
            synchronized (SecondaryTextOutput.this) {
                if (!closed && token == generation) onCues(cues);
            }
        };
    }

    public synchronized void reset() {
        generation++;
        onCues(CueGroup.EMPTY_TIME_ZERO);
    }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true; generation++; cues = CueGroup.EMPTY_TIME_ZERO;
        TextOutput previous = output; output = null;
        if (previous != null) previous.onCues(cues);
    }
}
