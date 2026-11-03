#!/usr/bin/env python3
"""Guard upstream-first Xray import and the private fork's disabled APK updater."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts/upstream"))
from xray_adapters import xray_import_action, disable_upstream_apk_update, setting_activity, setting_layout, UPDATER_PUBLIC_API


ACTION = """import com.fongmi.android.tv.event.ServerEvent;
class Action {
    void doJob(String param, Map<String, String> params) {
        switch (param) {
            case "danmaku" -> onDanmaku(params);
        }
    }
    private void onSetting(Map<String, String> params) {
    }
}"""
patched = xray_import_action(ACTION)
for require in ('case "xray" -> onXray(params);',
                "XrayImportEvent.post(link.trim());",
                "import com.fongmi.android.tv.event.XrayImportEvent;"):
    assert require in patched
assert "case \"danmaku\" -> onDanmaku(params);" in patched
assert xray_import_action(patched) == patched
try:
    xray_import_action(ACTION.replace('case "danmaku" -> onDanmaku(params);', 'case "changed" -> onDanmaku(params);'))
except ValueError:
    pass
else:
    raise AssertionError("Unrecognized upstream Action switch did not stop")


source = """package com.fongmi.android.tv;
public class Updater {
"""
# Simulated public 5.8.7 API; upstream changes must fail closed.
for name, args in sorted(UPDATER_PUBLIC_API):
    static = "static " if name in ("get", "transferText") else ""
    typ = "Updater" if name == "get" else "boolean" if name == "isPaused" else "String" if name == "transferText" else "void"
    source += f"    public {static}{typ} {name}({args}) {{}}\n"
source += "}\n"
safe = disable_upstream_apk_update(source)
for forbidden in ("Github.", "Download.", "FileUtil.openFile", "OkHttp", "update.apk",
                  "REQUEST_INSTALL_PACKAGES", "Updater.create()"):
    assert forbidden not in safe
assert "Intentionally disabled" in safe
assert "public static Updater get()" in safe
assert "public void start(FragmentActivity activity, boolean force)" in safe
assert "public void notifyModules()" in safe

unknown = source.replace("public void success(File file) {}", "public void success(File file) {}\npublic void installApk(File file) {}")
try:
    disable_upstream_apk_update(unknown)
except ValueError:
    pass
else:
    raise AssertionError("Unknown upstream public API allowed")

# Compile the real generated no-op class with minimal Android/UI type stubs.
with tempfile.TemporaryDirectory(prefix="fork-updater-javac-") as tmp:
    root = Path(tmp)
    stubs = {
        "android/view/View.java": "package android.view; public class View {}\n",
        "androidx/fragment/app/FragmentActivity.java": "package androidx.fragment.app; public class FragmentActivity {}\n",
        "com/fongmi/android/tv/ui/dialog/UpdateDialog.java":
            "package com.fongmi.android.tv.ui.dialog; public class UpdateDialog { public void dismissAllowingStateLoss() {} }\n",
        "com/fongmi/android/tv/Updater.java": safe,
    }
    for name, content in stubs.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(root / "classes"),
                    *(str(root / f) for f in stubs)], check=True)


# Newer FongMi settings pages have module controls absent from the old fork.
# The overlay must leave those upstream controls untouched.
SETTINGS = """import com.fongmi.android.tv.BuildConfig;
class SettingActivity {
    protected void initView(Bundle savedInstanceState) {
        mBinding.versionText.setText(BuildConfig.VERSION_NAME);
    }
    protected void initEvent() {
        mBinding.danmaku.setOnClickListener(this::onDanmaku);
        mBinding.module.setOnClickListener(view -> ModuleActivity.start(this));
    }
    private void onDanmaku(View view) {}
}
"""
settings = setting_activity(SETTINGS)
for value in ("mBinding.xray.setOnClickListener(this::onXray);",
              "SettingXrayActivity.start(this);", "setXrayText();",
              "XrayPreferences preferences = new XrayPreferences(this);"):
    assert value in settings
assert "ModuleActivity.start(this)" in settings
assert setting_activity(settings) == settings
try:
    setting_activity(SETTINGS.replace("mBinding.danmaku.setOnClickListener", "mBinding.other.setOnClickListener"))
except ValueError:
    pass
else:
    raise AssertionError("Unknown upstream settings event hooks accepted")

from xml.etree import ElementTree as ET
XML = """<settings xmlns:android="http://schemas.android.com/apk/res/android"
                 xmlns:tools="http://schemas.android.com/tools">
    <androidx.appcompat.widget.LinearLayoutCompat>
        <androidx.appcompat.widget.LinearLayoutCompat android:id="@+id/size">\n            <com.google.android.material.textview.MaterialTextView />\n        </androidx.appcompat.widget.LinearLayoutCompat>
    </androidx.appcompat.widget.LinearLayoutCompat>
    <androidx.appcompat.widget.LinearLayoutCompat android:id="@+id/incognito" />
</settings>"""
patched_xml = setting_layout(XML)
ET.fromstring(patched_xml)
assert patched_xml.count('android:id="@+id/xray"') == 1
assert patched_xml.count('android:id="@+id/xrayText"') == 1
assert 'android:id="@+id/size"' in patched_xml
assert setting_layout(patched_xml) == patched_xml
try:
    setting_layout(XML.replace('@+id/incognito', '@+id/changed'))
except ValueError:
    pass
else:
    raise AssertionError("Unknown upstream settings XML structure accepted")

print("PASS upstream Action Xray import / Updater API, Xray settings and valid XML; generated Java compiles")
