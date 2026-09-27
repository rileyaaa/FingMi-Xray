package androidx.media3.exoplayer.libass;

import java.util.Objects;

/** Reconstructed published uk1.c -> vk1/wk1 -> libass.g.h, not original source. */
final class LibassStyleOverride {
    final String family;
    final int foreground, background, edgeType, edgeColor;
    final float edgeWidth, shadowOffset;

    LibassStyleOverride(String family,int foreground,int background,int captionEdgeType,
                        int edgeColor,float edgeWidth,float shadowOffset) {
        LibassConfiguration.family(family);
        if(!Float.isFinite(edgeWidth)||edgeWidth<0||!Float.isFinite(shadowOffset)||shadowOffset<0)
            throw new IllegalArgumentException("Invalid edge width or shadow offset");
        this.family=family==null?"sans-serif":family;this.foreground=foreground;this.background=background;
        this.edgeType=captionEdgeType==0?0:captionEdgeType==2?2:1;
        this.edgeColor=edgeColor;this.edgeWidth=edgeWidth;this.shadowOffset=shadowOffset;
    }
    void apply(LibassTrack track,String familyOverride) {
        track.setStyleOverride(true,familyOverride==null?family:familyOverride,38f,
                foreground,background,edgeType,edgeColor,edgeWidth,shadowOffset);
    }
    @Override public boolean equals(Object o) {
        if(!(o instanceof LibassStyleOverride))return false;LibassStyleOverride s=(LibassStyleOverride)o;
        return family.equals(s.family)&&foreground==s.foreground&&background==s.background
                &&edgeType==s.edgeType&&edgeColor==s.edgeColor&&Float.compare(edgeWidth,s.edgeWidth)==0
                &&Float.compare(shadowOffset,s.shadowOffset)==0;
    }
    @Override public int hashCode(){return Objects.hash(family,foreground,background,edgeType,edgeColor,edgeWidth,shadowOffset);}
}
