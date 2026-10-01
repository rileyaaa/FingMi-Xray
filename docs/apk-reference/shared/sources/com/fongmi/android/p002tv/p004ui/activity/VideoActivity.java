package com.fongmi.android.p002tv.p004ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.text.SpannableStringBuilder;
import android.text.TextUtils;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.RelativeLayout;
import android.widget.TextView;
import androidx.appcompat.widget.AppCompatImageView;
import androidx.appcompat.widget.LinearLayoutCompat;
import androidx.core.widget.NestedScrollView;
import androidx.leanback.widget.HorizontalGridView;
import androidx.media3.p001ui.PlayerSeekView;
import androidx.media3.p001ui.PlayerView;
import com.bumptech.glide.ComponentCallbacks2C0223a;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.bean.Danmaku;
import com.fongmi.android.p002tv.bean.Episode;
import com.fongmi.android.p002tv.bean.Flag;
import com.fongmi.android.p002tv.bean.History;
import com.fongmi.android.p002tv.bean.Keep;
import com.fongmi.android.p002tv.bean.Result;
import com.fongmi.android.p002tv.bean.Sub;
import com.fongmi.android.p002tv.bean.Track;
import com.fongmi.android.p002tv.bean.Vod;
import com.fongmi.android.p002tv.p004ui.activity.VideoActivity;
import com.fongmi.android.p002tv.p004ui.custom.CustomUpDownView;
import com.fongmi.android.p002tv.p004ui.custom.ProgressLayout;
import com.fongmi.android.p002tv.service.PlaybackService;
import com.google.android.material.textview.MaterialTextView;
import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Timer;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import kotlin.jvm.JvmClassMappingKt;
import kotlin.reflect.KClass;
import org.greenrobot.eventbus.ThreadMode;
import org.simpleframework.xml.strategy.Name;
import p000.AbstractActivityC1142m7;
import p000.AbstractActivityC1828yh;
import p000.AbstractC0463d2;
import p000.AbstractC1163ml;
import p000.AbstractC1483pa;
import p000.C1206nh;
import p000.C1519q4;
import p000.C1542qr;
import p000.C1556r4;
import p000.C1566re;
import p000.C1747wa;
import p000.C1872zo;
import p000.ViewOnTouchListenerC1603se;
import p000.aa3;
import p000.af1;
import p000.af2;
import p000.ar3;
import p000.aw3;
import p000.bd2;
import p000.bl3;
import p000.br3;
import p000.bu3;
import p000.c53;
import p000.cd3;
import p000.cl3;
import p000.d81;
import p000.ep2;
import p000.es1;
import p000.fd2;
import p000.fv0;
import p000.g30;
import p000.gd2;
import p000.gp0;
import p000.h00;
import p000.h30;
import p000.ha1;
import p000.hc2;
import p000.hv3;
import p000.id3;
import p000.ig2;
import p000.it3;
import p000.j43;
import p000.jh2;
import p000.jj1;
import p000.k20;
import p000.l30;
import p000.la2;
import p000.m21;
import p000.mo0;
import p000.np3;
import p000.ns3;
import p000.o11;
import p000.op3;
import p000.os3;
import p000.p11;
import p000.p52;
import p000.p60;
import p000.pf2;
import p000.ps3;
import p000.pv1;
import p000.q11;
import p000.q50;
import p000.rc2;
import p000.rw1;
import p000.th2;
import p000.tp3;
import p000.u30;
import p000.uv3;
import p000.v11;
import p000.v93;
import p000.vq3;
import p000.vv3;
import p000.wq3;
import p000.xp0;
import p000.xz3;
import p000.yz3;
import p000.zq3;
import p000.zt3;
import p000.zv3;

public class VideoActivity extends af2 implements g30, xz3 {

    public static final int f3147q0 = 0;

    public C1556r4 f3148R;

    public os3 f3149S;

    public bd2 f3150T;

    public yz3 f3151U;

    public jj1 f3152V;

    public boolean f3153W;

    public fv0 f3154X;

    public mo0 f3155Y;

    public C1542qr f3156Z;

    public C1747wa f3157a0;

    public fd2 f3158b0;

    public fv0 f3159c0;

    public ViewGroup.LayoutParams f3160d0;

    public h30 f3161e0;

    public C1872zo f3162f0;

    public View f3163g0;

    public View f3164h0;

    public wq3 f3165i0;

    public wq3 f3166j0;

    public wq3 f3167k0;

    public wq3 f3168l0;

    public History f3169m0;

    public boolean f3171o0;

    public int f3170n0 = -1;

    public final br3 f3172p0 = new br3(this);

    public static void m2033R1(AbstractActivityC1142m7 abstractActivityC1142m7, String str) {
        Uri uriM7959U = q11.m7959U(str);
        try {
            if (DocumentsContract.isDocumentUri(abstractActivityC1142m7, uriM7959U) || "content".equals(uriM7959U.getScheme()) || "file".equalsIgnoreCase(uriM7959U.getScheme())) {
                String strM7723l = AbstractC1483pa.m7723l(uriM7959U);
                if (TextUtils.isEmpty(strM7723l)) {
                    return;
                }
                m2034j2(abstractActivityC1142m7, "push_agent", xp0.m10580j("file://", strM7723l), new File(strM7723l).getName(), null, null);
                return;
            }
        } catch (Exception unused) {
        }
        String strM4986b = j43.m4986b(str);
        m2034j2(abstractActivityC1142m7, "push_agent", strM4986b, strM4986b, null, null);
    }

    public static void m2034j2(Activity activity, String str, String str2, String str3, String str4, String str5) {
        m2035k2(activity, str, str2, str3, str4, str5, false, false);
    }

    public static void m2035k2(Activity activity, String str, String str2, String str3, String str4, String str5, boolean z, boolean z2) {
        Intent intent = new Intent(activity, (Class<?>) VideoActivity.class);
        intent.putExtra("collect", z);
        intent.putExtra("cast", z2);
        intent.putExtra("mark", str5);
        intent.putExtra("name", str3);
        intent.putExtra("pic", str4);
        intent.putExtra("key", str);
        intent.putExtra(Name.MARK, str2);
        activity.startActivity(intent);
    }

    public final void m2036A1() {
        if (m227c1()) {
            bd2 bd2Var = this.f3150T;
            if (((VideoActivity) bd2Var.f1919a).m227c1()) {
                History history = ((aw3) bd2Var.f1920b).f1594j;
                if (history == null || !history.isRevPlay()) {
                    bd2Var.m1205p(true, false);
                } else {
                    bd2Var.m1201l(true, true);
                }
            }
        }
    }

    public final void m2037B1() {
        this.f3163g0 = getCurrentFocus();
        this.f3148R.f15414C.requestFocus();
        this.f3148R.f15414C.setForeground(null);
        this.f3148R.f15414C.setLayoutParams(new RelativeLayout.LayoutParams(-1, -1));
        HorizontalGridView horizontalGridView = this.f3148R.f15426p;
        ArrayList arrayList = this.f3154X.f6072c;
        int i = 0;
        for (int i2 = 0; i2 < arrayList.size(); i2++) {
            if (((Flag) arrayList.get(i2)).isSelected()) {
                i = i2;
                break;
            }
        }
        horizontalGridView.setSelectedPosition(i);
        this.f3161e0.f6868j = true;
        this.f3171o0 = true;
        this.f3164h0 = null;
    }

    public final int m2038C1(int i) {
        List listAsList = Arrays.asList(Integer.valueOf(R.id.flag), Integer.valueOf(R.id.quality), Integer.valueOf(R.id.episode), Integer.valueOf(R.id.array), Integer.valueOf(R.id.part), Integer.valueOf(R.id.quick));
        for (int i2 = 0; i2 < listAsList.size(); i2++) {
            if (i2 > i && AbstractActivityC1828yh.m10758I0(findViewById(((Integer) listAsList.get(i2)).intValue()))) {
                return ((Integer) listAsList.get(i2)).intValue();
            }
        }
        return 0;
    }

    public final int m2039D1(int i) {
        List listAsList = Arrays.asList(Integer.valueOf(R.id.flag), Integer.valueOf(R.id.quality), Integer.valueOf(R.id.episode), Integer.valueOf(R.id.array), Integer.valueOf(R.id.part), Integer.valueOf(R.id.quick));
        for (int size = listAsList.size() - 1; size >= 0; size--) {
            if (size < i && AbstractActivityC1828yh.m10758I0(findViewById(((Integer) listAsList.get(size)).intValue()))) {
                return ((Integer) listAsList.get(size)).intValue();
            }
        }
        return 0;
    }

    @Override
    public final void mo1947E(long j) {
        if (m227c1()) {
            this.f3148R.f15415D.f7488j.setVisibility(0);
            this.f3148R.f15415D.f7490l.setText(this.f273K.f3037x.m9318e());
            this.f3148R.f15415D.f7493o.setText(this.f273K.f3037x.m9320g(j));
            this.f3148R.f15415D.f7487i.setImageResource(j > 0 ? R.drawable.ic_widget_forward : R.drawable.ic_widget_rewind);
            m2049N1();
        }
    }

