package p000;

import android.content.SharedPreferences;
import com.fongmi.android.p002tv.App;
import java.util.Objects;

public final class yz3 implements fz3 {

    public final lu2 f21708c;

    public final hz3 f21709h;

    public final xz3 f21710i;

    public boolean f21715n;

    public final wz3 f21716o;

    public final wz3 f21717p;

    public long f21712k = Long.MIN_VALUE;

    public long f21713l = Long.MIN_VALUE;

    public int f21714m = 1;

    public long f21711j = lz3.f11083a.incrementAndGet();

    /* JADX WARN: Type inference failed for: r1v0, types: [wz3] */
    /* JADX WARN: Type inference failed for: r1v1, types: [wz3] */
    public yz3(af2 af2Var, xz3 xz3Var) {
        final int i = 1;
        final int i2 = 0;
        this.f21716o = new Runnable(this) {

            public final yz3 f20483h;

            {
                this.f20483h = this;
            }

            @Override
            public final void run() {
                int i3 = i2;
                yz3 yz3Var = this.f20483h;
                switch (i3) {
                    case 0:
                        long j = yz3Var.f21712k;
                        if (j != Long.MIN_VALUE) {
                            yz3Var.f21712k = Long.MIN_VALUE;
                            int i4 = yz3Var.f21714m;
                            if (i4 != 3) {
                                if (!yz3Var.f21715n && i4 == 2) {
                                    yz3Var.m10883c("Previous Xray session cleanup timed out");
                                }
                                yz3Var.f21709h.m4230c(4, j);
                                break;
                            }
                        }
                        break;
                    default:
                        long j2 = yz3Var.f21713l;
                        if (j2 != Long.MIN_VALUE) {
                            yz3Var.f21713l = Long.MIN_VALUE;
                            App.m1883c(yz3Var.f21717p);
                            if (!yz3Var.f21715n && yz3Var.f21711j == j2 && yz3Var.f21714m == 2) {
                                yz3Var.m10883c("Xray startup timed out");
                                yz3Var.f21709h.m4230c(3, j2);
                                break;
                            }
                        }
                        break;
                }
            }
        };
        this.f21717p = new Runnable(this) {

            public final yz3 f20483h;

            {
                this.f20483h = this;
            }

            @Override
            public final void run() {
                int i3 = i;
                yz3 yz3Var = this.f20483h;
                switch (i3) {
                    case 0:
                        long j = yz3Var.f21712k;
                        if (j != Long.MIN_VALUE) {
                            yz3Var.f21712k = Long.MIN_VALUE;
                            int i4 = yz3Var.f21714m;
                            if (i4 != 3) {
                                if (!yz3Var.f21715n && i4 == 2) {
                                    yz3Var.m10883c("Previous Xray session cleanup timed out");
                                }
                                yz3Var.f21709h.m4230c(4, j);
                                break;
                            }
                        }
                        break;
                    default:
                        long j2 = yz3Var.f21713l;
                        if (j2 != Long.MIN_VALUE) {
                            yz3Var.f21713l = Long.MIN_VALUE;
                            App.m1883c(yz3Var.f21717p);
                            if (!yz3Var.f21715n && yz3Var.f21711j == j2 && yz3Var.f21714m == 2) {
                                yz3Var.m10883c("Xray startup timed out");
                                yz3Var.f21709h.m4230c(3, j2);
                                break;
                            }
                        }
                        break;
                }
            }
        };
        this.f21708c = new lu2((AbstractActivityC1828yh) af2Var);
        this.f21709h = new hz3(af2Var, this);
        this.f21710i = xz3Var;
    }

