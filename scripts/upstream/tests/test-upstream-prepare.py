#!/usr/bin/env python3
"""Offline contract tests for versioning, signed build overlays and TV one-shot hooks."""
from pathlib import Path
import sys
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts/upstream"))
from prepare_release import gradle, home, tests_proxy, fork_version, metadata, rewrite_guards

# The real repository documentation must also satisfy metadata()'s exact
# anchors. Fixture-only tests previously missed a duplicated historical section.
audit = (Path(__file__).resolve().parents[3] / "docs/DEVELOPMENT.md").read_text(encoding="utf-8")
for heading in (
    "##### 2026-11-02 上游 5.8.7 与通用一键升级 Actions",
    "##### 2026-11-02 5.8.7 官方 Exo 接线适配（候选生成器，未发布）",
    "##### 2026-11-02 Xray 播放器接线解耦（5.8.7 迁移第一阶段）",
):
    assert audit.count(heading) == 1, "Migration retrospective anchors are ambiguous: " + heading

APP = """def localProps = new Properties()
rootProject.file('local.properties').withInputStream {
    localProps.load(it)
}
android {
    defaultConfig {
        versionCode 587
        versionName "5.8.7"
    }
    signingConfigs {
        release {
            storeFile file(localProps['storeFile'])
            keyAlias localProps['keyAlias']
            keyPassword localProps['storePassword']
            storePassword localProps['storePassword']
        }
    }
    buildTypes {
        release {
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
dependencies {
    implementation project(':catvod')
    coreLibraryDesugaring libs.desugar
}
"""
converted = gradle(APP, "v5.8.7-xray.1", 587001)
for needle in ("versionCode 587001", 'versionName "v5.8.7-xray.1"',
               "signing/release-signing.properties", "'proguard-rules-media.pro'",
               "implementation project(':xray')", "implementation project(':tv-recovery')"):
    assert needle in converted, needle
assert "implementation project(':chaquo')" not in converted
assert "implementation project(':quickjs')" not in converted

HOME = """import android.content.Intent;
class HomeActivity {
    private Intent pendingAction;
    protected void initView(Bundle savedInstanceState) {
    }
    private void consumeAction() {
        pendingAction = null;
    }
    private void fireActionOnce() {
        consumeAction();
    }
    protected void onResume() {
        super.onResume();
        mClock.start();
    }

    @Override
    protected void onPause() {
    }
    protected void onDestroy() {
        if (--instanceCount == 0) { }
    }
}
"""
h = home(HOME)
assert h.count("new FongMiNetworkRecovery(") == 1
assert "checkAction(getIntent())" not in h
assert "if (hasFocus) checkNetworkGeneration();" in h
assert "if (mNetworkRecovery != null) mNetworkRecovery.close();" in h
for invalid in (HOME.replace("pendingAction = null;", ""), HOME.replace("mClock.start();", "mClock.start(x);")):
    try:
        home(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Fail-closed Home adapter accepted changed upstream API")

tests = """selector.policy(new URI("http://api_sub.example.com:8080/live"), null);
selector.policy(target, selector.policy(new URI("http://ott.example.com"), null));
assertNull(new URI("http://bad_host.example").getHost());
"""
p = tests_proxy(tests)
assert "selector.policy(new URI(" not in p
assert p.count("okhttp3.HttpUrl.get(") == 3
assert "assertNull(new URI(" in p
assert tests_proxy(p) == p, "Repeated upgrade must not double-wrap HttpUrl"

with tempfile.TemporaryDirectory(prefix="upstream-version-contract-") as temp:
    root = Path(temp)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "upgrade-test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "upgrade@test.invalid"], cwd=root, check=True)
    (root / "app").mkdir()
    source = root / "app/build.gradle"
    source.write_text('versionCode 563001\nversionName "v5.6.3-xray.1"\n')
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
    assert fork_version(root, "5.8.7", 587) == ("v5.6.3-xray.1", "v5.8.7-xray.1", 587001)
    source.write_text('versionCode 587001\nversionName "v5.8.7-xray.1"\n')
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "next"], cwd=root, check=True)
    assert fork_version(root, "5.8.7", 587) == ("v5.8.7-xray.1", "v5.8.7-xray.2", 587002)
    try:
        fork_version(root, "5.6.3", 563)
    except ValueError:
        pass
    else:
        raise AssertionError("Version rollback allowed")


