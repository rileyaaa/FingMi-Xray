#!/usr/bin/env python3
"""Narrow Xray application policy adapters, generated from canonical upstream.

Never rebase old app update code: only expose the selected upstream public
Updater API as a fork-safe no-op. Importing Xray nodes through /action is a
small, exact-anchor addition to the current upstream request handler.
"""
import re


def once(s, old, new, reason):
    if s.count(old) != 1:
        raise ValueError(f"Unknown upstream {reason}: expected exactly one source anchor")
    return s.replace(old, new, 1)


def xray_import_action(s):
    if 'case "xray" -> onXray(params);' in s:
        if "XrayImportEvent.post(link.trim());" not in s:
            raise ValueError("Unknown preexisting Xray import endpoint")
        return s
    s = once(s,
        "import com.fongmi.android.tv.event.ServerEvent;",
        "import com.fongmi.android.tv.event.ServerEvent;\n"
        "import com.fongmi.android.tv.event.XrayImportEvent;",
        "event import")
    s = once(s,
        '            case "danmaku" -> onDanmaku(params);',
        '            case "danmaku" -> onDanmaku(params);\n'
        '            case "xray" -> onXray(params);',
        "action route")
    s = once(s,
        "    private void onSetting(Map<String, String> params) {",
        """    private void onXray(Map<String, String> params) {
        String link = params.get("link");
        if (TextUtils.isEmpty(link)) return;
        XrayImportEvent.post(link.trim());
    }

    private void onSetting(Map<String, String> params) {""",
        "Xray node import handler")
    for required in ("XrayImportEvent.post(link.trim());", 'case "xray" -> onXray(params);'):
        if required not in s:
            raise ValueError("Xray import handler lost required wiring")
    return s




def setting_activity(s):
    """Keep the current upstream settings page, adding just Xray entry points."""
    if "mBinding.xray.setOnClickListener(this::onXray);" in s:
        if "setXrayText();" not in s or "SettingXrayActivity.start(this);" not in s:
            raise ValueError("Unrecognized existing Xray settings integration")
        return s
    s = once(s, "import com.fongmi.android.tv.BuildConfig;",
        "import com.fongmi.android.tv.BuildConfig;\n"
        "import com.fingmi.xray.config.XrayDisplay;\n"
        "import com.fingmi.xray.config.XrayPreferences;", "settings imports")
    s = once(s, "        mBinding.versionText.setText(BuildConfig.VERSION_NAME);",
        "        mBinding.versionText.setText(BuildConfig.VERSION_NAME);\n"
        "        setXrayText();", "settings Xray state")
    s = once(s, "        mBinding.danmaku.setOnClickListener(this::onDanmaku);",
        "        mBinding.danmaku.setOnClickListener(this::onDanmaku);\n"
        "        mBinding.xray.setOnClickListener(this::onXray);", "settings Xray click")
    if "protected void onResume()" in s:
        raise ValueError("Upstream added its own settings onResume; manual Xray review required")
    s = once(s, "    private void onDanmaku(View view) {",
        """    private void onXray(View view) {
        SettingXrayActivity.start(this);
    }

    private void setXrayText() {
        try {
            XrayPreferences preferences = new XrayPreferences(this);
            if (!preferences.isConfigured()) {
                mBinding.xrayText.setText(R.string.xray_not_configured);
                return;
            }
            mBinding.xrayText.setText(XrayDisplay.describe(preferences.getShareLink()));
        } catch (Exception | LinkageError ignored) {
            mBinding.xrayText.setText(R.string.xray_not_configured);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (mBinding != null) setXrayText();
    }

    private void onDanmaku(View view) {""", "settings Xray UI hook")
    return s


