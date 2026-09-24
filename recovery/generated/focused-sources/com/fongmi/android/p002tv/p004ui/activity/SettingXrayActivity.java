package com.fongmi.android.p002tv.p004ui.activity;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import androidx.appcompat.widget.LinearLayoutCompat;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.p004ui.activity.PushActivity;
import com.fongmi.android.p002tv.p004ui.activity.SettingXrayActivity;
import com.fongmi.android.p002tv.p004ui.custom.CustomEditText;
import com.google.android.material.materialswitch.MaterialSwitch;
import com.google.android.material.textview.MaterialTextView;
import org.greenrobot.eventbus.ThreadMode;
import p000.AbstractActivityC1828yh;
import p000.C1519q4;
import p000.a04;
import p000.d81;
import p000.fz3;
import p000.h00;
import p000.hz3;
import p000.kz3;
import p000.lu2;
import p000.lz3;
import p000.mz3;
import p000.ps3;
import p000.rc2;
import p000.rw1;
import p000.rz3;
import p000.v93;

public final class SettingXrayActivity extends AbstractActivityC1828yh implements fz3 {

    public static final int f3136P = 0;

    public C1519q4 f3137F;

    public lu2 f3138G;

    public hz3 f3139H;

    public long f3140I;

    public String f3141J;

    public boolean f3142K;

    public boolean f3143L;

    public int f3144M = -1;

    public long f3145N = Long.MIN_VALUE;

    public final rc2 f3146O = new rc2(this, 15);

    @Override
    public final void mo2028B(rz3 rz3Var) {
        if (rz3Var.f16224c != this.f3140I) {
            return;
        }
        m2029K0();
        int i = this.f3144M;
        this.f3143L = false;
        this.f3144M = -1;
        d81.m2567k();
        if (i == 2 && !m2030L0()) {
            d81.m2564T(R.string.xray_changed_retry);
            m2031M0();
            return;
        }
        if (!rz3Var.f16226i) {
            d81.m2565U(rz3Var.f16229l);
            m2031M0();
            return;
        }
        int i2 = rz3Var.f16225h;
        if (i2 == 5) {
            d81.m2564T(R.string.xray_deleted);
            m2031M0();
        } else if (i2 == 2) {
            d81.m2565U(getString(R.string.xray_test_success, Long.valueOf(rz3Var.f16228k)));
            m2031M0();
        }
    }

    @Override
    public final ps3 mo1948E0() {
        View viewInflate = getLayoutInflater().inflate(R.layout.activity_setting_xray, (ViewGroup) null, false);
        int i = R.id.delete;
        MaterialTextView materialTextView = (MaterialTextView) rw1.m8781l(R.id.delete, viewInflate);
        if (materialTextView != null) {
            i = R.id.link;
            CustomEditText customEditText = (CustomEditText) rw1.m8781l(R.id.link, viewInflate);
            if (customEditText != null) {
                i = R.id.phone;
                MaterialTextView materialTextView2 = (MaterialTextView) rw1.m8781l(R.id.phone, viewInflate);
                if (materialTextView2 != null) {
                    i = R.id.save;
                    MaterialTextView materialTextView3 = (MaterialTextView) rw1.m8781l(R.id.save, viewInflate);
                    if (materialTextView3 != null) {
                        i = R.id.test;
                        MaterialTextView materialTextView4 = (MaterialTextView) rw1.m8781l(R.id.test, viewInflate);
                        if (materialTextView4 != null) {
                            i = R.id.udp;
                            LinearLayoutCompat linearLayoutCompat = (LinearLayoutCompat) rw1.m8781l(R.id.udp, viewInflate);
                            if (linearLayoutCompat != null) {
                                i = R.id.udpSwitch;
                                MaterialSwitch materialSwitch = (MaterialSwitch) rw1.m8781l(R.id.udpSwitch, viewInflate);
                                if (materialSwitch != null) {
                                    C1519q4 c1519q4 = new C1519q4((LinearLayoutCompat) viewInflate, materialTextView, customEditText, materialTextView2, materialTextView3, materialTextView4, linearLayoutCompat, materialSwitch);
                                    this.f3137F = c1519q4;
                                    return c1519q4;
                                }
                            }
                        }
                    }
                }
            }
        }
        h00.m3905e("Missing required view with ID: ".concat(viewInflate.getResources().getResourceName(i)));
        return null;
    }

