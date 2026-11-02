#!/usr/bin/env python3
"""Regenerate approved fork integration from public FongMi source; fail closed."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from sync import git_tree, blob, upstream_version
from recovery_adapters import (
    site_view_model, base_loader, ok_http, ok_dns, img_util, ok_glide,
)


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
         "    implementation project(':catvod')\n    implementation project(':chaquo')\n    implementation project(':quickjs')\n    implementation project(':xray')\n    implementation project(':tv-recovery')"),
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


def rewrite_guards(root, upstream, tree):
    path=root/"tests/test-tv-network-recovery.py"
    s=path.read_text()
    pat=re.compile(r'("(?P<path>app/[^"]+)"\s*:\s*")[a-f0-9]{40}(")')
    count=0
    def fix(m):
        nonlocal count
        name=m.group("path")
        if name not in tree or not (root/name).is_file() or (root/name).read_bytes()!=blob(upstream,tree[name]):
            raise ValueError("Ordinary upstream recovery file drift: "+name)
        count+=1
        return m.group(1)+tree[name][1]+m.group(3)
    s=pat.sub(fix,s)
    if count!=9: raise ValueError("Unexpected upstream recovery guard count")
    path.write_text(s)
    path=root/"tests/test-xray-playback-parity.py"
    s=path.read_text()
    name="app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngine.java"
    if name not in tree or not (root/name).is_file() or (root/name).read_bytes()!=blob(upstream,tree[name]):
        raise ValueError("PlayerEngine no longer matches public upstream")
    p=re.compile(r'(git_blob_sha\("'+re.escape(name)+r'"\)\s*!=\s*")[a-f0-9]{40}(")')
    s,count=p.subn(lambda m:m.group(1)+tree[name][1]+m.group(2),s)
    if count!=1: raise ValueError("Unexpected player guard shape")
    path.write_text(s)


def metadata(root,old_tag,tag,new_upstream,code,upsha):
    old_upstream=old_tag.removeprefix("v").split("-xray.")[0]
    for name in (".github/workflows/current-main-build.yml",
                 ".github/workflows/publish-current-main-test-release.yml",
                 "scripts/build/resume-verified-release.py"):
        path=root/name
        s=path.read_text()
        s=s.replace("fingmi-xray-"+old_upstream,"fingmi-xray-"+new_upstream)
        s=s.replace("Compile current "+old_upstream+" Leanback source","Compile current "+new_upstream+" Leanback source")
        s=s.replace("Build and publish signed "+old_upstream+" fork release","Build and publish signed "+new_upstream+" fork release")
        s=s.replace('RELEASE_TAG: "'+old_tag+'"','RELEASE_TAG: "'+tag+'"')
        if name.endswith("resume-verified-release.py"):
            s=s.replace('default="'+old_tag+'"','default="'+tag+'"')
        path.write_text(s)
    readme=root/"README.md"
    s=readme.read_text()
    tick=chr(96)
    s=re.sub(r"当前 "+tick+r"main"+tick+r" 以 FongMi/TV \d+\.\d+\.\d+（"+tick+r"[a-f0-9]{40}"+tick+r"）",
             "当前 "+tick+"main"+tick+" 以 FongMi/TV "+new_upstream+"（"+tick+upsha+tick+"）",s,count=1)
    s=re.sub(r"当前正式版为 "+tick+r"v\d+\.\d+\.\d+-xray\.\d+"+tick+r" / "+tick+r"\d+"+tick,
             "当前源码版本配置： "+tick+tag+tick+" / "+tick+str(code)+tick+"；正式 APK 以 GitHub Releases/latest 为准",s,count=1)
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
           "完整构建与设备验证仍以实际运行证据为准。\n\n")
    dev.write_text(s[:a]+intro+s[b:])


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
    rewrite_guards(root,upstream,tree)
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
