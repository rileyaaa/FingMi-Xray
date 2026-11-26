#!/usr/bin/env python3
"""Stage only an isolated probe in disposable, pinned upstream checkout."""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from stage_mpv_jni_bridge import BASE, BASE_BLOB, MIT_BLOB, pinned, port

MEDIA = "3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
MPV = "1bf892e3271e73d8649f2d209027f1fb17515d15"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: stage_android_probe.py disposable-media-checkout pinned-mpv-checkout")
    media, mpv = (Path(p).resolve() for p in sys.argv[1:])
    for repo, commit in ((media, MEDIA), (mpv, MPV)):
        if git(repo, "rev-parse", "HEAD") != commit or git(repo, "status", "--porcelain"):
            raise SystemExit("wrong or dirty source: " + str(repo))
    for name, sha in (
        ("libraries/datasource/src/main/java/androidx/media3/datasource/DataSource.java", "fc93269055c2a260549ed348b50c18cdb0879c4d"),
        ("libraries/datasource/src/main/java/androidx/media3/datasource/DataSpec.java", "5d0e52cee49672ab418d4c14bacda64ec39b34aa"),
        ("libraries/datasource_okhttp/src/main/java/androidx/media3/datasource/okhttp/OkHttpDataSource.java", "2c1f61cc2d3148d1e3986480504d8d057fd18825"),
        ("gradle/libs.versions.toml", "7d0a7a49d49bce8f46c5a3007b24251c288b232b"),
    ):
        pinned(media / name, sha)
    pinned(mpv / "app/src/main/jni/stream.cpp", "a4ebe55984fa12de9b0a354da4a98cfcfa634d5d")
    bridge = port(pinned(media / BASE, BASE_BLOB), pinned(mpv / "LICENSE", MIT_BLOB))
    module = media / "mpv-stream-probe"
    module.mkdir()
    main = module / "src/main"
    adapter = main / "java/androidx/media3/mpvplayer/media"
    adapter.mkdir(parents=True)
    for name in ("Media3MpvInput.java", "MpvStreamOwner.java"):
        shutil.copyfile(HERE.parent / name, adapter / name)
        print("PROBE_INPUT", name, git(media, "hash-object", str(adapter / name)), flush=True)
    java = main / "java/is/xyz/mpv/MPVLib.java"
    java.parent.mkdir(parents=True)
    java.write_text(bridge, encoding="utf-8", newline="\n")
    print("PROBE_BRIDGE_SHA256", hashlib.sha256(java.read_bytes()).hexdigest(), flush=True)
    shutil.copyfile(HERE / "AndroidManifest.xml", main / "AndroidManifest.xml")
    shutil.copyfile(HERE / "build.gradle.kts", module / "build.gradle.kts")
    tests = module / "src/androidTest/java/org/fingmi/mpvprobe"
    tests.mkdir(parents=True)
    shutil.copyfile(HERE / "Media3MpvInputAndroidTest.java", tests / "Media3MpvInputAndroidTest.java")
    with (media / "settings.gradle.kts").open("a", encoding="utf-8") as f:
        f.write('\ninclude(":mpv-stream-probe")\n')
    print("STAGED_ANDROID_PROBE", MEDIA, MPV, flush=True)


if __name__ == "__main__":
    main()
