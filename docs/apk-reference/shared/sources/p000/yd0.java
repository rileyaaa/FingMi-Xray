package p000;

import android.content.Context;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Handler;
import android.os.Message;
import android.os.SystemClock;
import android.os.Trace;
import android.telephony.TelephonyManager;
import android.text.TextUtils;
import android.view.View;
import androidx.media3.p001ui.DefaultTimeBar;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.bean.Parse;
import com.fongmi.android.p002tv.p004ui.custom.CustomRecyclerView;
import com.google.android.material.button.MaterialButton;
import java.io.ByteArrayInputStream;
import java.lang.reflect.Method;
import java.nio.MappedByteBuffer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import kotlin.jvm.functions.Function0;
import okhttp3.OkHttpClient;

public final class yd0 implements Runnable {

    public final int f21296c;

    public final Object f21297h;

    public yd0(vr0 vr0Var, int i) {
        this.f21296c = 9;
        this.f21297h = vr0Var;
    }

    private final void m10739a() {
        fw0 fw0Var = (fw0) this.f21297h;
        synchronized (fw0Var.f6089i) {
            try {
                if (fw0Var.f6093m == null) {
                    return;
                }
                try {
                    pw0 pw0VarM3669c = fw0Var.m3669c();
                    int i = pw0VarM3669c.f14457e;
                    if (i == 2) {
                        synchronized (fw0Var.f6089i) {
                        }
                    }
                    if (i != 0) {
                        throw new RuntimeException("fetchFonts result is not OK. (" + i + ")");
                    }
                    try {
                        Method method = zj3.f22094b;
                        Trace.beginSection("EmojiCompat.FontRequestEmojiCompatConfig.buildTypeface");
                        Context context = fw0Var.f6087c;
                        pw0[] pw0VarArr = {pw0VarM3669c};
                        np3 np3Var = ln3.f10807a;
                        p11.m7597d("TypefaceCompat.createFromFontInfo");
                        try {
                            Typeface typefaceMo6260m = ln3.f10807a.mo6260m(context, pw0VarArr, 0);
                            Trace.endSection();
                            MappedByteBuffer mappedByteBufferM1663d0 = AbstractC0215ch.m1663d0(fw0Var.f6087c, pw0VarM3669c.f14453a);
                            if (mappedByteBufferM1663d0 == null || typefaceMo6260m == null) {
                                throw new RuntimeException("Unable to open file.");
                            }
                            try {
                                Trace.beginSection("EmojiCompat.MetadataRepo.create");
                                C1872zo c1872zo = new C1872zo(typefaceMo6260m, s11.m8829C(mappedByteBufferM1663d0));
                                Trace.endSection();
                                Trace.endSection();
                                synchronized (fw0Var.f6089i) {
                                    try {
                                        q11 q11Var = fw0Var.f6093m;
                                        if (q11Var != null) {
                                            q11Var.mo3586K(c1872zo);
                                        }
                                    } catch (Throwable th) {
                                        throw th;
                                    }
                                }
                                fw0Var.m3668b();
                            } catch (Throwable th2) {
                                Method method2 = zj3.f22094b;
                                Trace.endSection();
                                throw th2;
                            }
                        } catch (Throwable th3) {
                            Trace.endSection();
                            throw th3;
                        }
                    } catch (Throwable th4) {
                        Method method3 = zj3.f22094b;
                        Trace.endSection();
                        throw th4;
                    }
                } catch (Throwable th5) {
                    synchronized (fw0Var.f6089i) {
                        try {
                            q11 q11Var2 = fw0Var.f6093m;
                            if (q11Var2 != null) {
                                q11Var2.mo3585J(th5);
                            }
                            fw0Var.m3668b();
                        } catch (Throwable th6) {
                            throw th6;
                        }
                    }
                }
            } catch (Throwable th7) {
                throw th7;
            }
        }
    }

