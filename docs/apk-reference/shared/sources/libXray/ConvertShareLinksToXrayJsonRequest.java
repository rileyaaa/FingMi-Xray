package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class ConvertShareLinksToXrayJsonRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public ConvertShareLinksToXrayJsonRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof ConvertShareLinksToXrayJsonRequest)) {
            return false;
        }
        ConvertShareLinksToXrayJsonRequest convertShareLinksToXrayJsonRequest = (ConvertShareLinksToXrayJsonRequest) obj;
        String text = getText();
        String text2 = convertShareLinksToXrayJsonRequest.getText();
        if (text == null) {
            if (text2 != null) {
                return false;
            }
        } else if (!text.equals(text2)) {
            return false;
        }
        AgeDecryptConfig age = getAge();
        AgeDecryptConfig age2 = convertShareLinksToXrayJsonRequest.getAge();
        if (age == null) {
            return age2 == null;
        }
        return age.equals(age2);
    }

    public final native AgeDecryptConfig getAge();

    public final native String getText();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getText(), getAge()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setAge(AgeDecryptConfig ageDecryptConfig);

    public final native void setText(String str);

    public String toString() {
        return "ConvertShareLinksToXrayJsonRequest{Text:" + getText() + ",Age:" + getAge() + ",}";
    }

    public ConvertShareLinksToXrayJsonRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
