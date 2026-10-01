package com.fongmi.android.p002tv.p004ui.activity;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.view.ViewGroup;
import androidx.appcompat.widget.AppCompatImageView;
import androidx.appcompat.widget.LinearLayoutCompat;
import com.fongmi.android.p002tv.App;
import com.fongmi.android.p002tv.R;
import com.fongmi.android.p002tv.p004ui.activity.PushActivity;
import com.fongmi.android.p002tv.p004ui.activity.VideoActivity;
import com.github.catvod.Proxy;
import com.google.android.material.textview.MaterialTextView;
import java.util.regex.Pattern;
import org.mozilla.javascript.Context;
import p000.AbstractActivityC1828yh;
import p000.AbstractC0463d2;
import p000.C1872zo;
import p000.h00;
import p000.pp3;
import p000.ps3;
import p000.rw1;
import p000.t11;

public class PushActivity extends AbstractActivityC1828yh {

    public static final int f3116G = 0;

    public C1872zo f3117F;

    @Override
    public final ps3 mo1948E0() {
        View viewInflate = getLayoutInflater().inflate(R.layout.activity_push, (ViewGroup) null, false);
        int i = R.id.clip;
        MaterialTextView materialTextView = (MaterialTextView) rw1.m8781l(R.id.clip, viewInflate);
        if (materialTextView != null) {
            i = R.id.code;
            AppCompatImageView appCompatImageView = (AppCompatImageView) rw1.m8781l(R.id.code, viewInflate);
            if (appCompatImageView != null) {
                i = R.id.info;
                MaterialTextView materialTextView2 = (MaterialTextView) rw1.m8781l(R.id.info, viewInflate);
                if (materialTextView2 != null) {
                    C1872zo c1872zo = new C1872zo((LinearLayoutCompat) viewInflate, materialTextView, appCompatImageView, materialTextView2, 5, false);
                    this.f3117F = c1872zo;
                    return c1872zo;
                }
            }
        }
        h00.m3905e("Missing required view with ID: ".concat(viewInflate.getResources().getResourceName(i)));
        return null;
    }

    @Override
    public final void mo1951F0() {
        final int i = 0;
        ((AppCompatImageView) this.f3117F.f22157j).setOnClickListener(new View.OnClickListener(this) {

            public final PushActivity f5066h;

            {
                this.f5066h = this;
            }

            @Override
            public final void onClick(View view) {
                switch (i) {
                    case 0:
                        PushActivity pushActivity = this.f5066h;
                        int i2 = PushActivity.f3116G;
                        Intent intent = new Intent("android.intent.action.VIEW");
                        int intExtra = pushActivity.getIntent().getIntExtra("tab", 2);
                        StringBuilder sb = new StringBuilder("http://" + pp3.m7879d() + ":" + Proxy.getPort());
                        sb.append("?tab=");
                        sb.append(intExtra);
                        intent.setData(Uri.parse(sb.toString()));
                        pushActivity.startActivity(intent);
                        break;
                    default:
                        PushActivity pushActivity2 = this.f5066h;
                        int i3 = PushActivity.f3116G;
                        Pattern pattern = op3.f13178a;
                        ClipboardManager clipboardManager = (ClipboardManager) App.f2949l.getSystemService("clipboard");
                        ClipData primaryClip = clipboardManager == null ? null : clipboardManager.getPrimaryClip();
                        CharSequence text = (primaryClip == null || primaryClip.getItemCount() == 0) ? "" : primaryClip.getItemAt(0).getText();
                        if (!TextUtils.isEmpty(text)) {
                            String strM4986b = j43.m4986b(text.toString());
                            VideoActivity.m2034j2(pushActivity2, "push_agent", strM4986b, strM4986b, null, null);
                        }
                        break;
                }
            }
        });
        final int i2 = 1;
        ((MaterialTextView) this.f3117F.f22156i).setOnClickListener(new View.OnClickListener(this) {

            public final PushActivity f5066h;

            {
                this.f5066h = this;
            }

            @Override
            public final void onClick(View view) {
                switch (i2) {
                    case 0:
                        PushActivity pushActivity = this.f5066h;
                        int i3 = PushActivity.f3116G;
                        Intent intent = new Intent("android.intent.action.VIEW");
                        int intExtra = pushActivity.getIntent().getIntExtra("tab", 2);
                        StringBuilder sb = new StringBuilder("http://" + pp3.m7879d() + ":" + Proxy.getPort());
                        sb.append("?tab=");
                        sb.append(intExtra);
                        intent.setData(Uri.parse(sb.toString()));
                        pushActivity.startActivity(intent);
                        break;
                    default:
                        PushActivity pushActivity2 = this.f5066h;
                        int i4 = PushActivity.f3116G;
                        Pattern pattern = op3.f13178a;
                        ClipboardManager clipboardManager = (ClipboardManager) App.f2949l.getSystemService("clipboard");
                        ClipData primaryClip = clipboardManager == null ? null : clipboardManager.getPrimaryClip();
                        CharSequence text = (primaryClip == null || primaryClip.getItemCount() == 0) ? "" : primaryClip.getItemAt(0).getText();
                        if (!TextUtils.isEmpty(text)) {
                            String strM4986b = j43.m4986b(text.toString());
                            VideoActivity.m2034j2(pushActivity2, "push_agent", strM4986b, strM4986b, null, null);
                        }
                        break;
                }
            }
        });
    }

    @Override
    public final void mo206G0(Bundle bundle) {
        int intExtra = getIntent().getIntExtra("tab", 2);
        AppCompatImageView appCompatImageView = (AppCompatImageView) this.f3117F.f22157j;
        StringBuilder sb = new StringBuilder("http://" + pp3.m7879d() + ":" + Proxy.getPort());
        sb.append("?tab=");
        sb.append(intExtra);
        appCompatImageView.setImageBitmap(t11.m9185q(Context.VERSION_ECMASCRIPT, 1, sb.toString()));
        C1872zo c1872zo = this.f3117F;
        if (intExtra != 6) {
            ((MaterialTextView) c1872zo.f22158k).setText(AbstractC0463d2.m2462g(R.string.push_info, "http://" + pp3.m7879d() + ":" + Proxy.getPort()));
            return;
        }
        ((MaterialTextView) c1872zo.f22158k).setText(AbstractC0463d2.m2462g(R.string.xray_phone_scan_info, "http://" + pp3.m7879d() + ":" + Proxy.getPort()));
        ((MaterialTextView) this.f3117F.f22156i).setVisibility(8);
    }
}
