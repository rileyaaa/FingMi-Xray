package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class LibXrayInvokeRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public LibXrayInvokeRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        return obj != null && (obj instanceof LibXrayInvokeRequest) && getAPIVersion() == ((LibXrayInvokeRequest) obj).getAPIVersion();
    }

    public final native long getAPIVersion();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{Long.valueOf(getAPIVersion())});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setAPIVersion(long j);

    public String toString() {
        return "LibXrayInvokeRequest{APIVersion:" + getAPIVersion() + ",}";
    }

    public LibXrayInvokeRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
