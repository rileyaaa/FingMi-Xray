package p000;

import android.content.Context;
import com.fongmi.android.p002tv.xray.XrayService;
import java.security.KeyStore;

public final class tz3 implements Runnable {

    public final int f17965c;

    public final uz3 f17966h;

    public final long f17967i;

    public final h91 f17968j;

    public tz3(uz3 uz3Var, long j, h91 h91Var, int i) {
        this.f17965c = i;
        this.f17966h = uz3Var;
        this.f17967i = j;
        this.f17968j = h91Var;
    }

    @Override
    public final void run() {
        switch (this.f17965c) {
            case 0:
                uz3 uz3Var = this.f17966h;
                long j = this.f17967i;
                h91 h91Var = this.f17968j;
                XrayService xrayService = uz3Var.f18805d;
                int i = XrayService.f3215n;
                e63 e63Var = xrayService.f3217h;
                if (!e63Var.m3022f(j)) {
                    XrayService.m2087f(h91Var, j, 4, true, 0, -1L, "");
                    return;
                }
                try {
                    xrayService.m2092g();
                    XrayService.m2087f(h91Var, j, 4, true, 0, -1L, "");
                    return;
                } catch (Exception e) {
                    if (!e63Var.m3022f(j)) {
                        XrayService.m2087f(h91Var, j, 4, true, 0, -1L, "");
                        return;
                    } else {
                        if (XrayService.m2087f(h91Var, j, 4, false, 0, -1L, "Xray cleanup required process reset: ".concat(kz3.m5738a(e)))) {
                            return;
                        }
                        xrayService.m2091e(4, j);
                        return;
                    }
                }
            default:
                uz3 uz3Var2 = this.f17966h;
                long j2 = this.f17967i;
                h91 h91Var2 = this.f17968j;
                XrayService xrayService2 = uz3Var2.f18805d;
                int i2 = XrayService.f3215n;
                try {
                    xrayService2.m2090c(j2);
                    j81 j81Var = new j81((Context) xrayService2);
                    new j81(xrayService2.getSharedPreferences("xray_secure", 0)).m5011i();
                    j81Var.m5011i();
                    synchronized (j81.class) {
                        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
                        keyStore.load(null);
                        if (keyStore.containsAlias("fongmi_xray_hy2_pins_v1")) {
                            keyStore.deleteEntry("fongmi_xray_hy2_pins_v1");
                        }
                        break;
                    }
                    xrayService2.f3220k = new j81(new j81((Context) xrayService2), new e81(3));
                    xrayService2.f3221l = new x82(new j81((Context) xrayService2), new e81(13));
                    XrayService.m2087f(h91Var2, j2, 5, true, 0, -1L, "");
                    return;
                } catch (Exception e2) {
                    XrayService.m2087f(h91Var2, j2, 5, false, 0, -1L, kz3.m5738a(e2));
                    return;
                }
        }
    }
}
