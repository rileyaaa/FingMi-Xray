package libXray;

import p008go.Seq;

public abstract class LibXray {
    public static final long LibXrayAPIVersion = 2;

    public static final class proxyDialerController implements Seq.Proxy, DialerController {
        private final int refnum;

        public proxyDialerController(int i) {
            this.refnum = i;
            Seq.trackGoRef(i, this);
        }

        @Override
        public final int incRefnum() {
            Seq.incGoRef(this.refnum, this);
            return this.refnum;
        }

        @Override
        public native boolean protectFd(long j);
    }

    public static final class proxyProcessFinder implements Seq.Proxy, ProcessFinder {
        private final int refnum;

        public proxyProcessFinder(int i) {
            this.refnum = i;
            Seq.trackGoRef(i, this);
        }

        @Override
        public native long findProcessByConnection(String str, String str2, long j, String str3, long j2);

        @Override
        public final int incRefnum() {
            Seq.incGoRef(this.refnum, this);
            return this.refnum;
        }
    }

    static {
        Seq.touch();
        _init();
    }

    private LibXray() {
    }

    private static native void _init();

    public static native String invoke(String str);

    public static native void registerDialerController(DialerController dialerController);

    public static native void registerListenerController(DialerController dialerController);

    public static native void registerProcessFinder(ProcessFinder processFinder, long j);

    public static native void resetDNS();

    public static native void setDNS(DialerController dialerController, String str);

    public static void touch() {
    }
}
