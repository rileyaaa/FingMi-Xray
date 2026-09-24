package p000;

import android.net.Uri;
import android.os.Bundle;
import com.fongmi.android.p002tv.bean.Site;
import com.fongmi.android.p002tv.bean.Vod;
import com.xunlei.downloadlib.parameter.TorrentFileInfo;
import com.xunlei.downloadlib.parameter.TorrentInfo;
import java.lang.reflect.Method;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.util.Map;
import java.util.function.Function;
import java.util.function.IntFunction;

public final class u60 implements Function {

    public final int f18163a;

    public final Object f18164b;

    public u60(be1 be1Var, Map map) {
        this.f18163a = 3;
        this.f18164b = map;
    }

    @Override
    public final Object apply(Object obj) {
        int i = this.f18163a;
        Object obj2 = this.f18164b;
        switch (i) {
            case 0:
                return (String) ((IntFunction) obj2).apply(((Float) obj).intValue());
            case 1:
                return ((Class) obj2).cast((z82) obj);
            case 2:
                return ((Bundle) obj2).getString((String) obj);
            case 3:
                Map map = (Map) obj2;
                Method method = (Method) ((Map.Entry) obj).getValue();
                if (method == null) {
                    return null;
                }
                try {
                    return (Object[]) method.invoke(null, map);
                } catch (Throwable th) {
                    th.printStackTrace();
                    return null;
                }
            case 4:
                Map.Entry entry = (Map.Entry) obj;
                return new zq1((ue1) obj2, (String) entry.getKey(), (ue1) entry.getValue());
            case 5:
                Uri uri = (Uri) obj;
                ((wl2) obj2).getClass();
                InetSocketAddress inetSocketAddressCreateUnresolved = InetSocketAddress.createUnresolved(uri.getHost(), uri.getPort());
                if (wl2.m10388e(uri, "http")) {
                    return new Proxy(Proxy.Type.HTTP, inetSocketAddressCreateUnresolved);
                }
                if (wl2.m10388e(uri, "socks")) {
                    return new Proxy(Proxy.Type.SOCKS, inetSocketAddressCreateUnresolved);
                }
                return null;
            case 6:
                return ((TorrentInfo) obj2).lambda$getMedias$1((TorrentFileInfo) obj);
            case 7:
                Vod vod = (Vod) obj;
                return AbstractC1685um.m9797a("VS:" + ((Site) obj2).getKey() + '|' + vod.getId(), false, true, 6, vod.getName(), vod.getRemarks(), vod.getPic(), null);
            case 8:
                m21 m21Var = (m21) obj2;
                ue1 ue1Var = (ue1) obj;
                if (ue1Var.containsKey("compactVideoRenderer")) {
                    return new b14(ue1Var.m9764e("compactVideoRenderer"), m21Var);
                }
                if (ue1Var.containsKey("compactRadioRenderer")) {
                    return new m04(ue1Var.m9764e("compactRadioRenderer"));
                }
                if (ue1Var.containsKey("compactPlaylistRenderer")) {
                    return new m04(ue1Var.m9764e("compactPlaylistRenderer"));
                }
                if (!ue1Var.containsKey("lockupViewModel")) {
                    return null;
                }
                ue1 ue1VarM9764e = ue1Var.m9764e("lockupViewModel");
                String strM9765f = ue1VarM9764e.m9765f("contentType", null);
                if ("LOCKUP_CONTENT_TYPE_PLAYLIST".equals(strM9765f) || "LOCKUP_CONTENT_TYPE_PODCAST".equals(strM9765f)) {
                    return new n04(ue1VarM9764e);
                }
                if ("LOCKUP_CONTENT_TYPE_VIDEO".equals(strM9765f)) {
                    return new d14(ue1VarM9764e, m21Var);
                }
                return null;
            default:
                rd1 rd1Var = (rd1) obj;
                sd1 sd1Var = rd1Var.f15636h;
                C1488pf c1488pf = new C1488pf();
                c1488pf.f14052e = String.valueOf(sd1Var.f16530h);
                String str = rd1Var.f15635c;
                boolean z = rd1Var.f15637i;
                c1488pf.f14053f = str;
                c1488pf.f14051d = z;
                c1488pf.f14055h = sd1Var.f16529c;
                c1488pf.f14049b = sd1Var.f16531i;
                c1488pf.f14054g = sd1Var.f16544v;
                c1488pf.f14056i = sd1Var.f16546x;
                c1488pf.f14050c = sd1Var.f16528A;
                c1488pf.f14057j = sd1Var;
                int i2 = ((z04) obj2).f21743s;
                if (i2 == 4 || i2 == 6 || !z) {
                    c1488pf.f14048a = 2;
                }
                return c1488pf.m7789a();
        }
    }

    public u60(Object obj, int i) {
        this.f18163a = i;
        this.f18164b = obj;
    }
}
