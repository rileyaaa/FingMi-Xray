package com.fongmi.android.p002tv.p004ui.activity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import androidx.appcompat.widget.AppCompatImageView;
import androidx.appcompat.widget.LinearLayoutCompat;
import androidx.core.widget.NestedScrollView;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.bean.Config;
import com.fongmi.android.p002tv.bean.Live;
import com.fongmi.android.p002tv.bean.Site;
import com.fongmi.android.p002tv.p004ui.activity.SettingActivity;
import com.fongmi.android.p002tv.p004ui.activity.SettingDanmakuActivity;
import com.fongmi.android.p002tv.p004ui.activity.SettingPlayerActivity;
import com.fongmi.android.p002tv.p004ui.activity.SettingXrayActivity;
import com.google.android.material.textview.MaterialTextView;
import com.google.gson.Gson;
import java.util.ArrayList;
import java.util.Iterator;
import org.greenrobot.eventbus.ThreadMode;
import p000.AbstractActivityC1828yh;
import p000.AbstractC0463d2;
import p000.C0532ez;
import p000.C1139m4;
import p000.EnumC0495dz;
import p000.InterfaceC0571fz;
import p000.a04;
import p000.ek1;
import p000.ep2;
import p000.gp0;
import p000.h00;
import p000.ho0;
import p000.id3;
import p000.l33;
import p000.lu2;
import p000.np3;
import p000.nw3;
import p000.ow3;
import p000.p11;
import p000.ps3;
import p000.qz2;
import p000.rw1;
import p000.sz2;
import p000.tp3;
import p000.uv3;
import p000.v93;
import p000.vj1;
import p000.vv3;
import p000.wj1;
import p000.xh0;
import p000.yd0;
import p000.yu2;

public class SettingActivity extends AbstractActivityC1828yh implements InterfaceC0571fz, l33, ek1 {

    public static final int f3122H = 0;

    public C1139m4 f3123F;

    public String[] f3124G;

