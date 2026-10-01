package p000;

import android.os.Looper;
import android.text.TextUtils;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.bean.Danmaku;
import com.fongmi.android.p002tv.bean.Drm;
import com.fongmi.android.p002tv.bean.Sub;
import com.fongmi.android.p002tv.bean.Track;
import com.fongmi.android.p002tv.service.PlaybackService;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.BiConsumer;
import java.util.function.Consumer;
import okhttp3.OkHttpClient;

public final class th2 implements nc2 {

    public final p82 f17529a;

    public final rc2 f17530b;

    public final PlaybackService f17531c;

    public qh2 f17532d;

    public hh2 f17533e;

    public js3 f17534f;

    public tc2 f17535g;

    public C1519q4 f17536h;

    public ig2 f17537i;

    public long f17538j;

    public boolean f17539k;

    public int f17540l;

    public int f17541m;

    public int f17542n;

    public rh2 f17543o;

    public final ph2 f17544p;

    /* JADX WARN: Code duplicated, block: B:9:0x0033  */
    public th2(PlaybackService playbackService) {
        boolean zIsAvailable;
        int i;
        hh2 sq0Var;
        ph2 ph2Var = new ph2(this);
        this.f17544p = ph2Var;
        this.f17531c = playbackService;
        this.f17541m = 1;
        this.f17530b = new rc2(this, 4);
        this.f17538j = -9223372036854775807L;
        if (np3.m6605F() == 1) {
            try {
                ja1 ja1Var = s52.f16388S;
                zIsAvailable = s42.f16370a.isAvailable();
            } catch (Throwable unused) {
                zIsAvailable = false;
            }
            if (zIsAvailable) {
                i = 2;
            } else {
                i = 1;
            }
        } else {
            i = 1;
        }
        int iM6245x = AbstractC1163ml.m6245x(i);
        if (iM6245x == 0) {
            sq0Var = new sq0(1, ph2Var, 0);
        } else {
            if (iM6245x != 1) {
                throw new RuntimeException(null, null);
            }
            sq0Var = new z52(1, ph2Var);
        }
        this.f17533e = sq0Var;
        this.f17529a = new p82(new oh2(this, 0), 25);
        o11.m6812q();
        p11.m7608o("danmaku_show", true);
        this.f17537i = this.f17533e.mo4120f();
    }

    public final synchronized void m9308A(int i, boolean z) {
        sh2 sh2VarM8975y;
        C1519q4 c1519q4;
        try {
            int iMax = Math.max(0, i);
            if (this.f17542n == iMax) {
                return;
            }
            if (!z || (c1519q4 = this.f17536h) == null) {
                sh2VarM8975y = null;
            } else {
                rh2 rh2Var = this.f17543o;
                sh2VarM8975y = (iMax <= 0 || rh2Var == null || rh2Var.f15736c != c1519q4) ? sh2.m8975y(this.f17537i) : rh2Var.f15737h;
            }
            this.f17543o = null;
            this.f17542n = iMax;
            if (iMax > 0) {
                this.f17531c.m1942z();
            }
            m9316c();
            C1519q4 c1519q5 = this.f17536h;
            if (c1519q5 == null) {
                return;
            }
            m9335v(c1519q5);
            if (sh2VarM8975y == null) {
                return;
            }
            m9338y(15000L, sh2VarM8975y.f16616c);
            sh2VarM8975y.m8976z(this.f17537i);
        } catch (Throwable th) {
            throw th;
        }
    }

    public final float m9309B(float f) {
        if (!this.f17537i.mo336T0(13)) {
            return m9323j();
        }
        ig2 ig2Var = this.f17537i;
        ig2Var.setPlaybackParameters(new ef2(p11.m7598e(f), ig2Var.getPlaybackParameters().f4942b));
        return m9323j();
    }

    public final void m9310C(Sub sub) {
        C1519q4 c1519q4 = this.f17536h;
        if (c1519q4 != null) {
            List arrayList = (List) c1519q4.f14609i;
            if (arrayList == null) {
                arrayList = new ArrayList();
                c1519q4.f14609i = arrayList;
            }
            if (sub != null) {
                arrayList.remove(sub);
                for (Sub sub2 : (List) c1519q4.f14609i) {
                    if (sub2.isForced()) {
                        sub2.setFlag(4);
                    }
                }
                ((List) c1519q4.f14609i).add(0, sub);
            }
        }
        boolean zMo4123o0 = this.f17533e.mo4123o0(sub);
        ig2 ig2Var = this.f17537i;
        if (zMo4123o0) {
            ig2Var.mo347g0();
            return;
        }
        long currentPosition = ig2Var.getCurrentPosition();
        if (this.f17543o != null) {
            return;
        }
        m9338y(15000L, currentPosition);
    }

