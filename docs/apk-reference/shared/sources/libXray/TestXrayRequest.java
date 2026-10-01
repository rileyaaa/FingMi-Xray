package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class TestXrayRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public TestXrayRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof TestXrayRequest)) {
            return false;
        }
        String xrayJson = getXrayJson();
        String xrayJson2 = ((TestXrayRequest) obj).getXrayJson();
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
        return "TestXrayRequest{XrayJson:" + getXrayJson() + ",}";
    }

    public TestXrayRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
