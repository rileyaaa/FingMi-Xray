package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class PingBatchItemRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public PingBatchItemRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof PingBatchItemRequest)) {
            return false;
        }
        PingBatchItemRequest pingBatchItemRequest = (PingBatchItemRequest) obj;
        String xrayJson = getXrayJson();
        String xrayJson2 = pingBatchItemRequest.getXrayJson();
        if (xrayJson == null) {
            if (xrayJson2 != null) {
                return false;
            }
        } else if (!xrayJson.equals(xrayJson2)) {
            return false;
        }
        String outboundTag = getOutboundTag();
        String outboundTag2 = pingBatchItemRequest.getOutboundTag();
        if (outboundTag == null) {
            return outboundTag2 == null;
        }
        return outboundTag.equals(outboundTag2);
    }

    public final native String getOutboundTag();

    public final native String getXrayJson();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getXrayJson(), getOutboundTag()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setOutboundTag(String str);

    public final native void setXrayJson(String str);

    public String toString() {
        return "PingBatchItemRequest{XrayJson:" + getXrayJson() + ",OutboundTag:" + getOutboundTag() + ",}";
    }

    public PingBatchItemRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
