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
