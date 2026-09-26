package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class PingBatchRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public PingBatchRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof PingBatchRequest)) {
            return false;
        }
        PingBatchRequest pingBatchRequest = (PingBatchRequest) obj;
        if (getTimeout() != pingBatchRequest.getTimeout()) {
            return false;
        }
        String url = getURL();
        String url2 = pingBatchRequest.getURL();
        if (url == null) {
            return url2 == null;
        }
        return url.equals(url2);
    }

    public final native long getTimeout();

    public final native String getURL();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{Long.valueOf(getTimeout()), getURL()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setTimeout(long j);

    public final native void setURL(String str);

    public String toString() {
        return "PingBatchRequest{Timeout:" + getTimeout() + ",URL:" + getURL() + ",}";
    }

    public PingBatchRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
