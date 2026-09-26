package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class AgeDecryptConfig implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public AgeDecryptConfig() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof AgeDecryptConfig)) {
            return false;
        }
        String secretKey = getSecretKey();
        String secretKey2 = ((AgeDecryptConfig) obj).getSecretKey();
        if (secretKey == null) {
            return secretKey2 == null;
        }
        return secretKey.equals(secretKey2);
    }

    public final native String getSecretKey();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getSecretKey()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setSecretKey(String str);

    public String toString() {
        return "AgeDecryptConfig{SecretKey:" + getSecretKey() + ",}";
    }

    public AgeDecryptConfig(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
