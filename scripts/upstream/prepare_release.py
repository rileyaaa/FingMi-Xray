#!/usr/bin/env python3
"""Regenerate approved fork integration from public FongMi source; fail closed."""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
from sync import git_tree, blob, upstream_version
from recovery_adapters import (
    site_view_model, base_loader, ok_http, ok_dns, img_util, ok_glide,
)
from xray_adapters import xray_import_action, disable_upstream_apk_update, setting_activity, setting_layout
from exo_adapters import media_factory, exo_session, exo_engine, engine_factory
from player_manager_adapter import player_manager
from side_request_adapters import playback_service, danmaku_api, subtitle_api, download
from live_metadata_adapters import live_api, epg_parser, live_view_model
from live_ui_adapters import channel_adapter
from xray_resources import xray_strings, xray_control_layout
from playback_activity_adapter import playback_activity, video_view_model
from activity_adapters import live_activity, video_activity
from engine_dialog_adapter import player_engine_dialog
from build_policy_adapters import gitignore, proguard, leanback_manifest, main_manifest


def one(s, a, b):
    if s.count(a) != 1:
        raise ValueError("Upstream adapter anchor changed: " + a[:65])
    return s.replace(a, b, 1)


def original(upstream, tree, path):
    if path not in tree:
        raise ValueError("Upstream file missing: " + path)
    return blob(upstream, tree[path]).decode("utf-8")


def fork_version(root, upstream_name, code):
    src = subprocess.check_output(["git", "show", "HEAD:app/build.gradle"], cwd=root).decode()
    name = re.search(r'versionName "(v\d+\.\d+\.\d+-xray\.\d+)"', src)
    old_code = re.search(r'versionCode (\d+)', src)
    if not name or not old_code:
        raise ValueError("Current fork version unknown")
    match = re.fullmatch(r"v(\d+\.\d+\.\d+)-xray\.(\d+)", name.group(1))
    revision = int(match.group(2)) + 1 if match.group(1) == upstream_name else 1
    new_code = 1000 * code + revision
    if not 1 <= revision <= 999 or new_code <= int(old_code.group(1)):
        raise ValueError("Invalid/nonincreasing Android versionCode")
    return name.group(1), f"v{upstream_name}-xray.{revision}", new_code


def gradle(source, tag, code):
    s=one(source,
        "def localProps = new Properties()\nrootProject.file('local.properties').withInputStream {\n    localProps.load(it)\n}",
        "def releaseSigning = new Properties()\nrootProject.file('signing/release-signing.properties').withInputStream {\n    releaseSigning.load(it)\n}")
    for pattern, replacement in (
        (r'versionCode \d+', f'versionCode {code}'),
        (r'versionName "\d+\.\d+\.\d+"', 'versionName "'+tag+'"'),
    ):
        if len(re.findall(pattern,s))!=1: raise ValueError("Invalid version fields")
        s=re.sub(pattern,lambda _:replacement,s,count=1)
    for a,b in (
        ("storeFile file(localProps['storeFile'])", "storeFile rootProject.file(releaseSigning['storeFile'])"),
        ("keyAlias localProps['keyAlias']", "keyAlias releaseSigning['keyAlias']"),
        ("keyPassword localProps['storePassword']", "keyPassword releaseSigning['storePassword']"),
        ("storePassword localProps['storePassword']", "storePassword releaseSigning['storePassword']"),
        ("'proguard-rules.pro'", "'proguard-rules.pro', 'proguard-rules-media.pro'"),
        ("    implementation project(':catvod')",
         "    implementation project(':catvod')\n    implementation project(':xray')\n    implementation project(':tv-recovery')"),
        ("    coreLibraryDesugaring libs.desugar",
         "    testImplementation 'junit:junit:4.13.2'\n    coreLibraryDesugaring libs.desugar")
    ): s=one(s,a,b)
    return s


