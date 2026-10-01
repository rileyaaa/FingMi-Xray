package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class GenerateAgeKeyPairResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public GenerateAgeKeyPairResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof GenerateAgeKeyPairResponse)) {
            return false;
        }
        GenerateAgeKeyPairResponse generateAgeKeyPairResponse = (GenerateAgeKeyPairResponse) obj;
        String secretKey = getSecretKey();
        String secretKey2 = generateAgeKeyPairResponse.getSecretKey();
        if (secretKey == null) {
            if (secretKey2 != null) {
                return false;
            }
        } else if (!secretKey.equals(secretKey2)) {
            return false;
        }
        String publicKey = getPublicKey();
        String publicKey2 = generateAgeKeyPairResponse.getPublicKey();
        if (publicKey == null) {
            return publicKey2 == null;
        }
        return publicKey.equals(publicKey2);
    }

    public final native String getPublicKey();

    public final native String getSecretKey();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getSecretKey(), getPublicKey()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setPublicKey(String str);

    public final native void setSecretKey(String str);

    public String toString() {
        return "GenerateAgeKeyPairResponse{SecretKey:" + getSecretKey() + ",PublicKey:" + getPublicKey() + ",}";
    }

    public GenerateAgeKeyPairResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
