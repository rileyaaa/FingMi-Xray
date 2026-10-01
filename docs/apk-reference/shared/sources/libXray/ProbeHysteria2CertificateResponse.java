package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class ProbeHysteria2CertificateResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public ProbeHysteria2CertificateResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof ProbeHysteria2CertificateResponse)) {
            return false;
        }
        String sha256 = getSHA256();
        String sha257 = ((ProbeHysteria2CertificateResponse) obj).getSHA256();
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
        return "ProbeHysteria2CertificateResponse{SHA256:" + getSHA256() + ",}";
    }

    public ProbeHysteria2CertificateResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