def home(s):
    s=one(s,"import android.content.Intent;",
        "import android.content.Intent;\nimport com.fingmi.integration.recovery.FongMiNetworkRecovery;")
    s=one(s,"    private Intent pendingAction;",
        "    private Intent pendingAction;\n    private FongMiNetworkRecovery mNetworkRecovery;")
    s=one(s,"    protected void initView(Bundle savedInstanceState) {",
        """    protected void initView(Bundle savedInstanceState) {
        mNetworkRecovery = new FongMiNetworkRecovery(
                getApplication(),
                () -> { if (mViewModel != null) mViewModel.cancelResultRequest(); },
                () -> mBinding.progressLayout.showProgress(),
                () -> !isFinishing() && !isDestroyed(),
                () -> {
                    // Refresh only the content, never the consumed launch Intent.
                    mBinding.progressLayout.showContent();
                    setFocus();
                    getVideo();
                });""")
    s=one(s,"        mClock.start();\n    }\n\n    @Override\n    protected void onPause()",
        """        mClock.start();
        checkNetworkGeneration();
    }

    private void checkNetworkGeneration() {
        if (mNetworkRecovery != null) mNetworkRecovery.check();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) checkNetworkGeneration();
    }

    @Override
    protected void onPause()""")
    s=one(s,"    protected void onDestroy() {\n        if (--instanceCount",
        "    protected void onDestroy() {\n        if (mNetworkRecovery != null) mNetworkRecovery.close();\n        if (--instanceCount")
    for required in ("pendingAction = null;", "consumeAction();", "new FongMiNetworkRecovery("):
        if required not in s: raise ValueError("Home lost one-shot recovery contract")
    if "checkAction(getIntent())" in s: raise ValueError("Stale Home Intent replay")
    return s


def tests_proxy(s):
    prefix="selector.policy("
    parts=[]
    pos=0
    while True:
        i=s.find(prefix,pos)
        if i<0:
            parts.append(s[pos:]);break
        begin=i+len(prefix)
        parts.append(s[pos:begin])
        rest=s[begin:]
        if rest.startswith("okhttp3.HttpUrl.get(") or rest.startswith("HttpUrl.get("):
            # Already adapted after an earlier successful upstream upgrade.
            pos=begin
            continue
        if rest.startswith("new URI("):
            end=rest.find(")",len("new URI("))
            if end<0 or rest[end+1:end+2]!=",": raise ValueError("Unexpected URI test")
            parts.append("okhttp3.HttpUrl.get("+rest[len("new URI("):end]+")")
            pos=begin+end+1
        else:
            m=re.match(r"([A-Za-z_]\w*)\s*,",rest)
            if not m: raise ValueError("Unexpected proxy test argument")
            parts.append("okhttp3.HttpUrl.get("+m.group(1)+".toString())")
            pos=begin+len(m.group(1))
    return "".join(parts)


