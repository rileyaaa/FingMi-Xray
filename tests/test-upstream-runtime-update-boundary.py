#!/usr/bin/env python3
"""Verify the actual staged settings/update boundary and removed Download."""
import argparse
from pathlib import Path
import sys
import tempfile
import re
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/upstream-adaptation"))
from prepare_candidate import LOCK,blob,guard_fork,overlay,verified_checkout
from verify_recovery_batch import method

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-tv",type=Path,required=True);p.add_argument("--tv",type=Path,required=True)
    a=p.parse_args();old,tv=a.old_tv.resolve(),a.tv.resolve()
    guard_fork();verified_checkout(old,"old_tv");verified_checkout(tv,"tv")
    with tempfile.TemporaryDirectory(prefix="fingmi-590-settings-boundary-") as d:
        c=Path(d)/"candidate";conflicts,manual=overlay(old,tv,c)
        base="app/src/main/java/com/fongmi/android/tv/"
        path=base+"Updater.java";old_download=base+"utils/Download.java"
        row=next(x for x in LOCK["fork_scope"] if x["path"]==path)
        assert path not in conflicts+manual and blob(c/path)==row["resolved"]
        s=(c/path).read_text();original=(tv/path).read_text()
        for sig in ("private void checkModules()","private List<RuntimeModule> getInstalledModules()","private Map<RuntimeModule, Long> getModuleUpdates(","private void addModuleUpdate(","private void onModulesChecked(","public void notifyModules()","private String getModuleTitle(","public static String transferText("):
            assert method(s,sig)==method(original,sig),sig
        assert "if (force || modulesChecked) return;" in method(s,"public void start(")
        for sig in ("public void onConfirm(","public void onCancel(","public void onPause(","public void success("):
            assert method(s,sig).endswith("{ }"),sig
        for token in ("Github.","UpdateService.","FileUtil.openFile","checkRelease(","prepareRelease(","verifyCachedApk("):
            assert token not in s,token
        assert "dialog.dismissAllowingStateLoss();" in method(s,"public void attach(")
        assert not (c/old_download).exists() and old_download not in conflicts
        for java in (c/"app/src").rglob("*.java"):
            data=java.read_text()
            assert "com.fongmi.android.tv.utils.Download" not in data,str(java)
            assert "UpdateService.start(" not in data,str(java)
        runtime=base+"utils/RuntimeInstaller.java"
        assert blob(c/runtime)==blob(tv/runtime)
        assert "RuntimeInstaller.getCatalog(" in s and "RuntimeModule.refresh();" in s
        # Existing manifest policy is an explicit remaining blocker, not a
        # hidden permission relaxation or a removal of runtime installation.
        manifest="app/src/main/AndroidManifest.xml"
        assert manifest in conflicts and blob(c/manifest)==blob(tv/manifest)
        ns="{http://schemas.android.com/apk/res/android}"
        root=ET.parse(c/manifest).getroot()
        assert any(n.get(ns+"name")=="android.permission.REQUEST_INSTALL_PACKAGES" for n in root.findall("uses-permission"))
        assert any(n.get(ns+"name")==".service.UpdateService" and n.get(ns+"exported")=="false" for n in root.findall("application/service"))
        setting=(c/"app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java").read_text()
        assert "mBinding.version.setOnClickListener" not in setting and "mBinding.xray.setOnClickListener" in setting
        print("PASS actual staged app-update compatibility shell, unchanged runtime module notifications and removed legacy Download; manifest policy remains blocked",flush=True)
        print("REMAINING_SCOPE",len(conflicts),"unresolved",len(manual),"old-media-review",flush=True)
if __name__=="__main__":main()
