package p000;

import android.graphics.SurfaceTexture;
import android.os.HandlerThread;
import android.view.Surface;
import android.view.ViewGroup;
import android.view.ViewParent;
import android.widget.TextView;
import androidx.media3.p001ui.PlayerSeekView;
import androidx.media3.p001ui.PlayerView;
import androidx.media3.p001ui.SubtitleView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.bean.History;
import com.fongmi.android.p002tv.bean.Site;
import com.fongmi.android.p002tv.bean.Track;
import com.fongmi.android.p002tv.p004ui.activity.SettingXrayActivity;
import com.fongmi.android.p002tv.p004ui.custom.CustomRecyclerView;
import com.fongmi.android.p002tv.p004ui.custom.CustomVerticalGridView;
import com.google.android.material.sidesheet.SideSheetBehavior;
import com.google.android.material.textfield.TextInputLayout;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import org.jupnp.QueueingThreadPoolExecutor;
import org.jupnp.model.gena.RemoteGENASubscription;
import org.jupnp.protocol.sync.SendingRenewal;

public final class rc2 implements Runnable {

    public final int f15625c;

    public final Object f15626h;

    public rc2(Object obj, int i) {
        this.f15625c = i;
        this.f15626h = obj;
    }

    @Override
    public final void run() {
        int i = this.f15625c;
        int i2 = 0;
        Object obj = this.f15626h;
        switch (i) {
            case 0:
                tc2 tc2Var = (tc2) obj;
                nc2 nc2Var = tc2Var.f17407e;
                if (nc2Var != null) {
                    nc2Var.mo6514a();
                }
                tc2Var.m9262h();
                return;
            case 1:
                TextView textView = (TextView) obj;
                textView.setVisibility(8);
                textView.setText("");
                return;
            case 2:
                ((cg2) obj).f2737u--;
                return;
            case 3:
                ((vg2) obj).m10049s();
                return;
            case 4:
                th2 th2Var = (th2) obj;
                th2Var.f17531c.m1941y(AbstractC0463d2.m2461f(R.string.error_play_timeout));
                th2Var.m9313F();
                return;
            case 5:
                int i3 = PlayerSeekView.f1083N;
                ((PlayerSeekView) obj).m661w();
                return;
            case 6:
                ((PlayerView) obj).invalidate();
                return;
            case 7:
                fj2 fj2Var = (fj2) ((vj3) obj).f19290n;
                if (fj2Var != null) {
                    fj2Var.m3553a(false);
                    return;
                }
                return;
            case 8:
                qk2 qk2Var = (qk2) obj;
                th1 th1Var = qk2Var.f14960l;
                if (qk2Var.f14956h == 0) {
                    qk2Var.f14957i = true;
                    th1Var.m9304d(hh1.ON_PAUSE);
                }
                if (qk2Var.f14955c == 0 && qk2Var.f14957i) {
                    th1Var.m9304d(hh1.ON_STOP);
                    qk2Var.f14958j = true;
                    return;
                }
                return;
            case 9:
                ((QueueingThreadPoolExecutor) obj).lambda$createNewQueueThread$0();
                return;
            case 10:
                ((HandlerThread) obj).quit();
                return;
            case 11:
                ((SendingRenewal) obj).lambda$onRenewalFailure$0();
                return;
            case 12:
                ((RemoteGENASubscription) obj).establish();
                return;
            case 13:
                ((c11) obj).m1496p();
                return;
            case 14:
                ((s72) obj).stop();
                return;
            case 15:
                SettingXrayActivity settingXrayActivity = (SettingXrayActivity) obj;
                int i4 = SettingXrayActivity.f3136P;
                long j = settingXrayActivity.f3145N;
                if (j == Long.MIN_VALUE) {
                    return;
                }
                settingXrayActivity.f3145N = Long.MIN_VALUE;
                App.m1883c(settingXrayActivity.f3146O);
                if (settingXrayActivity.f3143L && settingXrayActivity.f3140I == j) {
                    int i5 = settingXrayActivity.f3144M;
                    settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                    settingXrayActivity.f3143L = false;
                    settingXrayActivity.f3144M = -1;
                    d81.m2567k();
                    d81.m2565U("Xray operation timed out");
                    hz3 hz3Var = settingXrayActivity.f3139H;
                    if (hz3Var != null) {
                        hz3Var.m4230c(i5, j);
                    }
                    settingXrayActivity.f3139H = new hz3(settingXrayActivity, settingXrayActivity);
                    return;
                }
                return;
            case 16:
                C0184bm c0184bm = (C0184bm) obj;
                c0184bm.f2091c = false;
                SideSheetBehavior sideSheetBehavior = (SideSheetBehavior) c0184bm.f2093e;
                lt3 lt3Var = sideSheetBehavior.f3530i;
                if (lt3Var != null && lt3Var.m5913f()) {
                    c0184bm.m1310a(c0184bm.f2090b);
                    return;
                } else {
                    if (sideSheetBehavior.f3529h == 2) {
                        sideSheetBehavior.m2244w(c0184bm.f2090b);
                        return;
                    }
                    return;
                }
            case 17:
                CustomRecyclerView customRecyclerView = (CustomRecyclerView) ((k33) obj).f9599u0.f14611k;
                List listM10217t = uv3.f18675a.m10217t();
                Site site = uv3.f18675a.f19527e;
                if (site == null) {
                    site = new Site();
                }
                customRecyclerView.scrollToPosition(listM10217t.indexOf(site));
                return;
            case 18:
                y53 y53Var = (y53) obj;
                int i6 = y53.f21155r;
                Surface surface = y53Var.f21163n;
                if (surface != null) {
                    Iterator it = y53Var.f21156c.iterator();
                    while (it.hasNext()) {
                        ((hr0) it.next()).f7414c.m6303c2(null);
                    }
                }
                SurfaceTexture surfaceTexture = y53Var.f21162m;
                if (surfaceTexture != null) {
                    surfaceTexture.release();
                }
                if (surface != null) {
                    surface.release();
                }
                y53Var.f21162m = null;
                y53Var.f21163n = null;
                return;
            case 19:
                ((b73) obj).m1153z();
                return;
            case 20:
                ya3 ya3Var = (ya3) obj;
                if (ya3Var.f21280x0 == null || !ya3Var.m10719f0()) {
                    return;
                }
                ya3Var.f21279w0.m6838b(false);
                ya3Var.m10726p0(((ArrayList) ya3Var.f21278v0.f15099b).size() == 0);
                return;
            case 21:
                SubtitleView subtitleView = (SubtitleView) obj;
                int i7 = SubtitleView.f1156t;
                subtitleView.f1169s = null;
                subtitleView.f1157c = Collections.EMPTY_LIST;
                subtitleView.m682c();
                return;
            case 22:
                int[] iArr = SwipeRefreshLayout.f1302Q;
                ((SwipeRefreshLayout) obj).m854l();
                return;
            case 23:
                nc3 nc3Var = ((pc3) obj).f14013a;
                ViewParent parent = nc3Var.getParent();
                if (parent instanceof ViewGroup) {
                    ((ViewGroup) parent).removeView(nc3Var);
                    return;
                }
                return;
            case 24:
                int[][] iArr2 = TextInputLayout.f3548J0;
                ((TextInputLayout) obj).f3595k.requestLayout();
                return;
            case 25:
                gk3 gk3Var = (gk3) obj;
                CustomRecyclerView customRecyclerView2 = (CustomRecyclerView) gk3Var.f6533w0.f17146j;
                ArrayList arrayList = (ArrayList) gk3Var.f6532v0.f15099b;
                for (int i8 = 0; i8 < arrayList.size(); i8++) {
                    if (((Track) arrayList.get(i8)).isSelected()) {
                        i2 = i8;
                        customRecyclerView2.scrollToPosition(i2);
                        return;
                    }
                }
                customRecyclerView2.scrollToPosition(i2);
                return;
            case 26:
                ((CustomVerticalGridView) ((kn3) obj).f9999g0.f22157j).scrollToPosition(0);
                return;
            case 27:
                ((ur3) obj).m9853c();
                return;
            case 28:
                ((History) obj).save();
                return;
            default:
                ez3 ez3Var = (ez3) obj;
                hz3 hz3Var2 = ez3Var.f5412j;
                synchronized (hz3Var2) {
                    if (ez3Var == hz3Var2.f7572e && hz3Var2.f7576i && hz3Var2.f7570c == null) {
                        hz3Var2.m4231d(ez3Var, "Xray service connection timed out");
                        return;
                    }
                    return;
                }
        }
    }
}
