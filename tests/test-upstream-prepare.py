#!/usr/bin/env python3
"""Offline contract tests for versioning, signed build overlays and TV one-shot hooks."""
from pathlib import Path
import sys
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/upstream"))
from prepare_release import gradle, home, tests_proxy, fork_version

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

print("PASS fork versioning, signed Gradle overlay, Home one-shot recovery and HttpUrl regressions")