    /* JADX WARN: Code duplicated, block: B:50:0x00b1 A[Catch: all -> 0x0075, TryCatch #3 {, blocks: (B:22:0x006a, B:24:0x006e, B:31:0x007b, B:35:0x0082, B:41:0x008e, B:43:0x0092, B:45:0x0098, B:47:0x00a2, B:49:0x00ac, B:51:0x00bd, B:50:0x00b1, B:52:0x00bf, B:54:0x00d2, B:56:0x00da), top: B:169:0x006a }] */
    @Override
    public final void run() {
        n53 n53Var;
        uk3 uk3Var;
        String strM9596Y0;
        TelephonyManager telephonyManager;
        int i = 0;
        switch (this.f21296c) {
            case 0:
                DefaultTimeBar defaultTimeBar = (DefaultTimeBar) this.f21297h;
                int i2 = DefaultTimeBar.f1037c0;
                defaultTimeBar.m649h(false);
                return;
            case 1:
                je0 je0Var = (je0) this.f21297h;
                if (!je0Var.f9093f.f4901A0 || Build.VERSION.SDK_INT < 32 || (n53Var = je0Var.f9095h) == null || !n53Var.f11992b || (uk3Var = je0Var.f9088a) == null) {
                    return;
                }
                uk3Var.mo1599a(null);
                return;
            case 2:
                ((ve0) this.f21297h).f19100i.mo3639e();
                return;
            case 3:
                ((gh0) this.f21297h).m3758c();
                return;
            case 4:
                ai0 ai0Var = (ai0) this.f21297h;
                ai0Var.f374t0.f20050i.scrollToPosition(ai0Var.f375u0.f22051c);
                return;
            case 5:
                mi0 mi0Var = (mi0) this.f21297h;
                fj2 fj2Var = mi0Var.f11426i;
                fj2Var.getClass();
                fj2Var.m3556d(mi0Var);
                return;
            case 6:
                fk0 fk0Var = (fk0) this.f21297h;
                boolean zIsPopupShowing = fk0Var.f5861h.isPopupShowing();
                fk0Var.m3569s(zIsPopupShowing);
                fk0Var.f5866m = zIsPopupShowing;
                return;
            case 7:
                wl0 wl0Var = (wl0) this.f21297h;
                CustomRecyclerView customRecyclerView = wl0Var.f20135v0.f18317i;
                ArrayList arrayList = (ArrayList) wl0Var.f20134u0.f15099b;
                for (int i3 = 0; i3 < arrayList.size(); i3++) {
                    if (((cu1) arrayList.get(i3)).f3750d) {
                        i = i3;
                        customRecyclerView.scrollToPosition(i);
                        return;
                    }
                }
                customRecyclerView.scrollToPosition(i);
                return;
            case 8:
                mr0 mr0Var = (mr0) this.f21297h;
                Context context = mr0Var.f11628l;
                String str = qp3.f15065a;
                int iGenerateAudioSessionId = AbstractC1240od.m6948k(context).generateAudioSessionId();
                if (iGenerateAudioSessionId == -1) {
                    iGenerateAudioSessionId = 0;
                }
                C0551fh c0551fh = mr0Var.f11587J;
                if (((Integer) c0551fh.m3542d()).intValue() != iGenerateAudioSessionId) {
                    Integer numValueOf = Integer.valueOf(iGenerateAudioSessionId);
                    c0551fh.f5811f = numValueOf;
                    RunnableC0514eh runnableC0514eh = new RunnableC0514eh(c0551fh, numValueOf, i);
                    sc3 sc3Var = (sc3) c0551fh.f5808c;
                    if (sc3Var.f16522a.getLooper().getThread().isAlive()) {
                        sc3Var.m8957e(runnableC0514eh);
                    }
                    sc3 sc3Var2 = mr0Var.f11642s.f19416m;
                    rc3 rc3VarM8955b = sc3Var2.m8955b(40, iGenerateAudioSessionId, 0);
                    Handler handler = sc3Var2.f16522a;
                    Message message = rc3VarM8955b.f15627a;
                    message.getClass();
                    handler.sendMessageAtFrontOfQueue(message);
                    rc3VarM8955b.m8577a();
                    return;
                }
                return;
            case 9:
                ha0 ha0Var = ((vr0) this.f21297h).f19429z;
                ha0Var.m3975N(ha0Var.m3970B(), 1034, new y90(7));
                return;
            case 10:
                vh2 vh2Var = (vh2) this.f21297h;
                try {
                    synchronized (vh2Var) {
                    }
                    try {
                        vh2Var.f19234a.handleMessage(vh2Var.f19236c, vh2Var.f19237d);
                        return;
                    } finally {
                        vh2Var.m10055a(true);
                    }
                } catch (oq0 e) {
                    q11.m7974n("ExoPlayerImplInternal", "Unexpected error delivering message on external thread.", e);
                    e81.m3053m(e);
                    return;
                }
            case 11:
                ps0 ps0Var = (ps0) this.f21297h;
                ps0Var.f14045c.m6332f(new ns0(ps0Var, 5), true);
                return;
            case 12:
                App.m1881a(new RunnableC0541f7((sz2) this.f21297h, AbstractC0215ch.m1660c(AbstractC0215ch.m1639I(u11.m9615i())), 25));
                return;
            case 13:
                m10739a();
                return;
            case 14:
                ox0 ox0Var = (ox0) this.f21297h;
                ox0Var.f13594V.f16210l.m6009Q(ox0Var.f13604j);
                ox0Var.f13604j = null;
                return;
            case 15:
                ((x82) this.f21297h).m10488A();
                return;
            case 16:
                ((Function0) this.f21297h).invoke();
                return;
            case 17:
                ((View) this.f21297h).requestFocus();
                return;
            case 18:
                ((dk1) this.f21297h).f4271t0.f20050i.scrollToPosition(vj1.f19277a.m10373p().indexOf(vj1.f19277a.m10372o()));
                return;
            case 19:
                sp3.m9040b((ByteArrayInputStream) this.f21297h);
                return;
            case 20:
                ((jn1) this.f21297h).m5133c();
                return;
            case 21:
                MaterialButton materialButton = (MaterialButton) this.f21297h;
                int[] iArr = MaterialButton.f3365T;
                materialButton.m2205r();
                return;
            case 22:
                ((es1) this.f21297h).m3249S0();
                return;
            case 23:
                ((Runnable) this.f21297h).run();
                return;
            case 24:
                synchronized (((ay1) this.f21297h).f1612h) {
                    break;
                }
                return;
            case 25:
                ((z32) this.f21297h).m10921d(3, 0, false);
                return;
            case 26:
                ((r42) this.f21297h).f15444d.run();
                return;
            case 27:
                r82 r82Var = (r82) this.f21297h;
                pa0 pa0Var = (pa0) r82Var.f15534a.get();
                if (pa0Var != null) {
                    int iM8931f = r82Var.f15536c.m8931f();
                    qa0 qa0Var = pa0Var.f13936a;
                    synchronized (qa0Var) {
                        int i4 = qa0Var.f14787o;
                        if (i4 == 0 || qa0Var.f14778f) {
                            if (i4 != iM8931f || qa0Var.f14788p == null) {
                                qa0Var.f14787o = iM8931f;
                                if (iM8931f != 1 && iM8931f != 0 && iM8931f != 8) {
                                    if (qa0Var.f14788p == null) {
                                        Context context2 = qa0Var.f14774b;
                                        String str2 = qp3.f15065a;
                                        if (context2 == null || (telephonyManager = (TelephonyManager) context2.getSystemService("phone")) == null) {
                                            strM9596Y0 = u11.m9596Y0(Locale.getDefault().getCountry());
                                        } else {
                                            String networkCountryIso = telephonyManager.getNetworkCountryIso();
                                            if (TextUtils.isEmpty(networkCountryIso)) {
                                                strM9596Y0 = u11.m9596Y0(Locale.getDefault().getCountry());
                                            } else {
                                                strM9596Y0 = u11.m9596Y0(networkCountryIso);
                                            }
                                        }
                                        qa0Var.f14788p = strM9596Y0;
                                    }
                                    qa0Var.f14785m = qa0Var.m8129e(iM8931f);
                                    qa0Var.f14777e.getClass();
                                    long jElapsedRealtime = SystemClock.elapsedRealtime();
                                    qa0Var.m8130g(qa0Var.f14782j, qa0Var.f14785m, qa0Var.f14780h > 0 ? (int) (jElapsedRealtime - qa0Var.f14781i) : 0);
                                    qa0Var.f14781i = jElapsedRealtime;
                                    qa0Var.f14782j = 0L;
                                    qa0Var.f14784l = 0L;
                                    qa0Var.f14783k = 0L;
                                    d43 d43Var = qa0Var.f14779g;
                                    ((ArrayList) d43Var.f3958e).clear();
                                    d43Var.f3954a = -1;
                                    d43Var.f3955b = 0;
                                    d43Var.f3956c = 0;
                                    return;
                                }
                                return;
                            }
                            return;
                        }
                        return;
                    }
                }
                return;
            case 28:
                OkHttpClient okHttpClient = (OkHttpClient) this.f21297h;
                try {
                    okHttpClient.dispatcher().cancelAll();
                    break;
                } catch (Throwable unused) {
                }
                try {
                    okHttpClient.connectionPool().evictAll();
                    break;
                } catch (Throwable unused2) {
                }
                try {
                    okHttpClient.dispatcher().executorService().shutdown();
                    return;
                } catch (Throwable unused3) {
                    return;
                }
            default:
                oc2 oc2Var = (oc2) this.f21297h;
                CustomRecyclerView customRecyclerView2 = (CustomRecyclerView) oc2Var.f12911u0.f15276i;
                List list = (List) oc2Var.f12912v0.f15099b;
                for (int i5 = 0; i5 < list.size(); i5++) {
                    if (((Parse) list.get(i5)).isSelected()) {
                        i = i5;
                        customRecyclerView2.scrollToPosition(i);
                        return;
                    }
                }
                customRecyclerView2.scrollToPosition(i);
                return;
        }
    }

    public yd0(mi0 mi0Var, boolean z) {
        this.f21296c = 5;
        this.f21297h = mi0Var;
    }

    public yd0(vr0 vr0Var, vh2 vh2Var) {
        this.f21296c = 10;
        this.f21297h = vh2Var;
    }

    public yd0(mv1 mv1Var, fw1 fw1Var, Runnable runnable) {
        this.f21296c = 23;
        this.f21297h = runnable;
    }

    public yd0(Object obj, int i) {
        this.f21296c = i;
        this.f21297h = obj;
    }
}
