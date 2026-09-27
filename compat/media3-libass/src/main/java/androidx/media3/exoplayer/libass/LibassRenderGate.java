package androidx.media3.exoplayer.libass;

/** Close waits for the current native/render operation and rejects all queued operations. */
final class LibassRenderGate {
    private boolean closed;
    synchronized void run(Runnable action){if(!closed)action.run();}
    synchronized boolean close(){if(closed)return false;closed=true;return true;}
}