    public final void m9311D(List list) {
        if (list.isEmpty()) {
            return;
        }
        ig2 ig2Var = this.f17537i;
        HashMap map = new HashMap();
        final HashMap map2 = new HashMap();
        Iterator it = list.iterator();
        while (it.hasNext()) {
            Track track = (Track) it.next();
            yk3 yk3Var = null;
            if (track.getFormat() != null) {
                rv0 rv0VarListIterator = ig2Var.mo1740b0().f432a.listIterator(0);
                while (rv0VarListIterator.hasNext()) {
                    zk3 zk3Var = (zk3) rv0VarListIterator.next();
                    if (zk3Var.f22119b.f9275c == track.getType()) {
                        for (int i = 0; i < zk3Var.f22118a; i++) {
                            if (track.getFormat().equals(q11.m7972l(zk3Var.m11031a(i)))) {
                                yk3Var = new yk3(zk3Var, i);
                                break;
                            }
                        }
                    }
                }
            }
            if (yk3Var != null) {
                jk3 jk3Var = yk3Var.f21400c.f22119b;
                int i2 = jk3Var.f9275c;
                map.put(Integer.valueOf(i2), jk3Var);
                if (track.isSelected()) {
                    map2.put(Integer.valueOf(i2), Integer.valueOf(yk3Var.f21401h));
                }
            }
        }
        final rk3 rk3VarMo3118a = ig2Var.mo1780z0().mo3118a();
        map.forEach(new BiConsumer() {
            @Override
            public final void accept(Object obj, Object obj2) {
                List listUnmodifiableList;
                jk3 jk3Var2 = (jk3) obj2;
                Integer num = (Integer) map2.get((Integer) obj);
                if (num != null) {
                    ArrayList arrayList = new ArrayList(1);
                    Object obj3 = new Object[]{num}[0];
                    Objects.requireNonNull(obj3);
                    arrayList.add(obj3);
                    listUnmodifiableList = Collections.unmodifiableList(arrayList);
                } else {
                    listUnmodifiableList = Collections.EMPTY_LIST;
                }
                rk3VarMo3118a.mo2651h(new pk3(jk3Var2, listUnmodifiableList));
            }
        });
        ig2Var.mo1725J(rk3VarMo3118a.mo2647b());
    }

    public final void m9312E(C1519q4 c1519q4, long j, long j2) {
        this.f17543o = null;
        this.f17536h = c1519q4;
        m9338y(j, j2);
    }

    public final void m9313F() {
        App.m1883c(this.f17530b);
        this.f17533e.stop();
        m9314G();
    }

    public final void m9314G() {
        tc2 tc2Var = this.f17535g;
        if (tc2Var != null) {
            tc2Var.m9262h();
        }
        this.f17535g = null;
        this.f17538j = -9223372036854775807L;
    }

    public final synchronized void m9315H(Consumer consumer) {
        consumer.accept(m9321h(la2.m5792c()));
    }

    @Override
    public final void mo6514a() {
        this.f17538j = -9223372036854775807L;
        this.f17531c.m1941y(AbstractC0463d2.m2461f(R.string.error_play_parse));
    }

    @Override
    public final void mo6515b(String str, String str2, Map map) {
        if (!TextUtils.isEmpty(str2)) {
            d81.m2565U(AbstractC0463d2.m2462g(R.string.parse_from, str2));
        }
        if (map != null) {
            map.remove("Range");
        }
        C1519q4 c1519q4 = this.f17536h;
        if (c1519q4 != null) {
            c1519q4.f14613m = map;
        }
        if (c1519q4 != null) {
            c1519q4.f14612l = str;
        }
        long j = this.f17538j;
        if (this.f17543o == null) {
            m9338y(15000L, j);
        }
        this.f17538j = -9223372036854775807L;
    }

    public final void m9316c() {
        this.f17532d = null;
        hh2 hh2Var = this.f17533e;
        if (hh2Var != null) {
            hh2Var.mo4119b0();
        }
    }

    public final void m9317d() {
        if (this.f17542n == 0) {
            return;
        }
        C1519q4 c1519q4 = this.f17536h;
        this.f17543o = c1519q4 == null ? null : new rh2(c1519q4, sh2.m8975y(this.f17537i));
        this.f17542n = 0;
        m9316c();
        C1519q4 c1519q5 = this.f17536h;
        if (c1519q5 != null) {
            m9335v(c1519q5);
        }
    }

