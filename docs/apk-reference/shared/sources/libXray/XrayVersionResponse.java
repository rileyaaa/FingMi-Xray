package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class XrayVersionResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public XrayVersionResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof XrayVersionResponse)) {
            return false;
        }
        String version = getVersion();
        String version2 = ((XrayVersionResponse) obj).getVersion();
        if (version == null) {
            return version2 == null;
        }
        return version.equals(version2);
    }

    public final native String getVersion();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getVersion()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setVersion(String str);

    public String toString() {
        return "XrayVersionResponse{Version:" + getVersion() + ",}";
    }

    public XrayVersionResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
