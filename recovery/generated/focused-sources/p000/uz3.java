package p000;

import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import com.fongmi.android.p002tv.xray.XrayService;

public final class uz3 extends Binder implements j91 {

    public static final int f18804e = 0;

    public final XrayService f18805d;

    public uz3(XrayService xrayService) {
        this.f18805d = xrayService;
        attachInterface(this, "com.fongmi.android.tv.xray.IXrayService");
    }

    @Override
    public final void mo4280X(int i, long j) {
        int i2 = XrayService.f3215n;
        this.f18805d.m2091e(i, j);
    }

    @Override
    public final void mo4281j0(long j, String str, boolean z, h91 h91Var) {
        XrayService xrayService = this.f18805d;
        xrayService.f3218i.m3018a(j);
        xrayService.f3216c.execute(new sz3(this, j, str, z, h91Var, 1));
    }

    @Override
    public final boolean onTransact(int i, Parcel parcel, Parcel parcel2, int i2) {
        if (i >= 1 && i <= 16777215) {
            parcel.enforceInterface("com.fongmi.android.tv.xray.IXrayService");
        }
        if (i == 1598968902) {
            parcel2.writeString("com.fongmi.android.tv.xray.IXrayService");
            return true;
        }
        switch (i) {
            case 1:
                boolean z = false;
                long j = parcel.readLong();
                String string = parcel.readString();
                if (parcel.readInt() != 0) {
                    z = true;
                }
                mo4281j0(j, string, z, dz3.m2940O0(parcel.readStrongBinder()));
                parcel2.writeNoException();
                return true;
            case 2:
                boolean z2 = false;
                long j2 = parcel.readLong();
                String string2 = parcel.readString();
                if (parcel.readInt() != 0) {
                    z2 = true;
                }
                mo4282s(j2, string2, z2, dz3.m2940O0(parcel.readStrongBinder()));
                parcel2.writeNoException();
                return true;
            case 3:
                boolean z3 = false;
                long j3 = parcel.readLong();
                String string3 = parcel.readString();
                if (parcel.readInt() != 0) {
                    z3 = true;
                }
                mo4284w0(j3, string3, z3, dz3.m2940O0(parcel.readStrongBinder()));
                parcel2.writeNoException();
                return true;
            case 4:
                mo4285y0(parcel.readLong(), dz3.m2940O0(parcel.readStrongBinder()));
                parcel2.writeNoException();
                return true;
            case 5:
                mo4283v(parcel.readLong(), dz3.m2940O0(parcel.readStrongBinder()));
                parcel2.writeNoException();
                return true;
            case 6:
                mo4280X(parcel.readInt(), parcel.readLong());
                parcel2.writeNoException();
                return true;
            default:
                return super.onTransact(i, parcel, parcel2, i2);
        }
    }

    @Override
    public final void mo4282s(long j, String str, boolean z, h91 h91Var) {
        XrayService xrayService = this.f18805d;
        xrayService.f3218i.m3018a(j);
        xrayService.f3216c.execute(new sz3(this, j, str, z, h91Var, 2));
    }

    @Override
    public final void mo4283v(long j, h91 h91Var) {
        XrayService xrayService = this.f18805d;
        xrayService.f3218i.m3018a(j);
        xrayService.f3216c.execute(new tz3(this, j, h91Var, 1));
    }

    @Override
    public final void mo4284w0(long j, String str, boolean z, h91 h91Var) {
        XrayService xrayService = this.f18805d;
        xrayService.f3217h.m3018a(j);
        xrayService.f3218i.m3018a(j);
        xrayService.f3216c.execute(new sz3(this, j, str, z, h91Var, 0));
    }

    @Override
    public final void mo4285y0(long j, h91 h91Var) {
        XrayService xrayService = this.f18805d;
        xrayService.f3217h.m3018a(j);
        xrayService.f3218i.m3018a(j);
        xrayService.f3216c.execute(new tz3(this, j, h91Var, 0));
    }

    @Override
    public final IBinder asBinder() {
        return this;
    }
}
