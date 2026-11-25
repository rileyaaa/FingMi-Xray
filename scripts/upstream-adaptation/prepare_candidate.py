#!/usr/bin/env python3
"""Stage exact upstream TV 5.9.0 + the frozen fork's explicit, minimal deltas.

Only public-source inputs and the sanitized, shallow development checkout are
read. A conflict leaves the upstream file intact and is a blocking report,
not a fabricated implementation. No historic fork checkout, signing, APK
download, untrusted media substitute, or release API is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
from recovery_loader import adapt_base_loader
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
LOCK = json.loads((ROOT / "scripts/upstream-adaptation/lock.json").read_text())
ABI = ("armeabi-v7a", "arm64-v8a")


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def blob(path):
    if not path.is_file():
        return None
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verified_checkout(path, name):
    p = LOCK["upstream"][name]
    if git(path, "rev-parse", "HEAD") != p["ref"]:
        raise RuntimeError(name + ": public commit mismatch")
    if git(path, "rev-parse", "HEAD^{tree}") != p["tree"]:
        raise RuntimeError(name + ": public tree mismatch")
    if git(path, "status", "--porcelain"):
        raise RuntimeError(name + ": expected clean source input")
    license_paths = [x for x in path.iterdir() if x.is_file() and
                     x.name.upper().startswith(("LICENSE", "COPYING"))]
    if not license_paths:
        raise RuntimeError(name + ": no tracked license file")
    print("SOURCE", name, p["repo"], p["ref"], p["tree"], p["license"],
          "license_sha256=" + ",".join(hashlib.sha256(x.read_bytes()).hexdigest()
                                      for x in sorted(license_paths)), flush=True)


def guard_fork():
    if (ROOT / "signing").exists():
        raise RuntimeError("Refusing checkout with tracked release signing")
    if git(ROOT, "rev-parse", "--is-shallow-repository") != "true":
        raise RuntimeError("Refusing non-shallow fork checkout")
    branch = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    print("SANITIZED_FORK", branch, "frozen_source", LOCK["frozen_main"], flush=True)


def overlay(old, target, dest):
    # Work on a separate actual public source tree. Never stage a mixed
    # upstream tree as the production checkout or mutate the frozen sources.
    shutil.copytree(target, dest, ignore=shutil.ignore_patterns(".git"), symlinks=True)
    merged, conflicts, manual = [], [], []
    for row in LOCK["fork_scope"]:
        p, strategy = row["path"], row["strategy"]
        a, b, c = old / p, ROOT / p, target / p
        for source, expected in ((a, row["old"]), (b, row["fork"]), (c, row["target"])):
            if blob(source) != expected:
                raise RuntimeError("Scope drift: " + p)
        output = dest / p
        if strategy == "gradle-wiring":
            continue
        if strategy == "old-media-compat-review":
            manual.append(p)
            print("REVIEW_OLD_MEDIA", p)
            continue
        if strategy == "recovery-loader-590":
            # Resolve only the reviewed TV recovery callback/queue contract on
            # the exact 5.9.0 host. Keep the frozen fork file unchanged.
            output.write_bytes(adapt_base_loader(c.read_bytes()))
            if blob(output) != row["resolved"]:
                raise RuntimeError("Reviewed recovery loader port drift: " + p)
            merged.append(p)
            print("RESOLVED_RECOVERY_LOADER", p, row["resolved"], flush=True)
            continue
        if strategy in ("module", "fork-addition"):
            if row["target"] is not None:
                if row["target"] != row["fork"]:
                    conflicts.append(p)
                    print("CONFLICT_ADDED_PATH", p)
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(b, output)
            merged.append(p)
            print("TRANSFER_FORK", p)
            continue
        if row["target"] == row["fork"]:
            print("ALREADY_UPSTREAM", p)
            continue
        if row["target"] is None or row["fork"] is None:
            conflicts.append(p)
            print("CONFLICT_REMOVED_PATH", p)
            continue
        if row["old"] == row["target"]:
            shutil.copyfile(b, output)
            merged.append(p)
            print("TRANSFER_UNCHANGED_UPSTREAM", p)
            continue
        # git merge-file on the real three source files. Do not accept conflict
        # markers, broad ours/theirs, or overwrite removed upstream classes.
        result = subprocess.run(["git", "merge-file", "-p", str(c), str(a), str(b)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            conflicts.append(p)
            print("CONFLICT_THREE_WAY", p)
            continue
        output.write_bytes(result.stdout)
        merged.append(p)
        print("MERGED_FOR_REVIEW", p)
    app = dest / "app/build.gradle"
    source = app.read_text()
    if source.count('versionCode 590') != 1 or source.count('versionName "5.9.0"') != 1:
        raise RuntimeError("Unexpected upstream app version")
    if source.count("    implementation project(':catvod')") != 1:
        raise RuntimeError("Unexpected upstream Gradle dependency anchor")
    source = source.replace('versionCode 590', 'versionCode 590001')
    source = source.replace('versionName "5.9.0"', 'versionName "v5.9.0-xray.1"')
    source = source.replace("    implementation project(':catvod')",
                            "    implementation project(':catvod')\n"
                            "    implementation project(':xray')\n"
                            "    implementation project(':tv-recovery')")
    app.write_text(source)
    settings = dest / "settings.gradle"
    with settings.open("a") as f:
        f.write("\ninclude ':libxray'\ninclude ':xray'\ninclude ':tv-recovery'\n")
    # Keep every untouched upstream runtime file byte-identical. Check source
    # independently of the upstream APK release and track all permitted deltas.
    allowed = set(merged) | {"app/build.gradle", "settings.gradle"}
    for p in git(target, "ls-files").splitlines():
        if p not in allowed and blob(target / p) != blob(dest / p):
            raise RuntimeError("Unscoped upstream change: " + p)
    for row in LOCK["fork_scope"]:
        if row["strategy"] == "module" and blob(dest / row["path"]) != row["fork"]:
            raise RuntimeError("Independent module not transferred: " + row["path"])
    print("OVERLAY_SUMMARY", "transferred_or_clean_merge", len(merged),
          "unresolved", len(conflicts), "old_media_review", len(manual),
          "untouched_upstream_verified", flush=True)
    return conflicts, manual


def media_contract(tv, media, label):
    # Source-level import existence gate, not a substitute for javac.
    # Consider enclosing source files for nested classes; ignore wildcard
    # and static imports. Print names only, not complete source or configs.
    source_types = set()
    for p in (media / "libraries").rglob("*"):
        if p.suffix not in (".java", ".kt"):
            continue
        if "main" not in p.parts or ("java" not in p.parts and "kotlin" not in p.parts):
            continue
        data = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?m)^\s*package\s+(androidx\.media3[\w.]*)", data)
        if m:
            source_types.add(m.group(1) + "." + p.stem)
    refs = {}
    for p in (tv / "app/src").rglob("*.java"):
        if not any(s in p.parts for s in ("main", "leanback")):
            continue
        data = p.read_text(encoding="utf-8", errors="replace")
        for imp in re.findall(r"(?m)^\s*import\s+(androidx\.media3[\w.]+)\s*;", data):
            refs.setdefault(imp, set()).add(str(p.relative_to(tv)))
    def exists(name):
        while name.startswith("androidx.media3."):
            if name in source_types:
                return True
            name = name.rsplit(".", 1)[0]
        return False
    missing = sorted(k for k in refs if not exists(k))
    print("MEDIA_SOURCE_CONTRACT", label, "imports", len(refs),
          "no_source_candidate", len(missing), flush=True)
    for name in missing:
        print("MISSING_MEDIA_SOURCE", label, name, "callers", ",".join(sorted(refs[name])))
    expected_archives = ("lib-mpvplayer-release.aar", "lib-decoder-ffmpeg-release.aar")
    for name in expected_archives:
        if not (tv / "app/libs" / name).is_file():
            print("MISSING_REQUIRED_AAR", name)
    for label2, name, symbol in (
        ("decoder", "androidx.media3.exoplayer.DefaultRenderersFactory", "setDecoderManager"),
        ("subtitle", "androidx.media3.ui.PlayerView", "setBackendPlayer"),
        ("mpv", "androidx.media3.mpvplayer.MpvPlayer", "getSubtitleOffsets")):
        if name not in source_types:
            continue
        path = name.replace(".", "/") + ".java"
        files = [p for p in (media / "libraries").rglob(path.rsplit("/", 1)[-1])
                 if p.as_posix().endswith(path) and "main" in p.parts]
        if files and not any(re.search(r"\b" + symbol + r"\s*\(", p.read_text(errors="replace")) for p in files):
            print("METHOD_REVIEW_REQUIRED", label, label2, name, symbol)
    return missing


def verified_shared_media(media, media_default):
    # Source equivalence only: do not substitute a standard Maven AAR for the
    # customized player or claim its cross-module binary contract is verified.
    for row in LOCK["shared_media_source"]:
        if git(media_default, "rev-parse", "HEAD") != row["official_ref"]:
            raise RuntimeError("Official Media3 source commit drift")
        for root in (media, media_default):
            if git(root, "rev-parse", "HEAD:" + row["path"]) != row["tree"]:
                raise RuntimeError("Shared Media3 module tree drift: " + row["path"])
        print("SHARED_MEDIA_SOURCE", row["coordinate"], row["tree"],
              "same official source; compiled AAR and custom common linkage pending", flush=True)


def public_inputs(tv):
    # Inventory exact tracked public AAR/SO/JAR inputs without executing any.
    for rel in git(tv, "ls-files").splitlines():
        if not rel.endswith((".aar", ".so", ".jar")):
            continue
        p = tv / rel
        print("UPSTREAM_BINARY_INPUT", rel, "bytes", p.stat().st_size,
              "sha256", hashlib.sha256(p.read_bytes()).hexdigest())
    for candidate in LOCK["public_native_candidates"]:
        print("PUBLIC_NATIVE_SOURCE_CANDIDATE", json.dumps(candidate, ensure_ascii=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("old-tv", "tv", "media", "media-default"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    guard_fork()
    for name, path in (("old_tv", args.old_tv), ("tv", args.tv),
                       ("media", args.media), ("media_default", args.media_default)):
        verified_checkout(path, name)
    verified_shared_media(args.media, args.media_default)
    public_inputs(args.tv)
    primary = media_contract(args.tv, args.media, "release-1.11.0-fongmi")
    alternate = media_contract(args.tv, args.media_default, "release")
    with tempfile.TemporaryDirectory(prefix="fongmi-upstream-source-") as tmp:
        conflicts, manual = overlay(args.old_tv, args.tv, Path(tmp) / "candidate")
    if primary and alternate:
        print("BLOCKED: neither pinned public media tree supplies the complete TV source contract", flush=True)
    if conflicts or manual or primary or alternate:
        raise SystemExit("CANDIDATE NOT BUILDABLE YET: unresolved host/media contracts; no APK produced")
    # A green source gate does not grant the right to use an arbitrary AAR.
    raise SystemExit("Source staging complete; explicit matched native dependency and full build required")


if __name__ == "__main__":
    main()