    @Override
    public final void mo1951F0() {
        final int i = 0;
        ((LinearLayoutCompat) this.f3137F.f14614n).setOnClickListener(new View.OnClickListener(this) {

            public final SettingXrayActivity f21707h;

            {
                this.f21707h = this;
            }

            @Override
            public final void onClick(View view) {
                int i2 = i;
                final int i3 = 0;
                final int i4 = 1;
                final SettingXrayActivity settingXrayActivity = this.f21707h;
                switch (i2) {
                    case 0:
                        int i5 = SettingXrayActivity.f3136P;
                        MaterialSwitch materialSwitch = (MaterialSwitch) settingXrayActivity.f3137F.f14615o;
                        materialSwitch.setChecked(!materialSwitch.isChecked());
                        return;
                    case 1:
                        int i6 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L && settingXrayActivity.f3144M == 5) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3138G.m5934f(a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString()), ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked());
                            d81.m2564T(R.string.xray_saved);
                            return;
                        } catch (Exception e) {
                            d81.m2565U(kz3.m5738a(e));
                            return;
                        }
                    case 2:
                        int i7 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3141J = a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString());
                            settingXrayActivity.f3142K = ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked();
                            settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                            settingXrayActivity.f3143L = true;
                            settingXrayActivity.f3144M = 2;
                            d81.m2563G(settingXrayActivity);
                            final long j = settingXrayActivity.f3140I;
                            hz3 hz3Var = settingXrayActivity.f3139H;
                            String str = settingXrayActivity.f3141J;
                            boolean z = settingXrayActivity.f3142K;
                            Runnable runnable = new Runnable() {
                                @Override
                                public final void run() {
                                    int i8 = i4;
                                    long j2 = j;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i8) {
                                        case 0:
                                            int i9 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j2) {
                                                settingXrayActivity2.f3145N = j2;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i10 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j2) {
                                                settingXrayActivity2.f3145N = j2;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var) {
                                hz3Var.m4232e(new gz3(j, 2, str, z, runnable));
                            }
                            return;
                        } catch (Exception e2) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2565U(kz3.m5738a(e2));
                            return;
                        }
                    case 3:
                        int i8 = SettingXrayActivity.f3136P;
                        int i9 = PushActivity.f3116G;
                        Intent intent = new Intent(settingXrayActivity, (Class<?>) PushActivity.class);
                        intent.putExtra("tab", 6);
                        settingXrayActivity.startActivity(intent);
                        return;
                    default:
                        int i10 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                        settingXrayActivity.f3143L = true;
                        settingXrayActivity.f3144M = 5;
                        d81.m2563G(settingXrayActivity);
                        settingXrayActivity.m2031M0();
                        try {
                            settingXrayActivity.f3138G.m5930a();
                            ((CustomEditText) settingXrayActivity.f3137F.f14612l).setText("");
                            ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).setChecked(false);
                            final long j2 = settingXrayActivity.f3140I;
                            hz3 hz3Var2 = settingXrayActivity.f3139H;
                            Runnable runnable2 = new Runnable() {
                                @Override
                                public final void run() {
                                    int i11 = i3;
                                    long j3 = j2;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i11) {
                                        case 0:
                                            int i12 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i13 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var2) {
                                hz3Var2.m4232e(new gz3(j2, 5, "", false, runnable2));
                            }
                            return;
                        } catch (Exception e3) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2567k();
                            d81.m2565U(kz3.m5738a(e3));
                            settingXrayActivity.m2031M0();
                            return;
                        }
                }
            }
        });
        final int i2 = 1;
        ((MaterialTextView) this.f3137F.f14610j).setOnClickListener(new View.OnClickListener(this) {

            public final SettingXrayActivity f21707h;

            {
                this.f21707h = this;
            }

            @Override
            public final void onClick(View view) {
                int i3 = i2;
                final int i4 = 0;
                final int i5 = 1;
                final SettingXrayActivity settingXrayActivity = this.f21707h;
                switch (i3) {
                    case 0:
                        int i6 = SettingXrayActivity.f3136P;
                        MaterialSwitch materialSwitch = (MaterialSwitch) settingXrayActivity.f3137F.f14615o;
                        materialSwitch.setChecked(!materialSwitch.isChecked());
                        return;
                    case 1:
                        int i7 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L && settingXrayActivity.f3144M == 5) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3138G.m5934f(a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString()), ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked());
                            d81.m2564T(R.string.xray_saved);
                            return;
                        } catch (Exception e) {
                            d81.m2565U(kz3.m5738a(e));
                            return;
                        }
                    case 2:
                        int i8 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3141J = a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString());
                            settingXrayActivity.f3142K = ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked();
                            settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                            settingXrayActivity.f3143L = true;
                            settingXrayActivity.f3144M = 2;
                            d81.m2563G(settingXrayActivity);
                            final long j = settingXrayActivity.f3140I;
                            hz3 hz3Var = settingXrayActivity.f3139H;
                            String str = settingXrayActivity.f3141J;
                            boolean z = settingXrayActivity.f3142K;
                            Runnable runnable = new Runnable() {
                                @Override
                                public final void run() {
                                    int i11 = i5;
                                    long j3 = j;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i11) {
                                        case 0:
                                            int i12 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i13 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var) {
                                hz3Var.m4232e(new gz3(j, 2, str, z, runnable));
                            }
                            return;
                        } catch (Exception e2) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2565U(kz3.m5738a(e2));
                            return;
                        }
                    case 3:
                        int i9 = SettingXrayActivity.f3136P;
                        int i10 = PushActivity.f3116G;
                        Intent intent = new Intent(settingXrayActivity, (Class<?>) PushActivity.class);
                        intent.putExtra("tab", 6);
                        settingXrayActivity.startActivity(intent);
                        return;
                    default:
                        int i11 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                        settingXrayActivity.f3143L = true;
                        settingXrayActivity.f3144M = 5;
                        d81.m2563G(settingXrayActivity);
                        settingXrayActivity.m2031M0();
                        try {
                            settingXrayActivity.f3138G.m5930a();
                            ((CustomEditText) settingXrayActivity.f3137F.f14612l).setText("");
                            ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).setChecked(false);
                            final long j2 = settingXrayActivity.f3140I;
                            hz3 hz3Var2 = settingXrayActivity.f3139H;
                            Runnable runnable2 = new Runnable() {
                                @Override
                                public final void run() {
                                    int i12 = i4;
                                    long j3 = j2;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i12) {
                                        case 0:
                                            int i13 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i14 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var2) {
                                hz3Var2.m4232e(new gz3(j2, 5, "", false, runnable2));
                            }
                            return;
                        } catch (Exception e3) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2567k();
                            d81.m2565U(kz3.m5738a(e3));
                            settingXrayActivity.m2031M0();
                            return;
                        }
                }
            }
        });
        final int i3 = 2;
        ((MaterialTextView) this.f3137F.f14611k).setOnClickListener(new View.OnClickListener(this) {

            public final SettingXrayActivity f21707h;

            {
                this.f21707h = this;
            }

            @Override
            public final void onClick(View view) {
                int i4 = i3;
                final int i5 = 0;
                final int i6 = 1;
                final SettingXrayActivity settingXrayActivity = this.f21707h;
                switch (i4) {
                    case 0:
                        int i7 = SettingXrayActivity.f3136P;
                        MaterialSwitch materialSwitch = (MaterialSwitch) settingXrayActivity.f3137F.f14615o;
                        materialSwitch.setChecked(!materialSwitch.isChecked());
                        return;
                    case 1:
                        int i8 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L && settingXrayActivity.f3144M == 5) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3138G.m5934f(a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString()), ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked());
                            d81.m2564T(R.string.xray_saved);
                            return;
                        } catch (Exception e) {
                            d81.m2565U(kz3.m5738a(e));
                            return;
                        }
                    case 2:
                        int i9 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3141J = a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString());
                            settingXrayActivity.f3142K = ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked();
                            settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                            settingXrayActivity.f3143L = true;
                            settingXrayActivity.f3144M = 2;
                            d81.m2563G(settingXrayActivity);
                            final long j = settingXrayActivity.f3140I;
                            hz3 hz3Var = settingXrayActivity.f3139H;
                            String str = settingXrayActivity.f3141J;
                            boolean z = settingXrayActivity.f3142K;
                            Runnable runnable = new Runnable() {
                                @Override
                                public final void run() {
                                    int i12 = i6;
                                    long j3 = j;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i12) {
                                        case 0:
                                            int i13 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i14 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var) {
                                hz3Var.m4232e(new gz3(j, 2, str, z, runnable));
                            }
                            return;
                        } catch (Exception e2) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2565U(kz3.m5738a(e2));
                            return;
                        }
                    case 3:
                        int i10 = SettingXrayActivity.f3136P;
                        int i11 = PushActivity.f3116G;
                        Intent intent = new Intent(settingXrayActivity, (Class<?>) PushActivity.class);
                        intent.putExtra("tab", 6);
                        settingXrayActivity.startActivity(intent);
                        return;
                    default:
                        int i12 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                        settingXrayActivity.f3143L = true;
                        settingXrayActivity.f3144M = 5;
                        d81.m2563G(settingXrayActivity);
                        settingXrayActivity.m2031M0();
                        try {
                            settingXrayActivity.f3138G.m5930a();
                            ((CustomEditText) settingXrayActivity.f3137F.f14612l).setText("");
                            ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).setChecked(false);
                            final long j2 = settingXrayActivity.f3140I;
                            hz3 hz3Var2 = settingXrayActivity.f3139H;
                            Runnable runnable2 = new Runnable() {
                                @Override
                                public final void run() {
                                    int i13 = i5;
                                    long j3 = j2;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i13) {
                                        case 0:
                                            int i14 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i15 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var2) {
                                hz3Var2.m4232e(new gz3(j2, 5, "", false, runnable2));
                            }
                            return;
                        } catch (Exception e3) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2567k();
                            d81.m2565U(kz3.m5738a(e3));
                            settingXrayActivity.m2031M0();
                            return;
                        }
                }
            }
        });
        final int i4 = 3;
        ((MaterialTextView) this.f3137F.f14609i).setOnClickListener(new View.OnClickListener(this) {

            public final SettingXrayActivity f21707h;

            {
                this.f21707h = this;
            }

            @Override
            public final void onClick(View view) {
                int i5 = i4;
                final int i6 = 0;
                final int i7 = 1;
                final SettingXrayActivity settingXrayActivity = this.f21707h;
                switch (i5) {
                    case 0:
                        int i8 = SettingXrayActivity.f3136P;
                        MaterialSwitch materialSwitch = (MaterialSwitch) settingXrayActivity.f3137F.f14615o;
                        materialSwitch.setChecked(!materialSwitch.isChecked());
                        return;
                    case 1:
                        int i9 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L && settingXrayActivity.f3144M == 5) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3138G.m5934f(a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString()), ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked());
                            d81.m2564T(R.string.xray_saved);
                            return;
                        } catch (Exception e) {
                            d81.m2565U(kz3.m5738a(e));
                            return;
                        }
                    case 2:
                        int i10 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3141J = a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString());
                            settingXrayActivity.f3142K = ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked();
                            settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                            settingXrayActivity.f3143L = true;
                            settingXrayActivity.f3144M = 2;
                            d81.m2563G(settingXrayActivity);
                            final long j = settingXrayActivity.f3140I;
                            hz3 hz3Var = settingXrayActivity.f3139H;
                            String str = settingXrayActivity.f3141J;
                            boolean z = settingXrayActivity.f3142K;
                            Runnable runnable = new Runnable() {
                                @Override
                                public final void run() {
                                    int i13 = i7;
                                    long j3 = j;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i13) {
                                        case 0:
                                            int i14 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i15 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var) {
                                hz3Var.m4232e(new gz3(j, 2, str, z, runnable));
                            }
                            return;
                        } catch (Exception e2) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2565U(kz3.m5738a(e2));
                            return;
                        }
                    case 3:
                        int i11 = SettingXrayActivity.f3136P;
                        int i12 = PushActivity.f3116G;
                        Intent intent = new Intent(settingXrayActivity, (Class<?>) PushActivity.class);
                        intent.putExtra("tab", 6);
                        settingXrayActivity.startActivity(intent);
                        return;
                    default:
                        int i13 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                        settingXrayActivity.f3143L = true;
                        settingXrayActivity.f3144M = 5;
                        d81.m2563G(settingXrayActivity);
                        settingXrayActivity.m2031M0();
                        try {
                            settingXrayActivity.f3138G.m5930a();
                            ((CustomEditText) settingXrayActivity.f3137F.f14612l).setText("");
                            ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).setChecked(false);
                            final long j2 = settingXrayActivity.f3140I;
                            hz3 hz3Var2 = settingXrayActivity.f3139H;
                            Runnable runnable2 = new Runnable() {
                                @Override
                                public final void run() {
                                    int i14 = i6;
                                    long j3 = j2;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i14) {
                                        case 0:
                                            int i15 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i16 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var2) {
                                hz3Var2.m4232e(new gz3(j2, 5, "", false, runnable2));
                            }
                            return;
                        } catch (Exception e3) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2567k();
                            d81.m2565U(kz3.m5738a(e3));
                            settingXrayActivity.m2031M0();
                            return;
                        }
                }
            }
        });
        final int i5 = 4;
        ((MaterialTextView) this.f3137F.f14608h).setOnClickListener(new View.OnClickListener(this) {

            public final SettingXrayActivity f21707h;

            {
                this.f21707h = this;
            }

            @Override
            public final void onClick(View view) {
                int i6 = i5;
                final int i7 = 0;
                final int i8 = 1;
                final SettingXrayActivity settingXrayActivity = this.f21707h;
                switch (i6) {
                    case 0:
                        int i9 = SettingXrayActivity.f3136P;
                        MaterialSwitch materialSwitch = (MaterialSwitch) settingXrayActivity.f3137F.f14615o;
                        materialSwitch.setChecked(!materialSwitch.isChecked());
                        return;
                    case 1:
                        int i10 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L && settingXrayActivity.f3144M == 5) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3138G.m5934f(a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString()), ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked());
                            d81.m2564T(R.string.xray_saved);
                            return;
                        } catch (Exception e) {
                            d81.m2565U(kz3.m5738a(e));
                            return;
                        }
                    case 2:
                        int i11 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        try {
                            settingXrayActivity.f3141J = a04.m19f(((CustomEditText) settingXrayActivity.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) settingXrayActivity.f3137F.f14612l).getText().toString());
                            settingXrayActivity.f3142K = ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).isChecked();
                            settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                            settingXrayActivity.f3143L = true;
                            settingXrayActivity.f3144M = 2;
                            d81.m2563G(settingXrayActivity);
                            final long j = settingXrayActivity.f3140I;
                            hz3 hz3Var = settingXrayActivity.f3139H;
                            String str = settingXrayActivity.f3141J;
                            boolean z = settingXrayActivity.f3142K;
                            Runnable runnable = new Runnable() {
                                @Override
                                public final void run() {
                                    int i14 = i8;
                                    long j3 = j;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i14) {
                                        case 0:
                                            int i15 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i16 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var) {
                                hz3Var.m4232e(new gz3(j, 2, str, z, runnable));
                            }
                            return;
                        } catch (Exception e2) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2565U(kz3.m5738a(e2));
                            return;
                        }
                    case 3:
                        int i12 = SettingXrayActivity.f3136P;
                        int i13 = PushActivity.f3116G;
                        Intent intent = new Intent(settingXrayActivity, (Class<?>) PushActivity.class);
                        intent.putExtra("tab", 6);
                        settingXrayActivity.startActivity(intent);
                        return;
                    default:
                        int i14 = SettingXrayActivity.f3136P;
                        if (settingXrayActivity.f3143L) {
                            return;
                        }
                        settingXrayActivity.f3140I = lz3.f11083a.incrementAndGet();
                        settingXrayActivity.f3143L = true;
                        settingXrayActivity.f3144M = 5;
                        d81.m2563G(settingXrayActivity);
                        settingXrayActivity.m2031M0();
                        try {
                            settingXrayActivity.f3138G.m5930a();
                            ((CustomEditText) settingXrayActivity.f3137F.f14612l).setText("");
                            ((MaterialSwitch) settingXrayActivity.f3137F.f14615o).setChecked(false);
                            final long j2 = settingXrayActivity.f3140I;
                            hz3 hz3Var2 = settingXrayActivity.f3139H;
                            Runnable runnable2 = new Runnable() {
                                @Override
                                public final void run() {
                                    int i15 = i7;
                                    long j3 = j2;
                                    SettingXrayActivity settingXrayActivity2 = settingXrayActivity;
                                    switch (i15) {
                                        case 0:
                                            int i16 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var);
                                                App.m1882b(rc2Var, 45000L);
                                                break;
                                            }
                                            break;
                                        default:
                                            int i17 = SettingXrayActivity.f3136P;
                                            rc2 rc2Var2 = settingXrayActivity2.f3146O;
                                            if (settingXrayActivity2.f3143L && settingXrayActivity2.f3140I == j3) {
                                                settingXrayActivity2.f3145N = j3;
                                                App.m1883c(rc2Var2);
                                                App.m1882b(rc2Var2, 45000L);
                                                break;
                                            }
                                            break;
                                    }
                                }
                            };
                            synchronized (hz3Var2) {
                                hz3Var2.m4232e(new gz3(j2, 5, "", false, runnable2));
                            }
                            return;
                        } catch (Exception e3) {
                            settingXrayActivity.m2029K0();
                            settingXrayActivity.f3143L = false;
                            settingXrayActivity.f3144M = -1;
                            d81.m2567k();
                            d81.m2565U(kz3.m5738a(e3));
                            settingXrayActivity.m2031M0();
                            return;
                        }
                }
            }
        });
    }

    @Override
    public final void mo206G0(Bundle bundle) {
        boolean z;
        this.f3138G = new lu2((AbstractActivityC1828yh) this);
        this.f3139H = new hz3(this, this);
        MaterialSwitch materialSwitch = (MaterialSwitch) this.f3137F.f14615o;
        lu2 lu2Var = this.f3138G;
        synchronized (lu2Var) {
            z = ((SharedPreferences) lu2Var.f10948a).getBoolean("udp", false);
        }
        materialSwitch.setChecked(z);
        try {
            ((CustomEditText) this.f3137F.f14612l).setText(this.f3138G.m5933e());
            CustomEditText customEditText = (CustomEditText) this.f3137F.f14612l;
            customEditText.setSelection(customEditText.length());
        } catch (Exception e) {
            d81.m2565U(kz3.m5738a(e));
        }
        ((CustomEditText) this.f3137F.f14612l).requestFocus();
    }

    public final void m2029K0() {
        this.f3145N = Long.MIN_VALUE;
        App.m1883c(this.f3146O);
    }

    public final boolean m2030L0() {
        try {
            return a04.m19f(((CustomEditText) this.f3137F.f14612l).getText() == null ? "" : ((CustomEditText) this.f3137F.f14612l).getText().toString()).equals(this.f3141J) && ((MaterialSwitch) this.f3137F.f14615o).isChecked() == this.f3142K;
        } catch (Exception unused) {
            return false;
        }
    }

    public final void m2031M0() {
        hz3 hz3Var = this.f3139H;
        if (hz3Var != null) {
            hz3Var.m4228a();
        }
        this.f3139H = new hz3(this, this);
    }

    @Override
    public final void mo2032Y(long j, String str) {
        if (j != this.f3140I) {
            return;
        }
        m2029K0();
        int i = this.f3144M;
        this.f3143L = false;
        this.f3144M = -1;
        d81.m2567k();
        if (i != 2 || m2030L0()) {
            d81.m2565U(str);
        } else {
            d81.m2564T(R.string.xray_changed_retry);
        }
        m2031M0();
    }

    @Override
    public final void onDestroy() {
        m2029K0();
        this.f3140I = lz3.f11083a.incrementAndGet();
        this.f3143L = false;
        this.f3144M = -1;
        hz3 hz3Var = this.f3139H;
        if (hz3Var != null) {
            hz3Var.m4228a();
        }
        d81.m2567k();
        super.onDestroy();
    }

    @v93(threadMode = ThreadMode.MAIN)
    public void onXrayImportEvent(mz3 mz3Var) {
        String str;
        if (mz3Var == null || (str = mz3Var.f11870c) == null) {
            return;
        }
        int length = str.length();
        int iCharCount = 0;
        while (iCharCount < length) {
            int iCodePointAt = str.codePointAt(iCharCount);
            if (!Character.isWhitespace(iCodePointAt)) {
                if (this.f3143L && this.f3144M != 5) {
                    m2029K0();
                    this.f3140I = lz3.f11083a.incrementAndGet();
                    this.f3143L = false;
                    this.f3144M = -1;
                    d81.m2567k();
                    m2031M0();
                }
                ((CustomEditText) this.f3137F.f14612l).setText(str.trim());
                CustomEditText customEditText = (CustomEditText) this.f3137F.f14612l;
                customEditText.setSelection(customEditText.length());
                d81.m2564T(R.string.xray_phone_received);
                return;
            }
            iCharCount += Character.charCount(iCodePointAt);
        }
    }
}
