package p000;

import android.os.StatFs;
import androidx.media3.exoplayer.rtsp.RtspMediaSource$Factory;
import com.fongmi.android.p002tv.App;
import java.io.File;
import java.util.Map;
import okhttp3.OkHttpClient;

public final class nq0 implements az1 {

    public static o73 f12433g;

    public static f23 f12434h;

    public final uc0 f12435a;

    public ma2 f12436b;

    public final e80 f12437c;

    public final lb0 f12438d;

    public final int f12439e;

    public final pz3 f12440f;

    public nq0(int i, pz3 pz3Var) {
        this.f12439e = i;
        this.f12440f = pz3Var;
        e80 m21Var = this.f12437c;
        int i2 = 16;
        if (m21Var == null) {
            bm1 bm1Var = new bm1(App.f2949l, m6687h());
            m21Var = i > 0 ? new m21(bm1Var, new kg0(16), i2) : new C1703v3(this, bm1Var, 21);
            this.f12437c = m21Var;
        }
        lb0 lb0Var = this.f12438d;
        if (lb0Var == null) {
            lb0 lb0Var2 = new lb0();
            synchronized (lb0Var2) {
                lb0Var2.f10530c = 1128000;
            }
            this.f12438d = lb0Var2;
            lb0Var = lb0Var2;
        }
        uc0 uc0Var = new uc0(m21Var, lb0Var);
        this.f12435a = uc0Var;
        if (i > 0) {
            C1872zo c1872zo = new C1872zo(16);
            c1872zo.f22158k = new m21(new bm1(App.f2949l, m6687h()), new kg0(16), i2);
            uc0Var.m9756h(c1872zo);
        }
    }

    public static synchronized f23 m6686g() {
        long availableBlocksLong;
        f23 f23Var = f12434h;
        if (f23Var != null) {
            return f23Var;
        }
        int i = u11.f18019z;
        File file = new File(u11.m9615i(), "exo");
        u11.m9630p0(file);
        long jM1639I = AbstractC0215ch.m1639I(file);
        try {
            StatFs statFs = new StatFs(file.getAbsolutePath());
            availableBlocksLong = statFs.getAvailableBlocksLong() * statFs.getBlockSizeLong();
        } catch (Exception unused) {
            availableBlocksLong = 0;
        }
        sg1 sg1Var = new sg1(Math.min(((long) q11.m7981u()) * 1048576, ((Math.max(0L, availableBlocksLong) + jM1639I) * 80) / 100));
        o73 o73Var = f12433g;
        if (o73Var == null) {
            o73Var = new o73(App.f2949l.getApplicationContext(), "exoplayer_internal.db", null, 1);
            f12433g = o73Var;
        }
        f23 f23Var2 = new f23(file, sg1Var, o73Var);
        f12434h = f23Var2;
        return f23Var2;
    }

    @Override
    public final AbstractC0181bj mo614d(tu1 tu1Var) {
        ou1 ou1Var;
        Map mapM8780k = rw1.m8780k(tu1Var);
        ((ma2) m6687h()).m6170a(mapM8780k);
        if (this.f12439e > 0 && (ou1Var = tu1Var.f17863b) != null) {
            String scheme = ou1Var.f13470a.getScheme();
            if ("rtsp".equalsIgnoreCase(scheme) || "rtspt".equalsIgnoreCase(scheme)) {
                pz3 pz3Var = this.f12440f;
                if (pz3Var == null) {
                    xw2.m10661h("Xray proxy resources are missing");
                    return null;
                }
                RtspMediaSource$Factory rtspMediaSource$Factory = new RtspMediaSource$Factory();
                rtspMediaSource$Factory.f1015c = true;
                rtspMediaSource$Factory.f1014b = pz3Var.f14528e;
                String str = (String) mapM8780k.get("User-Agent");
                if (str != null) {
                    int length = str.length();
                    int iCharCount = 0;
                    while (iCharCount < length) {
                        int iCodePointAt = str.codePointAt(iCharCount);
                        if (!Character.isWhitespace(iCodePointAt)) {
                            rtspMediaSource$Factory.f1013a = str;
                            break;
                        }
                        iCharCount += Character.charCount(iCodePointAt);
                    }
                }
                return rtspMediaSource$Factory.mo614d(tu1Var);
            }
        }
        return this.f12435a.mo614d(tu1Var);
    }

    public final z71 m6687h() {
        OkHttpClient okHttpClientM5798i;
        ma2 ma2Var = this.f12436b;
        if (ma2Var != null) {
            return ma2Var;
        }
        if (this.f12439e <= 0) {
            okHttpClientM5798i = la2.m5798i();
        } else {
            pz3 pz3Var = this.f12440f;
            if (pz3Var == null) {
                xw2.m10661h("Xray proxy resources are missing");
                return null;
            }
            okHttpClientM5798i = pz3Var.f14527d;
        }
        ma2 ma2Var2 = new ma2(okHttpClientM5798i);
        this.f12436b = ma2Var2;
        return ma2Var2;
    }

    @Override
    public final az1 mo615e(C1872zo c1872zo) {
        return this;
    }
}
