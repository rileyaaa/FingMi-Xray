package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class ProbeHysteria2CertificateRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public ProbeHysteria2CertificateRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof ProbeHysteria2CertificateRequest)) {
            return false;
        }
        ProbeHysteria2CertificateRequest probeHysteria2CertificateRequest = (ProbeHysteria2CertificateRequest) obj;
        String server = getServer();
        String server2 = probeHysteria2CertificateRequest.getServer();
        if (server == null) {
            if (server2 != null) {
                return false;
            }
        } else if (!server.equals(server2)) {
            return false;
        }
        if (getPort() != probeHysteria2CertificateRequest.getPort()) {
            return false;
        }
        String serverName = getServerName();
        String serverName2 = probeHysteria2CertificateRequest.getServerName();
        if (serverName == null) {
            if (serverName2 != null) {
                return false;
            }
        } else if (!serverName.equals(serverName2)) {
            return false;
        }
        return getTimeout() == probeHysteria2CertificateRequest.getTimeout();
    }

    public final native long getPort();

    public final native String getServer();

    public final native String getServerName();

    public final native long getTimeout();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getServer(), Long.valueOf(getPort()), getServerName(), Long.valueOf(getTimeout())});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setPort(long j);

    public final native void setServer(String str);

    public final native void setServerName(String str);

    public final native void setTimeout(long j);

    public String toString() {
        return "ProbeHysteria2CertificateRequest{Server:" + getServer() + ",Port:" + getPort() + ",ServerName:" + getServerName() + ",Timeout:" + getTimeout() + ",}";
    }

    public ProbeHysteria2CertificateRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
