package com.fongmi.android.p002tv.p004ui.activity;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.RelativeLayout;
import androidx.appcompat.widget.AppCompatImageView;
import androidx.appcompat.widget.LinearLayoutCompat;
import androidx.media3.p001ui.PlayerSeekView;
import androidx.media3.p001ui.PlayerView;
import androidx.recyclerview.widget.AbstractC0148q;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.ComponentCallbacks2C0223a;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.bean.Channel;
import com.fongmi.android.p002tv.bean.Config;
import com.fongmi.android.p002tv.bean.Epg;
import com.fongmi.android.p002tv.bean.EpgData;
import com.fongmi.android.p002tv.bean.Group;
import com.fongmi.android.p002tv.bean.Live;
import com.fongmi.android.p002tv.bean.Track;
import com.fongmi.android.p002tv.p004ui.activity.LiveActivity;
import com.fongmi.android.p002tv.p004ui.custom.CustomLiveListView;
import com.fongmi.android.p002tv.p004ui.custom.CustomUpDownView;
import com.google.android.material.textview.MaterialTextView;
import java.net.URI;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Timer;
import kotlin.jvm.JvmClassMappingKt;
import kotlin.reflect.KClass;
import okhttp3.OkHttpClient;
import org.greenrobot.eventbus.ThreadMode;
import org.mozilla.javascript.Token;
import p000.AbstractActivityC1828yh;
import p000.AbstractC0463d2;
import p000.AbstractC1163ml;
import p000.C1088kr;
import p000.C1125lr;
import p000.C1221nv;
import p000.C1566re;
import p000.C1629t3;
import p000.C1777x3;
import p000.C1872zo;
import p000.InterfaceC0571fz;
import p000.RunnableC0662id;
import p000.RunnableC0663ie;
import p000.RunnableC1518q3;
import p000.ViewOnLongClickListenerC0177bf;
import p000.ViewOnTouchListenerC1603se;
import p000.aa3;
import p000.af2;
import p000.bd2;
import p000.bl3;
import p000.bu3;
import p000.c53;
import p000.d53;
import p000.d81;
import p000.ek1;
import p000.eo0;
import p000.ep2;
import p000.er2;
import p000.f30;
import p000.gk1;
import p000.go0;
import p000.gr2;
import p000.h00;
import p000.hc2;
import p000.hd2;
import p000.hj1;
import p000.hk1;
import p000.ht3;
import p000.id3;
import p000.ij1;
import p000.iv3;
import p000.jh2;
import p000.jj1;
import p000.jk1;
import p000.k20;
import p000.k30;
import p000.la2;
import p000.m61;
import p000.mk1;
import p000.n61;
import p000.nk1;
import p000.np3;
import p000.oj1;
import p000.ox0;
import p000.p11;
import p000.pf2;
import p000.ps3;
import p000.pv1;
import p000.rw1;
import p000.th2;
import p000.v11;
import p000.v93;
import p000.vj1;
import p000.wj1;
import p000.xz3;
import p000.yd0;
import p000.yu2;
import p000.yz3;
import p000.zt3;

public class LiveActivity extends af2 implements k30, InterfaceC0571fz, ek1, xz3 {

    public static final int f3089r0 = 0;

    public C1777x3 f3090R;

    public nk1 f3091S;

    public d81 f3092T;

    public go0 f3093U;

    public C1125lr f3094V;

    public go0 f3095W;

    public f30 f3096X;

    public C1872zo f3097Y;

    public View f3098Z;

    public View f3099a0;

    public hj1 f3100b0;

    public hj1 f3101c0;

    public hj1 f3102d0;

    public hj1 f3103e0;

    public hj1 f3104f0;

    public RunnableC0663ie f3105g0;

    public ArrayList f3106h0;

    public Group f3107i0;

    public Channel f3108j0;

    public String f3109k0;

    public int f3110l0;

    public yz3 f3111m0;

    public jj1 f3112n0;

    public boolean f3113o0;

    public boolean f3114p0;

    public final ij1 f3115q0 = new ij1(this);

    public static Live m1980B1() {
        return vj1.f19277a.m10372o();
    }

    public static void m1981a2(Context context) {
        context.startActivity(new Intent(context, (Class<?>) LiveActivity.class).putExtra("empty", vj1.f19277a.m10372o().isEmpty()));
    }

    public final void m1982A1() {
        nk1 nk1Var = this.f3091S;
        if (nk1Var != null) {
            OkHttpClient okHttpClientM1991J1 = m1991J1();
            d81 d81Var = nk1Var.f12315g;
            d81Var.m2592f(mk1.f11469i);
            d81Var.m2592f(mk1.f11468h);
            String str = oj1.f13054a;
            la2.m5790a(la2.m5792c(), str);
            if (okHttpClientM1991J1 != null) {
                la2.m5790a(okHttpClientM1991J1, str);
            }
        }
    }

    public final void m1983C1() {
        int i = 1;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7434n.setText(vj1.f19277a.m10373p().size() == 1 ? getString(R.string.live_refresh) : m1980B1().getName());
        nk1 nk1Var = this.f3091S;
        Live liveM1980B1 = m1980B1();
        nk1Var.f12311c.m3040h(null);
        int i2 = 0;
        nk1Var.f12315g.m2601r(mk1.f11467c, 30000L, new hk1(liveM1980B1, i2), new jk1(nk1Var, i2), new jk1(nk1Var, i));
        m2006Y1();
    }

    @Override
    public final boolean mo1969D0() {
        return false;
    }

    public final boolean m1984D1() {
        return this.f3109k0 != null && m227c1() && m223Z0() && this.f273K.f3037x.m9325l();
    }

    public final void m1985E(long j) {
        if (!m227c1() || this.f273K.f3037x.m9328o()) {
            return;
        }
        ((iv3) this.f3090R.f20542p).f8278j.setVisibility(0);
        ((iv3) this.f3090R.f20542p).f8281m.setText(this.f273K.f3037x.m9318e());
        ((iv3) this.f3090R.f20542p).f8289u.setText(this.f273K.f3037x.m9320g(j));
        ((iv3) this.f3090R.f20542p).f8276h.setImageResource(j > 0 ? R.drawable.ic_widget_forward : R.drawable.ic_widget_rewind);
        m1989H1();
    }

