#!/usr/bin/env python3
"""Test the remaining fork adapters against ACTUAL selected FongMi source.

All public source hooks are evaluated before any sync or version generation.
Independent failures are collected, so one low-cost AC preview yields a useful
list rather than stopping at the first untested production source shape.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/upstream"))
from sync import git_tree, blob, upstream_version
from prepare_release import gradle, home
from recovery_adapters import (
    site_view_model, base_loader, ok_http, ok_dns, img_util, ok_glide,
)
from xray_adapters import (
    disable_upstream_apk_update, xray_import_action, setting_activity, setting_layout,
)


def verify(upstream, target):
    tree = git_tree(upstream, target)
    version, version_code = upstream_version(upstream, target)
    release_name = "v" + version + "-xray.1"
    android_code = version_code * 1000 + 1
    jobs = (
        ("app/build.gradle", "gradle", lambda s: gradle(s, release_name, android_code),
         ("versionName \"" + release_name + "\"", "versionCode " + str(android_code))),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java", "home", home,
         ("new FongMiNetworkRecovery(", "checkNetworkGeneration();")),
        ("app/src/main/java/com/fongmi/android/tv/Updater.java", "disable_upstream_apk_update",
         disable_upstream_apk_update, ("Intentionally disabled upstream APK updater", "public void start(")),
        ("app/src/main/java/com/fongmi/android/tv/server/process/Action.java", "xray_import_action",
         xray_import_action, ('case "xray" -> onXray(params);', "XrayImportEvent.post(link.trim());")),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java", "setting_activity",
         setting_activity, ("mBinding.xray.setOnClickListener", "SettingXrayActivity.start(this);")),
        ("app/src/leanback/res/layout/activity_setting.xml", "setting_layout",
         setting_layout, ('android:id="@+id/xray"', 'android:id="@+id/xrayText"')),
        ("app/src/main/java/com/fongmi/android/tv/model/SiteViewModel.java", "site_view_model",
         site_view_model, ("cancelResultRequest()",)),
        ("app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java", "base_loader",
         base_loader, ("clear(Runnable onComplete)",)),
        ("catvod/src/main/java/com/github/catvod/net/OkHttp.java", "ok_http",
         ok_http, ("resetApiNetworkForResume",)),
        ("catvod/src/main/java/com/github/catvod/net/OkDns.java", "ok_dns",
         ok_dns, ("resetForNetworkChange",)),
        ("app/src/main/java/com/fongmi/android/tv/utils/ImgUtil.java", "img_util",
         img_util, ("resetNetworkFailures",)),
        ("app/src/main/java/com/fongmi/android/tv/utils/OkGlideModule.java", "ok_glide",
         ok_glide, ("new OkHttpUrlLoader.Factory",)),
    )
    failures = []
    successes = 0
    for path, label, transform, markers in jobs:
        try:
            if path not in tree:
                raise ValueError("missing official source file")
            original = blob(upstream, tree[path]).decode("utf-8")
            generated = transform(original)
            if not generated or generated == original:
                raise ValueError("did not generate a changed candidate")
            for marker in markers:
                if marker not in generated:
                    raise ValueError("required generated contract missing: " + marker)
        except Exception as exc:
            failures.append(f"{label} ({path}): {type(exc).__name__}: {exc}")
            print("FAIL: " + failures[-1], file=sys.stderr)
        else:
            successes += 1
            print("PASS: " + label)
    if failures:
        raise AssertionError(f"{len(failures)}/{len(jobs)} real upstream hooks failed; "
                             "see all FAIL lines above. No source was modified.")
    print(f"PASS: {successes} previously fixture-only adapters against FongMi/TV "
          f"{version} at {target}")
    return successes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    verify(args.upstream, args.target)


if __name__ == "__main__":
    main()