    @Override
    public final ps3 mo1948E0() {
        View viewInflate = getLayoutInflater().inflate(R.layout.activity_setting, (ViewGroup) null, false);
        int i = R.id.backup;
        LinearLayoutCompat linearLayoutCompat = (LinearLayoutCompat) rw1.m8781l(R.id.backup, viewInflate);
        if (linearLayoutCompat != null) {
            i = R.id.cache;
            LinearLayoutCompat linearLayoutCompat2 = (LinearLayoutCompat) rw1.m8781l(R.id.cache, viewInflate);
            if (linearLayoutCompat2 != null) {
                i = R.id.cacheText;
                MaterialTextView materialTextView = (MaterialTextView) rw1.m8781l(R.id.cacheText, viewInflate);
                if (materialTextView != null) {
                    i = R.id.danmaku;
                    LinearLayoutCompat linearLayoutCompat3 = (LinearLayoutCompat) rw1.m8781l(R.id.danmaku, viewInflate);
                    if (linearLayoutCompat3 != null) {
                        i = R.id.doh;
                        LinearLayoutCompat linearLayoutCompat4 = (LinearLayoutCompat) rw1.m8781l(R.id.doh, viewInflate);
                        if (linearLayoutCompat4 != null) {
                            i = R.id.dohText;
                            MaterialTextView materialTextView2 = (MaterialTextView) rw1.m8781l(R.id.dohText, viewInflate);
                            if (materialTextView2 != null) {
                                i = R.id.incognito;
                                LinearLayoutCompat linearLayoutCompat5 = (LinearLayoutCompat) rw1.m8781l(R.id.incognito, viewInflate);
                                if (linearLayoutCompat5 != null) {
                                    i = R.id.incognitoText;
                                    MaterialTextView materialTextView3 = (MaterialTextView) rw1.m8781l(R.id.incognitoText, viewInflate);
                                    if (materialTextView3 != null) {
                                        i = R.id.live;
                                        LinearLayoutCompat linearLayoutCompat6 = (LinearLayoutCompat) rw1.m8781l(R.id.live, viewInflate);
                                        if (linearLayoutCompat6 != null) {
                                            i = R.id.liveHistory;
                                            AppCompatImageView appCompatImageView = (AppCompatImageView) rw1.m8781l(R.id.liveHistory, viewInflate);
                                            if (appCompatImageView != null) {
                                                i = R.id.liveHome;
                                                AppCompatImageView appCompatImageView2 = (AppCompatImageView) rw1.m8781l(R.id.liveHome, viewInflate);
                                                if (appCompatImageView2 != null) {
                                                    i = R.id.liveUrl;
                                                    MaterialTextView materialTextView4 = (MaterialTextView) rw1.m8781l(R.id.liveUrl, viewInflate);
                                                    if (materialTextView4 != null) {
                                                        i = R.id.player;
                                                        LinearLayoutCompat linearLayoutCompat7 = (LinearLayoutCompat) rw1.m8781l(R.id.player, viewInflate);
                                                        if (linearLayoutCompat7 != null) {
                                                            i = R.id.restore;
                                                            LinearLayoutCompat linearLayoutCompat8 = (LinearLayoutCompat) rw1.m8781l(R.id.restore, viewInflate);
                                                            if (linearLayoutCompat8 != null) {
                                                                i = R.id.size;
                                                                LinearLayoutCompat linearLayoutCompat9 = (LinearLayoutCompat) rw1.m8781l(R.id.size, viewInflate);
                                                                if (linearLayoutCompat9 != null) {
                                                                    i = R.id.sizeText;
                                                                    MaterialTextView materialTextView5 = (MaterialTextView) rw1.m8781l(R.id.sizeText, viewInflate);
                                                                    if (materialTextView5 != null) {
                                                                        i = R.id.version;
                                                                        if (((LinearLayoutCompat) rw1.m8781l(R.id.version, viewInflate)) != null) {
                                                                            i = R.id.versionText;
                                                                            MaterialTextView materialTextView6 = (MaterialTextView) rw1.m8781l(R.id.versionText, viewInflate);
                                                                            if (materialTextView6 != null) {
                                                                                i = R.id.vod;
                                                                                LinearLayoutCompat linearLayoutCompat10 = (LinearLayoutCompat) rw1.m8781l(R.id.vod, viewInflate);
                                                                                if (linearLayoutCompat10 != null) {
                                                                                    i = R.id.vodHistory;
                                                                                    AppCompatImageView appCompatImageView3 = (AppCompatImageView) rw1.m8781l(R.id.vodHistory, viewInflate);
                                                                                    if (appCompatImageView3 != null) {
                                                                                        i = R.id.vodHome;
                                                                                        AppCompatImageView appCompatImageView4 = (AppCompatImageView) rw1.m8781l(R.id.vodHome, viewInflate);
                                                                                        if (appCompatImageView4 != null) {
                                                                                            i = R.id.vodUrl;
                                                                                            MaterialTextView materialTextView7 = (MaterialTextView) rw1.m8781l(R.id.vodUrl, viewInflate);
                                                                                            if (materialTextView7 != null) {
                                                                                                i = R.id.wall;
                                                                                                LinearLayoutCompat linearLayoutCompat11 = (LinearLayoutCompat) rw1.m8781l(R.id.wall, viewInflate);
                                                                                                if (linearLayoutCompat11 != null) {
                                                                                                    i = R.id.wallDefault;
                                                                                                    AppCompatImageView appCompatImageView5 = (AppCompatImageView) rw1.m8781l(R.id.wallDefault, viewInflate);
                                                                                                    if (appCompatImageView5 != null) {
                                                                                                        i = R.id.wallRefresh;
                                                                                                        AppCompatImageView appCompatImageView6 = (AppCompatImageView) rw1.m8781l(R.id.wallRefresh, viewInflate);
                                                                                                        if (appCompatImageView6 != null) {
                                                                                                            i = R.id.wallUrl;
                                                                                                            MaterialTextView materialTextView8 = (MaterialTextView) rw1.m8781l(R.id.wallUrl, viewInflate);
                                                                                                            if (materialTextView8 != null) {
                                                                                                                i = R.id.xray;
                                                                                                                LinearLayoutCompat linearLayoutCompat12 = (LinearLayoutCompat) rw1.m8781l(R.id.xray, viewInflate);
                                                                                                                if (linearLayoutCompat12 != null) {
                                                                                                                    i = R.id.xrayText;
                                                                                                                    MaterialTextView materialTextView9 = (MaterialTextView) rw1.m8781l(R.id.xrayText, viewInflate);
                                                                                                                    if (materialTextView9 != null) {
                                                                                                                        C1139m4 c1139m4 = new C1139m4((NestedScrollView) viewInflate, linearLayoutCompat, linearLayoutCompat2, materialTextView, linearLayoutCompat3, linearLayoutCompat4, materialTextView2, linearLayoutCompat5, materialTextView3, linearLayoutCompat6, appCompatImageView, appCompatImageView2, materialTextView4, linearLayoutCompat7, linearLayoutCompat8, linearLayoutCompat9, materialTextView5, materialTextView6, linearLayoutCompat10, appCompatImageView3, appCompatImageView4, materialTextView7, linearLayoutCompat11, appCompatImageView5, appCompatImageView6, materialTextView8, linearLayoutCompat12, materialTextView9);
                                                                                                                        this.f3123F = c1139m4;
                                                                                                                        return c1139m4;
                                                                                                                    }
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
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
        this.f3123F.f11179y.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i2 = i;
                SettingActivity settingActivity = this.f14522h;
                switch (i2) {
                    case 0:
                        int i3 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i4 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i5 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i6 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i7 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i8 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i9 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i10 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i11 = SettingActivity.f3122H;
                        int i12 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i13 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i14 = SettingActivity.f3122H;
                        int i15 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i16 = SettingActivity.f3122H;
                        int i17 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i18 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i19 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i2 = 1;
        this.f3123F.f11166l.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i3 = i2;
                SettingActivity settingActivity = this.f14522h;
                switch (i3) {
                    case 0:
                        int i4 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i5 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i6 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i7 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i8 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i9 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i10 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i11 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i12 = SettingActivity.f3122H;
                        int i13 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i14 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i15 = SettingActivity.f3122H;
                        int i16 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i17 = SettingActivity.f3122H;
                        int i18 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i19 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i110 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i3 = 3;
        this.f3123F.f11170p.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i4 = i3;
                SettingActivity settingActivity = this.f14522h;
                switch (i4) {
                    case 0:
                        int i5 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i6 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i7 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i8 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i9 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i10 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i11 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i12 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i13 = SettingActivity.f3122H;
                        int i14 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i15 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i16 = SettingActivity.f3122H;
                        int i17 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i18 = SettingActivity.f3122H;
                        int i19 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i110 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i111 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i4 = 4;
        this.f3123F.f11155C.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i5 = i4;
                SettingActivity settingActivity = this.f14522h;
                switch (i5) {
                    case 0:
                        int i6 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i7 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i8 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i9 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i10 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i11 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i12 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i13 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i14 = SettingActivity.f3122H;
                        int i15 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i16 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i17 = SettingActivity.f3122H;
                        int i18 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i19 = SettingActivity.f3122H;
                        int i110 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i111 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i112 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i5 = 5;
        this.f3123F.f11176v.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i6 = i5;
                SettingActivity settingActivity = this.f14522h;
                switch (i6) {
                    case 0:
                        int i7 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i8 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i9 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i10 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i11 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i12 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i13 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i14 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i15 = SettingActivity.f3122H;
                        int i16 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i17 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i18 = SettingActivity.f3122H;
                        int i19 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i110 = SettingActivity.f3122H;
                        int i111 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i112 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i113 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i6 = 6;
        this.f3123F.f11163i.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i7 = i6;
                SettingActivity settingActivity = this.f14522h;
                switch (i7) {
                    case 0:
                        int i8 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i9 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i10 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i11 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i12 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i13 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i14 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i15 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i16 = SettingActivity.f3122H;
                        int i17 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i18 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i19 = SettingActivity.f3122H;
                        int i110 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i111 = SettingActivity.f3122H;
                        int i112 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i113 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i114 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i7 = 7;
        this.f3123F.f11162h.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i8 = i7;
                SettingActivity settingActivity = this.f14522h;
                switch (i8) {
                    case 0:
                        int i9 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i10 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i11 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i12 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i13 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i14 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i15 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i16 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i17 = SettingActivity.f3122H;
                        int i18 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i19 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i110 = SettingActivity.f3122H;
                        int i111 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i112 = SettingActivity.f3122H;
                        int i113 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i114 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i115 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i8 = 8;
        this.f3123F.f11174t.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i9 = i8;
                SettingActivity settingActivity = this.f14522h;
                switch (i9) {
                    case 0:
                        int i10 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i11 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i12 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i13 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i14 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i15 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i16 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i17 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i18 = SettingActivity.f3122H;
                        int i19 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i110 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i111 = SettingActivity.f3122H;
                        int i112 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i113 = SettingActivity.f3122H;
                        int i114 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i115 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i116 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i9 = 10;
        this.f3123F.f11165k.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i10 = i9;
                SettingActivity settingActivity = this.f14522h;
                switch (i10) {
                    case 0:
                        int i11 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i12 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i13 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i14 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i15 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i16 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i17 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i18 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i19 = SettingActivity.f3122H;
                        int i110 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i111 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i112 = SettingActivity.f3122H;
                        int i113 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i114 = SettingActivity.f3122H;
                        int i115 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i116 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i117 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i10 = 11;
        this.f3123F.f11159G.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i11 = i10;
                SettingActivity settingActivity = this.f14522h;
                switch (i11) {
                    case 0:
                        int i12 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i13 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i14 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i15 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i16 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i17 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i18 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i19 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i110 = SettingActivity.f3122H;
                        int i111 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i112 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i113 = SettingActivity.f3122H;
                        int i114 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i115 = SettingActivity.f3122H;
                        int i116 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i117 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i118 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i11 = 9;
        this.f3123F.f11175u.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i12 = i11;
                SettingActivity settingActivity = this.f14522h;
                switch (i12) {
                    case 0:
                        int i13 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i14 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i15 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i16 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i17 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i18 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i19 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i110 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i111 = SettingActivity.f3122H;
                        int i112 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i113 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i114 = SettingActivity.f3122H;
                        int i115 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i116 = SettingActivity.f3122H;
                        int i117 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i118 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i119 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        this.f3123F.f11179y.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final SettingActivity f16223h;

            {
                this.f16223h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i12 = i2;
                SettingActivity settingActivity = this.f16223h;
                switch (i12) {
                    case 0:
                        int i13 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 2;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i14 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.f3825v0 = true;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i15 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.f3825v0 = true;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i16 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.f3825v0 = true;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                }
                return true;
            }
        });
        final int i12 = 12;
        this.f3123F.f11153A.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i13 = i12;
                SettingActivity settingActivity = this.f14522h;
                switch (i13) {
                    case 0:
                        int i14 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i15 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i16 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i17 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i18 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i19 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i110 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i111 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i112 = SettingActivity.f3122H;
                        int i113 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i114 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i115 = SettingActivity.f3122H;
                        int i116 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i117 = SettingActivity.f3122H;
                        int i118 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i119 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i1110 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i13 = 2;
        this.f3123F.f11170p.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final SettingActivity f16223h;

            {
                this.f16223h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i14 = i13;
                SettingActivity settingActivity = this.f16223h;
                switch (i14) {
                    case 0:
                        int i15 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 2;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i16 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.f3825v0 = true;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i17 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.f3825v0 = true;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i18 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.f3825v0 = true;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                }
                return true;
            }
        });
        final int i14 = 13;
        this.f3123F.f11172r.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i15 = i14;
                SettingActivity settingActivity = this.f14522h;
                switch (i15) {
                    case 0:
                        int i16 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i17 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i18 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i19 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i110 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i111 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i112 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i113 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i114 = SettingActivity.f3122H;
                        int i115 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i116 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i117 = SettingActivity.f3122H;
                        int i118 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i119 = SettingActivity.f3122H;
                        int i1110 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i1111 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i1112 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        this.f3123F.f11155C.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final SettingActivity f16223h;

            {
                this.f16223h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i15 = i3;
                SettingActivity settingActivity = this.f16223h;
                switch (i15) {
                    case 0:
                        int i16 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 2;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i17 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.f3825v0 = true;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i18 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.f3825v0 = true;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i19 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.f3825v0 = true;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                }
                return true;
            }
        });
        final int i15 = 14;
        this.f3123F.f11168n.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i16 = i15;
                SettingActivity settingActivity = this.f14522h;
                switch (i16) {
                    case 0:
                        int i17 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i18 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i19 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i110 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i111 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i112 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i113 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i114 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i115 = SettingActivity.f3122H;
                        int i116 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i117 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i118 = SettingActivity.f3122H;
                        int i119 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i1110 = SettingActivity.f3122H;
                        int i1111 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i1112 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i1113 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i16 = 15;
        this.f3123F.f11180z.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i17 = i16;
                SettingActivity settingActivity = this.f14522h;
                switch (i17) {
                    case 0:
                        int i18 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i19 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i110 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i111 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i112 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i113 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i114 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i115 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i116 = SettingActivity.f3122H;
                        int i117 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i118 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i119 = SettingActivity.f3122H;
                        int i1110 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i1111 = SettingActivity.f3122H;
                        int i1112 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i1113 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i1114 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        final int i17 = 16;
        this.f3123F.f11171q.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i18 = i17;
                SettingActivity settingActivity = this.f14522h;
                switch (i18) {
                    case 0:
                        int i19 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i110 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i111 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i112 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i113 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i114 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i115 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i116 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i117 = SettingActivity.f3122H;
                        int i118 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i119 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i1110 = SettingActivity.f3122H;
                        int i1111 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i1112 = SettingActivity.f3122H;
                        int i1113 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i1114 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i1115 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        this.f3123F.f11156D.setOnClickListener(new qz2());
        this.f3123F.f11157E.setOnClickListener(new View.OnClickListener(this) {

            public final SettingActivity f14522h;

            {
                this.f14522h = this;
            }

            @Override
            public final void onClick(View view) {
                int i18 = i13;
                SettingActivity settingActivity = this.f14522h;
                switch (i18) {
                    case 0:
                        int i19 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i110 = SettingActivity.f3122H;
                        ai0 ai0Var = new ai0();
                        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
                        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
                        if (xh0Var == null) {
                            xh0Var = new xh0();
                        }
                        ai0Var.f376v0 = Math.max(0, arrayListM10213p.indexOf(xh0Var));
                        ai0Var.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i111 = SettingActivity.f3122H;
                        tp3.m9413U(0);
                        nw3.f12568a.m3163h(new sz2(settingActivity, 1));
                        break;
                    case 3:
                        int i112 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    case 4:
                        int i113 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                    case 5:
                        int i114 = SettingActivity.f3122H;
                        int iM6613U = np3.m6613U() + 1;
                        String[] strArr = settingActivity.f3124G;
                        int length = iM6613U % strArr.length;
                        settingActivity.f3123F.f11177w.setText(strArr[length]);
                        p11.m7580P(Integer.valueOf((int) Math.min(3L, Math.max(length, 0L))), "size");
                        gp0.m3810b().m3813e(new ep2(5));
                        break;
                    case 6:
                        int i115 = SettingActivity.f3122H;
                        id3.m4301a(new du0(new sz2(settingActivity, 2), 0));
                        break;
                    case 7:
                        int i116 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new jf2(settingActivity));
                        break;
                    case 8:
                        int i117 = SettingActivity.f3122H;
                        int i118 = SettingPlayerActivity.f3129J;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingPlayerActivity.class));
                        break;
                    case 9:
                        int i119 = SettingActivity.f3122H;
                        AbstractC0463d2.m2465j(settingActivity, new C1206nh(settingActivity, 18));
                        break;
                    case 10:
                        int i1110 = SettingActivity.f3122H;
                        int i1111 = SettingDanmakuActivity.f3125G;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingDanmakuActivity.class));
                        break;
                    case 11:
                        int i1112 = SettingActivity.f3122H;
                        int i1113 = SettingXrayActivity.f3136P;
                        settingActivity.startActivity(new Intent(settingActivity, (Class<?>) SettingXrayActivity.class));
                        break;
                    case 12:
                        int i1114 = SettingActivity.f3122H;
                        k33 k33Var = new k33();
                        k33Var.f9602x0 = true;
                        k33Var.m5224i0(settingActivity);
                        break;
                    case 13:
                        int i1115 = SettingActivity.f3122H;
                        dk1 dk1Var = new dk1();
                        dk1Var.f4273v0 = true;
                        dk1Var.m266W(settingActivity.m6086w0());
                        break;
                    case 14:
                        int i20 = SettingActivity.f3122H;
                        p11.m7580P(Boolean.valueOf(!tp3.m9403I()), "incognito");
                        settingActivity.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
                        break;
                    case 15:
                        int i21 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 0;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i22 = SettingActivity.f3122H;
                        v41 v41Var2 = new v41();
                        v41Var2.f18907w0 = 1;
                        v41Var2.m266W(settingActivity.m6086w0());
                        break;
                }
            }
        });
        this.f3123F.f11157E.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final SettingActivity f16223h;

            {
                this.f16223h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i18 = i;
                SettingActivity settingActivity = this.f16223h;
                switch (i18) {
                    case 0:
                        int i19 = SettingActivity.f3122H;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 2;
                        v41Var.m266W(settingActivity.m6086w0());
                        break;
                    case 1:
                        int i110 = SettingActivity.f3122H;
                        C0459cz c0459cz = new C0459cz();
                        c0459cz.f3827x0 = 0;
                        c0459cz.f3825v0 = true;
                        c0459cz.m266W(settingActivity.m6086w0());
                        break;
                    case 2:
                        int i111 = SettingActivity.f3122H;
                        C0459cz c0459cz2 = new C0459cz();
                        c0459cz2.f3827x0 = 1;
                        c0459cz2.f3825v0 = true;
                        c0459cz2.m266W(settingActivity.m6086w0());
                        break;
                    default:
                        int i112 = SettingActivity.f3122H;
                        C0459cz c0459cz3 = new C0459cz();
                        c0459cz3.f3827x0 = 2;
                        c0459cz3.f3825v0 = true;
                        c0459cz3.m266W(settingActivity.m6086w0());
                        break;
                }
                return true;
            }
        });
    }

    @Override
    public final void mo206G0(Bundle bundle) {
        this.f3123F.f11179y.requestFocus();
        this.f3123F.f11154B.setText(uv3.f18675a.m3160e().getDesc());
        this.f3123F.f11173s.setText(vj1.f19277a.m3160e().getDesc());
        this.f3123F.f11158F.setText(nw3.f12568a.m3160e().getDesc());
        this.f3123F.f11178x.setText("5.6.0-xray.5");
        id3.m4301a(new yd0(new sz2(this, 0), 12));
        m2020L0();
        m2021M0();
    }

    @Override
    public final void mo1971H(Site site) {
        vv3 vv3Var = uv3.f18675a;
        vv3Var.m10218v(vv3Var.m3160e(), site, true);
        gp0.m3810b().m3813e(new ep2(1));
    }

    public final void m2019K0(Config config) {
        int type = config.getType();
        int i = 1;
        if (type == 0) {
            vv3.m10211u(config, new sz2(this, i));
            return;
        }
        if (type != 1) {
            if (type != 2) {
                return;
            }
            tp3.m9413U(0);
            sz2 sz2Var = new sz2(this, i);
            ow3 ow3Var = nw3.f12568a;
            ow3Var.m7521n(config);
            ow3Var.m3163h(sz2Var);
            return;
        }
        sz2 sz2Var2 = new sz2(this, i);
        wj1 wj1Var = vj1.f19277a;
        wj1Var.f20116h = null;
        wj1Var.f20113e = null;
        wj1Var.f20114f = null;
        wj1Var.f20115g = null;
        yu2.f21617a.f2445h = true;
        wj1Var.m10371n(config);
        wj1Var.m3163h(sz2Var2);
    }

    public final void m2020L0() {
        MaterialTextView materialTextView = this.f3123F.f11167m;
        ArrayList arrayList = new ArrayList();
        Iterator it = uv3.f18675a.m10213p().iterator();
        while (it.hasNext()) {
            arrayList.add(((xh0) it.next()).m10548c());
        }
        String[] strArr = (String[]) arrayList.toArray(new String[0]);
        ArrayList arrayListM10213p = uv3.f18675a.m10213p();
        xh0 xh0Var = (xh0) new Gson().fromJson(p11.m7615v("doh"), xh0.class);
        if (xh0Var == null) {
            xh0Var = new xh0();
        }
        materialTextView.setText(strArr[Math.max(0, arrayListM10213p.indexOf(xh0Var))]);
        this.f3123F.f11169o.setText(tp3.m9397C(tp3.m9403I()));
        MaterialTextView materialTextView2 = this.f3123F.f11177w;
        String[] strArrM2463h = AbstractC0463d2.m2463h(R.array.select_size);
        this.f3124G = strArrM2463h;
        materialTextView2.setText(strArrM2463h[np3.m6613U()]);
    }

    public final void m2021M0() {
        try {
            lu2 lu2Var = new lu2((AbstractActivityC1828yh) this);
            this.f3123F.f11160H.setText(lu2Var.m5932d() ? a04.m20g(lu2Var.m5933e()) : getString(R.string.xray_not_configured));
        } catch (Exception unused) {
            this.f3123F.f11160H.setText(R.string.xray_not_configured);
        }
    }

    @Override
    public final void mo2008j(Live live) {
        wj1 wj1Var = vj1.f19277a;
        wj1Var.m10375r(wj1Var.m3160e(), live, true);
    }

    @v93(threadMode = ThreadMode.MAIN)
    public void onConfigEvent(C0532ez c0532ez) {
        if (c0532ez.f5394c != EnumC0495dz.f4515c) {
            return;
        }
        this.f3123F.f11154B.setText(uv3.f18675a.m3160e().getDesc());
        this.f3123F.f11173s.setText(vj1.f19277a.m3160e().getDesc());
        this.f3123F.f11158F.setText(nw3.f12568a.m3160e().getDesc());
    }

    @Override
    public final void onResume() {
        super.onResume();
        if (this.f3123F != null) {
            m2021M0();
        }
    }

    @Override
    public final void mo2010x(Config config) {
        if (config.getUrl().startsWith("file")) {
            AbstractC0463d2.m2465j(this, new ho0(this, config, 6));
        } else {
            m2019K0(config);
        }
    }
}
