package p000;

import com.fongmi.android.p002tv.bean.Epg;
import com.fongmi.android.p002tv.bean.Live;
import com.fongmi.android.p002tv.bean.Site;
import com.google.gson.JsonElement;
import java.util.Locale;
import java.util.function.Function;
import org.jupnp.model.ServiceReference;

public final class C0629hh implements Function {

    public final int f7145a;

    public final String f7146b;

    public C0629hh(String str, int i) {
        this.f7145a = i;
        this.f7146b = str;
    }

    @Override
    public final Object apply(Object obj) {
        int i = this.f7145a;
        String str = this.f7146b;
        switch (i) {
            case 0:
                fa1 fa1Var = (fa1) obj;
                return new v91(xp0.m10592v(str, fa1Var.f5677c), fa1Var.f5678h, fa1Var.f5679i, fa1Var.f5680j);
            case 1:
                return String.format(Locale.getDefault(), str, (Float) obj);
            case 2:
                return Epg.create(str, (String) obj);
            case 3:
                return Live.objectFrom((JsonElement) obj, str);
            case 4:
                return ((ue1) obj).m9764e(str).m9765f("url", "");
            case 5:
                return ((wl2) obj).m10390c(str, "http");
            case 6:
                ue1 ue1Var = (ue1) obj;
                return new v91(xp0.m10592v(str, ue1Var.m9765f("path", null)), -1, ue1Var.m9762c(-1, "width"), 4);
            case 7:
                return xp0.m10581k(str, ServiceReference.DELIMITER, (String) obj);
            case 8:
                return ((wl2) obj).m10390c(str, "socks");
            case 9:
                fa1 fa1Var2 = (fa1) obj;
                return new v91(String.format(str, fa1Var2.f5677c), fa1Var2.f5678h, fa1Var2.f5679i, fa1Var2.f5680j);
            case 10:
                return id3.f7901b.m10917f(new g80((Site) obj, str, 8));
            case 11:
                return Site.objectFrom((JsonElement) obj, str);
            case 12:
                return str;
            default:
                return ((ue1) obj).m9764e(str);
        }
    }
}