    /* JADX WARN: Code duplicated, block: B:104:0x0279 A[PHI: r9
      0x0279: PHI (r9v2 int) = (r9v1 int), (r9v3 int) binds: [B:29:0x00b2, B:31:0x00bf] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:106:0x0281 A[PHI: r7
      0x0281: PHI (r7v1 int) = (r7v0 int), (r7v3 int), (r7v4 int), (r7v5 int), (r7v6 int), (r7v7 int), (r7v8 int), (r7v9 int) binds: [B:9:0x0037, B:13:0x004c, B:15:0x0058, B:17:0x0064, B:19:0x0071, B:21:0x007e, B:23:0x008b, B:25:0x0098] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:113:0x02a9 A[PHI: r1
      0x02a9: PHI (r1v2 int) = (r1v1 int), (r1v4 int) binds: [B:3:0x0019, B:5:0x0022] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:98:0x0266 A[PHI: r8
      0x0266: PHI (r8v9 int) = (r8v8 int), (r8v10 int) binds: [B:45:0x0122, B:47:0x012b] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:99:0x0268 A[PHI: r4
      0x0268: PHI (r4v3 int) = (r4v2 int), (r4v4 int) binds: [B:41:0x010f, B:43:0x011a] A[DONT_GENERATE, DONT_INLINE]] */
    @Override
    public final ps3 mo1948E0() {
        ps3 ps3Var;
        int i;
        View viewInflate = getLayoutInflater().inflate(R.layout.activity_live, (ViewGroup) null, false);
        int i2 = R.id.channel;
        CustomLiveListView customLiveListView = (CustomLiveListView) rw1.m8781l(R.id.channel, viewInflate);
        if (customLiveListView != null) {
            i2 = R.id.control;
            View viewM8781l = rw1.m8781l(R.id.control, viewInflate);
            if (viewM8781l != null) {
                int i3 = R.id.action;
                View viewM8781l2 = rw1.m8781l(R.id.action, viewM8781l);
                if (viewM8781l2 != null) {
                    int i4 = R.id.across;
                    MaterialTextView materialTextView = (MaterialTextView) rw1.m8781l(R.id.across, viewM8781l2);
                    if (materialTextView == null) {
                        ps3Var = null;
                        i3 = i4;
                    } else {
                        MaterialTextView materialTextView2 = (MaterialTextView) rw1.m8781l(R.id.action, viewM8781l2);
                        if (materialTextView2 != null) {
                            i4 = R.id.audio;
                            MaterialTextView materialTextView3 = (MaterialTextView) rw1.m8781l(R.id.audio, viewM8781l2);
                            if (materialTextView3 != null) {
                                i4 = R.id.change;
                                MaterialTextView materialTextView4 = (MaterialTextView) rw1.m8781l(R.id.change, viewM8781l2);
                                if (materialTextView4 != null) {
                                    i4 = R.id.config;
                                    MaterialTextView materialTextView5 = (MaterialTextView) rw1.m8781l(R.id.config, viewM8781l2);
                                    if (materialTextView5 != null) {
                                        i4 = R.id.decode;
                                        MaterialTextView materialTextView6 = (MaterialTextView) rw1.m8781l(R.id.decode, viewM8781l2);
                                        if (materialTextView6 != null) {
                                            i4 = R.id.home;
                                            MaterialTextView materialTextView7 = (MaterialTextView) rw1.m8781l(R.id.home, viewM8781l2);
                                            if (materialTextView7 != null) {
                                                i4 = R.id.invert;
                                                MaterialTextView materialTextView8 = (MaterialTextView) rw1.m8781l(R.id.invert, viewM8781l2);
                                                if (materialTextView8 != null) {
                                                    i4 = R.id.line;
                                                    MaterialTextView materialTextView9 = (MaterialTextView) rw1.m8781l(R.id.line, viewM8781l2);
                                                    if (materialTextView9 != null) {
                                                        int i5 = R.id.player;
                                                        MaterialTextView materialTextView10 = (MaterialTextView) rw1.m8781l(R.id.player, viewM8781l2);
                                                        if (materialTextView10 != null) {
                                                            int i6 = R.id.scale;
                                                            MaterialTextView materialTextView11 = (MaterialTextView) rw1.m8781l(R.id.scale, viewM8781l2);
                                                            if (materialTextView11 != null) {
                                                                i6 = R.id.speed;
                                                                CustomUpDownView customUpDownView = (CustomUpDownView) rw1.m8781l(R.id.speed, viewM8781l2);
                                                                if (customUpDownView != null) {
                                                                    CustomUpDownView customUpDownView2 = (CustomUpDownView) rw1.m8781l(R.id.text, viewM8781l2);
                                                                    if (customUpDownView2 != null) {
                                                                        MaterialTextView materialTextView12 = (MaterialTextView) rw1.m8781l(R.id.video, viewM8781l2);
                                                                        if (materialTextView12 != null) {
                                                                            ps3Var = null;
                                                                            i = R.id.xray;
                                                                            MaterialTextView materialTextView13 = (MaterialTextView) rw1.m8781l(R.id.xray, viewM8781l2);
                                                                            if (materialTextView13 != null) {
                                                                                int i7 = R.id.video;
                                                                                ht3 ht3Var = new ht3((HorizontalScrollView) viewM8781l2, materialTextView, materialTextView2, materialTextView3, materialTextView4, materialTextView5, materialTextView6, materialTextView7, materialTextView8, materialTextView9, materialTextView10, materialTextView11, customUpDownView, customUpDownView2, materialTextView12, materialTextView13);
                                                                                PlayerSeekView playerSeekView = (PlayerSeekView) rw1.m8781l(R.id.seek, viewM8781l);
                                                                                if (playerSeekView != null) {
                                                                                    aa3 aa3Var = new aa3(6, (LinearLayoutCompat) viewM8781l, ht3Var, playerSeekView);
                                                                                    int i8 = R.id.epgData;
                                                                                    CustomLiveListView customLiveListView2 = (CustomLiveListView) rw1.m8781l(R.id.epgData, viewInflate);
                                                                                    if (customLiveListView2 != null) {
                                                                                        i8 = R.id.group;
                                                                                        CustomLiveListView customLiveListView3 = (CustomLiveListView) rw1.m8781l(R.id.group, viewInflate);
                                                                                        if (customLiveListView3 != null) {
                                                                                            PlayerView playerView = (PlayerView) rw1.m8781l(R.id.player, viewInflate);
                                                                                            if (playerView != null) {
                                                                                                i5 = R.id.progress;
                                                                                                View viewM8781l3 = rw1.m8781l(R.id.progress, viewInflate);
                                                                                                if (viewM8781l3 != null) {
                                                                                                    d81 d81VarM2566d = d81.m2566d(viewM8781l3);
                                                                                                    LinearLayoutCompat linearLayoutCompat = (LinearLayoutCompat) rw1.m8781l(R.id.recycler, viewInflate);
                                                                                                    if (linearLayoutCompat != null) {
                                                                                                        FrameLayout frameLayout = (FrameLayout) rw1.m8781l(i7, viewInflate);
                                                                                                        if (frameLayout != null) {
                                                                                                            i7 = R.id.widget;
                                                                                                            View viewM8781l4 = rw1.m8781l(R.id.widget, viewInflate);
                                                                                                            if (viewM8781l4 != null) {
                                                                                                                AppCompatImageView appCompatImageView = (AppCompatImageView) rw1.m8781l(R.id.action, viewM8781l4);
                                                                                                                if (appCompatImageView != null) {
                                                                                                                    i3 = R.id.bottom;
                                                                                                                    LinearLayoutCompat linearLayoutCompat2 = (LinearLayoutCompat) rw1.m8781l(R.id.bottom, viewM8781l4);
                                                                                                                    if (linearLayoutCompat2 != null) {
                                                                                                                        i3 = R.id.center;
                                                                                                                        LinearLayoutCompat linearLayoutCompat3 = (LinearLayoutCompat) rw1.m8781l(R.id.center, viewM8781l4);
                                                                                                                        if (linearLayoutCompat3 != null) {
                                                                                                                            i3 = R.id.clock;
                                                                                                                            MaterialTextView materialTextView14 = (MaterialTextView) rw1.m8781l(R.id.clock, viewM8781l4);
                                                                                                                            if (materialTextView14 != null) {
                                                                                                                                i3 = R.id.digital;
                                                                                                                                MaterialTextView materialTextView15 = (MaterialTextView) rw1.m8781l(R.id.digital, viewM8781l4);
                                                                                                                                if (materialTextView15 != null) {
                                                                                                                                    i3 = R.id.duration;
                                                                                                                                    MaterialTextView materialTextView16 = (MaterialTextView) rw1.m8781l(R.id.duration, viewM8781l4);
                                                                                                                                    if (materialTextView16 != null) {
                                                                                                                                        i3 = R.id.error;
                                                                                                                                        LinearLayoutCompat linearLayoutCompat4 = (LinearLayoutCompat) rw1.m8781l(R.id.error, viewM8781l4);
                                                                                                                                        if (linearLayoutCompat4 != null) {
                                                                                                                                            MaterialTextView materialTextView17 = (MaterialTextView) rw1.m8781l(R.id.line, viewM8781l4);
                                                                                                                                            if (materialTextView17 != null) {
                                                                                                                                                i3 = R.id.logo;
                                                                                                                                                AppCompatImageView appCompatImageView2 = (AppCompatImageView) rw1.m8781l(R.id.logo, viewM8781l4);
                                                                                                                                                if (appCompatImageView2 != null) {
                                                                                                                                                    i3 = R.id.message;
                                                                                                                                                    MaterialTextView materialTextView18 = (MaterialTextView) rw1.m8781l(R.id.message, viewM8781l4);
                                                                                                                                                    if (materialTextView18 != null) {
                                                                                                                                                        i3 = R.id.name;
                                                                                                                                                        MaterialTextView materialTextView19 = (MaterialTextView) rw1.m8781l(R.id.name, viewM8781l4);
                                                                                                                                                        if (materialTextView19 != null) {
                                                                                                                                                            i3 = R.id.number;
                                                                                                                                                            MaterialTextView materialTextView20 = (MaterialTextView) rw1.m8781l(R.id.number, viewM8781l4);
                                                                                                                                                            if (materialTextView20 != null) {
                                                                                                                                                                i3 = R.id.play;
                                                                                                                                                                MaterialTextView materialTextView21 = (MaterialTextView) rw1.m8781l(R.id.play, viewM8781l4);
                                                                                                                                                                if (materialTextView21 != null) {
                                                                                                                                                                    i3 = R.id.position;
                                                                                                                                                                    MaterialTextView materialTextView22 = (MaterialTextView) rw1.m8781l(R.id.position, viewM8781l4);
                                                                                                                                                                    if (materialTextView22 != null) {
                                                                                                                                                                        i3 = R.id.size;
                                                                                                                                                                        MaterialTextView materialTextView23 = (MaterialTextView) rw1.m8781l(R.id.size, viewM8781l4);
                                                                                                                                                                        if (materialTextView23 != null) {
                                                                                                                                                                            MaterialTextView materialTextView24 = (MaterialTextView) rw1.m8781l(R.id.text, viewM8781l4);
                                                                                                                                                                            if (materialTextView24 != null) {
                                                                                                                                                                                i3 = R.id.title;
                                                                                                                                                                                MaterialTextView materialTextView25 = (MaterialTextView) rw1.m8781l(R.id.title, viewM8781l4);
                                                                                                                                                                                if (materialTextView25 != null) {
                                                                                                                                                                                    i3 = R.id.top;
                                                                                                                                                                                    RelativeLayout relativeLayout = (RelativeLayout) rw1.m8781l(R.id.top, viewM8781l4);
                                                                                                                                                                                    if (relativeLayout != null) {
                                                                                                                                                                                        C1777x3 c1777x3 = new C1777x3((FrameLayout) viewInflate, customLiveListView, aa3Var, customLiveListView2, customLiveListView3, playerView, d81VarM2566d, linearLayoutCompat, frameLayout, new iv3((FrameLayout) viewM8781l4, appCompatImageView, linearLayoutCompat2, linearLayoutCompat3, materialTextView14, materialTextView15, materialTextView16, linearLayoutCompat4, materialTextView17, appCompatImageView2, materialTextView18, materialTextView19, materialTextView20, materialTextView21, materialTextView22, materialTextView23, materialTextView24, materialTextView25, relativeLayout));
                                                                                                                                                                                        this.f3090R = c1777x3;
                                                                                                                                                                                        return c1777x3;
                                                                                                                                                                                    }
                                                                                                                                                                                }
                                                                                                                                                                            } else {
                                                                                                                                                                                i3 = R.id.text;
                                                                                                                                                                            }
                                                                                                                                                                        }
                                                                                                                                                                    }
                                                                                                                                                                }
                                                                                                                                                            }
                                                                                                                                                        }
                                                                                                                                                    }
                                                                                                                                                }
                                                                                                                                            } else {
                                                                                                                                                i3 = R.id.line;
                                                                                                                                            }
                                                                                                                                        }
                                                                                                                                    }
                                                                                                                                }
                                                                                                                            }
                                                                                                                        }
                                                                                                                    }
                                                                                                                }
                                                                                                                h00.m3905e("Missing required view with ID: ".concat(viewM8781l4.getResources().getResourceName(i3)));
                                                                                                                return null;
                                                                                                            }
                                                                                                        }
                                                                                                        i2 = i7;
                                                                                                    } else {
                                                                                                        i2 = R.id.recycler;
                                                                                                    }
                                                                                                } else {
                                                                                                    i2 = i5;
                                                                                                }
                                                                                            } else {
                                                                                                i2 = i5;
                                                                                            }
                                                                                        } else {
                                                                                            i2 = i8;
                                                                                        }
                                                                                    } else {
                                                                                        i2 = i8;
                                                                                    }
                                                                                } else {
                                                                                    i3 = R.id.seek;
                                                                                }
                                                                            }
                                                                        } else {
                                                                            ps3Var = null;
                                                                            i = R.id.video;
                                                                        }
                                                                        i3 = i;
                                                                    } else {
                                                                        ps3Var = null;
                                                                        i3 = R.id.text;
                                                                    }
                                                                } else {
                                                                    ps3Var = null;
                                                                    i3 = i6;
                                                                }
                                                            } else {
                                                                ps3Var = null;
                                                                i3 = i6;
                                                            }
                                                        } else {
                                                            ps3Var = null;
                                                            i3 = R.id.player;
                                                        }
                                                    } else {
                                                        ps3Var = null;
                                                        i3 = i4;
                                                    }
                                                } else {
                                                    ps3Var = null;
                                                    i3 = i4;
                                                }
                                            } else {
                                                ps3Var = null;
                                                i3 = i4;
                                            }
                                        } else {
                                            ps3Var = null;
                                            i3 = i4;
                                        }
                                    } else {
                                        ps3Var = null;
                                        i3 = i4;
                                    }
                                } else {
                                    ps3Var = null;
                                    i3 = i4;
                                }
                            } else {
                                ps3Var = null;
                                i3 = i4;
                            }
                        } else {
                            ps3Var = null;
                        }
                    }
                    h00.m3905e("Missing required view with ID: ".concat(viewM8781l2.getResources().getResourceName(i3)));
                    return ps3Var;
                }
                ps3Var = null;
                h00.m3905e("Missing required view with ID: ".concat(viewM8781l.getResources().getResourceName(i3)));
                return ps3Var;
            }
            ps3Var = null;
        } else {
            ps3Var = null;
        }
        h00.m3905e("Missing required view with ID: ".concat(viewInflate.getResources().getResourceName(i2)));
        return ps3Var;
    }

