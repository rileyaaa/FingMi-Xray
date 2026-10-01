package p000;

import android.os.IBinder;
import android.os.Parcel;

public final class g91 implements h91 {

    public IBinder f6374d;

    @Override
    public final IBinder asBinder() {
        return this.f6374d;
    }

    @Override
    public final void mo2941m(long j, int i, boolean z, int i2, long j2, String str) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayCallback");
            parcelObtain.writeLong(j);
            parcelObtain.writeInt(i);
            parcelObtain.writeInt(z ? 1 : 0);
            parcelObtain.writeInt(i2);
            parcelObtain.writeLong(j2);
            parcelObtain.writeString(str);
            this.f6374d.transact(1, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }
}
