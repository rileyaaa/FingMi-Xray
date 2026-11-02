#!/usr/bin/env python3
"""Fail-closed, file-level three-way sync of public FongMi/TV into FingMi-Xray.

The upstream Git repository must already be fetched. This script never fetches,
commits, pushes, publishes or triggers CI. It only updates the working tree and
writes a concise JSON report. A caller must review validation before pushing.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

OWNED_PREFIXES = (
    "app/", "catvod/", "chaquo/", "quickjs/", "nodejs/", "thunder/",
    "forcetech/", "jianpian/", "tvbus/", "zlive/", "website/",
    "hook/", "runtime/", "buildSrc/", "gradle/",
)
OWNED_FILES = {
    ".gitignore", "build.gradle", "settings.gradle", "gradle.properties",
    "scripts/runtime_catalog.py", "scripts/sync_python_runtime.py",
}
# Upstream files regenerated from the selected public commit by prepare_release.py.
# Never three-way-merge their old fork versions into the new upstream.
REGENERATED_FILES = {
    "app/build.gradle", "settings.gradle",
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/HomeActivity.java",
    "catvod/src/main/java/com/github/catvod/net/OkProxySelector.java",
    # App/HTTP hooks exclusively for TV standby network generation.
    "app/src/main/java/com/fongmi/android/tv/model/SiteViewModel.java",
    "app/src/main/java/com/fongmi/android/tv/api/loader/BaseLoader.java",
    "catvod/src/main/java/com/github/catvod/net/OkHttp.java",
    "catvod/src/main/java/com/github/catvod/net/OkDns.java",
    "app/src/main/java/com/fongmi/android/tv/utils/ImgUtil.java",
    "app/src/main/java/com/fongmi/android/tv/utils/OkGlideModule.java",
    "app/src/main/java/com/fongmi/android/tv/Updater.java",
    "app/src/main/java/com/fongmi/android/tv/server/process/Action.java",
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java",
    "app/src/leanback/res/layout/activity_setting.xml",
    # Public 5.8.7 Exo media/decoder/ISO implementation with Xray-only hooks.
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java",
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerSession.java",
    "app/src/main/java/com/fongmi/android/tv/player/exo/ExoPlayerEngine.java",
    "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java",
}
PRESERVED_FILES = {
    "app/proguard-rules-media.pro",
    "catvod/src/test/java/com/github/catvod/net/OkProxySelectorTest.java",
}
PRESERVED_PREFIXES = (
    "app/src/main/java/com/fingmi/", "app/src/leanback/java/com/fingmi/",
    "app/src/mobile/java/com/fingmi/",
)
BASELINE = "scripts/upstream/baseline.json"
SCOPE_MANIFEST = "scripts/upstream/fork_scope.json"
SCOPE_STRATEGIES = {"generate", "upstream", "rebase", "project"}


def run(*args, cwd=None, input_bytes=None, check=True):
    result = subprocess.run(args, cwd=cwd, input=input_bytes,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(args)}: {result.stderr.decode(errors='replace')[:400]}")
    return result


def git_tree(repo, rev):
    entries = {}
    data = run("git", "ls-tree", "-r", "-z", rev, cwd=repo).stdout
    for record in data.split(b"\0"):
        if not record:
            continue
        meta, path_bytes = record.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split()
        if kind != "blob":
            continue
        path = path_bytes.decode("utf-8")
        entries[path] = (mode, oid)
    return entries


def tracked(path):
    return ((path in OWNED_FILES or path.startswith(OWNED_PREFIXES))
            and path not in PRESERVED_FILES
            and path not in REGENERATED_FILES
            and not path.startswith(PRESERVED_PREFIXES))


def blob(repo, entry):
    return run("git", "cat-file", "blob", entry[1], cwd=repo).stdout


def safe_path(root, name):
    parts = PurePosixPath(name).parts
    if not parts or any(p in (".", "..", ".git") for p in parts):
        raise ValueError(f"unsafe path: {name}")
    path = root.joinpath(*parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path escapes worktree: {name}")
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
        raise ValueError(f"symlink path not permitted: {name}")
    return path


def three_way(ours, base, theirs):
    if any(b"\0" in data for data in (ours, base, theirs)):
        return None
    with tempfile.TemporaryDirectory(prefix="fingmi-merge-") as directory:
        files = [Path(directory) / n for n in ("ours", "base", "theirs")]
        for path, content in zip(files, (ours, base, theirs)):
            path.write_bytes(content)
        result = run("git", "merge-file", "-p", "--diff3", *(str(p) for p in files), check=False)
        return result.stdout if result.returncode == 0 else None



def file_blob_sha(data):
    """Git SHA-1 blob identity for a tracked source snapshot."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def load_scope(root, baseline):
    """Only previously reviewed fork drift is eligible for an automatic merge."""
    path = root / SCOPE_MANIFEST
    scope = json.loads(path.read_text(encoding="utf-8"))
    if scope.get("schema") != 1 or scope.get("baseline_commit") != baseline:
        raise ValueError("Fork scope inventory is stale relative to pinned public baseline")
    files = scope.get("files")
    if not isinstance(files, dict):
        raise ValueError("Fork scope inventory lacks a path map")
    for name, data in files.items():
        if not isinstance(data, dict) or data.get("strategy") not in SCOPE_STRATEGIES:
            raise ValueError("Unreviewed fork scope strategy: " + name)
        if not data.get("scope") or not name.strip():
            raise ValueError("Unclassified original source deviation: " + name)
        safe_path(root, name)
        if data["strategy"] == "upstream" and not tracked(name):
            raise ValueError("Upstream-first file is outside source sync paths: " + name)
    return scope


