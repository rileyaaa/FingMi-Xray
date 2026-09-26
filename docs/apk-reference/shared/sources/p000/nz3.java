package p000;

import com.fongmi.android.p002tv.xray.XrayService;

public final class nz3 implements Runnable {

    public final int f12596c;

    public final Object f12597h;

    public nz3(Object obj, int i) {
        this.f12596c = i;
        this.f12597h = obj;
    }

    @Override
    public final void run() {
        int i = this.f12596c;
        Object obj = this.f12597h;
        switch (i) {
            case 0:
                pz3 pz3Var = (pz3) obj;
                pz3Var.getClass();
                try {
                    pz3Var.f14525b.cancelAll();
                    break;
                } catch (Throwable unused) {
                }
                try {
                    pz3Var.f14526c.evictAll();
                } catch (Throwable unused2) {
                    return;
                }
                break;
            case 1:
                XrayService xrayService = (XrayService) obj;
                int i2 = XrayService.f3215n;
                try {
                    xrayService.m2092g();
                } catch (Exception unused3) {
                    return;
                }
                break;
            default:
                ((hz3) obj).m4228a();
                break;
        }
    }
}
