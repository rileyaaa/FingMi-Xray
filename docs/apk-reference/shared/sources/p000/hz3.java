package p000;

import android.content.Context;
import android.content.Intent;
import android.os.IBinder;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.xray.XrayService;

public final class hz3 {

    public final Context f7568a;

    public final fz3 f7569b;

    public j91 f7570c;

    public gz3 f7571d;

    public ez3 f7572e;

    public long f7573f = Long.MIN_VALUE;

    public long f7574g;

    public long f7575h;

    public boolean f7576i;

    public hz3(Context context, fz3 fz3Var) {
        this.f7568a = context.getApplicationContext();
        this.f7569b = fz3Var;
    }

    public final synchronized void m4228a() {
        IBinder iBinder;
        this.f7574g++;
        ez3 ez3Var = this.f7572e;
        if (ez3Var != null) {
            App.m1883c(ez3Var.f5410h);
        }
        this.f7571d = null;
        this.f7573f = Long.MIN_VALUE;
        ez3 ez3Var2 = this.f7572e;
        this.f7572e = null;
        if (ez3Var2 != null && (iBinder = ez3Var2.f5411i) != null) {
            try {
                iBinder.unlinkToDeath(ez3Var2, 0);
            } catch (Exception unused) {
            }
            ez3Var2.f5411i = null;
        }
        this.f7570c = null;
        this.f7576i = false;
        if (ez3Var2 != null) {
            try {
                this.f7568a.unbindService(ez3Var2);
            } catch (IllegalArgumentException unused2) {
            }
        }
    }

    public final void m4229b() throws Throwable {
        gz3 gz3Var = this.f7571d;
        this.f7571d = null;
        if (gz3Var != null) {
            long j = gz3Var.f6822c;
            if (this.f7570c == null) {
                return;
            }
            this.f7573f = j;
            dz3 dz3Var = new dz3(this, this.f7574g);
            try {
                int i = gz3Var.f6823h;
                if (i == 1) {
                    this.f7570c.mo4281j0(gz3Var.f6822c, gz3Var.f6824i, gz3Var.f6825j, dz3Var);
                } else if (i == 2) {
                    this.f7570c.mo4282s(gz3Var.f6822c, gz3Var.f6824i, gz3Var.f6825j, dz3Var);
                } else if (i == 3) {
                    this.f7570c.mo4284w0(gz3Var.f6822c, gz3Var.f6824i, gz3Var.f6825j, dz3Var);
                } else if (i == 4) {
                    this.f7570c.mo4285y0(j, dz3Var);
                } else {
                    if (i != 5) {
                        throw new IllegalArgumentException("Unknown Xray operation");
                    }
                    this.f7570c.mo4283v(j, dz3Var);
                }
                gz3Var.f6826k.run();
            } catch (Exception e) {
                m4231d(this.f7572e, kz3.m5738a(e));
            }
        }
    }

    public final synchronized void m4230c(int i, long j) {
        j91 j91Var = this.f7570c;
        if (j91Var != null) {
            try {
                j91Var.mo4280X(i, j);
            } catch (Exception unused) {
            }
        }
        m4228a();
    }

