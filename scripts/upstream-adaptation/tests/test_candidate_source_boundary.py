#!/usr/bin/env python3
"""Exercise both real source-stage entrypoints with fixed, complete Git inputs."""
import argparse
from collections import Counter
import contextlib
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
assert __debug__, "Do not disable assertions"
BASE = "f8e1fcc7d89069e4f629f82d47767f9ee0ff0cfe"
BASE_TREE = "edb97fb227a0f45febf783cd7464d4b549cc53f3"
SCRIPT = "scripts/upstream-adaptation/prepare_candidate.py"
ORIGINAL = "2b234019c352e7ce5ed0f2eda42b76fafbd1e50a"
FIXED = "3d5b90296ef1fe40aa2e93f7418a4553cc8610a0"
LOCK = "d33ade8301812e7964edf16b07fe9437ff83e791"
PINS = {
    "old_tv": ("c616c0aa3613e87529791587a9f71b78c278c991", "8aa6eebcf6bdf320841ef1158f0434faabc7a61f"),
    "tv": ("d3a0b84b24cf6628d72a4dbc2be453875b005536", "82953e314d3009f039bb220db05ca537e0eadc92"),
    "media": ("3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d", "b7a4d78a2168bd5065034d37a242b7e51785ea4e"),
    "media_default": ("2bc207851df311340767e913931ca7b28cab1794", "246fb170134edf5a7b5f8a2ca6f4f8bc81903383"),
}
REQUIRED = ("lib-mpvplayer-release.aar", "lib-decoder-ffmpeg-release.aar")
TRACKED_AARS = {
    "app/libs/hook-release.aar": "179856a41a3e03ce569f00a66b8a82ca1071830c",
    "app/libs/tvbus-release.aar": "2fda22082087a1702436717c72efe05b65efe5ca",
}
BLOCKED = "CANDIDATE NOT BUILDABLE YET: unresolved host/media contracts; no APK produced"


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def rev(root, *args):
    return git(root, *args).decode().strip()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify(root, head, tree):
    assert rev(root, "rev-parse", "HEAD") == head, root
    assert rev(root, "rev-parse", "HEAD^{tree}") == tree, root
    assert not git(root, "status", "--porcelain", "--untracked-files=all"), root


def load(dev, raw):
    path = dev / SCRIPT
    ns = {"__file__": str(path), "__name__": "candidate_audit"}
    sys.path.insert(0, str(path.parent))
    try:
        exec(compile(raw, str(path), "exec"), ns)
    finally:
        sys.path.pop(0)
    return ns


def manifest(root):
    result = {}
    for path in root.rglob("*"):
        assert not path.is_symlink(), path
        if path.is_dir():
            continue
        assert path.is_file(), path
        rel = path.relative_to(root).as_posix()
        assert ".git" not in Path(rel).parts, rel
        data = path.read_bytes()
        result[rel] = (stat.S_IMODE(path.stat().st_mode), len(data), sha(data))
    return result


def canonical_digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True).encode("ascii"))


def same_files(actual, expected):
    assert actual.keys() == expected.keys(), (sorted(actual.keys() - expected.keys()),
                                               sorted(expected.keys() - actual.keys()))
    changed = sorted(k for k in expected if actual[k] != expected[k])
    assert not changed, changed


