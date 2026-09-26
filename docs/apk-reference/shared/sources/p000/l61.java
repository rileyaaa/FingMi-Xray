package p000;

import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.p004ui.activity.HomeActivity;
import com.fongmi.android.p002tv.p004ui.custom.CustomTitleView;

public final class l61 implements Runnable {

    public final int f10448c;
    public final HomeActivity f10449h;

    public l61(HomeActivity homeActivity, int i) {
        this.f10448c = i;
        this.f10449h = homeActivity;
    }

    @Override
    public final void run() {
        int i;
        Network activeNetwork;
        NetworkCapabilities networkCapabilities;
        int i2 = this.f10448c;
        HomeActivity homeActivity = this.f10449h;
        switch (i2) {
            case 0:
                int i3 = HomeActivity.f3068W;
                ((CustomTitleView) homeActivity.f3069F.f19289m).setFocusable(true);
                break;
            case 1:
                int i4 = HomeActivity.f3068W;
                if (homeActivity.isFinishing() || homeActivity.isDestroyed()) {
                    homeActivity.f3081R = false;
                } else if (gn3.m3798b() == homeActivity.f3078O) {
                    try {
                        ConnectivityManager connectivityManager = (ConnectivityManager) homeActivity.getSystemService("connectivity");
                        i = (connectivityManager == null || (activeNetwork = connectivityManager.getActiveNetwork()) == null || (networkCapabilities = connectivityManager.getNetworkCapabilities(activeNetwork)) == null || !networkCapabilities.hasCapability(12)) ? 0 : homeActivity.f3080Q + 1;
                    } catch (RuntimeException unused) {
                    }
                    homeActivity.f3080Q = i;
                    if (i < 2) {
                        int i5 = homeActivity.f3079P;
                        homeActivity.f3079P = i5 + 1;
                        if (i5 < 12) {
                            App.m1882b(homeActivity.f3084U, 500L);
                        }
                    }
                    if (homeActivity.isFinishing() || homeActivity.isDestroyed()) {
                        homeActivity.f3081R = false;
                    } else {
                        long j = homeActivity.f3078O;
                        boolean z = gn3.m3798b() == j;
                        homeActivity.f3077N = j;
                        homeActivity.f3081R = false;
                        if (z) {
                            homeActivity.m1979R0();
                            homeActivity.m1975N0();
                        }
                        homeActivity.m1976O0();
                    }
                } else {
                    homeActivity.f3081R = false;
                    homeActivity.m1976O0();
                }
                break;
            case 2:
                int i6 = HomeActivity.f3068W;
                homeActivity.m1973L0();
                break;
            default:
                j81 j81Var = new j81();
                j81Var.f9007c = homeActivity;
                j81Var.m5016u("android.permission.POST_NOTIFICATIONS").m4100e(new x82(26));
                break;
        }
    }
}
