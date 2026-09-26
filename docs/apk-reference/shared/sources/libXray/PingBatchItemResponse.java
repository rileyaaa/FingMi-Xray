package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class PingBatchItemResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public PingBatchItemResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof PingBatchItemResponse)) {
            return false;
        }
        PingBatchItemResponse pingBatchItemResponse = (PingBatchItemResponse) obj;
        if (getSuccess() != pingBatchItemResponse.getSuccess() || getDelay() != pingBatchItemResponse.getDelay()) {
            return false;
        }
        String error = getError();
        String error2 = pingBatchItemResponse.getError();
        if (error == null) {
            return error2 == null;
        }
        return error.equals(error2);
    }

    public final native long getDelay();

    public final native String getError();

    public final native boolean getSuccess();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{Boolean.valueOf(getSuccess()), Long.valueOf(getDelay()), getError()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setDelay(long j);

    public final native void setError(String str);

    public final native void setSuccess(boolean z);

    public String toString() {
        return "PingBatchItemResponse{Success:" + getSuccess() + ",Delay:" + getDelay() + ",Error:" + getError() + ",}";
    }

    public PingBatchItemResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
