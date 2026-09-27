package androidx.media3.exoplayer.libass;

import androidx.media3.common.C;
import androidx.media3.exoplayer.NoSampleRenderer;
import androidx.media3.exoplayer.ExoPlaybackException;

/** Reconstructed jk1 clock contract on the real Media3 NoSampleRenderer lifecycle. */
final class LibassClockRenderer extends NoSampleRenderer {
    interface Listener {
        void enabled();
        void position(long positionUs,boolean force);
        void offset(long offsetMs);
        void disabled();
    }
    private final Listener listener;
    private long offsetUs,lastPositionUs=C.TIME_UNSET,lastElapsedUs=C.TIME_UNSET;
    LibassClockRenderer(Listener listener){this.listener=listener;}
    @Override public String getName(){return "LibassClockRenderer";}
    @Override protected void onEnabled(boolean joining){listener.enabled();}
    @Override protected void onDisabled(){listener.disabled();lastPositionUs=C.TIME_UNSET;lastElapsedUs=C.TIME_UNSET;}
    @Override protected void onRendererOffsetChanged(long offsetUs){this.offsetUs=offsetUs;lastPositionUs=C.TIME_UNSET;lastElapsedUs=C.TIME_UNSET;}
    @Override protected void onPositionReset(long positionUs,boolean joining,boolean mayRenderStartOfStream){notifyPosition(positionUs,true);lastElapsedUs=C.TIME_UNSET;}
    @Override public void render(long positionUs,long elapsedRealtimeUs){
        if((lastElapsedUs==C.TIME_UNSET||elapsedRealtimeUs<lastElapsedUs||elapsedRealtimeUs-lastElapsedUs>=16666)&&positionUs-offsetUs!=lastPositionUs){
            lastElapsedUs=elapsedRealtimeUs;notifyPosition(positionUs,false);
        }else if(lastElapsedUs==C.TIME_UNSET)lastElapsedUs=elapsedRealtimeUs;
    }
    private void notifyPosition(long positionUs,boolean force){lastPositionUs=positionUs-offsetUs;listener.position(lastPositionUs,force);}
    @Override public void handleMessage(int type,Object message)throws ExoPlaybackException {
        if(type==24)listener.offset((Long)message);else super.handleMessage(type,message);
    }
}
