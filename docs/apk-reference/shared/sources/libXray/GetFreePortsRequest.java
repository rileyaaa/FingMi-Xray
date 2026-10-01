package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class GetFreePortsRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public GetFreePortsRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        return obj != null && (obj instanceof GetFreePortsRequest) && getCount() == ((GetFreePortsRequest) obj).getCount();
    }

    public final native long getCount();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{Long.valueOf(getCount())});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setCount(long j);

    public String toString() {
        return "GetFreePortsRequest{Count:" + getCount() + ",}";
    }

    public GetFreePortsRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
