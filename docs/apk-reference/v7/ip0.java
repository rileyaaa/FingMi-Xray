package p000;

import com.fongmi.android.p002tv.p004ui.activity.CastActivity;
import com.fongmi.android.p002tv.p004ui.activity.HomeActivity;
import com.fongmi.android.p002tv.p004ui.activity.KeepActivity;
import com.fongmi.android.p002tv.p004ui.activity.LiveActivity;
import com.fongmi.android.p002tv.p004ui.activity.SettingActivity;
import com.fongmi.android.p002tv.p004ui.activity.SettingXrayActivity;
import com.fongmi.android.p002tv.p004ui.activity.VideoActivity;
import com.fongmi.android.p002tv.p004ui.activity.VodActivity;
import com.fongmi.android.p002tv.service.PlaybackService;
import java.util.HashMap;
import org.greenrobot.eventbus.ThreadMode;

public final class ip0 {

    public static final HashMap f8104a = new HashMap();

    static {
        ThreadMode threadMode = ThreadMode.MAIN;
        m4349a(new l23(PlaybackService.class, new aa3[]{new aa3("onConfigEvent", C0532ez.class, threadMode)}));
        m4349a(new l23(d40.class, new aa3[]{new aa3("onConfigEvent", C0532ez.class, threadMode)}));
        m4349a(new l23(i42.class, new aa3[]{new aa3("onServerEvent", uy2.class, threadMode)}));
        m4349a(new l23(SettingActivity.class, new aa3[]{new aa3("onConfigEvent", C0532ez.class, threadMode)}));
        m4349a(new l23(AbstractActivityC1828yh.class, new aa3[]{new aa3("onSubscribe", Object.class, threadMode)}));
        m4349a(new l23(C0459cz.class, new aa3[]{new aa3("onServerEvent", uy2.class, threadMode)}));
        m4349a(new l23(KeepActivity.class, new aa3[]{new aa3("onRefreshEvent", ep2.class, threadMode)}));
        m4349a(new l23(SettingXrayActivity.class, new aa3[]{new aa3("onXrayImportEvent", mz3.class, threadMode)}));
        m4349a(new l23(HomeActivity.class, new aa3[]{new aa3("onConfigEvent", C0532ez.class, threadMode), new aa3("onRefreshEvent", ep2.class, threadMode), new aa3("onServerEvent", uy2.class, threadMode), new aa3("onCastEvent", C1087kq.class, threadMode)}));
        m4349a(new l23(VideoActivity.class, new aa3[]{new aa3("onRefreshEvent", ep2.class, threadMode)}));
        m4349a(new l23(ao3.class, new aa3[]{new aa3("onServerEvent", uy2.class, threadMode)}));
        m4349a(new l23(s50.class, new aa3[]{new aa3("onServerEvent", uy2.class, threadMode)}));
        m4349a(new l23(LiveActivity.class, new aa3[]{new aa3("onRefreshEvent", ep2.class, threadMode)}));
        m4349a(new l23(CastActivity.class, new aa3[]{new aa3("onRefreshEvent", ep2.class, threadMode)}));
        m4349a(new l23(VodActivity.class, new aa3[]{new aa3("onRefreshEvent", ep2.class, threadMode)}));
    }

    public static void m4349a(l23 l23Var) {
        f8104a.put(l23Var.f10355a, l23Var);
    }
}
