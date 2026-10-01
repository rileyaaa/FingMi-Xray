package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class PingBatchResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public PingBatchResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof PingBatchResponse)) {
            return false;
        }
        return true;
    }

    public int hashCode() {
        return Arrays.hashCode(new Object[0]);
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public String toString() {
        return "PingBatchResponse{}";
    }

    public PingBatchResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
