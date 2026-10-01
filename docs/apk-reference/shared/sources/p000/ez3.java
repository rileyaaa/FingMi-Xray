package p000;

import android.content.ComponentName;
import android.content.ServiceConnection;
import android.os.IBinder;
import android.os.IInterface;
import android.os.RemoteException;
import com.fongmi.android.p002tv.App;

public final class ez3 implements ServiceConnection, IBinder.DeathRecipient {

    public final long f5409c;

    public final rc2 f5410h = new rc2(this, 29);

    public IBinder f5411i;

    public final hz3 f5412j;

    public ez3(hz3 hz3Var, long j) {
        this.f5412j = hz3Var;
        this.f5409c = j;
    }

    @Override
    public final void binderDied() throws Throwable {
        this.f5412j.m4231d(this, "Xray service process died");
    }

    @Override
    public final void onBindingDied(ComponentName componentName) throws Throwable {
        this.f5412j.m4231d(this, "Xray service binding died");
    }

    @Override
    public final void onNullBinding(ComponentName componentName) throws Throwable {
        this.f5412j.m4231d(this, "Xray service returned no binder");
    }

    @Override
    public final void onServiceConnected(ComponentName componentName, IBinder iBinder) {
        j91 j91Var;
        hz3 hz3Var = this.f5412j;
        synchronized (hz3Var) {
            if (this != hz3Var.f7572e) {
                try {
                    hz3Var.f7568a.unbindService(this);
                } catch (IllegalArgumentException unused) {
                }
                return;
            }
            App.m1883c(this.f5410h);
            hz3Var.f7576i = false;
            this.f5411i = iBinder;
            int i = uz3.f18804e;
            if (iBinder == null) {
                j91Var = null;
            } else {
                IInterface iInterfaceQueryLocalInterface = iBinder.queryLocalInterface("com.fongmi.android.tv.xray.IXrayService");
                if (iInterfaceQueryLocalInterface == null || !(iInterfaceQueryLocalInterface instanceof j91)) {
                    i91 i91Var = new i91();
                    i91Var.f7864d = iBinder;
                    j91Var = i91Var;
                } else {
                    j91Var = (j91) iInterfaceQueryLocalInterface;
                }
            }
            hz3Var.f7570c = j91Var;
            try {
                iBinder.linkToDeath(this, 0);
                hz3Var.m4229b();
            } catch (RemoteException unused2) {
                hz3Var.m4231d(this, "Xray service connection died");
            }
        }
    }

    @Override
    public final void onServiceDisconnected(ComponentName componentName) throws Throwable {
        this.f5412j.m4231d(this, "Xray service disconnected");
    }

    public final String toString() {
        return "XrayBindConnection{" + this.f5409c + '}';
    }
}
