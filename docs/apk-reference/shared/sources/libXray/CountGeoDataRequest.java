package libXray;

import java.util.Arrays;
import p008go.Seq;

public final class CountGeoDataRequest implements Seq.Proxy {
    private final int refnum;

    static {
        LibXray.touch();
    }

    public CountGeoDataRequest() {
        int i__New = __New();
        this.refnum = i__New;
        Seq.trackGoRef(i__New, this);
    }

    private static native int __New();

    public boolean equals(Object obj) {
        if (obj == null || !(obj instanceof CountGeoDataRequest)) {
            return false;
        }
        CountGeoDataRequest countGeoDataRequest = (CountGeoDataRequest) obj;
        String name = getName();
        String name2 = countGeoDataRequest.getName();
        if (name == null) {
            if (name2 != null) {
                return false;
            }
        } else if (!name.equals(name2)) {
            return false;
        }
        String geoType = getGeoType();
        String geoType2 = countGeoDataRequest.getGeoType();
        if (geoType == null) {
            if (geoType2 != null) {
                return false;
            }
        } else if (!geoType.equals(geoType2)) {
            return false;
        }
        String datDir = getDatDir();
        String datDir2 = countGeoDataRequest.getDatDir();
        if (datDir == null) {
            return datDir2 == null;
        }
        return datDir.equals(datDir2);
    }

    public final native String getDatDir();

    public final native String getGeoType();

    public final native String getName();

    public int hashCode() {
        return Arrays.hashCode(new Object[]{getName(), getGeoType(), getDatDir()});
    }

    @Override
    public final int incRefnum() {
        Seq.incGoRef(this.refnum, this);
        return this.refnum;
    }

    public final native void setDatDir(String str);

    public final native void setGeoType(String str);

    public final native void setName(String str);

    public String toString() {
        return "CountGeoDataRequest{Name:" + getName() + ",GeoType:" + getGeoType() + ",DatDir:" + getDatDir() + ",}";
    }

    public CountGeoDataRequest(int i) {
        this.refnum = i;
        Seq.trackGoRef(i, this);
    }
}
