package p000;

import android.os.IBinder;
import android.os.Parcel;

public final class i91 implements j91 {

    public IBinder f7864d;

    @Override
    public final void mo4280X(int i, long j) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayService");
            parcelObtain.writeLong(j);
            parcelObtain.writeInt(i);
            this.f7864d.transact(6, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }

    @Override
    public final IBinder asBinder() {
        return this.f7864d;
    }

    @Override
    public final void mo4281j0(long j, String str, boolean z, h91 h91Var) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayService");
            parcelObtain.writeLong(j);
            parcelObtain.writeString(str);
            parcelObtain.writeInt(z ? 1 : 0);
            parcelObtain.writeStrongInterface(h91Var);
            this.f7864d.transact(1, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }

    @Override
    public final void mo4282s(long j, String str, boolean z, h91 h91Var) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayService");
            parcelObtain.writeLong(j);
            parcelObtain.writeString(str);
            parcelObtain.writeInt(z ? 1 : 0);
            parcelObtain.writeStrongInterface(h91Var);
            this.f7864d.transact(2, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }

    @Override
    public final void mo4283v(long j, h91 h91Var) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayService");
            parcelObtain.writeLong(j);
            parcelObtain.writeStrongInterface(h91Var);
            this.f7864d.transact(5, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }

    @Override
    public final void mo4284w0(long j, String str, boolean z, h91 h91Var) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayService");
            parcelObtain.writeLong(j);
            parcelObtain.writeString(str);
            parcelObtain.writeInt(z ? 1 : 0);
            parcelObtain.writeStrongInterface(h91Var);
            this.f7864d.transact(3, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }

    @Override
    public final void mo4285y0(long j, h91 h91Var) {
        Parcel parcelObtain = Parcel.obtain();
        Parcel parcelObtain2 = Parcel.obtain();
        try {
            parcelObtain.writeInterfaceToken("com.fongmi.android.tv.xray.IXrayService");
            parcelObtain.writeLong(j);
            parcelObtain.writeStrongInterface(h91Var);
            this.f7864d.transact(4, parcelObtain, parcelObtain2, 0);
            parcelObtain2.readException();
        } finally {
            parcelObtain2.recycle();
            parcelObtain.recycle();
        }
    }
}