    public final void m1986E1() {
        ((LinearLayoutCompat) ((aa3) this.f3090R.f20538l).f169h).setVisibility(8);
        ((iv3) this.f3090R.f20542p).f8293y.setVisibility(8);
        App.m1883c(this.f3101c0);
    }

    @Override
    public final void mo1951F0() {
        ((CustomLiveListView) this.f3090R.f20537k).setListener(this);
        ((CustomLiveListView) this.f3090R.f20535i).setListener(this);
        ((CustomLiveListView) this.f3090R.f20536j).setListener(this);
        final int i = 0;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7440t.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i2 = i;
                int i3 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i2) {
                    case 0:
                        int i4 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i5 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i6 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i7 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i8 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i9 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i10 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i11 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i12 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i14 = liveActivity.f3111m0.f21714m;
                            if (i14 == 2 || i14 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i3 = 1;
                                                }
                                            } else {
                                                i3 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i3;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i16 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i16;
                            th2Var4.f17533e.mo4114A(i16);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i17 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i18 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7430j.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i2 = i;
                int i3 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i2) {
                    case 0:
                        int i4 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i5 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i6 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i7 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i8 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i9 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i10 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i11 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i12 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i14 = liveActivity.f3111m0.f21714m;
                            if (i14 == 2 || i14 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i3 = 1;
                                                }
                                            } else {
                                                i3 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i3;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i16 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i16;
                            th2Var4.f17533e.mo4114A(i16);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i17 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i18 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7441u.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i2 = i;
                int i3 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i2) {
                    case 0:
                        int i4 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i5 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i6 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i7 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i8 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i9 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i10 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i11 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i12 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i14 = liveActivity.f3111m0.f21714m;
                            if (i14 == 2 || i14 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i3 = 1;
                                                }
                                            } else {
                                                i3 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i3;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i16 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i16;
                            th2Var4.f17533e.mo4114A(i16);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i17 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i18 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i2 = 11;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7434n.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i3 = i2;
                int i4 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i3) {
                    case 0:
                        int i5 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i6 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i7 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i8 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i9 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i10 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i11 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i12 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i14 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i15 = liveActivity.f3111m0.f21714m;
                            if (i15 == 2 || i15 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i4 = 1;
                                                }
                                            } else {
                                                i4 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i4;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i16 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i17 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i17;
                            th2Var4.f17533e.mo4114A(i17);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i18 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i19 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i3 = 12;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7436p.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i4 = i3;
                int i5 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i4) {
                    case 0:
                        int i6 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i7 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i8 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i9 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i10 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i11 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i12 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i13 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i14 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i16 = liveActivity.f3111m0.f21714m;
                            if (i16 == 2 || i16 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i5 = 1;
                                                }
                                            } else {
                                                i5 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i5;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i17 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i18 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i18;
                            th2Var4.f17533e.mo4114A(i18);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i19 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i110 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i4 = 1;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7438r.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i5 = i4;
                int i6 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i5) {
                    case 0:
                        int i7 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i8 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i9 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i10 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i11 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i12 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i13 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i14 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i16 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i17 = liveActivity.f3111m0.f21714m;
                            if (i17 == 2 || i17 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i6 = 1;
                                                }
                                            } else {
                                                i6 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i6;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i18 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i19 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i19;
                            th2Var4.f17533e.mo4114A(i19);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i110 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i111 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i5 = 2;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7439s.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i6 = i5;
                int i7 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i6) {
                    case 0:
                        int i8 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i9 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i10 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i11 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i12 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i13 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i14 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i15 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i16 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i17 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i18 = liveActivity.f3111m0.f21714m;
                            if (i18 == 2 || i18 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i7 = 1;
                                                }
                                            } else {
                                                i7 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i7;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i19 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i110 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i110;
                            th2Var4.f17533e.mo4114A(i110);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i111 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i112 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i6 = 3;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7432l.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i7 = i6;
                int i8 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i7) {
                    case 0:
                        int i9 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i10 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i11 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i12 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i14 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i15 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i16 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i17 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i18 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i19 = liveActivity.f3111m0.f21714m;
                            if (i19 == 2 || i19 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i8 = 1;
                                                }
                                            } else {
                                                i8 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i8;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i110 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i111 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i111;
                            th2Var4.f17533e.mo4114A(i111);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i112 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i113 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i7 = 4;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7429i.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i8 = i7;
                int i9 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i8) {
                    case 0:
                        int i10 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i11 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i12 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i13 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i14 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i15 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i16 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i17 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i18 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i19 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i110 = liveActivity.f3111m0.f21714m;
                            if (i110 == 2 || i110 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i9 = 1;
                                                }
                                            } else {
                                                i9 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i9;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i111 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i112 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i112;
                            th2Var4.f17533e.mo4114A(i112);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i113 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i114 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i8 = 5;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7435o.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i9 = i8;
                int i10 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i9) {
                    case 0:
                        int i11 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i12 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i14 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i16 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i17 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i18 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i19 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i110 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i111 = liveActivity.f3111m0.f21714m;
                            if (i111 == 2 || i111 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i10 = 1;
                                                }
                                            } else {
                                                i10 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i10;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i112 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i113 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i113;
                            th2Var4.f17533e.mo4114A(i113);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i114 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i115 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i9 = 6;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7428h.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i10 = i9;
                int i11 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i10) {
                    case 0:
                        int i12 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i13 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i14 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i15 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i16 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i17 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i18 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i19 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i110 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i111 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i112 = liveActivity.f3111m0.f21714m;
                            if (i112 == 2 || i112 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i11 = 1;
                                                }
                                            } else {
                                                i11 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i11;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i113 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i114 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i114;
                            th2Var4.f17533e.mo4114A(i114);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i115 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i116 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i10 = 7;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7431k.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i11 = i10;
                int i12 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i11) {
                    case 0:
                        int i13 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i14 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i16 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i17 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i18 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i19 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i110 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i111 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i112 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i113 = liveActivity.f3111m0.f21714m;
                            if (i113 == 2 || i113 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i12 = 1;
                                                }
                                            } else {
                                                i12 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i12;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i114 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i115 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i115;
                            th2Var4.f17533e.mo4114A(i115);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i116 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i117 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i11 = 8;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7437q.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i12 = i11;
                int i13 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i12) {
                    case 0:
                        int i14 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i15 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i16 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i17 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i18 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i19 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i110 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i111 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i112 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i113 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i114 = liveActivity.f3111m0.f21714m;
                            if (i114 == 2 || i114 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i13 = 1;
                                                }
                                            } else {
                                                i13 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i13;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i115 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i116 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i116;
                            th2Var4.f17533e.mo4114A(i116);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i117 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i118 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i12 = 9;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7442v.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i13 = i12;
                int i14 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i13) {
                    case 0:
                        int i15 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i16 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i17 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i18 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i19 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i110 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i111 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i112 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i113 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i114 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i115 = liveActivity.f3111m0.f21714m;
                            if (i115 == 2 || i115 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i14 = 1;
                                                }
                                            } else {
                                                i14 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i14;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i116 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i117 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i117;
                            th2Var4.f17533e.mo4114A(i117);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i118 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i119 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        final int i13 = 10;
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7433m.setOnClickListener(new View.OnClickListener(this) {

            public final LiveActivity f6506h;

            {
                this.f6506h = this;
            }

            /* JADX WARN: Code duplicated, block: B:46:0x00d4  */
            /* JADX WARN: Multi-variable type inference failed */
            /* JADX WARN: Type inference failed for: r0v39 */
            /* JADX WARN: Type inference failed for: r0v40 */
            /* JADX WARN: Type inference failed for: r0v51 */
            @Override
            public final void onClick(View view) {
                es1 es1Var;
                es1 es1Var2;
                ?? r0;
                boolean zM9191w;
                int i14 = i13;
                int i15 = 0;
                LiveActivity liveActivity = this.f6506h;
                switch (i14) {
                    case 0:
                        int i16 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var = liveActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var;
                            gk3Var.f6536z0 = th2Var != null ? th2Var.m9319f() : null;
                            gk3Var.f6534x0 = ((PlayerView) liveActivity.f3090R.f20539m).getSubtitleView();
                            gk3Var.m3782e0(liveActivity);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 1:
                        int i17 = LiveActivity.f3089r0;
                        int iMin = (int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L));
                        liveActivity.m2003V1(iMin != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iMin + 1 : 0);
                        break;
                    case 2:
                        int i18 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var2 = liveActivity.f273K.f3037x;
                            String strM9319f = th2Var2 != null ? th2Var2.m9319f() : null;
                            fy0 fy0VarM6086w0 = liveActivity.m6086w0();
                            Iterator it = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof t53) {
                                    liveActivity.m1986E1();
                                    break;
                                }
                            }
                            op3.m7095g(liveActivity);
                            new t53(th2Var2, strM9319f, false).m266W(fy0VarM6086w0);
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 3:
                        int i19 = LiveActivity.f3089r0;
                        v41 v41Var = new v41();
                        v41Var.f18907w0 = 1;
                        v41Var.f18906v0 = true;
                        v41Var.m266W(liveActivity.m6086w0());
                        liveActivity.m1986E1();
                        break;
                    case 4:
                        int i110 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            if (!liveActivity.f273K.f3037x.f17537i.isPlaying()) {
                                if (liveActivity.m227c1() && (es1Var = liveActivity.f271I) != null) {
                                    es1Var.mo347g0();
                                    break;
                                }
                            } else if (liveActivity.m227c1() && (es1Var2 = liveActivity.f271I) != null) {
                                es1Var2.pause();
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i111 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("invert", false)), "invert");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
                        break;
                    case 6:
                        int i112 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("across", true)), "across");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
                        break;
                    case 7:
                        int i113 = LiveActivity.f3089r0;
                        p11.m7580P(Boolean.valueOf(!p11.m7608o("change", true)), "change");
                        ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
                        break;
                    case 8:
                        int i114 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            jh2.m5089h0(liveActivity, ((ht3) ((aa3) liveActivity.f3090R.f20538l).f170i).f7437q, liveActivity.f273K.f3037x, new hj1(liveActivity, 5));
                            liveActivity.m1986E1();
                            break;
                        }
                        break;
                    case 9:
                        int i115 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            int i116 = liveActivity.f3111m0.f21714m;
                            if (i116 == 2 || i116 == 3) {
                                liveActivity.f3113o0 = false;
                                liveActivity.f3114p0 = false;
                                liveActivity.m1982A1();
                                liveActivity.f3111m0.m10882b();
                                th2 th2Var3 = liveActivity.f273K.f3037x;
                                th2Var3.m9308A(0, th2Var3.m9325l());
                                liveActivity.m2002U1(false);
                                liveActivity.m1994M1();
                            } else if (liveActivity.f3108j0 != null) {
                                boolean zM1984D1 = liveActivity.m1984D1();
                                Channel channel = liveActivity.f3108j0;
                                if (zM1984D1) {
                                    channel.getCurrent();
                                    zM9191w = t11.m9191w(liveActivity.f273K.f3037x.m9324k());
                                } else {
                                    String current = channel.getCurrent();
                                    if (t11.m9191w(current)) {
                                        try {
                                            URI uriCreate = URI.create(current.trim());
                                            String lowerCase = "";
                                            String lowerCase2 = uriCreate.getScheme() == null ? "" : uriCreate.getScheme().toLowerCase(Locale.ROOT);
                                            if ("http".equals(lowerCase2) || "https".equals(lowerCase2)) {
                                                String lowerCase3 = uriCreate.getPath() == null ? "" : uriCreate.getPath().toLowerCase(Locale.ROOT);
                                                if (uriCreate.getHost() != null) {
                                                    lowerCase = uriCreate.getHost().toLowerCase(Locale.ROOT);
                                                }
                                                if (!lowerCase3.endsWith(".strm") && !lowerCase.contains("youtube.com") && !lowerCase.contains("youtu.be")) {
                                                    i15 = 1;
                                                }
                                            } else {
                                                i15 = 1;
                                            }
                                        } catch (IllegalArgumentException unused) {
                                        }
                                    }
                                    r0 = i15;
                                }
                                if (r0 != 0) {
                                    r0 = zM9191w;
                                    liveActivity.f273K.f3037x.m9316c();
                                    liveActivity.f3113o0 = !zM1984D1;
                                    liveActivity.f3114p0 = zM1984D1;
                                    liveActivity.f3111m0.m10884d();
                                } else {
                                    r0 = zM9191w;
                                    d81.m2564T(R.string.xray_public_http_required);
                                }
                            } else {
                                d81.m2564T(R.string.xray_live_required);
                            }
                            break;
                        }
                        break;
                    case 10:
                        int i117 = LiveActivity.f3089r0;
                        if (liveActivity.m227c1()) {
                            th2 th2Var4 = liveActivity.f273K.f3037x;
                            int i118 = (th2Var4.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var4.f17541m = i118;
                            th2Var4.f17533e.mo4114A(i118);
                            th2Var4.f17531c.f3029p.forEach(new jf2(4));
                            break;
                        }
                        break;
                    case 11:
                        int i119 = LiveActivity.f3089r0;
                        if (vj1.f19277a.m10373p().size() == 1) {
                            liveActivity.mo2008j(LiveActivity.m1980B1());
                        } else {
                            new dk1().m266W(liveActivity.m6086w0());
                        }
                        liveActivity.m1986E1();
                        break;
                    default:
                        int i1110 = LiveActivity.f3089r0;
                        liveActivity.f3092T.m2585V(true, false);
                        break;
                }
            }
        });
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7439s.setOnLongClickListener(new ViewOnLongClickListenerC0177bf(this, i8));
        ((FrameLayout) this.f3090R.f20534h).setOnTouchListener(new ViewOnTouchListenerC1603se(this, i6));
        ((CustomLiveListView) this.f3090R.f20537k).addOnChildViewHolderSelectedListener(new C1221nv(this, i6));
    }

    public final void m1987F1() {
        ((CustomLiveListView) this.f3090R.f20535i).setVisibility(0);
        ((CustomLiveListView) this.f3090R.f20537k).setVisibility(0);
        ((CustomLiveListView) this.f3090R.f20536j).setVisibility(8);
        ((CustomLiveListView) this.f3090R.f20535i).requestFocus();
    }

    @Override
    public final void mo206G0(Bundle bundle) {
        super.mo206G0(bundle);
        this.f3097Y = C1872zo.m11041q(((iv3) this.f3090R.f20542p).f8279k);
        this.f3111m0 = new yz3(this, this);
        this.f3096X = new f30(this);
        this.f3106h0 = new ArrayList();
        this.f3100b0 = new hj1(this, 0);
        int i = 1;
        this.f3101c0 = new hj1(this, i);
        int i2 = 2;
        this.f3102d0 = new hj1(this, i2);
        int i3 = 3;
        this.f3103e0 = new hj1(this, i3);
        int i4 = 4;
        this.f3104f0 = new hj1(this, i4);
        ((CustomLiveListView) this.f3090R.f20537k).setItemAnimator(null);
        ((CustomLiveListView) this.f3090R.f20535i).setItemAnimator(null);
        ((CustomLiveListView) this.f3090R.f20536j).setItemAnimator(null);
        CustomLiveListView customLiveListView = (CustomLiveListView) this.f3090R.f20537k;
        go0 go0Var = new go0(this, 1);
        this.f3093U = go0Var;
        customLiveListView.setAdapter(go0Var);
        CustomLiveListView customLiveListView2 = (CustomLiveListView) this.f3090R.f20535i;
        C1125lr c1125lr = new C1125lr(this);
        this.f3094V = c1125lr;
        customLiveListView2.setAdapter(c1125lr);
        CustomLiveListView customLiveListView3 = (CustomLiveListView) this.f3090R.f20536j;
        go0 go0Var2 = new go0(this, 0);
        this.f3095W = go0Var2;
        customLiveListView3.setAdapter(go0Var2);
        m2003V1((int) Math.min(4L, Math.max(p11.m7611r(np3.m6612S(), "scale_live"), 0L)));
        View viewFindViewById = mo220W0().findViewById(R.id.exo_progress);
        if (viewFindViewById != null) {
            viewFindViewById.setNextFocusDownId(R.id.config);
        }
        af2.m204u1(((ht3) ((aa3) this.f3090R.f20538l).f170i).f7427c);
        jh2.m5088f0(null, ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7437q);
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7435o.setSelected(p11.m7608o("invert", false));
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7428h.setSelected(p11.m7608o("across", true));
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7431k.setSelected(p11.m7608o("change", true));
        bu3 bu3VarMo2323A = mo2323A();
        zt3 zt3VarM6618Z = np3.m6618Z(this);
        k20 k20VarM6617Y = np3.m6617Y(this);
        bu3VarMo2323A.getClass();
        zt3VarM6618Z.getClass();
        k20VarM6617Y.getClass();
        bd2 bd2Var = new bd2(bu3VarMo2323A, zt3VarM6618Z, k20VarM6617Y);
        KClass kotlinClass = JvmClassMappingKt.getKotlinClass(nk1.class);
        kotlinClass.getClass();
        String qualifiedName = kotlinClass.getQualifiedName();
        if (qualifiedName == null) {
            C1566re.m8586j("Local and anonymous classes can not be ViewModels");
            return;
        }
        nk1 nk1Var = (nk1) bd2Var.m1199j(kotlinClass, "androidx.lifecycle.ViewModelProvider.DefaultKey:".concat(qualifiedName));
        this.f3091S = nk1Var;
        this.f3092T = new d81(this, nk1Var.f12316h);
        m230f1(nk1Var.f12310b, new eo0(this, i));
        m230f1(this.f3091S.f12311c, new eo0(this, i2));
        this.f3091S.f12314f.m3036d(this, new eo0(this, i3));
        m230f1(this.f3091S.f12313e, new eo0(this, i4));
        this.f3091S.f12312d.m3036d(this, new eo0(this, 5));
        if (!getIntent().getBooleanExtra("empty", true)) {
            m1983C1();
            return;
        }
        wj1 wj1Var = vj1.f19277a;
        wj1Var.getClass();
        wj1Var.m10371n(Config.live());
        wj1Var.m3163h(new m61(this, i3));
    }

    public final void m1988G1() {
        ((iv3) this.f3090R.f20542p).f8277i.setVisibility(8);
        App.m1883c(this.f3103e0);
    }

    public final void m1989H1() {
        ((FrameLayout) ((d81) this.f3090R.f20540n).f4036h).setVisibility(8);
        App.m1883c(this.f3102d0);
        bl3.f2087c = 0L;
        bl3.f2088d = 0L;
    }

    public final void m1990I1() {
        App.m1883c(this.f3104f0);
        if (AbstractActivityC1828yh.m10757H0((LinearLayoutCompat) this.f3090R.f20541o)) {
            return;
        }
        ((LinearLayoutCompat) this.f3090R.f20541o).setVisibility(8);
        m2001T1();
    }

    public final OkHttpClient m1991J1() {
        if (this.f273K == null || !m222Y0()) {
            return la2.m5792c();
        }
        th2 th2Var = this.f273K.f3037x;
        th2Var.getClass();
        return th2Var.m9321h(la2.m5792c());
    }

    public final void m1992K1(Group group) {
        d81 d81Var = this.f3092T;
        ((C1629t3) d81Var.f4036h).f17149m = group;
        LiveActivity liveActivity = (LiveActivity) d81Var.f4037i;
        liveActivity.f3107i0 = group;
        ((CustomLiveListView) liveActivity.f3090R.f20537k).setSelectedPosition(liveActivity.f3093U.f6626c.indexOf(group));
        liveActivity.m1997P1(group);
        if (group.isKeep()) {
            int i = this.f3110l0 + 1;
            this.f3110l0 = i;
            if (i < 5 || this.f3106h0.isEmpty()) {
                return;
            }
            hd2 hd2Var = new hd2();
            Iterator it = m6086w0().f5352c.m11043B().iterator();
            while (it.hasNext()) {
                if (((ox0) it.next()) instanceof hd2) {
                    App.m1883c(this.f3104f0);
                    this.f3110l0 = 0;
                }
            }
            hd2Var.m266W(m6086w0());
            App.m1883c(this.f3104f0);
            this.f3110l0 = 0;
        }
    }

    public final void m1993L1() {
        View view = this.f3099a0;
        Object obj = (view == null || view.getVisibility() != 0) ? ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7432l : this.f3099a0;
        ((LinearLayoutCompat) ((aa3) this.f3090R.f20538l).f169h).setVisibility(0);
        ((iv3) this.f3090R.f20542p).f8293y.setVisibility(0);
        Objects.requireNonNull(obj);
        App.m1882b(new yd0(obj, 17), 25L);
        App.m1882b(this.f3101c0, 5000L);
        m1988G1();
    }

    public final void m1994M1() {
        if (this.f3108j0 == null || this.f273K == null || !m222Y0()) {
            return;
        }
        if (!m1980B1().getEpgXml().isEmpty() && this.f3108j0.getDataList().isEmpty()) {
            nk1 nk1Var = this.f3091S;
            Live liveM1980B1 = m1980B1();
            th2 th2Var = this.f273K.f3037x;
            th2Var.getClass();
            nk1Var.m6550d(liveM1980B1, th2Var.m9321h(la2.m5792c()));
        }
        nk1 nk1Var2 = this.f3091S;
        Channel channel = this.f3108j0;
        th2 th2Var2 = this.f273K.f3037x;
        th2Var2.getClass();
        nk1Var2.m6549c(channel, th2Var2.m9321h(la2.m5792c()));
    }

    public final void m1995N1(boolean z) {
        this.f3113o0 = false;
        this.f3114p0 = false;
        if (this.f273K == null || !m222Y0()) {
            return;
        }
        m1982A1();
        yz3 yz3Var = this.f3111m0;
        if (yz3Var != null && yz3Var.f21714m != 1) {
            yz3Var.m10882b();
        }
        if (m223Z0()) {
            if (!z && this.f273K.f3037x.f17542n > 0) {
                m213P0();
            }
            this.f273K.f3037x.m9308A(0, z);
        }
    }

    public final void m1996O1(EpgData epgData) {
        go0 go0Var = this.f3095W;
        Iterator it = go0Var.f6626c.iterator();
        while (it.hasNext()) {
            ((EpgData) it.next()).setSelected(epgData);
        }
        go0Var.notifyDataSetChanged();
        AbstractActivityC1828yh.m10759J0((CustomLiveListView) this.f3090R.f20536j, this.f3095W);
    }

    public final void m1997P1(Group group) {
        C1125lr c1125lr = this.f3094V;
        int iM2457b = AbstractC0463d2.m2457b(60);
        int iM2457b2 = AbstractC0463d2.m2457b(64);
        if (group.isKeep()) {
            group.setWidth(0);
        }
        if (group.getWidth() == 0) {
            for (Channel channel : group.getChannel()) {
                group.setWidth(Math.max(group.getWidth(), AbstractC0463d2.m2464i(16, channel.getNumber() + channel.getName()) + (channel.getLogo().isEmpty() ? 0 : iM2457b)));
            }
        }
        int iMin = group.getWidth() == 0 ? 0 : Math.min(group.getWidth() + iM2457b2, AbstractC0463d2.m2459d() / 2);
        CustomLiveListView customLiveListView = (CustomLiveListView) this.f3090R.f20535i;
        customLiveListView.post(new RunnableC0662id(customLiveListView, iMin, 4));
        List<Channel> channel2 = group.getChannel();
        ArrayList arrayList = c1125lr.f10864b;
        arrayList.clear();
        arrayList.addAll(channel2);
        c1125lr.notifyDataSetChanged();
        ((CustomLiveListView) this.f3090R.f20535i).setSelectedPosition(Math.max(group.getPosition(), 0));
    }

    public final void m1998Q1(pv1 pv1Var) {
        if (m227c1()) {
            if (m223Z0()) {
                this.f273K.f3037x.m9339z(pv1Var);
            }
            ((iv3) this.f3090R.f20542p).f8292x.setText(pv1Var.f14423e);
            ((iv3) this.f3090R.f20542p).f8292x.setSelected(true);
        }
    }

    public final void m1999R1() {
        this.f3091S.m6549c(this.f3108j0, m1991J1());
        ((iv3) this.f3090R.f20542p).f8288t.setText("");
        ((iv3) this.f3090R.f20542p).f8286r.setMaxEms(48);
        gr2 gr2VarM1878d = ComponentCallbacks2C0223a.m1878d(((iv3) this.f3090R.f20542p).f8284p);
        AppCompatImageView appCompatImageView = ((iv3) this.f3090R.f20542p).f8284p;
        gr2VarM1878d.getClass();
        gr2VarM1878d.m3827o(new er2(appCompatImageView));
        yz3 yz3Var = this.f3111m0;
        if (yz3Var == null || yz3Var.f21714m != 3) {
            this.f3108j0.loadLogo(((iv3) this.f3090R.f20542p).f8284p);
        } else {
            ((iv3) this.f3090R.f20542p).f8284p.setImageDrawable(null);
        }
        ((iv3) this.f3090R.f20542p).f8283o.setText(this.f3108j0.getLine());
        ((iv3) this.f3090R.f20542p).f8286r.setText(this.f3108j0.getShow());
        ((iv3) this.f3090R.f20542p).f8287s.setText(this.f3108j0.getNumber());
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7436p.setText(this.f3108j0.getLine());
        ((iv3) this.f3090R.f20542p).f8283o.setVisibility(this.f3108j0.getLineVisible());
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7436p.setVisibility(this.f3108j0.getLineVisible());
    }

    public final void m2000S1(int[] iArr) {
        int size;
        int i;
        if (iArr[0] == -1 || (size = this.f3093U.f6626c.size()) == 1 || (i = iArr[0]) >= size) {
            return;
        }
        this.f3107i0 = (Group) this.f3093U.f6626c.get(i);
        ((CustomLiveListView) this.f3090R.f20537k).setSelectedPosition(iArr[0]);
        this.f3107i0.setPosition(iArr[1]);
        d81 d81Var = this.f3092T;
        Group group = this.f3107i0;
        ((C1629t3) d81Var.f4036h).f17149m = group;
        LiveActivity liveActivity = (LiveActivity) d81Var.f4037i;
        liveActivity.f3107i0 = group;
        ((CustomLiveListView) liveActivity.f3090R.f20537k).setSelectedPosition(liveActivity.f3093U.f6626c.indexOf(group));
        liveActivity.m1997P1(group);
        this.f3092T.m2582Q(this.f3107i0.current());
    }

    @Override
    public final pf2 mo217T0() {
        return this.f3115q0;
    }

    public final void m2001T1() {
        Channel channel = this.f3108j0;
        if (channel == null) {
            return;
        }
        Group group = channel.getGroup();
        this.f3107i0 = group;
        int iIndexOf = this.f3093U.f6626c.indexOf(group);
        boolean z = ((CustomLiveListView) this.f3090R.f20537k).getSelectedPosition() != iIndexOf;
        if (z) {
            ((CustomLiveListView) this.f3090R.f20537k).setSelectedPosition(iIndexOf);
        }
        if (z) {
            C1125lr c1125lr = this.f3094V;
            List<Channel> channel2 = this.f3107i0.getChannel();
            ArrayList arrayList = c1125lr.f10864b;
            arrayList.clear();
            arrayList.addAll(channel2);
            c1125lr.notifyDataSetChanged();
        }
        ((CustomLiveListView) this.f3090R.f20535i).setSelectedPosition(this.f3107i0.getPosition());
    }

    @Override
    public final String mo218U0() {
        return this.f3109k0;
    }

    public final void m2002U1(boolean z) {
        C1125lr c1125lr = this.f3094V;
        if (c1125lr != null && c1125lr.f10866d != z) {
            c1125lr.f10866d = z;
            if (z && c1125lr.f10865c != null) {
                for (int i = 0; i < c1125lr.f10865c.getChildCount(); i++) {
                    RecyclerView recyclerView = c1125lr.f10865c;
                    AbstractC0148q childViewHolder = recyclerView.getChildViewHolder(recyclerView.getChildAt(i));
                    if (childViewHolder instanceof C1088kr) {
                        C1125lr.m5894a((C1088kr) childViewHolder);
                    }
                }
            }
            c1125lr.notifyDataSetChanged();
        }
        gr2 gr2VarM1878d = ComponentCallbacks2C0223a.m1878d(((iv3) this.f3090R.f20542p).f8284p);
        AppCompatImageView appCompatImageView = ((iv3) this.f3090R.f20542p).f8284p;
        gr2VarM1878d.getClass();
        gr2VarM1878d.m3827o(new er2(appCompatImageView));
        if (z) {
            ((iv3) this.f3090R.f20542p).f8284p.setImageDrawable(null);
            return;
        }
        Channel channel = this.f3108j0;
        if (channel != null) {
            channel.loadLogo(((iv3) this.f3090R.f20542p).f8284p);
        }
    }

    @Override
    public final PlayerView mo219V0() {
        return (PlayerView) this.f3090R.f20539m;
    }

    public final void m2003V1(int i) {
        p11.m7580P(Integer.valueOf((int) Math.min(4L, Math.max(i, 0L))), "scale_live");
        ((PlayerView) this.f3090R.f20539m).setResizeMode(i);
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7438r.setText(AbstractC0463d2.m2463h(R.array.select_scale)[i]);
    }

    @Override
    public final PlayerSeekView mo220W0() {
        return (PlayerSeekView) ((aa3) this.f3090R.f20538l).f171j;
    }

    public final void m2004W1(Channel channel) {
        Channel channel2 = this.f3108j0;
        if (channel2 == null || channel2.getData(this.f3091S.f12317i).getList().isEmpty() || this.f3095W.f6626c.size() == 0 || !this.f3108j0.equals(channel) || !this.f3108j0.getGroup().equals(this.f3107i0)) {
            return;
        }
        ((CustomLiveListView) this.f3090R.f20536j).setSelectedPosition(this.f3108j0.getData(this.f3091S.f12317i).getSelected());
        ((CustomLiveListView) this.f3090R.f20536j).setVisibility(0);
        ((CustomLiveListView) this.f3090R.f20535i).setVisibility(8);
        ((CustomLiveListView) this.f3090R.f20537k).setVisibility(8);
        ((CustomLiveListView) this.f3090R.f20536j).requestFocus();
    }

    public final void m2005X1(String str) {
        hc2.m4032D(((iv3) this.f3090R.f20542p).f8285q);
        ((iv3) this.f3090R.f20542p).f8282n.setVisibility(0);
        ((iv3) this.f3090R.f20542p).f8291w.setText(str);
        m1989H1();
    }

    public final void m2006Y1() {
        ((FrameLayout) ((d81) this.f3090R.f20540n).f4036h).setVisibility(0);
        App.m1882b(this.f3102d0, 0L);
        ((iv3) this.f3090R.f20542p).f8276h.setImageResource(R.drawable.ic_widget_play);
        ((iv3) this.f3090R.f20542p).f8278j.setVisibility(8);
        ((iv3) this.f3090R.f20542p).f8282n.setVisibility(8);
        ((iv3) this.f3090R.f20542p).f8291w.setText("");
    }

    public final void m2007Z1() {
        if (((LinearLayoutCompat) this.f3090R.f20541o).getVisibility() == 0 || this.f3093U.f6626c.size() == 0) {
            return;
        }
        ((LinearLayoutCompat) this.f3090R.f20541o).setVisibility(0);
        m2001T1();
        App.m1882b(this.f3104f0, 5000L);
        m1987F1();
    }

    @Override
    public final boolean dispatchKeyEvent(KeyEvent keyEvent) {
        if (((LinearLayoutCompat) ((aa3) this.f3090R.f20538l).f169h).getVisibility() == 0) {
            App.m1882b(this.f3101c0, 5000L);
        }
        if (((LinearLayoutCompat) ((aa3) this.f3090R.f20538l).f169h).getVisibility() == 0) {
            this.f3099a0 = getCurrentFocus();
        }
        this.f3096X.getClass();
        if ((v11.m9903B(keyEvent) || v11.m9907F(keyEvent) || v11.m9902A(keyEvent) || v11.m9904C(keyEvent) || v11.m9906E(keyEvent) || v11.m9946z(keyEvent) || v11.m9905D(keyEvent) || keyEvent.isLongPress()) && m227c1()) {
            f30 f30Var = this.f3096X;
            LiveActivity liveActivity = f30Var.f5487i;
            if (AbstractActivityC1828yh.m10757H0((LinearLayoutCompat) liveActivity.f3090R.f20541o) && AbstractActivityC1828yh.m10757H0((LinearLayoutCompat) ((aa3) liveActivity.f3090R.f20538l).f169h)) {
                if (keyEvent.getAction() == 0 && v11.m9904C(keyEvent)) {
                    long j = f30Var.f5488j - 10000;
                    f30Var.f5488j = j;
                    liveActivity.m1985E(j);
                } else if (keyEvent.getAction() == 0 && v11.m9906E(keyEvent)) {
                    long j2 = f30Var.f5488j + 10000;
                    f30Var.f5488j = j2;
                    liveActivity.m1985E(j2);
                } else {
                    int i = 1;
                    if (keyEvent.getAction() == 0 && v11.m9907F(keyEvent)) {
                        if (liveActivity.m227c1()) {
                            boolean zM7608o = p11.m7608o("invert", false);
                            d81 d81Var = liveActivity.f3092T;
                            if (zM7608o) {
                                d81Var.m2569B(1);
                            } else {
                                d81Var.m2569B(-1);
                            }
                        }
                    } else if (keyEvent.getAction() == 0 && v11.m9902A(keyEvent)) {
                        if (liveActivity.m227c1()) {
                            boolean zM7608o2 = p11.m7608o("invert", false);
                            d81 d81Var2 = liveActivity.f3092T;
                            if (zM7608o2) {
                                d81Var2.m2569B(-1);
                            } else {
                                d81Var2.m2569B(1);
                            }
                        }
                    } else if (keyEvent.getAction() == 1 && v11.m9904C(keyEvent)) {
                        long j3 = f30Var.f5488j;
                        if (liveActivity.m227c1()) {
                            if (liveActivity.f273K.f3037x.m9328o()) {
                                liveActivity.f3092T.m2585V(false, true);
                            } else {
                                RunnableC0663ie runnableC0663ie = liveActivity.f3105g0;
                                if (runnableC0663ie != null) {
                                    App.m1883c(runnableC0663ie);
                                }
                                RunnableC0663ie runnableC0663ie2 = new RunnableC0663ie(liveActivity, j3, i);
                                liveActivity.f3105g0 = runnableC0663ie2;
                                App.m1882b(runnableC0663ie2, 250L);
                            }
                        }
                    } else if (keyEvent.getAction() == 1 && v11.m9906E(keyEvent)) {
                        long j4 = f30Var.f5488j;
                        if (liveActivity.m227c1()) {
                            if (liveActivity.f273K.f3037x.m9328o()) {
                                liveActivity.f3092T.m2585V(true, true);
                            } else {
                                RunnableC0663ie runnableC0663ie3 = liveActivity.f3105g0;
                                if (runnableC0663ie3 != null) {
                                    App.m1883c(runnableC0663ie3);
                                }
                                RunnableC0663ie runnableC0663ie4 = new RunnableC0663ie(liveActivity, j4, i);
                                liveActivity.f3105g0 = runnableC0663ie4;
                                App.m1882b(runnableC0663ie4, 250L);
                            }
                        }
                    } else if (keyEvent.getAction() == 1 && v11.m9946z(keyEvent)) {
                        int keyCode = keyEvent.getKeyCode();
                        RunnableC1518q3 runnableC1518q3 = f30Var.f5489k;
                        StringBuilder sb = f30Var.f5486h;
                        if (sb.length() < 4) {
                            sb.append(keyCode >= 144 ? keyCode - Token.LABEL : keyCode - 7);
                            ((iv3) liveActivity.f3090R.f20542p).f8280l.setText(sb.toString());
                            ((iv3) liveActivity.f3090R.f20542p).f8280l.setVisibility(0);
                            App.m1883c(runnableC1518q3);
                            App.m1882b(runnableC1518q3, 2000L);
                        }
                    } else if (keyEvent.getAction() == 1 && v11.m9903B(keyEvent)) {
                        if (liveActivity.m227c1()) {
                            liveActivity.m1988G1();
                            liveActivity.m2007Z1();
                        }
                    } else if (v11.m9905D(keyEvent) || (keyEvent.isLongPress() && v11.m9903B(keyEvent))) {
                        liveActivity.m1993L1();
                    }
                }
            }
        }
        return super.dispatchKeyEvent(keyEvent);
    }

    @Override
    public final void mo231g1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            ht3 ht3Var = (ht3) ((aa3) this.f3090R.f20538l).f170i;
            MaterialTextView materialTextView = ht3Var.f7437q;
            MaterialTextView materialTextView2 = ht3Var.f7433m;
            materialTextView.setText(AbstractC0463d2.m2463h(R.array.select_engine)[hc2.m4078v(th2Var)]);
            materialTextView2.setText(th2Var == null ? "" : AbstractC0463d2.m2463h(R.array.select_decode)[th2Var.f17541m]);
        }
    }

    @Override
    public final void mo232h1(String str) {
        d81 d81Var = this.f3092T;
        LiveActivity liveActivity = (LiveActivity) d81Var.f4037i;
        if (liveActivity.m227c1()) {
            liveActivity.m1995N1(false);
            liveActivity.m2002U1(false);
            th2 th2Var = liveActivity.f273K.f3037x;
            Track.delete(th2Var.m9319f());
            th2Var.m9337x();
            th2Var.m9336w();
            th2Var.m9313F();
            liveActivity.m2005X1(str);
        }
        Channel channel = (Channel) ((C1629t3) d81Var.f4036h).f17148l;
        if (!p11.m7608o("change", true) || channel == null || channel.isLast()) {
            return;
        }
        d81Var.m2585V(true, true);
    }

    @Override
    public final void mo2008j(Live live) {
        if (m227c1()) {
            m1995N1(false);
            m2002U1(false);
            if (live.isSelected()) {
                live.getGroups().clear();
            }
            wj1 wj1Var = vj1.f19277a;
            wj1Var.m10375r(wj1Var.m3160e(), live, true);
            this.f273K.f3037x.m9336w();
            th2 th2Var = this.f273K.f3037x;
            th2Var.f17543o = null;
            th2Var.f17536h = null;
            th2Var.m9313F();
            ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7436p.setVisibility(8);
            ((iv3) this.f3090R.f20542p).f8292x.setText("");
            go0 go0Var = this.f3095W;
            go0Var.f6626c.clear();
            go0Var.notifyDataSetChanged();
            C1125lr c1125lr = this.f3094V;
            c1125lr.f10864b.clear();
            c1125lr.notifyDataSetChanged();
            go0 go0Var2 = this.f3093U;
            go0Var2.f6626c.clear();
            go0Var2.notifyDataSetChanged();
            this.f3106h0.clear();
            this.f3108j0 = null;
            this.f3107i0 = null;
            m1986E1();
            C1629t3 c1629t3 = (C1629t3) this.f3092T.f4036h;
            c1629t3.f17144h = null;
            c1629t3.f17145i = null;
            c1629t3.f17146j = null;
            c1629t3.f17147k = null;
            c1629t3.f17148l = null;
            c1629t3.f17149m = null;
            m1983C1();
        }
    }

    @Override
    public final void mo234j1() {
        this.f3091S.f12315g.m2592f(mk1.f11470j);
        c53.f2497a.m2548c();
        App.m1883c(this.f3102d0);
        RunnableC0663ie runnableC0663ie = this.f3105g0;
        if (runnableC0663ie != null) {
            App.m1883c(runnableC0663ie);
        }
        this.f3105g0 = null;
        m1982A1();
        this.f3113o0 = false;
        this.f3114p0 = false;
        yz3 yz3Var = this.f3111m0;
        if (yz3Var != null && yz3Var.f21714m != 1) {
            yz3Var.m10882b();
        }
        if (this.f273K == null || !m222Y0()) {
            return;
        }
        if (this.f273K.f3037x.f17542n > 0) {
            m213P0();
        }
        th2 th2Var = this.f273K.f3037x;
        th2Var.f17543o = null;
        if (th2Var.f17542n == 0) {
            return;
        }
        th2Var.f17542n = 0;
        th2Var.m9316c();
    }

    @Override
    public final void mo235k1(boolean z) {
        if (z || m225a1()) {
            ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7429i.setText(z ? R.string.pause : R.string.play);
        }
    }

    @Override
    public final void mo2009l(int i, int i2, String str) {
        int i3;
        yz3 yz3Var;
        if (m227c1()) {
            int iCharCount = 0;
            ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7442v.setSelected(i == 3);
            MaterialTextView materialTextView = ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7442v;
            int iM6245x = AbstractC1163ml.m6245x(i);
            if (iM6245x == 0) {
                i3 = R.string.xray_off;
            } else if (iM6245x == 1) {
                i3 = R.string.xray_starting;
            } else if (iM6245x == 2) {
                i3 = R.string.xray_on;
            } else {
                if (iM6245x != 3) {
                    throw new RuntimeException(null, null);
                }
                i3 = R.string.xray_error;
            }
            materialTextView.setText(i3);
            if (i == 3) {
                this.f3114p0 = false;
                m1982A1();
                m2002U1(true);
                if (this.f3112n0 != null) {
                    ComponentCallbacks2C0223a.m1877c(App.f2949l).m3827o(this.f3112n0);
                }
                if (this.f273K.f3037x.f17542n == 0) {
                    m213P0();
                }
                if (this.f3113o0) {
                    this.f3113o0 = false;
                    this.f273K.f3037x.m9308A(i2, false);
                    d81 d81Var = this.f3092T;
                    if (((LiveActivity) d81Var.f4037i).m227c1() && (yz3Var = ((LiveActivity) d81Var.f4037i).f3111m0) != null && yz3Var.f21714m != 1) {
                        C1629t3 c1629t3 = (C1629t3) d81Var.f4036h;
                        Channel channel = (Channel) c1629t3.f17148l;
                        if (channel != null) {
                            gk1 gk1Var = (gk1) c1629t3.f17144h;
                            if (gk1Var == null) {
                                gk1Var = (gk1) c1629t3.f17145i;
                            }
                            if (gk1Var == null || !gk1Var.m3778a(channel)) {
                                gk1Var = new gk1(channel, null, -9223372036854775807L);
                            }
                            wj1 wj1Var = vj1.f19277a;
                            if (wj1Var.f20113e != null && !channel.getGroup().isHidden()) {
                                wj1Var.f20113e.keep(channel).save();
                            }
                            d81Var.m2579N(gk1Var, true, false);
                        }
                    }
                } else {
                    this.f273K.f3037x.m9308A(i2, true);
                }
                m1994M1();
            }
            if (i != 4) {
                if (i == 1) {
                    this.f3113o0 = false;
                    this.f3114p0 = false;
                    int length = str.length();
                    while (iCharCount < length) {
                        int iCodePointAt = str.codePointAt(iCharCount);
                        if (!Character.isWhitespace(iCodePointAt)) {
                            d81.m2565U(str);
                            return;
                        }
                        iCharCount += Character.charCount(iCodePointAt);
                    }
                    return;
                }
                return;
            }
            boolean z = this.f3114p0;
            this.f3113o0 = false;
            this.f3114p0 = false;
            boolean z2 = this.f273K.f3037x.f17542n > 0;
            if (z2) {
                m1982A1();
            }
            if (z2) {
                m213P0();
            }
            if (z2) {
                this.f273K.f3037x.m9317d();
            }
            m2002U1(false);
            if (z2) {
                m1994M1();
            }
            if (!z) {
                m2005X1(str);
            }
            d81.m2565U(str);
        }
    }

    @Override
    public final void mo236l1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            ht3 ht3Var = (ht3) ((aa3) this.f3090R.f20538l).f170i;
            MaterialTextView materialTextView = ht3Var.f7437q;
            MaterialTextView materialTextView2 = ht3Var.f7433m;
            materialTextView.setText(AbstractC0463d2.m2463h(R.array.select_engine)[hc2.m4078v(th2Var)]);
            materialTextView2.setText(th2Var == null ? "" : AbstractC0463d2.m2463h(R.array.select_decode)[th2Var.f17541m]);
        }
    }

    @Override
    public final void mo237m1() {
        this.f3092T.m2574I();
    }

    @Override
    public final void mo1964o0() {
        if (((LinearLayoutCompat) ((aa3) this.f3090R.f20538l).f169h).getVisibility() == 0) {
            m1986E1();
            return;
        }
        if (((iv3) this.f3090R.f20542p).f8277i.getVisibility() == 0) {
            m1988G1();
        } else {
            if (((LinearLayoutCompat) this.f3090R.f20541o).getVisibility() == 0) {
                m1990I1();
                return;
            }
            if (isTaskRoot()) {
                startActivity(new Intent(this, (Class<?>) HomeActivity.class).addFlags(872415232));
            }
            finish();
        }
    }

    @Override
    public final void mo239o1() {
        d81 d81Var = this.f3092T;
        C1629t3 c1629t3 = (C1629t3) d81Var.f4036h;
        LiveActivity liveActivity = (LiveActivity) d81Var.f4037i;
        if (liveActivity.m227c1()) {
            String str = (String) c1629t3.f17147k;
            if (str != null && liveActivity.m227c1() && liveActivity.f273K.f3037x.m9325l() && str.equals(liveActivity.f273K.f3037x.m9319f())) {
                liveActivity.f3109k0 = str;
                liveActivity.m249y1(str);
            }
            pv1 pv1Var = (pv1) c1629t3.f17146j;
            if (pv1Var != null) {
                liveActivity.m1998Q1(pv1Var);
            }
            C1629t3 c1629t4 = (C1629t3) d81Var.f4036h;
            gk1 gk1Var = (gk1) c1629t4.f17145i;
            if (gk1Var != null && gk1Var.m3778a((Channel) c1629t4.f17148l) && !liveActivity.m1984D1()) {
                d81Var.m2574I();
                return;
            }
            if (((Channel) c1629t3.f17148l) != null) {
                gk1 gk1Var2 = (gk1) c1629t3.f17144h;
                if (gk1Var2 == null) {
                    gk1Var2 = (gk1) c1629t3.f17145i;
                }
                if (gk1Var2 == null) {
                    d81Var.m2578M();
                }
            }
        }
    }

    @Override
    public final void onDestroy() {
        long j;
        if (this.f3112n0 != null) {
            ComponentCallbacks2C0223a.m1877c(App.f2949l).m3827o(this.f3112n0);
        }
        yz3 yz3Var = this.f3111m0;
        if (yz3Var != null) {
            yz3Var.m10881a();
        }
        C1872zo c1872zo = this.f3097Y;
        Timer timer = (Timer) c1872zo.f22158k;
        if (timer != null) {
            timer.cancel();
        }
        if (((VideoActivity) c1872zo.f22156i) != null) {
            c1872zo.f22156i = null;
        }
        d53 d53Var = c53.f2497a;
        synchronized (d53Var.f3985a) {
            j = d53Var.f3989e;
        }
        id3.m4301a(new RunnableC0663ie(d53Var, j, 3));
        f30 f30Var = this.f3096X;
        App.m1883c(f30Var.f5489k);
        f30Var.f5486h.setLength(0);
        f30Var.f5488j = 0L;
        RunnableC0663ie runnableC0663ie = this.f3105g0;
        if (runnableC0663ie != null) {
            App.m1883c(runnableC0663ie);
        }
        this.f3105g0 = null;
        App.m1884d(this.f3100b0, this.f3101c0, this.f3102d0, this.f3103e0, this.f3104f0);
        super.onDestroy();
    }

    @v93(threadMode = ThreadMode.MAIN)
    public void onRefreshEvent(ep2 ep2Var) {
        if (m227c1()) {
            int iM6245x = AbstractC1163ml.m6245x(ep2Var.f5139a);
            if (iM6245x == 6) {
                mo2008j(m1980B1());
            } else {
                if (iM6245x != 8) {
                    return;
                }
                this.f3092T.m2574I();
            }
        }
    }

    @Override
    public final void onStart() {
        super.onStart();
        C1872zo c1872zo = this.f3097Y;
        c1872zo.m11053O();
        c1872zo.m11052N();
    }

    @Override
    public final void onStop() {
        m1995N1(!isFinishing() && !np3.m6628e0() && this.f273K != null && m222Y0() && m223Z0() && this.f273K.f3037x.m9325l());
        super.onStop();
        if (np3.m6628e0()) {
            this.f3097Y.m11053O();
        }
    }

    @Override
    public final void mo241p1() {
        ((iv3) this.f3090R.f20542p).f8290v.setText(this.f273K.f3037x.m9322i());
    }

    @Override
    public final void mo242q1(int i) {
        if (i == 2) {
            m2006Y1();
            return;
        }
        if (i == 3) {
            m1989H1();
            this.f273K.f3037x.m9336w();
            return;
        }
        if (i != 4) {
            return;
        }
        d81 d81Var = this.f3092T;
        LiveActivity liveActivity = (LiveActivity) d81Var.f4037i;
        if (liveActivity.m227c1() && liveActivity.f273K.f3037x.m9328o()) {
            Channel channel = (Channel) ((C1629t3) d81Var.f4036h).f17148l;
            if (channel != null) {
                Epg data = channel.getData(((LiveActivity) d81Var.f4037i).f3091S.f12317i);
                int inRange = data.getInRange();
                int selected = data.getSelected() + 1;
                EpgData epgData = (selected > inRange || selected <= 0 || selected >= data.getList().size()) ? null : data.getList().get(selected);
                if (epgData == null || !d81Var.m2583R(epgData, -9223372036854775807L)) {
                    EpgData epgDataM2604u = d81Var.m2604u(channel);
                    if (epgDataM2604u != null) {
                        ((LiveActivity) d81Var.f4037i).m1996O1(epgDataM2604u);
                    }
                    d81Var.m2574I();
                }
            }
        } else {
            d81Var.m2569B(1);
        }
        ((ht3) ((aa3) this.f3090R.f20538l).f170i).f7429i.setText(R.string.play);
    }

    @Override
    public final void mo243r1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            ht3 ht3Var = (ht3) ((aa3) this.f3090R.f20538l).f170i;
            CustomUpDownView customUpDownView = ht3Var.f7440t;
            MaterialTextView materialTextView = ht3Var.f7430j;
            MaterialTextView materialTextView2 = ht3Var.f7441u;
            CustomUpDownView customUpDownView2 = ht3Var.f7439s;
            hc2.m4058f0(th2Var, customUpDownView, materialTextView, materialTextView2);
            hc2.m4059g0(customUpDownView2, th2Var != null && th2Var.m9331r());
        }
    }

    @Override
    public final void mo2010x(Config config) {
        n61 n61Var = new n61(this, vj1.f19277a.m3160e(), 2);
        wj1 wj1Var = vj1.f19277a;
        wj1Var.f20116h = null;
        wj1Var.f20113e = null;
        wj1Var.f20114f = null;
        wj1Var.f20115g = null;
        yu2.f21617a.f2445h = true;
        wj1Var.m10371n(config);
        wj1Var.m3163h(n61Var);
    }

    public final boolean m2011z1() {
        return (isFinishing() || isDestroyed()) ? false : true;
    }
}