def rewrite_guards(root, upstream, tree, version):
    path = root / "tests/test-tv-network-recovery.py"
    source = path.read_text(encoding="utf-8")
    # Keep the 5.6.3 table as immutable historical evidence. The 5.8.7
    # table inherits nine paths and overrides seven legitimate new blobs.
    # Blindly rewriting all literal hashes would match 16 entries, corrupt
    # the old baseline, then fail the former count==9 invariant.
    nodes = {}
    for node in ast.parse(source).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            name = node.targets[0].id
            if name in ("UPSTREAM_EXACT_BLOBS", "UPSTREAM_EXACT_BLOBS_587"):
                if name in nodes:
                    raise ValueError("Duplicate TV recovery SHA table: " + name)
                nodes[name] = node.value
    if (version != "5.8.7" or
            source.count('elif upstream_version == "5.8.7":') != 1):
        raise ValueError("Unreviewed TV recovery SHA baseline for upstream " + version)
    base_node = nodes.get("UPSTREAM_EXACT_BLOBS")
    override_node = nodes.get("UPSTREAM_EXACT_BLOBS_587")
    if not isinstance(base_node, ast.Dict) or not isinstance(override_node, ast.Dict):
        raise ValueError("Missing TV recovery SHA tables")
    old = ast.literal_eval(base_node)
    if len(old) != 9 or len(override_node.keys) != 8:
        raise ValueError("Unexpected TV recovery SHA table size")
    if (override_node.keys[0] is not None or
            not isinstance(override_node.values[0], ast.Name) or
            override_node.values[0].id != "UPSTREAM_EXACT_BLOBS"):
        raise ValueError("TV recovery 5.8.7 pins must inherit the 5.6.3 table")
    overrides = {}
    for key_node, value_node in zip(override_node.keys[1:], override_node.values[1:]):
        name = ast.literal_eval(key_node)
        sha = ast.literal_eval(value_node)
        if name not in old or name in overrides:
            raise ValueError("Unexpected 5.8.7 recovery pin: " + str(name))
        overrides[name] = sha
    if len(overrides) != 7:
        raise ValueError("Unexpected 5.8.7 recovery SHA override count")
    pins = {**old, **overrides}
    for name, expected in pins.items():
        if (not isinstance(expected, str) or
                re.fullmatch(r"[a-f0-9]{40}", expected) is None or
                name not in tree or tree[name][1] != expected):
            raise ValueError("Official 5.8.7 TV recovery pin mismatch: " + name)
        actual_file = root / name
        if not actual_file.is_file() or actual_file.read_bytes() != blob(upstream, tree[name]):
            raise ValueError("Ordinary upstream recovery file drift: " + name)

    # The engine guard is current-version-only and can be updated after
    # confirming the generated engine remains byte-identical to upstream.
    path = root / "tests/test-xray-playback-parity.py"
    engine_source = path.read_text(encoding="utf-8")
    name = "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngine.java"
    if (name not in tree or not (root / name).is_file() or
            (root / name).read_bytes() != blob(upstream, tree[name])):
        raise ValueError("PlayerEngine no longer matches public upstream")
    pattern = re.compile(r'(git_blob_sha\("' + re.escape(name) + r'"\)\s*!=\s*")[a-f0-9]{40}(")')
    updated, count = pattern.subn(
        lambda m: m.group(1) + tree[name][1] + m.group(2), engine_source)
    if count != 1:
        raise ValueError("Unexpected player guard shape")
    path.write_text(updated, encoding="utf-8")


def metadata(root,old_tag,tag,new_upstream,code,upsha):
    old_upstream=old_tag.removeprefix("v").split("-xray.")[0]
    # GitHub's built-in Actions token cannot rewrite .github/workflows files.
    # Manual workflows now resolve their artifact names and release tags from
    # the checked-out app version; only the ordinary resume helper changes.
    path=root/"scripts/build/resume-verified-release.py"
    s=path.read_text()
    old_default='default="'+old_tag+'"'
    if s.count(old_default)!=1:
        raise ValueError("Current resume helper release tag anchor changed")
    path.write_text(s.replace(old_default,'default="'+tag+'"',1))
    readme=root/"README.md"
    s=readme.read_text()
    tick=chr(96)
    s=re.sub(r"当前 "+tick+r"main"+tick+r" 以 FongMi/TV \d+\.\d+\.\d+（"+tick+r"[a-f0-9]{40}"+tick+r"）",
             "当前 "+tick+"main"+tick+" 以 FongMi/TV "+new_upstream+"（"+tick+upsha+tick+"）",s,count=1)
    s=re.sub(r"当前正式版为 "+tick+r"v\d+\.\d+\.\d+-xray\.\d+"+tick+r" / "+tick+r"\d+"+tick,
             "当前源码版本配置： "+tick+tag+tick+" / "+tick+str(code)+tick+"；正式 APK 以 GitHub Releases/latest 为准",s,count=1)
    # Keep the current upstream version table synchronized with the APK.
    old_cell = "| FongMi/TV 公开源码 | **" + old_upstream + "**"
    new_cell = "| FongMi/TV 公开源码 | **" + new_upstream + "**"
    if s.count(old_cell) != 1:
        raise ValueError("README current upstream version table changed")
    s = s.replace(old_cell, new_cell, 1)
    row = next((x for x in s.splitlines() if x.startswith(new_cell)), None)
    if row is None:
        raise ValueError("README current upstream row missing")
    s = s.replace(row, new_cell + "（commit " + tick + upsha + tick + "） |", 1)
    readme.write_text(s)
    dev=root/"docs/DEVELOPMENT.md"
    s=dev.read_text()
    a=s.index("## 1. 当前工程基线")
    b=s.index("### 维护范围",a)
    intro=("\n## 1. 当前工程基线\n\n"
           "公开 FongMi/TV 固定源码 "+new_upstream+"（"+upsha+"）。"
           "FingMi-Xray 版本 "+tag+"，versionCode "+str(code)+"。"
           "本 fork 只维护 Xray 与待机网络恢复及必要接线；"
           "原 OkProxySelector 空 Host 崩溃修复已改为跟随上游 HttpUrl 版本。"
           "完整构建与设备验证仍以实际运行证据为准。"
           "下方按日期保留的 5.6.3→5.8.7 候选迁移笔记属于历史阶段记录；"
           "其中当时的未升级、未发布状态不得覆盖本段的当前源码基线。\n\n")
    s = s[:a] + intro + s[b:]
    # Keep pre-integration status reports as dated history, not the current
    # main or Release state after a verified upstream integration.
    if old_upstream == "5.6.3" and new_upstream == "5.8.7":
        dated = (
            "##### 2026-11-02 上游 5.8.7 与通用一键升级 Actions",
            "##### 2026-11-02 5.8.7 官方 Exo 接线适配（候选生成器，未发布）",
            "##### 2026-11-02 Xray 播放器接线解耦（5.8.7 迁移第一阶段）",
        )
        for heading in dated:
            if s.count(heading) != 1:
                raise ValueError("Cannot identify consolidated historical migration notes: " + heading)
            s = s.replace(
                heading,
                heading + "\n\n> 历史记录：本节保留原 5.6.3 迁移期间的候选状态和判断；"
                "当前源码版本以本文第一节为准，APK 验证与正式发布以 GitHub 记录为准。",
                1,
            )
    dev.write_text(s)