    public final String m9318e() {
        return op3.m7096h(Math.max(0L, this.f17537i.getDuration()));
    }

    public final String m9319f() {
        C1519q4 c1519q4 = this.f17536h;
        if (c1519q4 != null) {
            return (String) c1519q4.f14611k;
        }
        return null;
    }

    public final String m9320g(long j) {
        long currentPosition = this.f17537i.getCurrentPosition() + j;
        long jMax = Math.max(0L, this.f17537i.getDuration());
        if (0 <= jMax) {
            return op3.m7096h(Math.min(jMax, Math.max(currentPosition, 0L)));
        }
        C1566re.m8586j(w43.m10260e(jMax, "0 > "));
        return null;
    }

    public final OkHttpClient m9321h(OkHttpClient okHttpClient) {
        hh2 hh2Var = this.f17533e;
        if (hh2Var instanceof sq0) {
            sq0 sq0Var = (sq0) hh2Var;
            if (sq0Var.f16856l > 0) {
                pz3 pz3Var = (pz3) sq0Var.f16852h.f20989k;
                return pz3Var == null ? la2.m5798i() : pz3Var.f14527d;
            }
        }
        if (this.f17542n <= 0) {
            return okHttpClient;
        }
        xw2.m10661h("Xray session requires ExoPlayerEngine");
        return null;
    }

    public final String m9322i() {
        js3 js3Var = this.f17534f;
        if ((js3Var == null ? 0 : js3Var.f9399a) == 0) {
            if ((js3Var == null ? 0 : js3Var.f9400b) == 0) {
                return "";
            }
        }
        StringBuilder sb = new StringBuilder();
        js3 js3Var2 = this.f17534f;
        sb.append(js3Var2 == null ? 0 : js3Var2.f9399a);
        sb.append(" x ");
        js3 js3Var3 = this.f17534f;
        sb.append(js3Var3 != null ? js3Var3.f9400b : 0);
        return sb.toString();
    }

    public final float m9323j() {
        return this.f17537i.getPlaybackParameters().f4941a;
    }

    public final String m9324k() {
        C1519q4 c1519q4 = this.f17536h;
        if (c1519q4 != null) {
            return (String) c1519q4.f14612l;
        }
        return null;
    }

    public final boolean m9325l() {
        return this.f17536h != null;
    }

    public final boolean m9326m(int i) {
        return this.f17537i.mo1740b0().f432a.stream().filter(new xk3(i, 0)).mapToInt(new C0938jw(3)).sum() > 0;
    }

    public final boolean m9327n() {
        C1519q4 c1519q4 = this.f17536h;
        return c1519q4 == null || TextUtils.isEmpty((String) c1519q4.f14612l);
    }

    public final boolean m9328o() {
        return this.f17537i.mo329L0() != null && this.f17537i.mo342b1();
    }

    public final boolean m9329p() {
        return this.f17537i == null;
    }

    public final boolean m9330q() {
        return this.f17537i.mo1745e() == 1;
    }

    public final boolean m9331r() {
        return (this.f17537i.mo329L0() == null || this.f17537i.mo342b1()) ? false : true;
    }

    public final boolean m9332s() {
        if (this.f17542n > 0) {
            return true;
        }
        hh2 hh2Var = this.f17533e;
        return (hh2Var instanceof sq0) && ((sq0) hh2Var).f16856l > 0;
    }

    public final void m9333t() {
        C1519q4 c1519q4 = this.f17536h;
        Danmaku danmaku = c1519q4 != null ? (Danmaku) ((ArrayList) c1519q4.f14614n).stream().filter(new u30(21)).findFirst().orElse(null) : null;
        this.f17531c.f3029p.forEach(new C1206nh(danmaku != null ? danmaku.getUri() : null, 16));
    }

    public final void m9334u() {
        this.f17537i.pause();
    }

