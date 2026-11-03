#!/usr/bin/env python3
"""Git regression: public bundled JS is exempt, local source is never exempt."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/upstream/check_vendor_whitespace.py"
spec = importlib.util.spec_from_file_location("fingmi_vendor_whitespace", SCRIPT)
verify_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_module)


def git(repo, *args, allowed=False):
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if not allowed and result.returncode:
        raise AssertionError(f"git {' '.join(args)}: {result.stderr}")
    return result


def put(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


with tempfile.TemporaryDirectory(prefix="fingmi-upstream-vendor-whitespace-") as directory:
    work = Path(directory)
    upstream, local = work / "public", work / "fork"
    upstream.mkdir()
    local.mkdir()
    for repo in (upstream, local):
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")
    asset = verify_module.ASSET
    original = b"const estree = `precompiled`\n"
    with_whitespace = b"const estree = `template trailing spaces  \nnext line`;\n"
    put(upstream, asset, with_whitespace)
    git(upstream, "add", "-A")
    git(upstream, "commit", "-qm", "public target")
    target = git(upstream, "rev-parse", "HEAD").stdout.strip()
    put(local, asset, original)
    put(local, "app/src/main/java/XrayIntegration.java", b"class XrayIntegration {}\n")
    git(local, "add", "-A")
    git(local, "commit", "-qm", "previous fork")

    put(local, asset, with_whitespace)
    git_before = git(local, "diff", "--check", allowed=True)
    assert git_before.returncode != 0 and "trailing whitespace" in git_before.stdout
    put(local, ".gitattributes", (ROOT / ".gitattributes").read_bytes())
    verify_module.verify(local, upstream, target)
    assert git(local, "diff", "--check", allowed=True).returncode == 0
    git(local, "add", "-A")
    assert git(local, "diff", "--cached", "--check", allowed=True).returncode == 0

    put(local, "app/src/main/java/XrayIntegration.java", b"class XrayIntegration {}  \n")
    assert "trailing whitespace" in git(local, "diff", "--check", allowed=True).stdout
    git(local, "add", "-A")
    assert "trailing whitespace" in git(local, "diff", "--cached", "--check", allowed=True).stdout
    put(local, asset, b"modified by fork  \n")
    try:
        verify_module.verify(local, upstream, target)
    except ValueError as exc:
        assert "changed from" in str(exc)
    else:
        raise AssertionError("Modified vendor asset bypassed upstream identity check")

    put(local, asset, with_whitespace)
    put(local, ".gitattributes", (ROOT / ".gitattributes").read_bytes() + b"*.java -whitespace\n")
    try:
        verify_module.verify(local, upstream, target)
    except ValueError as exc:
        assert "exact" in str(exc) or "only" in str(exc)
    else:
        raise AssertionError("Broadened whitespace exception was accepted")

workflow = (ROOT / ".github/workflows/manual-upstream-sync.yml").read_text(encoding="utf-8")
preview = workflow.index('if [[ "$APPLY_TO_MAIN" != "true" ]]')
for marker in ('git diff --check', 'git add -A', 'git diff --cached --check',
               'scripts/upstream/check_vendor_whitespace.py'):
    assert workflow.index(marker) < preview, f"Preview must run {marker} before exit"
assert workflow.index("git diff --check") < workflow.index("git add -A")
assert workflow.index("git add -A") < workflow.index("git diff --cached --check")
assert workflow.index('git commit -m "chore(upstream)') > preview
print("PASS upstream ESTree whitespace: verified public blob, both Git diff checks, local-source failure, anti-bypass")
