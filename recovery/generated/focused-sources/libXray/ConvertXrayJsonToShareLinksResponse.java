package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class ConvertXrayJsonToShareLinksResponse implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public ConvertXrayJsonToShareLinksResponse() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof ConvertXrayJsonToShareLinksResponse)) {
            return false;
        }
        String links = getLinks();
        String links2 = ((ConvertXrayJsonToShareLinksResponse) obj).getLinks();
        if (links == null) {
            return links2 == null;
        }
        return links.equals(links2);
    }

    public final native String getLinks();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getLinks()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setLinks(String str);

    public String toString() {
        return "ConvertXrayJsonToShareLinksResponse{Links:" + getLinks() + ",}";
    }

    public ConvertXrayJsonToShareLinksResponse(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
