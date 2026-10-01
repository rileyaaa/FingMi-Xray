package p000;

import com.fongmi.android.p002tv.xray.XrayService;
import org.json.JSONObject;

public final class sz3 implements Runnable {

    public final int f17015c;

    public final uz3 f17016h;

    public final long f17017i;

    public final String f17018j;

    public final boolean f17019k;

    public final h91 f17020l;

    public sz3(uz3 uz3Var, long j, String str, boolean z, h91 h91Var, int i) {
        this.f17015c = i;
        this.f17016h = uz3Var;
        this.f17017i = j;
        this.f17018j = str;
        this.f17019k = z;
        this.f17020l = h91Var;
    }

    /* JADX WARN: Multi-variable type inference failed */
    /* JADX WARN: Type inference failed for: r11v3, types: [h91] */
    /* JADX WARN: Type inference failed for: r4v16 */
    /* JADX WARN: Type inference failed for: r4v17 */
    /* JADX WARN: Type inference failed for: r4v18, types: [long] */
    /* JADX WARN: Type inference failed for: r4v19 */
    /* JADX WARN: Type inference failed for: r4v21 */
    /* JADX WARN: Type inference failed for: r4v24 */
    /* JADX WARN: Type inference failed for: r4v25 */
    /* JADX WARN: Type inference failed for: r4v26 */
    /* JADX WARN: Type inference failed for: r4v27 */
    @Override
    public final void run() throws Exception {
        boolean z;
        boolean z2;
        boolean z3;
        long j;
        h91 h91Var;
        ?? r4;
        Exception exc = null;
        switch (this.f17015c) {
            case 0:
                uz3 uz3Var = this.f17016h;
                long j2 = this.f17017i;
                String str = this.f17018j;
                boolean z4 = this.f17019k;
                h91 h91Var2 = this.f17020l;
                XrayService xrayService = uz3Var.f18805d;
                int i = XrayService.f3215n;
                if (xrayService.m2088a(j2, h91Var2)) {
                    return;
                }
                try {
                    xrayService.m2092g();
                    if (xrayService.m2088a(j2, h91Var2)) {
                        return;
                    }
                    Exception e = null;
                    int i2 = 0;
                    while (i2 < 3) {
                        if (xrayService.m2088a(j2, h91Var2)) {
                            return;
                        }
                        int iM8845m = s11.m8845m();
                        JSONObject jSONObjectM2089b = xrayService.m2089b(iM8845m, str, z4);
                        if (xrayService.m2088a(j2, h91Var2)) {
                            return;
                        }
                        try {
                            s11.m8833I(jSONObjectM2089b);
                            if (xrayService.m2088a(j2, h91Var2)) {
                                return;
                            }
                            s11.m8849q("runXray", new JSONObject().put("xrayJson", jSONObjectM2089b.toString()));
                            xrayService.f3219j = j2;
                            if (!s11.m8855y(s11.m8849q("getXrayState", null)).optBoolean("running")) {
                                throw new IllegalStateException("Xray core did not enter running state");
                            }
                            if (!xrayService.f3217h.m3022f(j2)) {
                                try {
                                    xrayService.m2092g();
                                    break;
                                } catch (Exception unused) {
                                }
                                xrayService.m2088a(j2, h91Var2);
                                return;
                            } else {
                                if (XrayService.m2087f(h91Var2, j2, 3, true, iM8845m, -1L, "")) {
                                    return;
                                }
                                try {
                                    xrayService.m2092g();
                                    z3 = true;
                                } catch (Exception unused2) {
                                    z3 = false;
                                }
                                if (z3) {
                                    return;
                                }
                                xrayService.m2091e(3, j2);
                                return;
                            }
                        } catch (Exception e2) {
                            e = e2;
                            try {
                                xrayService.m2092g();
                                z2 = true;
                            } catch (Exception unused3) {
                                z2 = false;
                            }
                            if (xrayService.m2088a(j2, h91Var2)) {
                                return;
                            }
                            if (!z2) {
                                throw e;
                            }
                            if (!XrayService.m2086d(e)) {
                                throw e;
                            }
                            i2++;
                            if (i2 >= 3) {
                                throw e;
                            }
                        }
                    }
                    if (e != null) {
                        throw e;
                    }
                    return;
                } catch (Exception e3) {
                    try {
                        xrayService.m2092g();
                        z = true;
                    } catch (Exception unused4) {
                        z = false;
                    }
                    if (xrayService.m2088a(j2, h91Var2)) {
                        return;
                    }
                    String strM5738a = kz3.m5738a(e3);
                    if (!z) {
                        strM5738a = "Xray cleanup required process reset: ".concat(strM5738a);
                    }
                    boolean zM2087f = XrayService.m2087f(h91Var2, j2, 3, false, 0, -1L, strM5738a);
                    if (z && zM2087f) {
                        return;
                    }
                    xrayService.m2091e(3, j2);
                    return;
                }
            case 1:
                uz3 uz3Var2 = this.f17016h;
                long j3 = this.f17017i;
                String str2 = this.f17018j;
                boolean z5 = this.f17019k;
                h91 h91Var3 = this.f17020l;
                XrayService xrayService2 = uz3Var2.f18805d;
                int i3 = XrayService.f3215n;
                try {
                    xrayService2.m2090c(j3);
                    try {
                        if (xrayService2.f3219j != Long.MIN_VALUE || s11.m8855y(s11.m8849q("getXrayState", null)).optBoolean("running")) {
                            throw new IllegalStateException("Xray live session is running");
                        }
                        int i4 = 0;
                        while (i4 < 3) {
                            JSONObject jSONObjectM2089b2 = xrayService2.m2089b(s11.m8845m(), str2, z5);
                            try {
                                xrayService2.m2090c(j3);
                                s11.m8833I(jSONObjectM2089b2);
                                xrayService2.m2090c(j3);
                                xrayService2.m2090c(j3);
                                XrayService.m2087f(h91Var3, j3, 1, true, 0, -1L, "");
                                return;
                            } catch (Exception e4) {
                                j = j3;
                                h91Var = h91Var3;
                                exc = e4;
                                if (!XrayService.m2086d(exc)) {
                                    throw exc;
                                }
                                i4++;
                                if (i4 >= 3) {
                                    throw exc;
                                }
                                h91Var3 = h91Var;
                                j3 = j;
                            }
                        }
                        if (exc != null) {
                            throw exc;
                        }
                        throw new IllegalStateException("Unable to allocate Xray port");
                    } catch (Exception e5) {
                        e = e5;
                        XrayService.m2087f(h91Var, j, 1, false, 0, -1L, kz3.m5738a(e));
                        return;
                    }
                } catch (Exception e6) {
                    e = e6;
                    j = j3;
                    h91Var = h91Var3;
                }
                break;
            default:
                uz3 uz3Var3 = this.f17016h;
                long j4 = this.f17017i;
                String str3 = this.f17018j;
                boolean z6 = this.f17019k;
                h91 h91Var4 = this.f17020l;
                XrayService xrayService3 = uz3Var3.f18805d;
                int i5 = XrayService.f3215n;
                try {
                    xrayService3.m2090c(j4);
                    ?? r5 = xrayService3.f3219j;
                    try {
                        if (r5 != Long.MIN_VALUE || s11.m8855y(s11.m8849q("getXrayState", null)).optBoolean("running")) {
                            throw new IllegalStateException("Xray live session is running");
                        }
                        et1 et1Var = new et1(xrayService3, j4);
                        int i6 = 0;
                        while (i6 < 3) {
                            r5 = r5;
                            h91Var4 = h91Var4;
                            try {
                                long jLongValue = ((Long) et1Var.m3261c(xrayService3.m2089b(s11.m8845m(), str3, z6))).longValue();
                                xrayService3.m2090c(j4);
                                h91 h91Var5 = h91Var4;
                                try {
                                    XrayService.m2087f(h91Var5, j4, 2, true, 0, jLongValue, "");
                                    return;
                                } catch (Exception e7) {
                                    e = e7;
                                    r4 = h91Var5;
                                }
                            } catch (Exception e8) {
                                h91 h91Var6 = h91Var4;
                                exc = e8;
                                if (!XrayService.m2086d(exc)) {
                                    throw exc;
                                }
                                i6++;
                                if (i6 >= 3) {
                                    throw exc;
                                }
                                h91Var4 = h91Var6;
                                r5 = h91Var6;
                            }
                        }
                        r5 = r5;
                        h91Var4 = h91Var4;
                        if (exc != null) {
                            throw exc;
                        }
                        throw new IllegalStateException("Unable to allocate Xray port");
                    } catch (Exception e9) {
                        e = e9;
                        r4 = r5;
                    }
                } catch (Exception e10) {
                    e = e10;
                    r4 = h91Var4;
                }
                XrayService.m2087f(r4, j4, 2, false, 0, -1L, kz3.m5738a(e));
                return;
        }
    }
}