def run(label, ns, old, tv, media, media_default):
    # Observe the real overlay result before main's TemporaryDirectory is
    # removed. No replacement of source checks, merge logic or return values.
    overlay = ns["overlay"]
    captured = []

    def observe(a, b, dest):
        result = overlay(a, b, dest)
        captured.append((result, manifest(dest)))
        return result

    argv = sys.argv
    out = io.StringIO()
    ns["overlay"] = observe
    sys.argv = [SCRIPT, "--old-tv", str(old), "--tv", str(tv),
                "--media", str(media), "--media-default", str(media_default)]
    try:
        with contextlib.redirect_stdout(out):
            try:
                ns["main"]()
            except SystemExit as exc:
                assert exc.code == BLOCKED, (label, exc.code)
            else:
                raise AssertionError("Expected original blocking exit: " + label)
    except BaseException:
        print(out.getvalue(), end="")
        raise
    finally:
        sys.argv = argv
        ns["overlay"] = overlay
    assert len(captured) == 1, label
    (conflicts, manual), files = captured[0]
    lines = sorted(out.getvalue().splitlines())
    print("RESULT", label, "files", len(files), "manifest_sha256", canonical_digest(files),
          "log_sha256", canonical_digest(lines), "conflicts", len(conflicts), "manual", len(manual), flush=True)
    print("CONFLICTS", label, json.dumps(conflicts, ensure_ascii=True))
    print("MANUAL", label, json.dumps(manual, ensure_ascii=True))
    for line in lines:
        if line.startswith(("SOURCE ", "SHARED_MEDIA_SOURCE ", "MEDIA_SOURCE_CONTRACT ",
                            "METHOD_REVIEW_REQUIRED ", "MISSING_REQUIRED_AAR ", "OVERLAY_SUMMARY ")):
            print(label, line)
    print("EXPECTED_BLOCKED_EXIT", label, BLOCKED, flush=True)
    return (conflicts, manual), files, Counter(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("dev", "old-tv", "tv", "media", "media-default", "candidate"):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    dev, old, tv, media, default, candidate = (getattr(a, n).resolve() for n in
        ("dev", "old_tv", "tv", "media", "media_default", "candidate"))
    verify(dev, BASE, BASE_TREE)
    assert rev(dev, "rev-parse", "--is-shallow-repository") == "true"
    assert not (dev / "signing").exists()
    for key, root in zip(PINS, (old, tv, media, default)):
        verify(root, *PINS[key])
        print("PIN", key, *PINS[key])
    original = git(dev, "show", BASE + ":" + SCRIPT)
    fixed = candidate.read_bytes()
    assert blob(original) == ORIGINAL and blob(fixed) == FIXED
    print("SCRIPT_BLOBS", blob(original), blob(fixed), "fixed_sha256", sha(fixed))
    for name in ("lock.json", "recovery_loader.py", "reviewed_recovery_host.py",
                 "reviewed_recovery_host.json", "reviewed_live_host.json", "reviewed_media_host.json"):
        rel = "scripts/upstream-adaptation/" + name
        data = git(dev, "show", BASE + ":" + rel)
        assert (dev / rel).read_bytes() == data, rel
        if name == "lock.json":
            assert blob(data) == LOCK
    orig, new = load(dev, original), load(dev, fixed)
    assert orig["LOCK"] == new["LOCK"]
    assert len(new["LOCK"]["fork_scope"]) == 110
    manual = [r["path"] for r in new["LOCK"]["fork_scope"] if r["strategy"] == "old-media-compat-review"]
    assert len(manual) == 5
    for key, (head, tree) in PINS.items():
        assert (new["LOCK"]["upstream"][key]["ref"], new["LOCK"]["upstream"][key]["tree"]) == (head, tree)
    stale = git(old, "show", PINS["old_tv"][0] + ":app/libs/tvbus-release.aar")
    assert blob(stale) == "e58c69089ca7f649ad208810549c0bacafe7cad1"
    sentinels = {"app/libs/lib-stale.aar": stale}
    sentinels.update({"app/libs/" + name: b"test-only missing dependency marker\n" for name in REQUIRED})
    missing = Counter({"MISSING_REQUIRED_AAR " + name: 2 for name in REQUIRED})
    with tempfile.TemporaryDirectory(prefix="fingmi-source-boundary-") as work:
        target = Path(work) / "target"
        target.mkdir()
        git(target, "init", "-q")
        git(target, "-c", "protocol.file.allow=always", "fetch", "--depth=1", "--no-tags",
            tv.as_uri(), PINS["tv"][0])
        git(target, "checkout", "--detach", "FETCH_HEAD")
        verify(target, *PINS["tv"])
        assert not git(target, "status", "--porcelain", "--ignored", "--untracked-files=all")
        base = run("original-clean", orig, old, target, media, default)
        clean = run("fixed-clean", new, old, target, media, default)
        same_files(clean[1], base[1])
        assert clean[0] == base[0] and clean[2] == base[2]
        assert clean[0][1] == manual
        assert all(base[2][line] == count for line, count in missing.items())
        assert {p for p in clean[1] if p.startswith("app/libs/") and p.endswith(".aar")} == set(TRACKED_AARS)
        for rel, oid in TRACKED_AARS.items():
            data = git(target, "show", "HEAD:" + rel)
            assert blob(data) == oid
            assert clean[1][rel] == (0o644, len(data), sha(data))
            print("TRACKED_AAR", rel, oid, len(data), sha(data))
        print("PASS_CLEAN_EQUIVALENCE", len(clean[1]), flush=True)
        for rel, data in sentinels.items():
            with (target / rel).open("xb") as f:
                f.write(data)
            assert rev(target, "check-ignore", "--", rel) == rel
            print("IGNORED_INPUT", rel, len(data), sha(data))
        verify(target, *PINS["tv"])
        dirty_orig = run("original-ignored", orig, old, target, media, default)
        dirty = run("fixed-ignored", new, old, target, media, default)
        expected = dict(base[1])
        for rel, data in sentinels.items():
            assert rel not in expected
            expected[rel] = (stat.S_IMODE((target / rel).stat().st_mode), len(data), sha(data))
            assert (target / rel).read_bytes() == data
        same_files(dirty_orig[1], expected)
        assert dirty_orig[0] == base[0] and dirty_orig[2] == base[2] - missing
        print("PASS_ORIGINAL_NEGATIVE_CONTROL", sorted(sentinels), flush=True)
        same_files(dirty[1], clean[1])
        assert dirty[0] == clean[0] and dirty[2] == clean[2]
        print("PASS_FIXED_IGNORED_EQUAL", len(dirty[1]), canonical_digest(dirty[1]), flush=True)
        verify(target, *PINS["tv"])
        for rel, data in sentinels.items():
            assert (target / rel).read_bytes() == data
            assert rev(target, "check-ignore", "--", rel) == rel
        print("PASS_IGNORED_INPUT_UNCHANGED", len(sentinels))
    verify(dev, BASE, BASE_TREE)
    for key, root in zip(PINS, (old, tv, media, default)):
        verify(root, *PINS[key])
    print("PASS_EXACT_FIXED_SOURCE_BOUNDARY", "scope", 110, "old_media_review", 5,
          "conflicts", len(base[0][0]), "candidate_files", len(clean[1]), flush=True)


if __name__ == "__main__":
    main()