def prepare(root,upstream,target,report):
    tree=git_tree(upstream,target)
    upstream_name,upcode=upstream_version(upstream,target)
    old,tag,code=fork_version(root,upstream_name,upcode)
    settings=original(upstream,tree,"settings.gradle")
    for key in ("app","catvod","chaquo","quickjs"):
        if "include ':"+key+"'" not in settings: raise ValueError("Upstream module missing: "+key)
    proxy=original(upstream,tree,"catvod/src/main/java/com/github/catvod/net/OkProxySelector.java")
    if "Policy(HttpUrl url" not in proxy or "this.host = url.host();" not in proxy:
        raise ValueError("Public upstream null-host crash fix not confirmed")
    additions={
        "app/build.gradle":gradle(original(upstream,tree,"app/build.gradle"),tag,code),
        "settings.gradle":settings.rstrip()+"\ninclude ':libxray'\ninclude ':xray'\ninclude ':tv-recovery'\n",
        "catvod/src/main/java/com/github/catvod/net/OkProxySelector.java":proxy,
        "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java":
            home(original(upstream,tree,"app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java"))
    }
    tests=root/"catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java"
    if not tests.exists(): raise ValueError("Fork proxy regression suite missing")
    additions["catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java"]=tests_proxy(tests.read_text())
    # Fork policy / Xray web import integrations follow the new upstream API;
    # the APK auto-updater must never overwrite a manually installed Xray build.
    xray_hooks = (
        ("app/src/main/java/com/fongmi/android/tv/Updater.java", disable_upstream_apk_update),
        ("app/src/main/java/com/fongmi/android/tv/server/process/Action.java", xray_import_action),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java", setting_activity),
        ("app/src/leanback/res/layout/activity_setting.xml", setting_layout),
    )
    for filename, transform in xray_hooks:
        additions[filename] = transform(original(upstream, tree, filename))
    # Build Xray transport on top of the *selected new* FongMi Media3/Exo
    # implementations. 5.6.3's player implementations are never reused.
    exo_hooks = (
        ("app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java", media_factory),
        ("app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerSession.java", exo_session),
        ("app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java", exo_engine),
        ("app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java", engine_factory),
        ("app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java", player_manager),
    )
    for filename, transform in exo_hooks:
        additions[filename] = transform(original(upstream, tree, filename))
    # Auth.Context does not exist in the current 5.6.3 fork: compile this
    # source only when the target upstream's new API is being integrated.
    template = root / "scripts/upstream/templates/XrayPlaybackDataSourceFactory.java.in"
    bridge = template.read_text(encoding="utf-8")
    if "Auth.Context auth" not in bridge or "proxy.client()" not in bridge:
        raise ValueError("Missing guarded Xray 5.8.7 HTTP Auth adapter template")
    additions["app/src/main/java/com/fingmi/integration/xray/XrayPlaybackDataSourceFactory.java"] = bridge
    # Retained only as AC inputs. The 5.6.3 app source remains byte-identical
    # to the proven release; generated candidate gets the Xray-only adapters.
    for helper in ("XrayGuardedPlaybackDataSource", "XrayPlaybackRouting"):
        source = root / "scripts/upstream/reference" / (helper + ".java")
        code = source.read_text(encoding="utf-8")
        if not code.startswith("package com.fingmi.integration.xray;"):
            raise ValueError("Unrecognized retained Xray adapter: " + helper)
        additions["app/src/main/java/com/fingmi/integration/xray/" + helper + ".java"] = code

    # PlaybackService owns side-call network identity and remote-artwork
    # cancellation. Public 5.8.7 subtitle/danmaku APIs keep request IDs
    # and normal upstream direct-mode behavior unchanged.
    side_request_hooks = (
        ("app/src/main/java/com/fongmi/android/tv/service/PlaybackService.java", playback_service),
        ("app/src/main/java/com/fongmi/android/tv/api/DanmakuApi.java", danmaku_api),
        ("app/src/main/java/com/fongmi/android/tv/api/SubtitleApi.java", subtitle_api),
        ("catvod/src/main/java/com/github/catvod/net/Download.java", download),
        ("app/src/main/java/com/fongmi/android/tv/api/LiveApi.java", live_api),
        ("app/src/main/java/com/fongmi/android/tv/api/parser/EpgParser.java", epg_parser),
        ("app/src/main/java/com/fongmi/android/tv/model/LiveViewModel.java", live_view_model),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/adapter/ChannelAdapter.java", channel_adapter),
    )
    for filename, transform in side_request_hooks:
        additions[filename] = transform(original(upstream, tree, filename))
    side_gate = root / "scripts/upstream/templates/XraySideRequestGate.java.in"
    gate_source = side_gate.read_text(encoding="utf-8")
    if "getPlaybackHttpClient(null)" not in gate_source or "usePlaybackTransport(" not in gate_source:
        raise ValueError("Missing Xray side-request network gate")
    additions["app/src/main/java/com/fingmi/integration/xray/XraySideRequestGate.java"] = gate_source

    # Regenerate three Leanback locale resources from the new upstream.
    # Preserve ONLY approved xray_* labels from each old fork locale.
    for strings_name in (
        "app/src/leanback/res/values/strings.xml",
        "app/src/leanback/res/values-zh-rCN/strings.xml",
        "app/src/leanback/res/values-zh-rTW/strings.xml",
    ):
        additions[strings_name]=xray_strings(
            original(upstream,tree,strings_name),
            (root/strings_name).read_text(encoding="utf-8"))
    for filename in (
        "app/src/leanback/res/layout/view_control_live_action.xml",
        "app/src/leanback/res/layout/view_control_vod_action.xml",
    ):
        additions[filename]=xray_control_layout(original(upstream,tree,filename))

    # PlaybackActivity's owner-lost hook must remain narrow: the official
    # service, PIP, picture/decoder, focus and browser controls stay untouched.
    ui_hooks = (
        ("app/src/main/java/com/fongmi/android/tv/ui/activity/PlaybackActivity.java", playback_activity),
        ("app/src/main/java/com/fongmi/android/tv/model/VideoViewModel.java", video_view_model),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java", live_activity),
        ("app/src/leanback/java/com/fongmi/android/tv/ui/activity/VideoActivity.java", video_activity),
        ("app/src/main/java/com/fongmi/android/tv/ui/dialog/PlayerEngineDialog.java", player_engine_dialog),
    )
    for filename, transform in ui_hooks:
        additions[filename] = transform(original(upstream, tree, filename))

    # 5.8.7 dropped its old PushActivity and replaced the public web UI.
    # Retain Xray's phone QR flow as a self-contained xray.html page, served
    # by the unchanged Nano static-asset handler. No old Push business code.
    setting_xray_name="app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingXrayActivity.java"
    setting_xray=(root/setting_xray_name).read_text(encoding="utf-8")
    setting_xray=one(setting_xray,"import com.fongmi.android.tv.R;",
        "import com.fongmi.android.tv.R;\nimport com.fingmi.integration.xray.XrayPhoneImportDialog;")
    setting_xray=one(setting_xray,"PushActivity.start(this, 6);",
        "XrayPhoneImportDialog.show(this);")
    additions[setting_xray_name]=setting_xray
    additions["app/src/main/java/com/fingmi/integration/xray/XrayPhoneImportDialog.java"]=(
        root/"scripts/upstream/templates/XrayPhoneImportDialog.java.in").read_text(encoding="utf-8")
    xray_page=(root/"scripts/upstream/templates/xray.html.in").read_text(encoding="utf-8")
    if 'new URLSearchParams({do:"xray",link:value})' not in xray_page:
        raise ValueError("Missing Xray page safe form encoding")
    additions["app/src/main/assets/xray.html"]=xray_page
    nano=original(upstream,tree,"app/src/main/java/com/fongmi/android/tv/server/Nano.java")
    if "return getAssets(url.substring(1));" not in nano or "InputStream is = Asset.open(path);" not in nano:
        raise ValueError("New upstream no longer serves the standalone Xray asset page")

    # Preserve official 5.8.7 manifest declarations, R8 behavior and Git
    # ignore rules; add only Xray settings/JNI/installer safety boundaries.
    build_hooks = (
        (".gitignore", gitignore),
        ("app/proguard-rules.pro", proguard),
        ("app/src/leanback/AndroidManifest.xml", leanback_manifest),
        ("app/src/main/AndroidManifest.xml", main_manifest),
    )
    for filename, transform in build_hooks:
        additions[filename] = transform(original(upstream, tree, filename))

    # Regenerate the old fork's recovery hooks from the selected *new*
    # public FongMi implementations, never carry forward 5.6.3 business code.
    recovery_hooks = (
        ("app/src/main/java/com/fongmi/android/tv/model/SiteViewModel.java", site_view_model),
        ("app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java", base_loader),
        ("catvod/src/main/java/com/github/catvod/net/OkHttp.java", ok_http),
        ("catvod/src/main/java/com/github/catvod/net/OkDns.java", ok_dns),
        ("app/src/main/java/com/fongmi/android/tv/utils/ImgUtil.java", img_util),
        ("app/src/main/java/com/fongmi/android/tv/utils/OkGlideModule.java", ok_glide),
    )
    for filename, transform in recovery_hooks:
        additions[filename] = transform(original(upstream, tree, filename))

    for rel,text in additions.items():
        dest=root/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(text)
    rewrite_guards(root,upstream,tree,upstream_name)
    metadata(root,old,tag,upstream_name,code,target)
    lock=root/"scripts/upstream/baseline.json"
    data=json.loads(lock.read_text())
    if data["commit"]!=target or data["version"]!=upstream_name:
        raise ValueError("Pinned base mismatch")
    data["version_code"]=upcode
    lock.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    info={"release_tag":tag,"version_code":code,"upstream_commit":target,"upstream_version":upstream_name,
          "regenerated_files":list(additions)}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n")
    print("PREPARED: "+tag+" (not compiled or published)")
    return info


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path.cwd())
    p.add_argument("--upstream",type=Path,required=True)
    p.add_argument("--target",required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    prepare(args.root.resolve(),args.upstream.resolve(),args.target,args.report.resolve())


if __name__=="__main__":main()