def setting_layout(s):
    """Add one Xray row without replacing newer upstream module/settings rows."""
    if 'android:id="@+id/xray"' in s:
        if 'android:id="@+id/xrayText"' not in s:
            raise ValueError("Unrecognized existing Xray settings row")
        return s
    size='android:id="@+id/size"'
    if s.count(size) != 1 or s.count('android:id="@+id/incognito"') != 1:
        raise ValueError("Upstream settings layout no longer has unique row anchors")
    start=s.index(size)
    closing="</androidx.appcompat.widget.LinearLayoutCompat>"
    inner=s.find(closing,start)
    if inner < 0: raise ValueError("Missing settings size row close tag")
    outer=s.find(closing,inner+len(closing))
    if outer < 0: raise ValueError("Missing settings size container close tag")
    after=outer+len(closing)
    if s.find('android:id="@+id/incognito"',after,after+2500)<0:
        raise ValueError("Upstream settings rows changed; manual Xray layout review")
    row="""

        <androidx.appcompat.widget.LinearLayoutCompat
            android:id="@+id/xray"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            android:background="@drawable/selector_item"
            android:focusable="true"
            android:focusableInTouchMode="true"
            android:orientation="horizontal">

            <com.google.android.material.textview.MaterialTextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginEnd="16dp"
                android:text="@string/xray_setting"
                android:textColor="@color/white"
                android:textSize="18sp" />

            <com.google.android.material.textview.MaterialTextView
                android:id="@+id/xrayText"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:ellipsize="end"
                android:gravity="end"
                android:singleLine="true"
                android:textColor="@color/white"
                android:textSize="18sp"
                tools:text="VLESS  e***.com:443" />

        </androidx.appcompat.widget.LinearLayoutCompat>"""
    return s[:after]+row+s[after:]


# The public 5.8.7 API. Stop when future upstream adds a new method rather
# than generating an incomplete stub that compiles only by accident.
UPDATER_PUBLIC_API = {
    ("get", ""),
    ("start", "FragmentActivity activity, boolean force"),
    ("notifyModules", ""),
    ("attach", "UpdateDialog dialog"),
    ("detach", "UpdateDialog dialog"),
    ("onConfirm", "View view"),
    ("onCancel", "View view"),
    ("onPause", "View view"),
    ("isPaused", ""),
    ("transferText", "long total, long downloaded, long speed"),
    ("paused", ""),
    ("progress", "int progress"),
    ("error", "String msg"),
    ("success", "File file"),
}


def disable_upstream_apk_update(source):
    public = {
        (m.group(1), " ".join(m.group(2).split()))
        for m in re.finditer(
            r'(?m)^\s*public\s+(?:static\s+)?[\w<>?]+\s+(\w+)\s*\(([^)]*)\)',
            source,
        )
    }
    if public != UPDATER_PUBLIC_API:
        missing = sorted(UPDATER_PUBLIC_API - public)
        extra = sorted(public - UPDATER_PUBLIC_API)
        raise ValueError(f"Unknown upstream Updater API. missing={missing} added={extra}")
    if "class Updater {" not in source:
        raise ValueError("Unexpected upstream Updater declaration")
    return """package com.fongmi.android.tv;

import android.view.View;
import androidx.fragment.app.FragmentActivity;
import com.fongmi.android.tv.ui.dialog.UpdateDialog;
import java.io.File;

/**
 * Intentionally disabled upstream APK updater for the private Xray fork.
 * Retains the current public FongMi API to avoid call-site drift.
 * Updates are shipped only through a verified, manually triggered GitHub run.
 */
public final class Updater {

    private static final Updater INSTANCE = new Updater();

    private Updater() {}

    public static Updater get() { return INSTANCE; }

    public void start(FragmentActivity activity, boolean force) {
        // Intentionally disabled: never fetch or install upstream APKs.
    }

    public void notifyModules() {}
    public void attach(UpdateDialog dialog) {
        if (dialog != null) dialog.dismissAllowingStateLoss();
    }
    public void detach(UpdateDialog dialog) {}
    public void onConfirm(View view) {}
    public void onCancel(View view) {}
    public void onPause(View view) {}
    public boolean isPaused() { return false; }
    public static String transferText(long total, long downloaded, long speed) { return ""; }
    public void paused() {}
    public void progress(int progress) {}
    public void error(String msg) {}
    public void success(File file) {}
}
"""
