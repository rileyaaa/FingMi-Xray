package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class ProbeTLSCertificateResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public ProbeTLSCertificateResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof ProbeTLSCertificateResponse)) {
            return false;
        }
        String sha256 = getSHA256();
        String sha257 = ((ProbeTLSCertificateResponse) obj).getSHA256();
        if (sha256 == null) {
            return sha257 == null;
        }
        return sha256.equals(sha257);
    }

    public final native String getSHA256();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getSHA256()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setSHA256(String str);

    public String toString() {
        return "ProbeTLSCertificateResponse{SHA256:" + getSHA256() + ",}";
    }

    public ProbeTLSCertificateResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