with tempfile.TemporaryDirectory(prefix="upstream-doc-version-contract-") as temp:
    root = Path(temp)
    old = "v5.6.3-xray.1"
    new = "v5.8.7-xray.1"
    sha = "8626650ebcbc0d028e16d859e826fcf439720f3a"
    for name in (".github/workflows/01-当前源码编译与APK验证.yml",
                 ".github/workflows/02-正式APK构建与发布.yml",
                 "scripts/build/resume-verified-release.py"):
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('RELEASE_TAG: "' + old + '"\n'
                        'fingmi-xray-5.6.3-build-failure-reports\n'
                        'Compile current 5.6.3 Leanback source\n'
                        'default="' + old + '"\n', encoding="utf-8")
    # Record the original workflow bytes. Candidate upgrade commits must
    # never attempt to rewrite protected .github/workflows definitions.
    workflows = (".github/workflows/01-当前源码编译与APK验证.yml",
                 ".github/workflows/02-正式APK构建与发布.yml")
    frozen_workflows = {name: (root / name).read_bytes() for name in workflows}
    readme = root / "README.md"
    readme.write_text(
        '当前 `main` 以 FongMi/TV 5.6.3（`' + "c616c0aa3613e87529791587a9f71b78c278c991" + '`）\n'
        '当前正式版为 `' + old + '` / `563001`\n'
        '| FongMi/TV 公开源码 | **5.6.3**（commit `c616c0aa3613e87529791587a9f71b78c278c991`） |\n',
        encoding="utf-8")
    development = root / "docs/DEVELOPMENT.md"
    development.parent.mkdir(parents=True, exist_ok=True)
    development.write_text(
        "# Development\n## 1. 当前工程基线\n原 5.6.3 基线\n"
        "### 维护范围\n仅 Xray 和 TV 网络恢复\n"
        "##### 2026-11-02 上游 5.8.7 与通用一键升级 Actions\n"
        "5.8.7 当时尚未发布。\n"
        "##### 2026-11-02 5.8.7 官方 Exo 接线适配（候选生成器，未发布）\n"
        "适配进行中。\n"
        "##### 2026-11-02 Xray 播放器接线解耦（5.8.7 迁移第一阶段）\n"
        "当时尚未编译。\n", encoding="utf-8")
    metadata(root, old, new, "5.8.7", 587001, sha)
    updated = development.read_text(encoding="utf-8")
    assert "固定源码 5.8.7（" + sha + "）" in updated
    assert "FingMi-Xray 版本 " + new + "，versionCode 587001" in updated
    assert "候选迁移笔记属于历史阶段记录" in updated
    assert "5.8.7 当时尚未发布。" in updated
    readme_output = readme.read_text(encoding="utf-8")
    assert "FongMi/TV 5.8.7（`" + sha + "`）" in readme_output
    assert "| FongMi/TV 公开源码 | **5.8.7**（commit `" + sha + "`） |" in readme_output
    for name in workflows:
        assert (root / name).read_bytes() == frozen_workflows[name], name
    helper = (root / "scripts/build/resume-verified-release.py").read_text(encoding="utf-8")
    assert 'default="' + new + '"' in helper
    assert 'default="' + old + '"' not in helper


# The real 5.8.7 guard has 9 historical pins and 7 revised pins.
# Exercise the candidate preparation against that exact shape without AC.
# Synthetic blob content isolates SHA-table selection from network/git access.
from unittest.mock import patch
import re
with tempfile.TemporaryDirectory(prefix="upstream-recovery-pins-") as temp:
    root = Path(temp)
    repo_root = Path(__file__).resolve().parents[3]
    guard_name = "tests/test-tv-network-recovery.py"
    guard = (repo_root / guard_name).read_text(encoding="utf-8")
    pins = re.findall(r'"(app/[^"]+)"\s*:\s*"([a-f0-9]{40})"', guard)
    assert len(pins) == 16, "Current TV recovery baselines must retain 9+7 literals"
    selected = dict(pins)
    assert len(selected) == 9
    engine = "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngine.java"
    engine_guard = "tests/test-xray-playback-parity.py"
    for relative, contents in (
        (guard_name, guard),
        (engine_guard, (repo_root / engine_guard).read_text(encoding="utf-8")),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    tree = {name: ("100644", sha) for name, sha in selected.items()}
    tree[engine] = ("100644", "a" * 40)
    for relative in tree:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"official-upstream-fixture")

    with patch("prepare_release.blob", return_value=b"official-upstream-fixture"):
        rewrite_guards(root, root, tree, "5.8.7")
        assert (root / guard_name).read_text(encoding="utf-8") == guard, (
            "Historical 5.6.3 SHA pins may not be rewritten during 5.8.7 upgrade"
        )
        assert '"'+("a" * 40)+'"' in (root / engine_guard).read_text(encoding="utf-8")

        try:
            rewrite_guards(root, root, tree, "5.8.8")
        except ValueError:
            pass
        else:
            raise AssertionError("Unknown upstream version bypassed recovery scope review")

        changed = dict(tree)
        first = next(iter(selected))
        changed[first] = ("100644", "b" * 40)
        try:
            rewrite_guards(root, root, changed, "5.8.7")
        except ValueError:
            pass
        else:
            raise AssertionError("Changed official source SHA bypassed TV recovery guard")

        (root / first).write_bytes(b"unapproved-local-change")
        try:
            rewrite_guards(root, root, tree, "5.8.7")
        except ValueError:
            pass
        else:
            raise AssertionError("Modified business source bypassed TV recovery guard")

print("PASS fork versioning, signed Gradle overlay, Home one-shot recovery and HttpUrl regressions and regenerated metadata and 5.8.7 recovery pins")