def inspect_existing_drift(root, original, policies):
    """Cover original files even if upstream did not touch them this release."""
    missing = []
    for name, (mode, oid) in original.items():
        if mode not in ("100644", "100755"):
            continue
        path = safe_path(root, name)
        ours = path.read_bytes() if path.exists() else None
        if ours is not None and file_blob_sha(ours) == oid:
            continue
        if name not in policies:
            missing.append(name)
    return missing


def upstream_version(upstream, target):
    tree = git_tree(upstream, target)
    item = tree.get("app/build.gradle")
    if item is None:
        raise ValueError("upstream app/build.gradle missing")
    gradle = blob(upstream, item).decode("utf-8")
    name = re.search(r'(?m)^\s*versionName\s+["\x27](\d+\.\d+\.\d+)["\x27]', gradle)
    code = re.search(r'(?m)^\s*versionCode\s+(\d+)', gradle)
    if not name or not code:
        raise ValueError("upstream versionName/versionCode unrecognized")
    return name.group(1), int(code.group(1))


def sync(root, upstream, target, report):
    lock_path = root / BASELINE
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    base = lock["commit"]
    for sha in (base, target):
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError(f"invalid upstream SHA: {sha}")
    base_tree = git_tree(upstream, base)
    target_tree = git_tree(upstream, target)
    version, code = upstream_version(upstream, target)
    scope = load_scope(root, base)
    policies = scope["files"]
    unaudited = inspect_existing_drift(root, base_tree, policies)
    changed = []
    unchanged = 0
    plans = {}
    conflicts = []
    ignored = []

    for name in sorted(set(base_tree) | set(target_tree)):
        old, new = base_tree.get(name), target_tree.get(name)
        policy = policies.get(name, {}).get("strategy")
        if policy in ("generate", "project"):
            if old != new:
                ignored.append(name)
            continue
        if old == new and policy != "upstream":
            continue
        if not tracked(name):
            if old != new:
                ignored.append(name)
            continue
        changed.append(name)
        path = safe_path(root, name)
        old_bytes = blob(upstream, old) if old else None
        new_bytes = blob(upstream, new) if new else None
        ours = path.read_bytes() if path.exists() else None
        if (old and old[0] not in ("100644", "100755")) or (new and new[0] not in ("100644", "100755")):
            conflicts.append(name + " [unsupported file mode]")
            continue
        if ours == new_bytes:
            unchanged += 1
            continue
        if policy == "upstream":
            # An explicitly audited obsolete patch must NOT leak across the
            # new upstream baseline, even when the upstream blob is unchanged.
            plans[name] = (new_bytes, new[0] if new else None)
            continue
        if ours == old_bytes:
            plans[name] = (new_bytes, new[0] if new else None)
            continue
        if old_bytes is None or new_bytes is None or ours is None:
            conflicts.append(name + " [added/deleted vs fork modification]")
            continue
        merged = three_way(ours, old_bytes, new_bytes)
        if merged is None:
            conflicts.append(name + " [three-way conflict]")
        else:
            plans[name] = (merged, new[0])

    result = {
        "upstream_repository": lock["repository"], "from": base, "to": target,
        "upstream_version": version, "upstream_version_code": code,
        "upstream_changed_paths": len(changed) + len(ignored),
        "sync_eligible_paths": len(changed), "protected_or_excluded_paths": ignored,
        "already_equal": unchanged, "planned_paths": sorted(plans),
        "scope_inventory_paths": len(policies),
        "upstream_first_paths": sorted(p for p in plans if policies.get(p, {}).get("strategy") == "upstream"),
        "unreviewed_fork_drift": unaudited,
        "conflicts": conflicts + [p + " [unreviewed fork edit]" for p in unaudited],
        "status": "blocked" if conflicts or unaudited else "prepared",
        "note": "Source sync only; not a build, APK, release, or on-device verification",
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blocked = conflicts + [p + " [unreviewed fork edit]" for p in unaudited]
    if blocked:
        print(f"BLOCKED: {len(blocked)} source paths need review; no files changed. Report: {report}")
        for name in blocked[:80]:
            print(" - " + name)
        return 2

    for name, (content, mode) in plans.items():
        path = safe_path(root, name)
        if content is None:
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o755 if mode == "100755" else 0o644)

    lock["commit"] = target
    lock["version"] = version
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    scope["baseline_commit"] = target
    (root / SCOPE_MANIFEST).write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PREPARED: FongMi/TV {version}, {len(plans)} file changes; report: {report}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(sync(args.root.resolve(), args.upstream.resolve(), args.target, args.report.resolve()))


if __name__ == "__main__":
    main()
