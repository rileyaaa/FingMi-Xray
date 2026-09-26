package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class GetXrayStateResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public GetXrayStateResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        return obj != null && (obj instanceof GetXrayStateResponse) && getRunning() == ((GetXrayStateResponse) obj).getRunning();
    }

    public final native boolean getRunning();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{Boolean.valueOf(getRunning())});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setRunning(boolean z);

    public String toString() {
        return "GetXrayStateResponse{Running:" + getRunning() + ",}";
    }

    public GetXrayStateResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
