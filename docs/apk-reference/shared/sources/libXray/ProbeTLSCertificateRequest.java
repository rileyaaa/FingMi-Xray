package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class ProbeTLSCertificateRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public ProbeTLSCertificateRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof ProbeTLSCertificateRequest)) {
            return false;
        }
        ProbeTLSCertificateRequest probeTLSCertificateRequest = (ProbeTLSCertificateRequest) obj;
        String server = getServer();
        String server2 = probeTLSCertificateRequest.getServer();
        if (server == null) {
            if (server2 != null) {
                return false;
            }
        } else if (!server.equals(server2)) {
            return false;
        }
        if (getPort() != probeTLSCertificateRequest.getPort()) {
            return false;
        }
        String serverName = getServerName();
        String serverName2 = probeTLSCertificateRequest.getServerName();
        if (serverName == null) {
            if (serverName2 != null) {
                return false;
            }
        } else if (!serverName.equals(serverName2)) {
            return false;
        }
        String fingerprint = getFingerprint();
        String fingerprint2 = probeTLSCertificateRequest.getFingerprint();
        if (fingerprint == null) {
            if (fingerprint2 != null) {
                return false;
            }
        } else if (!fingerprint.equals(fingerprint2)) {
            return false;
        }
        return getTimeout() == probeTLSCertificateRequest.getTimeout();
    }

    public final native String getFingerprint();

    public final native long getPort();

    public final native String getServer();

    public final native String getServerName();

    public final native long getTimeout();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getServer(), Long.valueOf(getPort()), getServerName(), getFingerprint(), Long.valueOf(getTimeout())});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setFingerprint(String str);

    public final native void setPort(long j);

    public final native void setServer(String str);

    public final native void setServerName(String str);

    public final native void setTimeout(long j);

    public String toString() {
        return "ProbeTLSCertificateRequest{Server:" + getServer() + ",Port:" + getPort() + ",ServerName:" + getServerName() + ",Fingerprint:" + getFingerprint() + ",Timeout:" + getTimeout() + ",}";
    }

    public ProbeTLSCertificateRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