    /* JADX WARN: Code duplicated, block: B:121:0x0318 A[PHI: r5
      0x0318: PHI (r5v2 int) = (r5v1 int), (r5v3 int) binds: [B:89:0x022b, B:91:0x0236] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:122:0x031a A[PHI: r12
      0x031a: PHI (r12v19 int) = (r12v18 int), (r12v20 int), (r12v21 int), (r12v22 int), (r12v23 int), (r12v24 int), (r12v25 int), (r12v26 int) binds: [B:73:0x01d6, B:75:0x01e1, B:77:0x01ec, B:79:0x01f7, B:81:0x0202, B:83:0x020d, B:85:0x0218, B:87:0x0223] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:123:0x031c A[PHI: r11
      0x031c: PHI (r11v16 int) = (r11v11 int), (r11v17 int) binds: [B:69:0x01ba, B:71:0x01c3] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:124:0x031e A[PHI: r3
      0x031e: PHI (r3v3 int) = (r3v2 int), (r3v4 int), (r3v5 int), (r3v6 int), (r3v7 int), (r3v8 int) binds: [B:57:0x017b, B:59:0x0186, B:61:0x0191, B:63:0x019c, B:65:0x01a7, B:67:0x01b2] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:130:0x0336 A[PHI: r12
      0x0336: PHI (r12v11 int) = (r12v10 int), (r12v12 int), (r12v13 int), (r12v14 int), (r12v15 int), (r12v16 int) binds: [B:37:0x00e9, B:39:0x00f6, B:41:0x0103, B:43:0x0110, B:45:0x011d, B:47:0x012a] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:131:0x033a A[PHI: r11
      0x033a: PHI (r11v1 int) = 
      (r11v0 int)
      (r11v3 int)
      (r11v4 int)
      (r11v5 int)
      (r11v6 int)
      (r11v7 int)
      (r11v8 int)
      (r11v9 int)
      (r11v10 int)
      (r11v11 int)
     binds: [B:17:0x0067, B:19:0x0074, B:21:0x0081, B:23:0x008e, B:25:0x009b, B:27:0x00a8, B:29:0x00b5, B:31:0x00c2, B:33:0x00cf, B:35:0x00dc] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:136:0x035c A[PHI: r1
      0x035c: PHI (r1v2 int) = (r1v1 int), (r1v4 int), (r1v5 int), (r1v6 int), (r1v7 int), (r1v8 int) binds: [B:3:0x0019, B:5:0x0025, B:7:0x0031, B:9:0x003d, B:11:0x0049, B:13:0x0052] A[DONT_GENERATE, DONT_INLINE]] */
    @Override
    public final ps3 mo1948E0() {
        ps3 ps3Var;
        View viewInflate = getLayoutInflater().inflate(R.layout.activity_video, (ViewGroup) null, false);
        int i = R.id.actor;
        MaterialTextView materialTextView = (MaterialTextView) rw1.m8781l(R.id.actor, viewInflate);
        if (materialTextView != null) {
            i = R.id.area;
            MaterialTextView materialTextView2 = (MaterialTextView) rw1.m8781l(R.id.area, viewInflate);
            if (materialTextView2 != null) {
                i = R.id.array;
                HorizontalGridView horizontalGridView = (HorizontalGridView) rw1.m8781l(R.id.array, viewInflate);
                if (horizontalGridView != null) {
                    i = R.id.change;
                    MaterialTextView materialTextView3 = (MaterialTextView) rw1.m8781l(R.id.change, viewInflate);
                    if (materialTextView3 != null) {
                        i = R.id.content;
                        MaterialTextView materialTextView4 = (MaterialTextView) rw1.m8781l(R.id.content, viewInflate);
                        if (materialTextView4 != null) {
                            i = R.id.control;
                            View viewM8781l = rw1.m8781l(R.id.control, viewInflate);
                            if (viewM8781l != null) {
                                int i2 = R.id.action;
                                View viewM8781l2 = rw1.m8781l(R.id.action, viewM8781l);
                                if (viewM8781l2 != null) {
                                    int i3 = R.id.audio;
                                    MaterialTextView materialTextView5 = (MaterialTextView) rw1.m8781l(R.id.audio, viewM8781l2);
                                    if (materialTextView5 != null) {
                                        i3 = R.id.chapter;
                                        MaterialTextView materialTextView6 = (MaterialTextView) rw1.m8781l(R.id.chapter, viewM8781l2);
                                        if (materialTextView6 != null) {
                                            i3 = R.id.danmaku;
                                            MaterialTextView materialTextView7 = (MaterialTextView) rw1.m8781l(R.id.danmaku, viewM8781l2);
                                            if (materialTextView7 != null) {
                                                i3 = R.id.decode;
                                                MaterialTextView materialTextView8 = (MaterialTextView) rw1.m8781l(R.id.decode, viewM8781l2);
                                                if (materialTextView8 != null) {
                                                    i3 = R.id.edition;
                                                    MaterialTextView materialTextView9 = (MaterialTextView) rw1.m8781l(R.id.edition, viewM8781l2);
                                                    if (materialTextView9 != null) {
                                                        i3 = R.id.ending;
                                                        CustomUpDownView customUpDownView = (CustomUpDownView) rw1.m8781l(R.id.ending, viewM8781l2);
                                                        if (customUpDownView != null) {
                                                            i3 = R.id.next;
                                                            MaterialTextView materialTextView10 = (MaterialTextView) rw1.m8781l(R.id.next, viewM8781l2);
                                                            if (materialTextView10 != null) {
                                                                i3 = R.id.opening;
                                                                CustomUpDownView customUpDownView2 = (CustomUpDownView) rw1.m8781l(R.id.opening, viewM8781l2);
                                                                if (customUpDownView2 != null) {
                                                                    i3 = R.id.parse;
                                                                    MaterialTextView materialTextView11 = (MaterialTextView) rw1.m8781l(R.id.parse, viewM8781l2);
                                                                    if (materialTextView11 != null) {
                                                                        i3 = R.id.player;
                                                                        MaterialTextView materialTextView12 = (MaterialTextView) rw1.m8781l(R.id.player, viewM8781l2);
                                                                        if (materialTextView12 != null) {
                                                                            int i4 = R.id.prev;
                                                                            MaterialTextView materialTextView13 = (MaterialTextView) rw1.m8781l(R.id.prev, viewM8781l2);
                                                                            if (materialTextView13 != null) {
                                                                                i4 = R.id.repeat;
                                                                                MaterialTextView materialTextView14 = (MaterialTextView) rw1.m8781l(R.id.repeat, viewM8781l2);
                                                                                if (materialTextView14 != null) {
                                                                                    i4 = R.id.replay;
                                                                                    MaterialTextView materialTextView15 = (MaterialTextView) rw1.m8781l(R.id.replay, viewM8781l2);
                                                                                    if (materialTextView15 != null) {
                                                                                        i4 = R.id.reset;
                                                                                        MaterialTextView materialTextView16 = (MaterialTextView) rw1.m8781l(R.id.reset, viewM8781l2);
                                                                                        if (materialTextView16 != null) {
                                                                                            i4 = R.id.scale;
                                                                                            MaterialTextView materialTextView17 = (MaterialTextView) rw1.m8781l(R.id.scale, viewM8781l2);
                                                                                            if (materialTextView17 != null) {
                                                                                                i4 = R.id.speed;
                                                                                                CustomUpDownView customUpDownView3 = (CustomUpDownView) rw1.m8781l(R.id.speed, viewM8781l2);
                                                                                                if (customUpDownView3 != null) {
                                                                                                    CustomUpDownView customUpDownView4 = (CustomUpDownView) rw1.m8781l(R.id.text, viewM8781l2);
                                                                                                    if (customUpDownView4 != null) {
                                                                                                        MaterialTextView materialTextView18 = (MaterialTextView) rw1.m8781l(R.id.video, viewM8781l2);
                                                                                                        if (materialTextView18 != null) {
                                                                                                            MaterialTextView materialTextView19 = (MaterialTextView) rw1.m8781l(R.id.xray, viewM8781l2);
                                                                                                            if (materialTextView19 != null) {
                                                                                                                HorizontalScrollView horizontalScrollView = (HorizontalScrollView) viewM8781l2;
                                                                                                                int i5 = R.id.video;
                                                                                                                it3 it3Var = new it3(horizontalScrollView, materialTextView5, materialTextView6, materialTextView7, materialTextView8, materialTextView9, customUpDownView, materialTextView10, customUpDownView2, materialTextView11, materialTextView12, materialTextView13, materialTextView14, materialTextView15, materialTextView16, materialTextView17, customUpDownView3, customUpDownView4, materialTextView18, materialTextView19);
                                                                                                                PlayerSeekView playerSeekView = (PlayerSeekView) rw1.m8781l(R.id.seek, viewM8781l);
                                                                                                                if (playerSeekView != null) {
                                                                                                                    ps3Var = null;
                                                                                                                    aa3 aa3Var = new aa3(7, (LinearLayoutCompat) viewM8781l, it3Var, playerSeekView);
                                                                                                                    int i6 = R.id.director;
                                                                                                                    MaterialTextView materialTextView20 = (MaterialTextView) rw1.m8781l(R.id.director, viewInflate);
                                                                                                                    if (materialTextView20 != null) {
                                                                                                                        i6 = R.id.episode;
                                                                                                                        HorizontalGridView horizontalGridView2 = (HorizontalGridView) rw1.m8781l(R.id.episode, viewInflate);
                                                                                                                        if (horizontalGridView2 != null) {
                                                                                                                            i6 = R.id.flag;
                                                                                                                            HorizontalGridView horizontalGridView3 = (HorizontalGridView) rw1.m8781l(R.id.flag, viewInflate);
                                                                                                                            if (horizontalGridView3 != null) {
                                                                                                                                i6 = R.id.keep;
                                                                                                                                MaterialTextView materialTextView21 = (MaterialTextView) rw1.m8781l(R.id.keep, viewInflate);
                                                                                                                                if (materialTextView21 != null) {
                                                                                                                                    i6 = R.id.name;
                                                                                                                                    MaterialTextView materialTextView22 = (MaterialTextView) rw1.m8781l(R.id.name, viewInflate);
                                                                                                                                    if (materialTextView22 != null) {
                                                                                                                                        i6 = R.id.part;
                                                                                                                                        HorizontalGridView horizontalGridView4 = (HorizontalGridView) rw1.m8781l(R.id.part, viewInflate);
                                                                                                                                        if (horizontalGridView4 != null) {
                                                                                                                                            PlayerView playerView = (PlayerView) rw1.m8781l(R.id.player, viewInflate);
                                                                                                                                            if (playerView != null) {
                                                                                                                                                i3 = R.id.progress;
                                                                                                                                                View viewM8781l3 = rw1.m8781l(R.id.progress, viewInflate);
                                                                                                                                                if (viewM8781l3 != null) {
                                                                                                                                                    d81 d81VarM2566d = d81.m2566d(viewM8781l3);
                                                                                                                                                    ProgressLayout progressLayout = (ProgressLayout) viewInflate;
                                                                                                                                                    int i7 = R.id.quality;
                                                                                                                                                    HorizontalGridView horizontalGridView5 = (HorizontalGridView) rw1.m8781l(R.id.quality, viewInflate);
                                                                                                                                                    if (horizontalGridView5 != null) {
                                                                                                                                                        i7 = R.id.quick;
                                                                                                                                                        HorizontalGridView horizontalGridView6 = (HorizontalGridView) rw1.m8781l(R.id.quick, viewInflate);
                                                                                                                                                        if (horizontalGridView6 != null) {
                                                                                                                                                            i7 = R.id.remark;
                                                                                                                                                            MaterialTextView materialTextView23 = (MaterialTextView) rw1.m8781l(R.id.remark, viewInflate);
                                                                                                                                                            if (materialTextView23 != null) {
                                                                                                                                                                i7 = R.id.row1;
                                                                                                                                                                if (((LinearLayoutCompat) rw1.m8781l(R.id.row1, viewInflate)) != null) {
                                                                                                                                                                    i7 = R.id.row2;
                                                                                                                                                                    if (((LinearLayoutCompat) rw1.m8781l(R.id.row2, viewInflate)) != null) {
                                                                                                                                                                        i7 = R.id.scroll;
                                                                                                                                                                        NestedScrollView nestedScrollView = (NestedScrollView) rw1.m8781l(R.id.scroll, viewInflate);
                                                                                                                                                                        if (nestedScrollView != null) {
                                                                                                                                                                            i7 = R.id.site;
                                                                                                                                                                            MaterialTextView materialTextView24 = (MaterialTextView) rw1.m8781l(R.id.site, viewInflate);
                                                                                                                                                                            if (materialTextView24 != null) {
                                                                                                                                                                                i7 = R.id.type;
                                                                                                                                                                                MaterialTextView materialTextView25 = (MaterialTextView) rw1.m8781l(R.id.type, viewInflate);
                                                                                                                                                                                if (materialTextView25 != null) {
                                                                                                                                                                                    FrameLayout frameLayout = (FrameLayout) rw1.m8781l(i5, viewInflate);
                                                                                                                                                                                    if (frameLayout != null) {
                                                                                                                                                                                        i5 = R.id.widget;
                                                                                                                                                                                        View viewM8781l4 = rw1.m8781l(R.id.widget, viewInflate);
                                                                                                                                                                                        if (viewM8781l4 != null) {
                                                                                                                                                                                            AppCompatImageView appCompatImageView = (AppCompatImageView) rw1.m8781l(R.id.action, viewM8781l4);
                                                                                                                                                                                            if (appCompatImageView != null) {
                                                                                                                                                                                                i2 = R.id.center;
                                                                                                                                                                                                LinearLayoutCompat linearLayoutCompat = (LinearLayoutCompat) rw1.m8781l(R.id.center, viewM8781l4);
                                                                                                                                                                                                if (linearLayoutCompat != null) {
                                                                                                                                                                                                    i2 = R.id.clock;
                                                                                                                                                                                                    MaterialTextView materialTextView26 = (MaterialTextView) rw1.m8781l(R.id.clock, viewM8781l4);
                                                                                                                                                                                                    if (materialTextView26 != null) {
                                                                                                                                                                                                        i2 = R.id.duration;
                                                                                                                                                                                                        MaterialTextView materialTextView27 = (MaterialTextView) rw1.m8781l(R.id.duration, viewM8781l4);
                                                                                                                                                                                                        if (materialTextView27 != null) {
                                                                                                                                                                                                            i2 = R.id.error;
                                                                                                                                                                                                            LinearLayoutCompat linearLayoutCompat2 = (LinearLayoutCompat) rw1.m8781l(R.id.error, viewM8781l4);
                                                                                                                                                                                                            if (linearLayoutCompat2 != null) {
                                                                                                                                                                                                                i2 = R.id.message;
                                                                                                                                                                                                                MaterialTextView materialTextView28 = (MaterialTextView) rw1.m8781l(R.id.message, viewM8781l4);
                                                                                                                                                                                                                if (materialTextView28 != null) {
                                                                                                                                                                                                                    i2 = R.id.position;
                                                                                                                                                                                                                    MaterialTextView materialTextView29 = (MaterialTextView) rw1.m8781l(R.id.position, viewM8781l4);
                                                                                                                                                                                                                    if (materialTextView29 != null) {
                                                                                                                                                                                                                        i2 = R.id.size;
                                                                                                                                                                                                                        MaterialTextView materialTextView30 = (MaterialTextView) rw1.m8781l(R.id.size, viewM8781l4);
                                                                                                                                                                                                                        if (materialTextView30 != null) {
                                                                                                                                                                                                                            MaterialTextView materialTextView31 = (MaterialTextView) rw1.m8781l(R.id.text, viewM8781l4);
                                                                                                                                                                                                                            if (materialTextView31 != null) {
                                                                                                                                                                                                                                i2 = R.id.title;
                                                                                                                                                                                                                                MaterialTextView materialTextView32 = (MaterialTextView) rw1.m8781l(R.id.title, viewM8781l4);
                                                                                                                                                                                                                                if (materialTextView32 != null) {
                                                                                                                                                                                                                                    i2 = R.id.top;
                                                                                                                                                                                                                                    RelativeLayout relativeLayout = (RelativeLayout) rw1.m8781l(R.id.top, viewM8781l4);
                                                                                                                                                                                                                                    if (relativeLayout != null) {
                                                                                                                                                                                                                                        hv3 hv3Var = new hv3((FrameLayout) viewM8781l4, appCompatImageView, linearLayoutCompat, materialTextView26, materialTextView27, linearLayoutCompat2, materialTextView28, materialTextView29, materialTextView30, materialTextView31, materialTextView32, relativeLayout, 1);
                                                                                                                                                                                                                                        i = R.id.year;
                                                                                                                                                                                                                                        MaterialTextView materialTextView33 = (MaterialTextView) rw1.m8781l(R.id.year, viewInflate);
                                                                                                                                                                                                                                        if (materialTextView33 != null) {
                                                                                                                                                                                                                                            C1556r4 c1556r4 = new C1556r4(progressLayout, materialTextView, materialTextView2, horizontalGridView, materialTextView3, materialTextView4, aa3Var, materialTextView20, horizontalGridView2, horizontalGridView3, materialTextView21, materialTextView22, horizontalGridView4, playerView, d81VarM2566d, progressLayout, horizontalGridView5, horizontalGridView6, materialTextView23, nestedScrollView, materialTextView24, materialTextView25, frameLayout, hv3Var, materialTextView33);
                                                                                                                                                                                                                                            this.f3148R = c1556r4;
                                                                                                                                                                                                                                            return c1556r4;
                                                                                                                                                                                                                                        }
                                                                                                                                                                                                                                    }
                                                                                                                                                                                                                                }
                                                                                                                                                                                                                            } else {
                                                                                                                                                                                                                                i2 = R.id.text;
                                                                                                                                                                                                                            }
                                                                                                                                                                                                                        }
                                                                                                                                                                                                                    }
                                                                                                                                                                                                                }
                                                                                                                                                                                                            }
                                                                                                                                                                                                        }
                                                                                                                                                                                                    }
                                                                                                                                                                                                }
                                                                                                                                                                                            }
                                                                                                                                                                                            h00.m3905e("Missing required view with ID: ".concat(viewM8781l4.getResources().getResourceName(i2)));
                                                                                                                                                                                            return null;
                                                                                                                                                                                        }
                                                                                                                                                                                        i = i5;
                                                                                                                                                                                    } else {
                                                                                                                                                                                        i = i5;
                                                                                                                                                                                    }
                                                                                                                                                                                } else {
                                                                                                                                                                                    i = i7;
                                                                                                                                                                                }
                                                                                                                                                                            } else {
                                                                                                                                                                                i = i7;
                                                                                                                                                                            }
                                                                                                                                                                        } else {
                                                                                                                                                                            i = i7;
                                                                                                                                                                        }
                                                                                                                                                                    } else {
                                                                                                                                                                        i = i7;
                                                                                                                                                                    }
                                                                                                                                                                } else {
                                                                                                                                                                    i = i7;
                                                                                                                                                                }
                                                                                                                                                            } else {
                                                                                                                                                                i = i7;
                                                                                                                                                            }
                                                                                                                                                        } else {
                                                                                                                                                            i = i7;
                                                                                                                                                        }
                                                                                                                                                    } else {
                                                                                                                                                        i = i7;
                                                                                                                                                    }
                                                                                                                                                } else {
                                                                                                                                                    i = i3;
                                                                                                                                                }
                                                                                                                                            } else {
                                                                                                                                                i = i3;
                                                                                                                                            }
                                                                                                                                        } else {
                                                                                                                                            i = i6;
                                                                                                                                        }
                                                                                                                                    } else {
                                                                                                                                        i = i6;
                                                                                                                                    }
                                                                                                                                } else {
                                                                                                                                    i = i6;
                                                                                                                                }
                                                                                                                            } else {
                                                                                                                                i = i6;
                                                                                                                            }
                                                                                                                        } else {
                                                                                                                            i = i6;
                                                                                                                        }
                                                                                                                    } else {
                                                                                                                        i = i6;
                                                                                                                    }
                                                                                                                } else {
                                                                                                                    i2 = R.id.seek;
                                                                                                                }
                                                                                                            } else {
                                                                                                                i3 = R.id.xray;
                                                                                                            }
                                                                                                        } else {
                                                                                                            i3 = R.id.video;
                                                                                                        }
                                                                                                    } else {
                                                                                                        i3 = R.id.text;
                                                                                                    }
                                                                                                } else {
                                                                                                    i3 = i4;
                                                                                                }
                                                                                            } else {
                                                                                                i3 = i4;
                                                                                            }
                                                                                        } else {
                                                                                            i3 = i4;
                                                                                        }
                                                                                    } else {
                                                                                        i3 = i4;
                                                                                    }
                                                                                } else {
                                                                                    i3 = i4;
                                                                                }
                                                                            } else {
                                                                                i3 = i4;
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
                                    h00.m3905e("Missing required view with ID: ".concat(viewM8781l2.getResources().getResourceName(i3)));
                                    return 0;
                                }
                                h00.m3905e("Missing required view with ID: ".concat(viewM8781l.getResources().getResourceName(i2)));
                                return null;
                            }
                            ps3Var = null;
                        } else {
                            ps3Var = null;
                        }
                    } else {
                        ps3Var = null;
                    }
                } else {
                    ps3Var = null;
                }
            } else {
                ps3Var = null;
            }
        } else {
            ps3Var = null;
        }
        h00.m3905e("Missing required view with ID: ".concat(viewInflate.getResources().getResourceName(i)));
        return ps3Var;
    }

    public final View m2040E1() {
        View view = this.f3164h0;
        if (view != null && view.getVisibility() == 0) {
            View view2 = this.f3164h0;
            it3 it3Var = (it3) this.f3148R.f15423m.f170i;
            if (view2 != it3Var.f8216o && view2 != it3Var.f8214m) {
                return view2;
            }
        }
        return ((it3) this.f3148R.f15423m.f170i).f8215n;
    }

    @Override
    public final void mo1950F() {
        if (this.f3171o0) {
            mo1962h0();
        }
    }

    @Override
    public final void mo1951F0() {
        final int i = 0;
        this.f3148R.f15427q.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i2 = i;
                int i3 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i2) {
                    case 0:
                        int i4 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i5 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i3));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i6 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i7 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i8 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i8;
                            th2Var.f17533e.mo4114A(i8);
                            th2Var.f17531c.f3029p.forEach(new jf2(i3));
                            break;
                        }
                        break;
                    case 4:
                        int i9 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i10 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i11 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i12 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i2 = 2;
        this.f3148R.f15414C.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i3 = i2;
                int i4 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i3) {
                    case 0:
                        int i5 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i6 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i4));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i7 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i8 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i9 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i9;
                            th2Var.f17533e.mo4114A(i9);
                            th2Var.f17531c.f3029p.forEach(new jf2(i4));
                            break;
                        }
                        break;
                    case 4:
                        int i10 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i11 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i12 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i3 = 10;
        this.f3148R.f15421k.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i4 = i3;
                int i5 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i4) {
                    case 0:
                        int i6 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i7 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i5));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i8 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i9 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i10 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i10;
                            th2Var.f17533e.mo4114A(i10);
                            th2Var.f17531c.f3029p.forEach(new jf2(i5));
                            break;
                        }
                        break;
                    case 4:
                        int i11 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i12 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i4 = 11;
        this.f3148R.f15422l.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i5 = i4;
                int i6 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i5) {
                    case 0:
                        int i7 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i8 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i6));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i9 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i10 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i11 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i11;
                            th2Var.f17533e.mo4114A(i11);
                            th2Var.f17531c.f3029p.forEach(new jf2(i6));
                            break;
                        }
                        break;
                    case 4:
                        int i12 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i5 = 12;
        ((it3) this.f3148R.f15423m.f170i).f8225x.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i6 = i5;
                int i7 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i6) {
                    case 0:
                        int i8 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i9 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i7));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i10 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i11 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i12 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i12;
                            th2Var.f17533e.mo4114A(i12);
                            th2Var.f17531c.f3029p.forEach(new jf2(i7));
                            break;
                        }
                        break;
                    case 4:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8209h.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i6 = i5;
                int i7 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i6) {
                    case 0:
                        int i8 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i9 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i7));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i10 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i11 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i12 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i12;
                            th2Var.f17533e.mo4114A(i12);
                            th2Var.f17531c.f3029p.forEach(new jf2(i7));
                            break;
                        }
                        break;
                    case 4:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8226y.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i6 = i5;
                int i7 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i6) {
                    case 0:
                        int i8 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i9 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i7));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i10 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i11 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i12 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i12;
                            th2Var.f17533e.mo4114A(i12);
                            th2Var.f17531c.f3029p.forEach(new jf2(i7));
                            break;
                        }
                        break;
                    case 4:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i6 = 1;
        ((it3) this.f3148R.f15423m.f170i).f8214m.setUpListener(new vq3(this, i6));
        ((it3) this.f3148R.f15423m.f170i).f8214m.setDownListener(new vq3(this, i2));
        final int i7 = 3;
        ((it3) this.f3148R.f15423m.f170i).f8216o.setUpListener(new vq3(this, i7));
        ((it3) this.f3148R.f15423m.f170i).f8216o.setDownListener(new vq3(this, i));
        final int i8 = 13;
        ((it3) this.f3148R.f15423m.f170i).f8215n.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i9 = i8;
                int i10 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i9) {
                    case 0:
                        int i11 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i12 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i10));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i13 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i15 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i15;
                            th2Var.f17533e.mo4114A(i15);
                            th2Var.f17531c.f3029p.forEach(new jf2(i10));
                            break;
                        }
                        break;
                    case 4:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i9 = 14;
        ((it3) this.f3148R.f15423m.f170i).f8227z.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i10 = i9;
                int i11 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i10) {
                    case 0:
                        int i12 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i13 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i11));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i14 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i16 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i16;
                            th2Var.f17533e.mo4114A(i16);
                            th2Var.f17531c.f3029p.forEach(new jf2(i11));
                            break;
                        }
                        break;
                    case 4:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i10 = 15;
        ((it3) this.f3148R.f15423m.f170i).f8219r.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i11 = i10;
                int i12 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i11) {
                    case 0:
                        int i13 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i14 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i12));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i15 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i17 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i17;
                            th2Var.f17533e.mo4114A(i17);
                            th2Var.f17531c.f3029p.forEach(new jf2(i12));
                            break;
                        }
                        break;
                    case 4:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i11 = 16;
        ((it3) this.f3148R.f15423m.f170i).f8223v.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i12 = i11;
                int i13 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i12) {
                    case 0:
                        int i14 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i15 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i13));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i16 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i18 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i18;
                            th2Var.f17533e.mo4114A(i18);
                            th2Var.f17531c.f3029p.forEach(new jf2(i13));
                            break;
                        }
                        break;
                    case 4:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i12 = 17;
        ((it3) this.f3148R.f15423m.f170i).f8224w.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i13 = i12;
                int i14 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i13) {
                    case 0:
                        int i15 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i16 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i14));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i17 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i19 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i19;
                            th2Var.f17533e.mo4114A(i19);
                            th2Var.f17531c.f3029p.forEach(new jf2(i14));
                            break;
                        }
                        break;
                    case 4:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i13 = 18;
        ((it3) this.f3148R.f15423m.f170i).f8222u.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i14 = i13;
                int i15 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i14) {
                    case 0:
                        int i16 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i17 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i15));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i18 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i110 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i110;
                            th2Var.f17533e.mo4114A(i110);
                            th2Var.f17531c.f3029p.forEach(new jf2(i15));
                            break;
                        }
                        break;
                    case 4:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i14 = 19;
        ((it3) this.f3148R.f15423m.f170i).f8221t.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i15 = i14;
                int i16 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i15) {
                    case 0:
                        int i17 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i18 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i16));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i19 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i111 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i111;
                            th2Var.f17533e.mo4114A(i111);
                            th2Var.f17531c.f3029p.forEach(new jf2(i16));
                            break;
                        }
                        break;
                    case 4:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i15 = 20;
        ((it3) this.f3148R.f15423m.f170i).f8217p.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i16 = i15;
                int i17 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i16) {
                    case 0:
                        int i18 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i17));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i110 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i112 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i112;
                            th2Var.f17533e.mo4114A(i112);
                            th2Var.f17531c.f3029p.forEach(new jf2(i17));
                            break;
                        }
                        break;
                    case 4:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8218q.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i16 = i6;
                int i17 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i16) {
                    case 0:
                        int i18 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i17));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i110 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i112 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i112;
                            th2Var.f17533e.mo4114A(i112);
                            th2Var.f17531c.f3029p.forEach(new jf2(i17));
                            break;
                        }
                        break;
                    case 4:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8212k.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i16 = i7;
                int i17 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i16) {
                    case 0:
                        int i18 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i19 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i17));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i110 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i112 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i112;
                            th2Var.f17533e.mo4114A(i112);
                            th2Var.f17531c.f3029p.forEach(new jf2(i17));
                            break;
                        }
                        break;
                    case 4:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i16 = 4;
        ((it3) this.f3148R.f15423m.f170i).f8214m.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i17 = i16;
                int i18 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i17) {
                    case 0:
                        int i19 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i18));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i111 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i113 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i113;
                            th2Var.f17533e.mo4114A(i113);
                            th2Var.f17531c.f3029p.forEach(new jf2(i18));
                            break;
                        }
                        break;
                    case 4:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i17 = 5;
        ((it3) this.f3148R.f15423m.f170i).f8220s.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i18 = i17;
                int i19 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i18) {
                    case 0:
                        int i110 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i19));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i112 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i114 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i114;
                            th2Var.f17533e.mo4114A(i114);
                            th2Var.f17531c.f3029p.forEach(new jf2(i19));
                            break;
                        }
                        break;
                    case 4:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i18 = 6;
        ((it3) this.f3148R.f15423m.f170i).f8211j.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i19 = i18;
                int i110 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i19) {
                    case 0:
                        int i111 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i110));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i113 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i115 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i115;
                            th2Var.f17533e.mo4114A(i115);
                            th2Var.f17531c.f3029p.forEach(new jf2(i110));
                            break;
                        }
                        break;
                    case 4:
                        int i116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1114 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i19 = 7;
        ((it3) this.f3148R.f15423m.f170i).f8213l.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i110 = i19;
                int i111 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i110) {
                    case 0:
                        int i112 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i111));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i114 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i116 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i116;
                            th2Var.f17533e.mo4114A(i116);
                            th2Var.f17531c.f3029p.forEach(new jf2(i111));
                            break;
                        }
                        break;
                    case 4:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1114 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i20 = videoActivity.f3151U.f21714m;
                            if (i20 == 2 || i20 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i21 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i22 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i23 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i26 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i20 = 8;
        ((it3) this.f3148R.f15423m.f170i).f8210i.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i110 = i20;
                int i111 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i110) {
                    case 0:
                        int i112 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i111));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i114 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i116 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i116;
                            th2Var.f17533e.mo4114A(i116);
                            th2Var.f17531c.f3029p.forEach(new jf2(i111));
                            break;
                        }
                        break;
                    case 4:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1114 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i21 = videoActivity.f3151U.f21714m;
                            if (i21 == 2 || i21 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i22 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i23 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i24 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i26 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i27 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        final int i21 = 9;
        ((it3) this.f3148R.f15423m.f170i).f8216o.setOnClickListener(new View.OnClickListener(this) {

            public final VideoActivity f17740h;

            {
                this.f17740h = this;
            }

            @Override
            public final void onClick(View view) {
                int i110 = i21;
                int i111 = 4;
                VideoActivity videoActivity = this.f17740h;
                switch (i110) {
                    case 0:
                        int i112 = VideoActivity.f3147q0;
                        Keep keepFind = Keep.find(videoActivity.m2041F1());
                        d81.m2564T(keepFind != null ? R.string.keep_del : R.string.keep_add);
                        if (keepFind != null) {
                            keepFind.delete();
                        } else {
                            Keep keep = new Keep();
                            keep.setKey(videoActivity.m2041F1());
                            keep.setCid(vv3.m10210o());
                            keep.setVodPic(videoActivity.f3169m0.getVodPic());
                            keep.setVodName(videoActivity.f3169m0.getVodName());
                            keep.setSiteName(uv3.f18675a.m10216s(videoActivity.m2043H1()).getName());
                            keep.setCreateTime(System.currentTimeMillis());
                            keep.save();
                        }
                        videoActivity.f3148R.f15427q.setCompoundDrawablesWithIntrinsicBounds(Keep.find(videoActivity.m2041F1()) == null ? R.drawable.ic_detail_keep_off : R.drawable.ic_detail_keep_on, 0, 0, 0);
                        break;
                    case 1:
                        int i113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            jh2.m5089h0(videoActivity, ((it3) videoActivity.f3148R.f15423m.f170i).f8218q, videoActivity.f273K.f3037x, new wq3(videoActivity, i111));
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 2:
                        int i114 = VideoActivity.f3147q0;
                        if (!videoActivity.f3171o0) {
                            videoActivity.m2037B1();
                        }
                        break;
                    case 3:
                        int i115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3162f0.f22156i = null;
                            th2 th2Var = videoActivity.f273K.f3037x;
                            int i116 = (th2Var.f17541m == 1 ? 1 : 0) ^ 1;
                            th2Var.f17541m = i116;
                            th2Var.f17533e.mo4114A(i116);
                            th2Var.f17531c.f3029p.forEach(new jf2(i111));
                            break;
                        }
                        break;
                    case 4:
                        int i117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition > 0 && duration > 0) {
                                if (duration - currentPosition <= (duration < 900000 ? 180000L : duration < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2059Y1(duration - currentPosition);
                                }
                                break;
                            }
                        }
                        break;
                    case 5:
                        int i118 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var2 = videoActivity.f273K.f3037x;
                            th2Var2.f17537i.mo1752j0(!th2Var2.m9330q() ? 1 : 0);
                            ((it3) videoActivity.f3148R.f15423m.f170i).f8220s.setSelected(videoActivity.f273K.f3037x.m9330q());
                            break;
                        }
                        break;
                    case 6:
                        int i119 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            y50 y50Var = new y50();
                            th2 th2Var3 = videoActivity.f273K.f3037x;
                            y50Var.f21148w0 = th2Var3;
                            y50Var.f21149x0 = th2Var3 != null ? th2Var3.m9319f() : null;
                            Iterator it = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it.hasNext()) {
                                if (((ox0) it.next()) instanceof y50) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            y50Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 7:
                        int i1110 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            wl0 wl0Var = new wl0();
                            th2 th2Var4 = videoActivity.f273K.f3037x;
                            wl0Var.f20136w0 = th2Var4;
                            wl0Var.f20137x0 = th2Var4 != null ? th2Var4.m9319f() : null;
                            Iterator it2 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it2.hasNext()) {
                                if (((ox0) it2.next()) instanceof wl0) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            wl0Var.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 8:
                        int i1111 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            C1579rr c1579rr = new C1579rr();
                            th2 th2Var5 = videoActivity.f273K.f3037x;
                            c1579rr.f16045w0 = th2Var5;
                            c1579rr.f16046x0 = th2Var5 != null ? th2Var5.m9319f() : null;
                            Iterator it3 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                            while (it3.hasNext()) {
                                if (((ox0) it3.next()) instanceof C1579rr) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            c1579rr.m266W(videoActivity.m6086w0());
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 9:
                        int i1112 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            long currentPosition2 = videoActivity.f273K.f3037x.f17537i.getCurrentPosition();
                            long duration2 = videoActivity.f273K.f3037x.f17537i.getDuration();
                            videoActivity.f273K.f3037x.getClass();
                            if (currentPosition2 > 0 && duration2 > 0) {
                                if (currentPosition2 <= (duration2 < 900000 ? 180000L : duration2 < 1800000 ? 360000L : 600000L)) {
                                    videoActivity.m2061a2(currentPosition2);
                                }
                                break;
                            }
                        }
                        break;
                    case 10:
                        int i1113 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            bd2 bd2Var = videoActivity.f3150T;
                            VideoActivity videoActivity2 = (VideoActivity) bd2Var.f1919a;
                            if (videoActivity2.m227c1()) {
                                videoActivity2.m2050O1();
                                ((aa3) bd2Var.f1921c).m106i(true);
                                break;
                            }
                        }
                        break;
                    case 11:
                        int i1114 = VideoActivity.f3147q0;
                        if (videoActivity.f3148R.f15422l.getTag() != null) {
                            q00 q00Var = new q00();
                            q00Var.f14537u0 = videoActivity.f3148R.f15422l.getTag().toString();
                            q00Var.m266W(videoActivity.m6086w0());
                            break;
                        }
                        break;
                    case 12:
                        int i1115 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            gk3 gk3Var = new gk3();
                            gk3Var.f6529A0 = Integer.parseInt(view.getTag().toString());
                            th2 th2Var6 = videoActivity.f273K.f3037x;
                            gk3Var.f6535y0 = th2Var6;
                            gk3Var.f6536z0 = th2Var6 != null ? th2Var6.m9319f() : null;
                            gk3Var.f6534x0 = videoActivity.f3148R.f15430t.getSubtitleView();
                            gk3Var.m3782e0(videoActivity);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 13:
                        int i1116 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            videoActivity.f3150T.m1200k(true);
                            break;
                        }
                        break;
                    case 14:
                        int i1117 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            int i22 = videoActivity.f3151U.f21714m;
                            if (i22 == 2 || i22 == 3) {
                                videoActivity.m2053S1(videoActivity.f273K.f3037x.m9325l());
                            } else if (videoActivity.f3153W && videoActivity.m2045J1() && videoActivity.f273K.f3037x.m9325l()) {
                                videoActivity.f273K.f3037x.m9324k();
                                if (!t11.m9191w(videoActivity.f273K.f3037x.m9324k())) {
                                    d81.m2564T(R.string.xray_vod_public_http_required);
                                } else {
                                    videoActivity.f273K.f3037x.m9316c();
                                    videoActivity.f3151U.m10884d();
                                }
                            } else {
                                d81.m2564T(R.string.xray_vod_required);
                            }
                            break;
                        }
                        break;
                    case 15:
                        int i23 = VideoActivity.f3147q0;
                        videoActivity.m2036A1();
                        break;
                    case 16:
                        int i24 = VideoActivity.f3147q0;
                        History history = videoActivity.f3169m0;
                        int iM6612S = (history == null || history.getScale() == -1) ? np3.m6612S() : videoActivity.f3169m0.getScale();
                        videoActivity.m2064d2(iM6612S != AbstractC0463d2.m2463h(R.array.select_scale).length - 1 ? iM6612S + 1 : 0);
                        break;
                    case 17:
                        int i25 = VideoActivity.f3147q0;
                        if (videoActivity.m227c1()) {
                            th2 th2Var7 = videoActivity.f273K.f3037x;
                            String strM9319f = th2Var7 != null ? th2Var7.m9319f() : null;
                            fy0 fy0VarM6086w0 = videoActivity.m6086w0();
                            Iterator it4 = fy0VarM6086w0.f5352c.m11043B().iterator();
                            while (it4.hasNext()) {
                                if (((ox0) it4.next()) instanceof t53) {
                                    videoActivity.m2047L1();
                                    break;
                                }
                            }
                            op3.m7095g(videoActivity);
                            new t53(th2Var7, strM9319f, true).m266W(fy0VarM6086w0);
                            videoActivity.m2047L1();
                            break;
                        }
                        break;
                    case 18:
                        int i26 = VideoActivity.f3147q0;
                        videoActivity.f3150T.m1207r();
                        break;
                    case 19:
                        int i27 = VideoActivity.f3147q0;
                        videoActivity.m2051P1();
                        break;
                    default:
                        int i28 = VideoActivity.f3147q0;
                        oc2 oc2Var = new oc2();
                        Iterator it5 = videoActivity.m6086w0().f5352c.m11043B().iterator();
                        while (it5.hasNext()) {
                            if (((ox0) it5.next()) instanceof oc2) {
                                videoActivity.m2047L1();
                                break;
                            }
                        }
                        oc2Var.m266W(videoActivity.m6086w0());
                        videoActivity.m2047L1();
                        break;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8224w.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final VideoActivity f18524h;

            {
                this.f18524h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i22 = i;
                VideoActivity videoActivity = this.f18524h;
                switch (i22) {
                    case 0:
                        int i23 = VideoActivity.f3147q0;
                        if (!videoActivity.m227c1()) {
                            return false;
                        }
                        p11.m7580P(Float.valueOf(p11.m7598e(hc2.m4063i0(videoActivity.f273K.f3037x, videoActivity.f3148R.f15415D.f7492n))), "speed_playback");
                        return true;
                    case 1:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.m2059Y1(0L);
                        return true;
                    default:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2061a2(0L);
                        return true;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8214m.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final VideoActivity f18524h;

            {
                this.f18524h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i22 = i6;
                VideoActivity videoActivity = this.f18524h;
                switch (i22) {
                    case 0:
                        int i23 = VideoActivity.f3147q0;
                        if (!videoActivity.m227c1()) {
                            return false;
                        }
                        p11.m7580P(Float.valueOf(p11.m7598e(hc2.m4063i0(videoActivity.f273K.f3037x, videoActivity.f3148R.f15415D.f7492n))), "speed_playback");
                        return true;
                    case 1:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.m2059Y1(0L);
                        return true;
                    default:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2061a2(0L);
                        return true;
                }
            }
        });
        ((it3) this.f3148R.f15423m.f170i).f8216o.setOnLongClickListener(new View.OnLongClickListener(this) {

            public final VideoActivity f18524h;

            {
                this.f18524h = this;
            }

            @Override
            public final boolean onLongClick(View view) {
                int i22 = i2;
                VideoActivity videoActivity = this.f18524h;
                switch (i22) {
                    case 0:
                        int i23 = VideoActivity.f3147q0;
                        if (!videoActivity.m227c1()) {
                            return false;
                        }
                        p11.m7580P(Float.valueOf(p11.m7598e(hc2.m4063i0(videoActivity.f273K.f3037x, videoActivity.f3148R.f15415D.f7492n))), "speed_playback");
                        return true;
                    case 1:
                        int i24 = VideoActivity.f3147q0;
                        videoActivity.m2059Y1(0L);
                        return true;
                    default:
                        int i25 = VideoActivity.f3147q0;
                        videoActivity.m2061a2(0L);
                        return true;
                }
            }
        });
        this.f3148R.f15414C.setOnTouchListener(new ViewOnTouchListenerC1603se(this, i16));
        this.f3148R.f15426p.addOnChildViewHolderSelectedListener(new zq3(this, i));
        this.f3148R.f15425o.addOnChildViewHolderSelectedListener(new zq3(this, i6));
        this.f3148R.f15420j.addOnChildViewHolderSelectedListener(new zq3(this, i2));
    }

    public final String m2041F1() {
        return m2043H1().concat("@@@").concat(m2042G1()).concat("@@@") + vv3.m10210o();
    }

    @Override
    public final void mo206G0(Bundle bundle) {
        super.mo206G0(bundle);
        this.f3160d0 = this.f3148R.f15414C.getLayoutParams();
        this.f3162f0 = C1872zo.m11041q(this.f3148R.f15415D.f7489k);
        this.f3151U = new yz3(this, this);
        this.f3161e0 = new h30(this);
        this.f3165i0 = new wq3(this, 0);
        this.f3166j0 = new wq3(this, 1);
        this.f3167k0 = new wq3(this, 2);
        this.f3168l0 = new wq3(this, 3);
        this.f3148R.f15426p.setHorizontalSpacing(AbstractC0463d2.m2457b(8));
        this.f3148R.f15426p.setRowHeight(-2);
        HorizontalGridView horizontalGridView = this.f3148R.f15426p;
        fv0 fv0Var = new fv0(this, 0);
        this.f3154X = fv0Var;
        horizontalGridView.setAdapter(fv0Var);
        this.f3148R.f15425o.setHorizontalSpacing(AbstractC0463d2.m2457b(8));
        this.f3148R.f15425o.setRowHeight(-2);
        HorizontalGridView horizontalGridView2 = this.f3148R.f15425o;
        mo0 mo0Var = new mo0(this);
        this.f3155Y = mo0Var;
        horizontalGridView2.setAdapter(mo0Var);
        this.f3148R.f15433w.setHorizontalSpacing(AbstractC0463d2.m2457b(8));
        this.f3148R.f15433w.setRowHeight(-2);
        HorizontalGridView horizontalGridView3 = this.f3148R.f15433w;
        C1542qr c1542qr = new C1542qr(this);
        this.f3156Z = c1542qr;
        horizontalGridView3.setAdapter(c1542qr);
        this.f3148R.f15420j.setHorizontalSpacing(AbstractC0463d2.m2457b(8));
        this.f3148R.f15420j.setRowHeight(-2);
        HorizontalGridView horizontalGridView4 = this.f3148R.f15420j;
        C1747wa c1747wa = new C1747wa(this);
        this.f3157a0 = c1747wa;
        horizontalGridView4.setAdapter(c1747wa);
        this.f3148R.f15429s.setHorizontalSpacing(AbstractC0463d2.m2457b(8));
        this.f3148R.f15429s.setRowHeight(-2);
        HorizontalGridView horizontalGridView5 = this.f3148R.f15429s;
        fd2 fd2Var = new fd2(new vq3(this, 8));
        this.f3158b0 = fd2Var;
        horizontalGridView5.setAdapter(fd2Var);
        this.f3148R.f15434x.setHorizontalSpacing(AbstractC0463d2.m2457b(8));
        this.f3148R.f15434x.setRowHeight(-2);
        HorizontalGridView horizontalGridView6 = this.f3148R.f15434x;
        fv0 fv0Var2 = new fv0(this, 1);
        this.f3159c0 = fv0Var2;
        horizontalGridView6.setAdapter(fv0Var2);
        View viewFindViewById = mo220W0().findViewById(R.id.exo_progress);
        if (viewFindViewById != null) {
            viewFindViewById.setNextFocusDownId(R.id.next);
        }
        af2.m204u1(((it3) this.f3148R.f15423m.f170i).f8208c);
        jh2.m5088f0(null, ((it3) this.f3148R.f15423m.f170i).f8218q);
        ((it3) this.f3148R.f15423m.f170i).f8211j.setVisibility(o11.m6771M() ? 0 : 8);
        bu3 bu3VarMo2323A = mo2323A();
        zt3 zt3VarM6618Z = np3.m6618Z(this);
        k20 k20VarM6617Y = np3.m6617Y(this);
        bu3VarMo2323A.getClass();
        zt3VarM6618Z.getClass();
        k20VarM6617Y.getClass();
        bd2 bd2Var = new bd2(bu3VarMo2323A, zt3VarM6618Z, k20VarM6617Y);
        KClass kotlinClass = JvmClassMappingKt.getKotlinClass(os3.class);
        kotlinClass.getClass();
        String qualifiedName = kotlinClass.getQualifiedName();
        if (qualifiedName == null) {
            C1566re.m8586j("Local and anonymous classes can not be ViewModels");
            return;
        }
        os3 os3Var = (os3) bd2Var.m1199j(kotlinClass, "androidx.lifecycle.ViewModelProvider.DefaultKey:".concat(qualifiedName));
        this.f3149S = os3Var;
        this.f3150T = new bd2(this, os3Var.f13420k);
        m230f1(this.f3149S.f13416g, new vq3(this, 4));
        m230f1(this.f3149S.f16361c, new vq3(this, 5));
        m230f1(this.f3149S.f13417h, new vq3(this, 6));
        m230f1(this.f3149S.f13418i, new vq3(this, 7));
        if (!getIntent().getBooleanExtra("cast", false) || this.f3171o0) {
            this.f3148R.f15432v.m2085a(2);
        } else {
            m2037B1();
        }
        m2072z1();
    }

    public final String m2042G1() {
        return Objects.toString(getIntent().getStringExtra(Name.MARK), "");
    }

    public final String m2043H1() {
        return Objects.toString(getIntent().getStringExtra("key"), "");
    }

    public final String m2044I1() {
        String string = this.f3148R.f15428r.getText().toString();
        return string.isEmpty() ? Objects.toString(getIntent().getStringExtra("name"), "") : string;
    }

    public final boolean m2045J1() {
        return m227c1() && m223Z0() && this.f273K.f3037x.m9325l();
    }

    public final void m2046K1() {
        this.f3148R.f15415D.f7487i.setImageResource(R.drawable.ic_widget_play);
        m2048M1();
    }

    public final void m2047L1() {
        ((LinearLayoutCompat) this.f3148R.f15423m.f169h).setVisibility(8);
        App.m1883c(this.f3165i0);
    }

    public final void m2048M1() {
        this.f3148R.f15415D.f7497s.setVisibility(8);
        this.f3148R.f15415D.f7488j.setVisibility(8);
    }

    public final void m2049N1() {
        ((FrameLayout) this.f3148R.f15431u.f4036h).setVisibility(8);
        App.m1883c(this.f3167k0);
        bl3.f2087c = 0L;
        bl3.f2088d = 0L;
    }

    public final void m2050O1() {
        this.f3153W = false;
        if (this.f273K == null || !m222Y0()) {
            return;
        }
        yz3 yz3Var = this.f3151U;
        if (yz3Var != null && yz3Var.f21714m != 1) {
            yz3Var.m10882b();
        }
        if (m223Z0()) {
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
    }

    public final void m2051P1() {
        if (m227c1()) {
            bd2 bd2Var = this.f3150T;
            VideoActivity videoActivity = (VideoActivity) bd2Var.f1919a;
            if (videoActivity.m227c1()) {
                History history = ((aw3) bd2Var.f1920b).f1594j;
                if (history != null) {
                    history.setPosition(-9223372036854775807L);
                }
                if (!videoActivity.m227c1() || videoActivity.f273K.f3037x.m9327n()) {
                    bd2Var.m1207r();
                    return;
                }
                long jM1188A = bd2Var.m1188A();
                if (videoActivity.m227c1()) {
                    th2 th2Var = videoActivity.f273K.f3037x;
                    ig2 ig2Var = th2Var.f17537i;
                    if (jM1188A == -9223372036854775807L) {
                        ig2Var.mo379z();
                    } else {
                        ig2Var.mo328L(jM1188A);
                    }
                    th2Var.f17537i.mo347g0();
                }
            }
        }
    }

    @Override
    public final void mo1958Q(long j) {
        if (m227c1()) {
            if (m245t1(j)) {
                m2046K1();
            }
            h30 h30Var = this.f3161e0;
            h30Var.f6869k = 0L;
            h30Var.f6870l = 0L;
        }
    }

    public final void m2052Q1(long j) {
        if (m227c1() && m223Z0() && this.f273K.f3037x.m9331r()) {
            long currentPosition = this.f273K.f3037x.f17537i.getCurrentPosition();
            long duration = this.f273K.f3037x.f17537i.getDuration();
            if (currentPosition < 0 || duration <= 0) {
                return;
            }
            bd2 bd2Var = this.f3150T;
            History history = ((aw3) bd2Var.f1920b).f1594j;
            if (history != null) {
                bd2Var.f1922d = history;
            }
            if (history != null && currentPosition >= 0 && duration > 0) {
                history.setCreateTime(j);
                history.setPosition(currentPosition);
                history.setDuration(duration);
            }
            if (history != null && history.canSave() && history.canScheduleSave() && !tp3.m9403I()) {
                history.markSaveScheduled();
                History historyCopy = history.copy();
                Objects.requireNonNull(historyCopy);
                id3.f7902c.execute(new rc2(historyCopy, 28));
            }
            if (history == null || history.getEnding() <= 0 || history.getEnding() + currentPosition < duration) {
                return;
            }
            bd2Var.m1200k(false);
        }
    }

    @Override
    public final void mo1959R() {
        if (m227c1() && this.f273K.f3037x.f17537i.isPlaying()) {
            hc2.m4057e0(this.f3148R.f15415D.f7492n, this.f273K.f3037x.m9309B(p11.m7613t()));
        }
    }

    public final void m2053S1(boolean z) {
        if (this.f273K == null || !m222Y0()) {
            return;
        }
        yz3 yz3Var = this.f3151U;
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

    @Override
    public final pf2 mo217T0() {
        return this.f3172p0;
    }

    public final void m2054T1(List list) {
        this.f3148R.f15426p.setVisibility(list.isEmpty() ? 8 : 0);
        fv0 fv0Var = this.f3154X;
        ArrayList arrayList = fv0Var.f6072c;
        arrayList.clear();
        arrayList.addAll(list);
        fv0Var.notifyDataSetChanged();
    }

    @Override
    public final String mo218U0() {
        return m2041F1();
    }

    public final void m2055U1(pv1 pv1Var) {
        if (m227c1()) {
            if (m223Z0()) {
                this.f273K.f3037x.m9339z(pv1Var);
            }
            this.f3148R.f15415D.f7496r.setText(pv1Var.f14423e);
            this.f3148R.f15415D.f7496r.setSelected(true);
        }
    }

    @Override
    public final PlayerView mo219V0() {
        return this.f3148R.f15430t;
    }

    public final void m2056V1(ArrayList arrayList) {
        fv0 fv0Var = this.f3159c0;
        ArrayList arrayList2 = fv0Var.f6072c;
        int size = arrayList2.size();
        arrayList2.addAll(arrayList);
        fv0Var.notifyItemRangeInserted(size, arrayList.size());
        this.f3148R.f15434x.setVisibility(this.f3159c0.f6072c.size() == 0 ? 8 : 0);
    }

    @Override
    public final PlayerSeekView mo220W0() {
        return (PlayerSeekView) this.f3148R.f15423m.f171j;
    }

    public final void m2057W1(boolean z) {
        PlaybackService playbackService = this.f273K;
        boolean z2 = playbackService != null && m222Y0() && playbackService.m1940w() && m2041F1().equals(playbackService.f3037x.m9319f());
        long currentPosition = z2 ? playbackService.f3037x.f17537i.getCurrentPosition() : -9223372036854775807L;
        long duration = z2 ? playbackService.f3037x.f17537i.getDuration() : -9223372036854775807L;
        bd2 bd2Var = this.f3150T;
        if (bd2Var != null) {
            bd2Var.m1213x(System.currentTimeMillis(), currentPosition, duration, z);
        }
    }

    public final void m2058X1() {
        if (this.f3152V != null) {
            ComponentCallbacks2C0223a.m1877c(App.f2949l).m3827o(this.f3152V);
        }
        if (!m227c1() || this.f273K.f3037x.m9332s()) {
            return;
        }
        if (this.f3152V == null) {
            this.f3152V = new jj1(this, 1);
        }
        ha1.m3984c(this, this.f3169m0.getVodPic(), this.f3152V);
    }

    public final void m2059Y1(long j) {
        History history = ((aw3) this.f3150T.f1920b).f1594j;
        if (history != null) {
            history.setEnding(j);
        }
        ((it3) this.f3148R.f15423m.f170i).f8214m.setText(j <= 0 ? getString(R.string.play_ed) : op3.m7096h(this.f3169m0.getEnding()));
    }

    public final void m2060Z1(List list) {
        int i = 0;
        this.f3148R.f15425o.setVisibility(list.isEmpty() ? 8 : 0);
        mo0 mo0Var = this.f3155Y;
        ArrayList arrayList = mo0Var.f11537b;
        arrayList.clear();
        arrayList.addAll(list);
        mo0Var.notifyDataSetChanged();
        int size = list.size();
        ArrayList arrayList2 = new ArrayList();
        arrayList2.add(getString(R.string.play_reverse));
        arrayList2.add(getString(this.f3169m0.getRevPlayText()));
        this.f3148R.f15420j.setVisibility(size > 1 ? 0 : 8);
        if (this.f3169m0.isRevSort()) {
            while (size > 0) {
                arrayList2.add(size + "-" + Math.max(size - 19, 1));
                size += -20;
            }
        } else {
            while (i < size) {
                StringBuilder sb = new StringBuilder();
                sb.append(i + 1);
                sb.append("-");
                i += 20;
                sb.append(Math.min(i, size));
                arrayList2.add(sb.toString());
            }
        }
        C1747wa c1747wa = this.f3157a0;
        ArrayList arrayList3 = c1747wa.f19964b;
        arrayList3.clear();
        arrayList3.addAll(arrayList2);
        c1747wa.notifyDataSetChanged();
        App.m1882b(this.f3166j0, 500L);
    }

    public final void m2061a2(long j) {
        History history = ((aw3) this.f3150T.f1920b).f1594j;
        if (history != null) {
            history.setOpening(j);
        }
        ((it3) this.f3148R.f15423m.f170i).f8216o.setText(j <= 0 ? getString(R.string.play_op) : op3.m7096h(this.f3169m0.getOpening()));
    }

    /* JADX WARN: Code duplicated, block: B:14:0x004e  */
    /* JADX WARN: Code duplicated, block: B:26:0x00b1  */
    public final void m2062b2() {
        String[] strArrSplit;
        fd2 fd2Var = this.f3158b0;
        String vodName = this.f3169m0.getVodName();
        Pattern pattern = gd2.f6422a;
        LinkedHashSet linkedHashSet = new LinkedHashSet();
        if (vodName.contains("：")) {
            strArrSplit = vodName.split("：");
        } else if (vodName.contains("第") && vodName.contains("季")) {
            Matcher matcher = gd2.f6422a.matcher(vodName);
            if (matcher.find()) {
                String strTrim = matcher.group(1).trim();
                if (strTrim.isEmpty()) {
                    strArrSplit = (String[]) Arrays.stream(vodName.split("第")).filter(new u30(18)).toArray(new p60(1));
                } else {
                    strArrSplit = new String[]{strTrim};
                }
            } else {
                strArrSplit = (String[]) Arrays.stream(vodName.split("第")).filter(new u30(18)).toArray(new p60(1));
            }
        } else if (vodName.contains("(")) {
            strArrSplit = new String[]{vodName.split(Pattern.quote("("))[0]};
        } else if (vodName.contains(" ")) {
            strArrSplit = vodName.split(" ");
        } else {
            Matcher matcher2 = gd2.f6423b.matcher(vodName);
            if (matcher2.find()) {
                String strTrim2 = matcher2.group(1).trim();
                if (strTrim2.isEmpty()) {
                    strArrSplit = new String[0];
                } else {
                    strArrSplit = new String[]{strTrim2};
                }
            } else {
                strArrSplit = new String[0];
            }
        }
        linkedHashSet.add(vodName);
        Arrays.stream(strArrSplit).map(new af1(25)).map(new af1(26)).filter(new u30(17)).forEach(new C1206nh(linkedHashSet, 12));
        ArrayList arrayList = new ArrayList(linkedHashSet);
        ArrayList arrayList2 = fd2Var.f5747b;
        arrayList2.clear();
        arrayList2.addAll(arrayList);
        fd2Var.notifyDataSetChanged();
        this.f3148R.f15429s.setVisibility(0);
        App.m1882b(this.f3166j0, 500L);
    }

    public final void m2063c2(boolean z) {
        this.f3148R.f15433w.setVisibility(z ? 0 : 8);
        App.m1882b(this.f3166j0, 500L);
    }

    public final void m2064d2(int i) {
        History history = ((aw3) this.f3150T.f1920b).f1594j;
        if (history != null) {
            history.setScale(i);
        }
        this.f3148R.f15430t.setResizeMode(i);
        ((it3) this.f3148R.f15423m.f170i).f8223v.setText(AbstractC0463d2.m2463h(R.array.select_scale)[i]);
    }

    @Override
    public final boolean dispatchKeyEvent(KeyEvent keyEvent) {
        es1 es1Var;
        es1 es1Var2;
        if (this.f3171o0 && v11.m9905D(keyEvent)) {
            if (((LinearLayoutCompat) this.f3148R.f15423m.f169h).getVisibility() == 0) {
                m2047L1();
            } else {
                m2067g2(m2040E1());
            }
        }
        if (((LinearLayoutCompat) this.f3148R.f15423m.f169h).getVisibility() == 0 && !this.f276N) {
            App.m1882b(this.f3165i0, 5000L);
        }
        if (((LinearLayoutCompat) this.f3148R.f15423m.f169h).getVisibility() == 0) {
            this.f3164h0 = getCurrentFocus();
        }
        if (this.f3171o0 && AbstractActivityC1828yh.m10757H0((LinearLayoutCompat) this.f3148R.f15423m.f169h)) {
            this.f3161e0.getClass();
            if (h30.m3935a(keyEvent) && m227c1()) {
                this.f3161e0.m3936b(keyEvent);
                return true;
            }
        }
        if (keyEvent.getAction() == 1 && keyEvent.getKeyCode() == 90) {
            if (!m227c1() || (es1Var2 = this.f271I) == null) {
                return false;
            }
            es1Var2.mo325D0();
            return true;
        }
        if (keyEvent.getAction() != 1 || keyEvent.getKeyCode() != 89) {
            return super.dispatchKeyEvent(keyEvent);
        }
        if (!m227c1() || (es1Var = this.f271I) == null) {
            return false;
        }
        es1Var.mo326F0();
        return true;
    }

    @Override
    public final void mo1960e() {
        if (m227c1()) {
            m2067g2(m2040E1());
        }
    }

    public final void m2065e2(TextView textView, int i, String str) {
        if (!TextUtils.isEmpty(str) || TextUtils.isEmpty(textView.getText())) {
            String string = i > 0 ? getString(i, str) : str;
            Pattern pattern = j43.f8913a;
            SpannableStringBuilder spannableStringBuilder = new SpannableStringBuilder();
            Matcher matcher = j43.f8913a.matcher(string);
            int iEnd = 0;
            while (matcher.find()) {
                spannableStringBuilder.append((CharSequence) string, iEnd, matcher.start());
                int length = spannableStringBuilder.length();
                spannableStringBuilder.append((CharSequence) cl3.m1788b(matcher.group(2).trim()));
                spannableStringBuilder.setSpan(new ar3(this, Result.type(matcher.group(1))), length, spannableStringBuilder.length(), 33);
                iEnd = matcher.end();
            }
            spannableStringBuilder.append((CharSequence) string, iEnd, string.length());
            textView.setText(spannableStringBuilder, TextView.BufferType.SPANNABLE);
            textView.setVisibility(str.isEmpty() ? 8 : 0);
            textView.setLinkTextColor(-5317);
            l30.m5756b(textView);
        }
    }

    @Override
    public final void mo1961f() {
        if (this.f3171o0) {
            if (((LinearLayoutCompat) this.f3148R.f15423m.f169h).getVisibility() == 0) {
                m2047L1();
            } else {
                m2067g2(m2040E1());
            }
        }
    }

    public final void m2066f2(Vod vod) {
        this.f3148R.f15422l.setTag(vod.getContent());
        m2065e2(this.f3148R.f15416E, R.string.detail_year, vod.getYear());
        m2065e2(this.f3148R.f15419i, R.string.detail_area, vod.getArea());
        m2065e2(this.f3148R.f15413B, R.string.detail_type, vod.getTypeName());
        m2065e2(this.f3148R.f15412A, R.string.detail_site, uv3.f18675a.m10216s(m2043H1()).getName());
        m2065e2(this.f3148R.f15424n, R.string.detail_director, vod.getDirector());
        m2065e2(this.f3148R.f15418h, R.string.detail_actor, vod.getActor());
        m2065e2(this.f3148R.f15435y, 0, vod.getRemarks());
    }

    @Override
    public final void mo231g1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            it3 it3Var = (it3) this.f3148R.f15423m.f170i;
            MaterialTextView materialTextView = it3Var.f8218q;
            MaterialTextView materialTextView2 = it3Var.f8212k;
            materialTextView.setText(AbstractC0463d2.m2463h(R.array.select_engine)[hc2.m4078v(th2Var)]);
            materialTextView2.setText(th2Var == null ? "" : AbstractC0463d2.m2463h(R.array.select_decode)[th2Var.f17541m]);
        }
    }

    public final void m2067g2(View view) {
        ((LinearLayoutCompat) this.f3148R.f15423m.f169h).setVisibility(0);
        view.requestFocus();
        if (this.f276N) {
            return;
        }
        App.m1882b(this.f3165i0, 5000L);
    }

    @Override
    public final void mo1962h0() {
        es1 es1Var;
        if (m227c1()) {
            if (this.f273K.f3037x.f17537i.isPlaying()) {
                if (m227c1() && (es1Var = this.f271I) != null) {
                    es1Var.pause();
                }
            } else if (this.f273K.f3037x.m9327n()) {
                this.f3150T.m1207r();
            } else if (m227c1() && this.f271I != null) {
                if (this.f3169m0 != null && m229e1(4)) {
                    this.f271I.mo328L(this.f3169m0.getOpening());
                }
                if (!this.f273K.f3037x.m9327n() && m229e1(1)) {
                    this.f271I.mo1738a();
                }
                this.f271I.mo347g0();
            }
            m2047L1();
        }
    }

    @Override
    public final void mo232h1(String str) {
        bd2 bd2Var = this.f3150T;
        bd2Var.m1191b();
        VideoActivity videoActivity = (VideoActivity) bd2Var.f1919a;
        if (videoActivity.m227c1()) {
            if (videoActivity.f273K.f3037x.f17542n > 0) {
                videoActivity.m2057W1(false);
            }
            videoActivity.f3153W = false;
            th2 th2Var = videoActivity.f273K.f3037x;
            videoActivity.f3162f0.f22156i = null;
            Track.delete(th2Var.m9319f());
            th2Var.m9337x();
            th2Var.m9336w();
            th2Var.m9313F();
            videoActivity.m2053S1(false);
            videoActivity.m2068h2(str);
        }
        ((aa3) bd2Var.f1921c).m105h();
    }

    public final void m2068h2(String str) {
        hc2.m4032D(this.f3148R.f15415D.f7492n);
        this.f3148R.f15415D.f7491m.setVisibility(0);
        this.f3148R.f15415D.f7495q.setText(str);
        m2049N1();
    }

    @Override
    public final void mo2069i(int i) {
        if (m227c1()) {
            ((it3) this.f3148R.f15423m.f170i).f8220s.setSelected(this.f273K.f3037x.m9330q());
        }
    }

    @Override
    public final void mo1963i0() {
        long j;
        if (m227c1()) {
            long currentPosition = this.f273K.f3037x.f17537i.getCurrentPosition();
            long duration = this.f273K.f3037x.f17537i.getDuration();
            this.f273K.f3037x.getClass();
            long j2 = 600000;
            if (currentPosition > 0 && duration > 0) {
                if (duration < 900000) {
                    j = 180000;
                } else {
                    j = duration < 1800000 ? 360000L : 600000L;
                }
                if (currentPosition <= j) {
                    m2067g2(((it3) this.f3148R.f15423m.f170i).f8216o);
                    return;
                }
            }
            this.f273K.f3037x.getClass();
            if (currentPosition > 0 && duration > 0) {
                long j3 = duration - currentPosition;
                if (duration < 900000) {
                    j2 = 180000;
                } else if (duration < 1800000) {
                    j2 = 360000;
                }
                if (j3 <= j2) {
                    m2067g2(((it3) this.f3148R.f15423m.f170i).f8214m);
                    return;
                }
            }
            m2067g2(m2040E1());
        }
    }

    @Override
    public final void mo233i1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            it3 it3Var = (it3) this.f3148R.f15423m.f170i;
            MaterialTextView materialTextView = it3Var.f8213l;
            MaterialTextView materialTextView2 = it3Var.f8210i;
            boolean z = false;
            hc2.m4059g0(materialTextView, (th2Var == null || th2Var.f17537i.mo1759p().isEmpty()) ? false : true);
            if (th2Var != null && !th2Var.f17537i.mo1724I0().isEmpty()) {
                z = true;
            }
            hc2.m4059g0(materialTextView2, z);
        }
    }

    public final void m2070i2() {
        ((FrameLayout) this.f3148R.f15431u.f4036h).setVisibility(0);
        App.m1882b(this.f3167k0, 0L);
        m2046K1();
        this.f3148R.f15415D.f7491m.setVisibility(8);
        this.f3148R.f15415D.f7495q.setText("");
    }

    @Override
    public final void mo234j1() {
        os3 os3Var = this.f3149S;
        os3Var.f13419j.m2592f(ns3.f12469h);
        os3Var.f13419j.m2592f(ns3.f12470i);
        c53.f2497a.m2548c();
        App.m1883c(this.f3167k0);
        m2050O1();
    }

    @Override
    public final void mo235k1(boolean z) {
        if (z) {
            m2046K1();
            return;
        }
        if (m225a1()) {
            if (!this.f3171o0) {
                m2048M1();
            } else if (m227c1()) {
                this.f3148R.f15415D.f7497s.setVisibility(0);
                this.f3148R.f15415D.f7488j.setVisibility(0);
                this.f3148R.f15415D.f7490l.setText(this.f273K.f3037x.m9318e());
                this.f3148R.f15415D.f7493o.setText(this.f273K.f3037x.m9320g(0L));
            }
        }
    }

    @Override
    public final void mo2009l(int i, int i2, String str) {
        int i3;
        if (m227c1()) {
            int iCharCount = 0;
            ((it3) this.f3148R.f15423m.f170i).f8227z.setSelected(i == 3);
            MaterialTextView materialTextView = ((it3) this.f3148R.f15423m.f170i).f8227z;
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
                os3 os3Var = this.f3149S;
                os3Var.f13419j.m2592f(ns3.f12468c);
                os3Var.f13419j.m2592f(ns3.f12469h);
                os3Var.f13419j.m2592f(ns3.f12470i);
                c53.f2497a.m2548c();
                la2.m5792c().dispatcher().cancelAll();
                this.f3150T.m1191b();
                if (this.f3152V != null) {
                    ComponentCallbacks2C0223a.m1877c(App.f2949l).m3827o(this.f3152V);
                }
                if (this.f273K.f3037x.f17542n == 0) {
                    m213P0();
                }
                this.f273K.f3037x.m9308A(i2, true);
                return;
            }
            if (i == 4) {
                iCharCount = this.f273K.f3037x.f17542n > 0 ? 1 : 0;
                if (iCharCount != 0) {
                    m213P0();
                }
                if (iCharCount != 0) {
                    this.f273K.f3037x.m9317d();
                }
                if (iCharCount != 0) {
                    m2068h2(str);
                }
                d81.m2565U(str);
                return;
            }
            if (i == 1) {
                int length = str.length();
                while (iCharCount < length) {
                    int iCodePointAt = str.codePointAt(iCharCount);
                    if (!Character.isWhitespace(iCodePointAt)) {
                        d81.m2565U(str);
                        return;
                    }
                    iCharCount += Character.charCount(iCodePointAt);
                }
            }
        }
    }

    @Override
    public final void mo236l1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            it3 it3Var = (it3) this.f3148R.f15423m.f170i;
            MaterialTextView materialTextView = it3Var.f8218q;
            MaterialTextView materialTextView2 = it3Var.f8212k;
            materialTextView.setText(AbstractC0463d2.m2463h(R.array.select_engine)[hc2.m4078v(th2Var)]);
            materialTextView2.setText(th2Var == null ? "" : AbstractC0463d2.m2463h(R.array.select_decode)[th2Var.f17541m]);
        }
    }

    public final void m2071l2() {
        if (m227c1()) {
            this.f273K.f3037x.m9313F();
            th2 th2Var = this.f273K.f3037x;
            th2Var.f17543o = null;
            th2Var.f17536h = null;
            this.f3162f0.f22156i = null;
        }
    }

    @Override
    public final void mo237m1() {
        this.f3150T.m1207r();
    }

    @Override
    public final void mo238n1(boolean z) {
        if (z) {
            App.m1883c(this.f3165i0);
        } else {
            if (((LinearLayoutCompat) this.f3148R.f15423m.f169h).getVisibility() != 0 || this.f276N) {
                return;
            }
            App.m1882b(this.f3165i0, 5000L);
        }
    }

    @Override
    public final void mo1964o0() {
        if (((LinearLayoutCompat) this.f3148R.f15423m.f169h).getVisibility() == 0) {
            m2047L1();
            return;
        }
        if (this.f3148R.f15415D.f7488j.getVisibility() == 0) {
            m2046K1();
            return;
        }
        if (this.f3171o0) {
            this.f3148R.f15414C.setForeground(App.f2949l.getDrawable(R.drawable.selector_video));
            this.f3148R.f15414C.setLayoutParams(this.f3160d0);
            View view = this.f3163g0;
            ((view == null || view.getVisibility() != 0) ? this.f3148R.f15414C : this.f3163g0).requestFocus();
            this.f3161e0.f6868j = false;
            this.f3171o0 = false;
            this.f3164h0 = null;
            m2048M1();
            return;
        }
        m21 m21Var = this.f3149S.f16364f;
        ((AtomicInteger) m21Var.f11127i).incrementAndGet();
        CopyOnWriteArrayList copyOnWriteArrayList = (CopyOnWriteArrayList) m21Var.f11126h;
        copyOnWriteArrayList.forEach(new cd3(11));
        copyOnWriteArrayList.clear();
        if (isTaskRoot()) {
            startActivity(new Intent(this, (Class<?>) HomeActivity.class).addFlags(872415232));
        }
        finish();
    }

    @Override
    public final void mo239o1() {
        bd2 bd2Var = this.f3150T;
        aw3 aw3Var = (aw3) bd2Var.f1920b;
        VideoActivity videoActivity = (VideoActivity) bd2Var.f1919a;
        if (videoActivity.m227c1()) {
            pv1 pv1Var = aw3Var.f1590f;
            if (pv1Var != null) {
                videoActivity.m2055U1(pv1Var);
            }
            zv3 zv3Var = aw3Var.f1589e;
            if (zv3Var == null || videoActivity.m2045J1()) {
                return;
            }
            bd2Var.m1210u(zv3Var);
            bd2Var.m1209t();
        }
    }

    @Override
    public final void onActivityResult(int i, int i2, Intent intent) {
        super.onActivityResult(i, i2, intent);
        if (i2 == -1 && i == 1001) {
            String str = this.f272J;
            this.f272J = null;
            PlaybackService playbackService = this.f273K;
            if (playbackService == null || str == null || !m226b1(playbackService.f3037x, str)) {
                return;
            }
            p52 p52Var = new p52(this, str, 9);
            if (intent != null) {
                try {
                    if (intent.getExtras() == null) {
                        return;
                    }
                    long j = intent.getExtras().getInt("position", 0);
                    String string = intent.getExtras().getString("end_by", "");
                    if ("playback_completion".equals(string)) {
                        App.m1881a(p52Var);
                    }
                    if ("user".equals(string)) {
                        PlaybackService playbackService2 = this.f273K;
                        es1 es1Var = this.f271I;
                        if (playbackService2 == null || es1Var == null || !m226b1(playbackService2.f3037x, str)) {
                            return;
                        }
                        es1Var.mo328L(j);
                    }
                } catch (Exception unused) {
                }
            }
        }
    }

    @Override
    public final void onDestroy() {
        if (this.f3152V != null) {
            ComponentCallbacks2C0223a.m1877c(App.f2949l).m3827o(this.f3152V);
        }
        yz3 yz3Var = this.f3151U;
        if (yz3Var != null) {
            yz3Var.m10881a();
        }
        C1872zo c1872zo = this.f3162f0;
        Timer timer = (Timer) c1872zo.f22158k;
        if (timer != null) {
            timer.cancel();
        }
        if (((VideoActivity) c1872zo.f22156i) != null) {
            c1872zo.f22156i = null;
        }
        m2057W1(true);
        q50.m8003a(this.f3170n0);
        this.f3170n0 = -1;
        gp0.m3810b().m3813e(new ep2(4));
        h30 h30Var = this.f3161e0;
        App.m1883c(h30Var.f6871m);
        h30Var.f6867i = false;
        h30Var.f6868j = false;
        h30Var.f6869k = 0L;
        h30Var.f6870l = 0L;
        App.m1884d(this.f3165i0, this.f3166j0, this.f3167k0, this.f3168l0);
        super.onDestroy();
    }

    @Override
    public final void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (TextUtils.isEmpty(intent.getStringExtra(Name.MARK))) {
            return;
        }
        String string = Objects.toString(intent.getStringExtra("key"), "");
        String string2 = Objects.toString(intent.getStringExtra(Name.MARK), "");
        if (TextUtils.equals(string, m2043H1()) && TextUtils.equals(string2, m2042G1())) {
            return;
        }
        m2057W1(true);
        bd2 bd2Var = this.f3150T;
        ((VideoActivity) bd2Var.f1919a).m2050O1();
        bd2Var.m1191b();
        ((aw3) bd2Var.f1920b).m1022f();
        setIntent(intent);
        m249y1(mo218U0());
        m2072z1();
    }

    @v93(threadMode = ThreadMode.MAIN)
    public void onRefreshEvent(ep2 ep2Var) {
        if (this.f277O || !m227c1()) {
            return;
        }
        int i = ep2Var.f5139a;
        String str = ep2Var.f5140b;
        if (i == 8) {
            this.f3150T.m1208s();
            return;
        }
        if (i == 9) {
            this.f3150T.m1207r();
            return;
        }
        if (i != 12) {
            if (i == 10) {
                this.f273K.f3037x.m9310C(Sub.from(str));
                return;
            }
            if (i == 11) {
                th2 th2Var = this.f273K.f3037x;
                Danmaku danmakuFrom = Danmaku.from(str);
                C1519q4 c1519q4 = th2Var.f17536h;
                if (c1519q4 == null) {
                    return;
                }
                c1519q4.m8000e(danmakuFrom);
                th2Var.m9333t();
                return;
            }
            return;
        }
        bd2 bd2Var = this.f3150T;
        Vod vod = ep2Var.f5141c;
        aw3 aw3Var = (aw3) bd2Var.f1920b;
        History history = aw3Var.f1594j;
        String id = vod.getId();
        VideoActivity videoActivity = (VideoActivity) bd2Var.f1919a;
        if (!id.isEmpty() && !id.equals(videoActivity.m2042G1())) {
            String strM2041F1 = videoActivity.m2041F1();
            videoActivity.getIntent().putExtra(Name.MARK, id);
            String strM2041F2 = videoActivity.m2041F1();
            history.replace(strM2041F2);
            Keep.replace(strM2041F1, strM2041F2);
        }
        List<Flag> flags = vod.getFlags();
        if (!flags.isEmpty()) {
            boolean zM1021e = aw3Var.m1021e();
            ArrayList arrayList = aw3Var.f1587c;
            if (zM1021e) {
                Flag flagM1018b = aw3Var.m1018b();
                for (Flag flag : flags) {
                    Flag flagM1196g = bd2Var.m1196g(flag);
                    if (flagM1196g == null) {
                        arrayList.add(flag);
                    } else {
                        List<Episode> episodes = flag.getEpisodes();
                        History history2 = aw3Var.f1594j;
                        flagM1196g.mergeEpisodes(episodes, history2 != null && history2.isRevSort());
                        if (flagM1196g.equals(flagM1018b)) {
                            videoActivity.m2060Z1(flagM1196g.getEpisodes());
                        }
                    }
                }
                videoActivity.m2054T1(arrayList);
            } else {
                arrayList.clear();
                arrayList.addAll(flags);
                videoActivity.m2054T1(arrayList);
            }
        }
        String pic = vod.getPic();
        String name = vod.getName();
        boolean zIsEmpty = pic.isEmpty();
        boolean zIsEmpty2 = name.isEmpty();
        if (!zIsEmpty) {
            history.setVodPic(pic);
        }
        if (!zIsEmpty2) {
            history.setVodName(name);
        }
        if ((!zIsEmpty2 || !zIsEmpty) && history != null && !tp3.m9403I()) {
            history.markSaveScheduled();
            History historyCopy = history.copy();
            Objects.requireNonNull(historyCopy);
            id3.f7902c.execute(new rc2(historyCopy, 28));
        }
        if (!vod.getId().isEmpty()) {
            videoActivity.m249y1(videoActivity.mo218U0());
        }
        String name2 = vod.getName();
        String pic2 = vod.getPic();
        if (!name2.isEmpty() || !pic2.isEmpty()) {
            if (!name2.isEmpty()) {
                videoActivity.f3148R.f15428r.setText(name2);
            }
            if (!name2.isEmpty()) {
                videoActivity.m2062b2();
            }
            if (!pic2.isEmpty()) {
                videoActivity.m2058X1();
            }
            Keep keepFind = Keep.find(videoActivity.m2041F1());
            if (keepFind != null) {
                keepFind.setVodName(videoActivity.f3169m0.getVodName());
                keepFind.setVodPic(videoActivity.f3169m0.getVodPic());
                keepFind.save();
            }
        }
        videoActivity.m2066f2(vod);
        zv3 zv3Var = aw3Var.f1588d;
        if (zv3Var == null) {
            zv3Var = aw3Var.f1589e;
        }
        Episode episodeM1194e = bd2Var.m1194e(zv3Var);
        if (episodeM1194e != null) {
            bd2Var.m1206q(episodeM1194e);
        }
    }

    @Override
    public final void onStart() {
        super.onStart();
        C1872zo c1872zo = this.f3162f0;
        c1872zo.m11053O();
        c1872zo.m11052N();
    }

    @Override
    public final void onStop() {
        m2053S1(!isFinishing() && !np3.m6628e0() && this.f273K != null && m222Y0() && m223Z0() && this.f273K.f3037x.m9325l());
        super.onStop();
        m2057W1(false);
        if (np3.m6628e0()) {
            this.f3162f0.m11053O();
        }
    }

    @Override
    public final void mo241p1() {
        this.f3148R.f15415D.f7494p.setText(this.f273K.f3037x.m9322i());
    }

    @Override
    public final void mo242q1(int i) {
        if (i == 2) {
            m2070i2();
            this.f3162f0.f22156i = null;
            return;
        }
        if (i == 3) {
            m2049N1();
            this.f3153W = true;
            this.f273K.f3037x.m9336w();
            this.f3162f0.f22156i = this;
            return;
        }
        if (i != 4) {
            return;
        }
        m2049N1();
        this.f3150T.m1200k(true);
        this.f3153W = false;
        m2053S1(false);
        this.f3162f0.f22156i = null;
    }

    @Override
    public final void mo243r1() {
        if (m227c1()) {
            th2 th2Var = this.f273K.f3037x;
            it3 it3Var = (it3) this.f3148R.f15423m.f170i;
            hc2.m4058f0(th2Var, it3Var.f8225x, it3Var.f8209h, it3Var.f8226y);
        }
    }

    @Override
    public final void mo1965w() {
        if (m227c1()) {
            hc2.m4032D(this.f3148R.f15415D.f7492n);
            this.f273K.f3037x.m9309B(p11.m7598e(p11.m7610q("speed_playback", 1.0f)));
        }
    }

    public final void m2072z1() {
        bd2 bd2Var = this.f3150T;
        VideoActivity videoActivity = (VideoActivity) bd2Var.f1919a;
        String strM2042G1 = videoActivity.m2042G1();
        if (strM2042G1.startsWith("push://")) {
            videoActivity.getIntent().putExtra("key", "push_agent").putExtra(Name.MARK, strM2042G1.substring(7));
            strM2042G1 = videoActivity.m2042G1();
        }
        if (strM2042G1.isEmpty() || strM2042G1.startsWith("msearch:")) {
            bd2Var.m1193d(false);
            return;
        }
        aw3 aw3Var = (aw3) bd2Var.f1920b;
        if (aw3Var.f1595k.equals(videoActivity.m2043H1()) && aw3Var.f1596l.equals(strM2042G1)) {
            return;
        }
        bd2Var.m1208s();
    }
}
