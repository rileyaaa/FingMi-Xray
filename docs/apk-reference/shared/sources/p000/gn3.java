package p000;

import android.app.Activity;
import android.app.Application;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import com.fongmi.android.p002tv.service.DLNARendererService;

public final class gn3 implements Application.ActivityLifecycleCallbacks {

    public static volatile gn3 f6612l;

    public final Application f6613c;

    public int f6614h;

    public long f6615i;

    public boolean f6616j;

    public boolean f6617k;

    public gn3(Application application) {
        this.f6613c = application;
        C1853z5 c1853z5 = new C1853z5(this, 5);
        application.registerActivityLifecycleCallbacks(this);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction("android.intent.action.SCREEN_OFF");
        intentFilter.addAction("android.intent.action.SCREEN_ON");
        application.registerReceiver(c1853z5, intentFilter);
    }

    public static long m3798b() {
        long j;
        gn3 gn3Var = f6612l;
        if (gn3Var == null) {
            return 0L;
        }
        synchronized (gn3Var) {
            j = gn3Var.f6615i;
        }
        return j;
    }

    public final void m3799a() {
        boolean z;
        synchronized (this) {
            z = true;
            try {
                this.f6616j = true;
                if (this.f6617k) {
                    this.f6617k = false;
                } else {
                    z = false;
                }
            } catch (Throwable th) {
                throw th;
            }
        }
        if (z) {
            try {
                Application application = this.f6613c;
                int i = DLNARendererService.f3012s;
                application.stopService(new Intent(application, (Class<?>) DLNARendererService.class));
            } catch (RuntimeException unused) {
            }
        }
    }

    public final void m3800c() {
        synchronized (this) {
            try {
                if (this.f6616j) {
                    this.f6616j = false;
                    this.f6615i++;
                }
            } catch (Throwable th) {
                throw th;
            }
        }
    }

    @Override
    public final void onActivityResumed(Activity activity) {
        boolean z;
        synchronized (this) {
            try {
                z = this.f6617k;
                if (!z) {
                    this.f6617k = true;
                }
            } catch (Throwable th) {
                throw th;
            }
        }
        if (z) {
            return;
        }
        try {
            Application application = this.f6613c;
            int i = DLNARendererService.f3012s;
            application.startService(new Intent(application, (Class<?>) DLNARendererService.class));
        } catch (RuntimeException unused) {
            synchronized (this) {
                this.f6617k = false;
            }
        }
    }

    @Override
    public final void onActivityStarted(Activity activity) {
        boolean z;
        synchronized (this) {
            z = true;
            int i = this.f6614h + 1;
            this.f6614h = i;
            if (i != 1) {
                z = false;
            }
        }
        if (z) {
            m3800c();
        }
    }

    @Override
    public final void onActivityStopped(Activity activity) {
        boolean z;
        synchronized (this) {
            z = true;
            int iMax = Math.max(0, this.f6614h - 1);
            this.f6614h = iMax;
            if (iMax != 0) {
                z = false;
            }
        }
        if (!z || activity.isChangingConfigurations()) {
            return;
        }
        m3799a();
    }

    @Override public final void onActivityDestroyed(Activity activity) {}
    @Override public final void onActivityPaused(Activity activity) {}
    @Override public final void onActivityCreated(Activity activity, Bundle bundle) {}
    @Override public final void onActivitySaveInstanceState(Activity activity, Bundle bundle) {}
}