    /* JADX WARN: Code duplicated, block: B:23:0x0028 A[Catch: all -> 0x001e, TRY_ENTER, TRY_LEAVE, TryCatch #8 {all -> 0x001e, blocks: (B:5:0x0005, B:7:0x0009, B:10:0x000e, B:12:0x0013, B:11:0x0011, B:23:0x0028, B:26:0x0031, B:31:0x0046, B:34:0x004b, B:35:0x004e, B:39:0x005d), top: B:84:0x0005 }] */
    /* JADX WARN: Code duplicated, block: B:26:0x0031 A[Catch: all -> 0x001e, TRY_ENTER, TRY_LEAVE, TryCatch #8 {all -> 0x001e, blocks: (B:5:0x0005, B:7:0x0009, B:10:0x000e, B:12:0x0013, B:11:0x0011, B:23:0x0028, B:26:0x0031, B:31:0x0046, B:34:0x004b, B:35:0x004e, B:39:0x005d), top: B:84:0x0005 }] */
    /* JADX WARN: Code duplicated, block: B:28:0x0035 A[Catch: all -> 0x0082, TRY_ENTER, TryCatch #2 {all -> 0x0082, blocks: (B:21:0x0024, B:24:0x002d, B:29:0x0038, B:36:0x0050, B:28:0x0035), top: B:72:0x0024 }] */
    /* JADX WARN: Code duplicated, block: B:42:0x0066  */
    /* JADX WARN: Code duplicated, block: B:68:0x005d A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:72:0x0024 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:82:0x0068 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    public final synchronized void m4231d(ez3 ez3Var, String str) throws Throwable {
        Throwable th;
        hz3 hz3Var;
        gz3 gz3Var;
        long j;
        long j2;
        long j3;
        ez3 ez3Var2;
        IBinder iBinder;
        if (ez3Var == null) {
            if (ez3Var == null) {
                ez3Var = this.f7572e;
            }
            if (ez3Var != null) {
                App.m1883c(ez3Var.f5410h);
            }
            gz3Var = this.f7571d;
            if (gz3Var != null) {
                j = gz3Var.f6822c;
            } else {
                j = this.f7573f;
            }
            j2 = j;
            j3 = this.f7574g + 1;
            this.f7574g = j3;
            ez3Var2 = this.f7572e;
            this.f7572e = null;
            if (ez3Var2 != null) {
                iBinder.unlinkToDeath(ez3Var2, 0);
                ez3Var2.f5411i = null;
            }
            this.f7570c = null;
            this.f7571d = null;
            this.f7573f = Long.MIN_VALUE;
            this.f7576i = false;
            if (ez3Var2 != null) {
                this.f7568a.unbindService(ez3Var2);
            }
            if (j2 == Long.MIN_VALUE) {
                hz3Var = this;
            } else {
                hz3Var = this;
                App.m1881a(new RunnableC0587ge(hz3Var, j3, j2, kz3.m5739b(str)));
            }
            return;
        }
        try {
            if (ez3Var != this.f7572e) {
                IBinder iBinder2 = ez3Var.f5411i;
                if (iBinder2 != null) {
                    try {
                        iBinder2.unlinkToDeath(ez3Var, 0);
                    } catch (Exception unused) {
                    }
                    ez3Var.f5411i = null;
                }
                try {
                    this.f7568a.unbindService(ez3Var);
                } catch (IllegalArgumentException unused2) {
                }
            }
            if (ez3Var == null) {
                try {
                    ez3Var = this.f7572e;
                } catch (Throwable th2) {
                    hz3Var = this;
                    th = th2;
                }
            }
            if (ez3Var != null) {
                App.m1883c(ez3Var.f5410h);
            }
            gz3Var = this.f7571d;
            if (gz3Var != null) {
                j = gz3Var.f6822c;
            } else {
                j = this.f7573f;
            }
            j2 = j;
            j3 = this.f7574g + 1;
            this.f7574g = j3;
            ez3Var2 = this.f7572e;
            this.f7572e = null;
            if (ez3Var2 != null && (iBinder = ez3Var2.f5411i) != null) {
                try {
                    iBinder.unlinkToDeath(ez3Var2, 0);
                } catch (Exception unused3) {
                }
                ez3Var2.f5411i = null;
            }
            this.f7570c = null;
            this.f7571d = null;
            this.f7573f = Long.MIN_VALUE;
            this.f7576i = false;
            if (ez3Var2 != null) {
                try {
                    this.f7568a.unbindService(ez3Var2);
                } catch (IllegalArgumentException unused4) {
                }
            }
            if (j2 == Long.MIN_VALUE) {
                hz3Var = this;
            } else {
                try {
                    try {
                        hz3Var = this;
                        try {
                            App.m1881a(new RunnableC0587ge(hz3Var, j3, j2, kz3.m5739b(str)));
                        } catch (Throwable th3) {
                            th = th3;
                            th = th;
                            while (true) {
                                try {
                                    throw th;
                                } catch (Throwable th4) {
                                    th = th4;
                                }
                                th = th4;
                            }
                        }
                    } catch (Throwable th5) {
                        th = th5;
                        hz3Var = this;
                    }
                } catch (Throwable th6) {
                    th = th6;
                    hz3Var = this;
                }
            }
            return;
        } catch (Throwable th7) {
            th = th7;
            hz3Var = this;
        }
        while (true) {
            throw th;
            th = th4;
        }
    }

    public final void m4232e(gz3 gz3Var) throws Throwable {
        this.f7571d = gz3Var;
        if (this.f7570c != null) {
            m4229b();
            return;
        }
        if (this.f7576i) {
            return;
        }
        this.f7576i = true;
        long j = this.f7575h + 1;
        this.f7575h = j;
        ez3 ez3Var = new ez3(this, j);
        this.f7572e = ez3Var;
        rc2 rc2Var = ez3Var.f5410h;
        App.m1883c(rc2Var);
        App.m1882b(rc2Var, 5000L);
        Context context = this.f7568a;
        if (context.bindService(new Intent(context, (Class<?>) XrayService.class), ez3Var, 1)) {
            return;
        }
        m4231d(ez3Var, "Xray service bind failed");
    }
}
