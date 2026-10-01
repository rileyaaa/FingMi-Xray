package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class RunXrayRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public RunXrayRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof RunXrayRequest)) {
            return false;
        }
        String xrayJson = getXrayJson();
        String xrayJson2 = ((RunXrayRequest) obj).getXrayJson();
        if (xrayJson == null) {
            return xrayJson2 == null;
        }
        return xrayJson.equals(xrayJson2);
    }

    public final native String getXrayJson();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getXrayJson()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setXrayJson(String str);

    public String toString() {
        return "RunXrayRequest{XrayJson:" + getXrayJson() + ",}";
    }

    public RunXrayRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