    /* JADX WARN: Code duplicated, block: B:4:0x0011  */
    public final void m9335v(C1519q4 c1519q4) {
        boolean zIsAvailable;
        int i;
        hh2 sq0Var;
        hh2 hh2Var = this.f17533e;
        ig2 ig2Var = this.f17537i;
        ph2 ph2Var = this.f17544p;
        ig2Var.mo1755l0(ph2Var);
        int i2 = this.f17541m;
        int i3 = this.f17542n;
        if (i3 <= 0 && ((Drm) c1519q4.f14615o) == null) {
            String str = (String) c1519q4.f14612l;
            if (!"smb".equals(str == null ? "" : q11.m7955O(q11.m7959U(str))) && np3.m6605F() == 1) {
                try {
                    ja1 ja1Var = s52.f16388S;
                    zIsAvailable = s42.f16370a.isAvailable();
                } catch (Throwable unused) {
                    zIsAvailable = false;
                }
                if (zIsAvailable) {
                    i = 2;
                } else {
                    i = 1;
                }
            } else {
                i = 1;
            }
        } else {
            i = 1;
        }
        int iM6245x = AbstractC1163ml.m6245x(i);
        if (iM6245x == 0) {
            sq0Var = new sq0(i2, ph2Var, i3);
        } else {
            if (iM6245x != 1) {
                throw new RuntimeException(null, null);
            }
            sq0Var = new z52(i2, ph2Var);
        }
        this.f17533e = sq0Var;
        ig2 ig2VarMo4120f = sq0Var.mo4120f();
        this.f17537i = ig2VarMo4120f;
        PlaybackService playbackService = this.f17531c;
        ig2 ig2Var2 = playbackService.f3039z;
        mf2 mf2Var = playbackService.f3028A;
        ig2Var2.mo1755l0(mf2Var);
        playbackService.f3039z = ig2VarMo4120f;
        ig2VarMo4120f.mo1766s(mf2Var);
        zu1 zu1Var = playbackService.f3033t;
        int i4 = 15;
        if (zu1Var != null) {
            mv1 mv1Var = zu1Var.f22294a;
            lf2 lf2Var = new lf2(playbackService, ig2VarMo4120f);
            ig2 ig2Var3 = (ig2) lf2Var.f14529c;
            q80.m8097i(ig2Var3.mo331N0());
            Looper looperMo2514V0 = ig2Var3.mo2514V0();
            mv1Var.m6381K();
            q80.m8097i(looperMo2514V0 == ((ig2) mv1Var.f11812t.f14529c).mo2514V0());
            q80.m8106r(ig2Var3.mo2514V0() == Looper.myLooper());
            mv1Var.getClass();
            mv1Var.m6375D(new ep1(mv1Var, lf2Var, i4));
        }
        playbackService.f3029p.forEach(new C1206nh(ig2VarMo4120f, i4));
        hh2Var.release();
    }

    public final void m9336w() {
        App.m1883c(this.f17530b);
        this.f17540l = 0;
    }

    public final void m9337x() {
        ig2 ig2Var = this.f17537i;
        rk3 rk3VarMo2648c = ig2Var.mo1780z0().mo3118a().mo2648c();
        rk3VarMo2648c.mo2655l(2, false);
        rk3VarMo2648c.mo2655l(1, false);
        rk3VarMo2648c.mo2655l(3, false);
        ig2Var.mo1725J(rk3VarMo2648c.mo2647b());
    }

    public final void m9338y(long j, long j2) {
        C1519q4 c1519q4 = this.f17536h;
        if (c1519q4 == null || ((String) c1519q4.f14612l) == null) {
            return;
        }
        c1519q4.m7998b();
        if (!tp3.m9407M(this.f17533e, c1519q4, this.f17542n)) {
            m9335v(c1519q4);
        }
        this.f17532d = null;
        this.f17539k = false;
        this.f17533e.mo4118Q(this.f17536h, j2);
        m9333t();
        rc2 rc2Var = this.f17530b;
        App.m1883c(rc2Var);
        App.m1882b(rc2Var, j);
        this.f17531c.f3029p.forEach(new C1166mo(27));
    }

    public final void m9339z(pv1 pv1Var) {
        tu1 tu1VarMo329L0;
        C1519q4 c1519q4 = this.f17536h;
        if (c1519q4 == null || pv1Var.equals((pv1) c1519q4.f14608h)) {
            return;
        }
        C1519q4 c1519q5 = this.f17536h;
        c1519q5.f14608h = pv1Var;
        if (TextUtils.isEmpty((String) c1519q5.f14612l) || (tu1VarMo329L0 = this.f17537i.mo329L0()) == null) {
            return;
        }
        ig2 ig2Var = this.f17537i;
        int iMo1751i0 = ig2Var.mo1751i0();
        gu1 gu1VarM9485a = tu1VarMo329L0.m9485a();
        gu1VarM9485a.f6751k = pv1Var;
        ig2Var.mo371u0(iMo1751i0, gu1VarM9485a.m3854a());
    }
}
