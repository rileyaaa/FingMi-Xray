package p000;

import android.os.Binder;
import android.os.IBinder;
import android.os.IInterface;
import android.os.Parcel;
import com.fongmi.android.p002tv.App;

public final class dz3 extends Binder implements h91 {

    public final long f4548d;

    public final hz3 f4549e;

    public dz3(hz3 hz3Var, long j) {
        this.f4549e = hz3Var;
        this.f4548d = j;
        attachInterface(this, "com.fongmi.android.tv.xray.IXrayCallback");
    }

    public static h91 m2940O0(IBinder iBinder) {
        if (iBinder == null) {
            return null;
        }
        IInterface iInterfaceQueryLocalInterface = iBinder.queryLocalInterface("com.fongmi.android.tv.xray.IXrayCallback");
        if (iInterfaceQueryLocalInterface != null && (iInterfaceQueryLocalInterface instanceof h91)) {
            return (h91) iInterfaceQueryLocalInterface;
        }
        g91 g91Var = new g91();
        g91Var.f6374d = iBinder;
        return g91Var;
    }

    @Override
    public final void mo2941m(long j, int i, boolean z, int i2, long j2, String str) {
        App.m1881a(new w40(this, this.f4548d, new rz3(j, i, z, i2, j2, str), 3));
    }

    @Override
    public final boolean onTransact(int i, Parcel parcel, Parcel parcel2, int i2) {
        if (i >= 1 && i <= 16777215) {
            parcel.enforceInterface("com.fongmi.android.tv.xray.IXrayCallback");
        }
        if (i == 1598968902) {
            parcel2.writeString("com.fongmi.android.tv.xray.IXrayCallback");
            return true;
        }
        if (i != 1) {
            return super.onTransact(i, parcel, parcel2, i2);
        }
        mo2941m(parcel.readLong(), parcel.readInt(), parcel.readInt() != 0, parcel.readInt(), parcel.readLong(), parcel.readString());
        parcel2.writeNoException();
        return true;
    }

    @Override
    public final IBinder asBinder() {
        return this;
    }
}