    @Override
    public final void mo2028B(rz3 rz3Var) {
        int i = rz3Var.f16225h;
        String str = rz3Var.f16229l;
        boolean z = rz3Var.f16226i;
        long j = rz3Var.f16224c;
        xz3 xz3Var = this.f21710i;
        wz3 wz3Var = this.f21716o;
        hz3 hz3Var = this.f21709h;
        if (i == 4 && j == this.f21712k) {
            this.f21712k = Long.MIN_VALUE;
            App.m1883c(wz3Var);
            boolean z2 = this.f21715n;
            if (!z) {
                if (!z2) {
                    String strM5739b = kz3.m5739b(str);
                    if (this.f21714m == 1) {
                        xz3Var.mo2009l(1, 0, strM5739b);
                    } else {
                        m10883c(strM5739b);
                    }
                }
                hz3Var.m4230c(4, j);
                return;
            }
            if (z2) {
                hz3Var.m4228a();
                return;
            } else if (j != this.f21711j) {
                return;
            }
        }
        if (this.f21715n || j != this.f21711j) {
            return;
        }
        if (i == 3) {
            this.f21712k = Long.MIN_VALUE;
            App.m1883c(wz3Var);
            this.f21713l = Long.MIN_VALUE;
            App.m1883c(this.f21717p);
            if (!z) {
                m10883c(str);
                hz3Var.m4228a();
                return;
            } else {
                int i2 = rz3Var.f16227j;
                this.f21714m = 3;
                xz3Var.mo2009l(3, i2, "");
                return;
            }
        }
        if (i == 4) {
            this.f21712k = Long.MIN_VALUE;
            App.m1883c(wz3Var);
            if (z) {
                hz3Var.m4228a();
                return;
            }
            String strM5739b2 = kz3.m5739b(str);
            if (this.f21714m == 1) {
                xz3Var.mo2009l(1, 0, strM5739b2);
            } else {
                m10883c(strM5739b2);
            }
            hz3Var.m4230c(4, j);
        }
    }

    @Override
    public final void mo2032Y(long j, String str) {
        int i;
        if (j == this.f21713l) {
            this.f21713l = Long.MIN_VALUE;
            App.m1883c(this.f21717p);
        }
        long j2 = this.f21712k;
        wz3 wz3Var = this.f21716o;
        if (j == j2) {
            this.f21712k = Long.MIN_VALUE;
            App.m1883c(wz3Var);
        }
        if (j != this.f21711j) {
            return;
        }
        this.f21712k = Long.MIN_VALUE;
        App.m1883c(wz3Var);
        if (!this.f21715n && ((i = this.f21714m) == 2 || i == 3)) {
            m10883c(str);
        }
        this.f21709h.m4228a();
    }

    public final void m10881a() {
        if (this.f21715n) {
            return;
        }
        if (this.f21714m != 1) {
            m10882b();
        }
        this.f21715n = true;
        if (this.f21712k == Long.MIN_VALUE) {
            hz3 hz3Var = this.f21709h;
            Objects.requireNonNull(hz3Var);
            App.m1882b(new nz3(hz3Var, 2), 500L);
        }
    }

    public final void m10882b() {
        if (this.f21715n || this.f21714m == 1) {
            return;
        }
        this.f21713l = Long.MIN_VALUE;
        App.m1883c(this.f21717p);
        long jIncrementAndGet = lz3.f11083a.incrementAndGet();
        this.f21711j = jIncrementAndGet;
        this.f21714m = 1;
        this.f21710i.mo2009l(1, 0, "");
        this.f21712k = jIncrementAndGet;
        hz3 hz3Var = this.f21709h;
        vz3 vz3Var = new vz3(this, jIncrementAndGet, 0);
        synchronized (hz3Var) {
            hz3Var.m4232e(new gz3(jIncrementAndGet, 4, "", false, vz3Var));
        }
    }

    public final void m10883c(String str) {
        if (str == null) {
            str = "";
        }
        this.f21714m = 1;
        xz3 xz3Var = this.f21710i;
        xz3Var.mo2009l(4, 0, str);
        xz3Var.mo2009l(1, 0, "");
    }

    public final void m10884d() {
        int i;
        boolean z;
        if (this.f21715n || (i = this.f21714m) == 2 || i == 3) {
            return;
        }
        try {
            String strM5933e = this.f21708c.m5933e();
            if (strM5933e.isEmpty()) {
                m10883c("Xray is not configured");
                return;
            }
            long jIncrementAndGet = lz3.f11083a.incrementAndGet();
            this.f21711j = jIncrementAndGet;
            this.f21713l = jIncrementAndGet;
            this.f21714m = 2;
            this.f21710i.mo2009l(2, 0, "");
            hz3 hz3Var = this.f21709h;
            lu2 lu2Var = this.f21708c;
            synchronized (lu2Var) {
                z = ((SharedPreferences) lu2Var.f10948a).getBoolean("udp", false);
            }
            vz3 vz3Var = new vz3(this, jIncrementAndGet, 1);
            synchronized (hz3Var) {
                hz3Var.m4232e(new gz3(jIncrementAndGet, 3, strM5933e, z, vz3Var));
            }
        } catch (Exception e) {
            this.f21713l = Long.MIN_VALUE;
            App.m1883c(this.f21717p);
            m10883c(kz3.m5738a(e));
        }
    }
}
