#!/usr/bin/env python3
"""Regression for failed full upgrades: bundled public JS and staged diff."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/upstream/check_vendor_whitespace.py"
spec = importlib.util.spec_from_file_location("fingmi_vendor_whitespace", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def git(repo, *args, allowed=False):
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if not allowed and result.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def put(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


with tempfile.TemporaryDirectory(prefix="fingmi-vendor-whitespace-") as directory:
    work = Path(directory)
    upstream, local = work / "upstream", work / "candidate"
    upstream.mkdir()
    local.mkdir()
    for repo in (upstream, local):
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")

    old = b"const source = 'baseline';\n"
    upstream_js = {
        module.ASSETS[0]: b"const editor = `spider \t\n next`;\n",
        module.ASSETS[1]: b"const chunk = `word  \n trailing`;\n",
        module.ASSETS[2]: b"const dist = `word \t\n trailing`;\n",
        module.ASSETS[3]: b"const estree = `word  \n trailing`;\n",
    }
    for name, contents in upstream_js.items():
        put(upstream, name, contents)
        put(local, name, old)
    java = "app/src/main/java/XrayIntegration.java"
    put(local, java, b"class XrayIntegration {}\n")
    git(upstream, "add", "-A")
    git(upstream, "commit", "-qm", "official resources")
    target = git(upstream, "rev-parse", "HEAD").stdout.strip()
    git(local, "add", "-A")
    git(local, "commit", "-qm", "previous fork")

    for name, contents in upstream_js.items():
        put(local, name, contents)
    # Without exceptions the staged Git diff matches the real failed Actions.
    git(local, "add", "-A")
    report = git(local, "diff", "--cached", "--check", allowed=True)
    assert report.returncode != 0
    for name in module.ASSETS:
        assert name in report.stdout, "Expected public asset wasn't caught: " + name

    put(local, ".gitattributes", (ROOT / ".gitattributes").read_bytes())
    module.verify(local, upstream, target)
    assert git(local, "diff", "--check", allowed=True).returncode == 0
    git(local, "add", "-A")
    assert git(local, "diff", "--cached", "--check", allowed=True).returncode == 0

    # The exact-path exceptions must not disable checks on our own Java code.
    put(local, java, b"class XrayIntegration {}  \n")
    assert "trailing whitespace" in git(local, "diff", "--check", allowed=True).stdout
    git(local, "add", "-A")
    assert "trailing whitespace" in git(local, "diff", "--cached", "--check", allowed=True).stdout
    put(local, java, b"class XrayIntegration {}\n")

    # Never allow modified vendor JavaScript to hide behind a bundled path.
    for name in module.ASSETS:
        put(local, name, b"modified by fork  \n")
        try:
            module.verify(local, upstream, target)
        except ValueError as exc:
            assert "modified or drifted" in str(exc)
        else:
            raise AssertionError("Modified public blob was accepted: " + name)
        put(local, name, upstream_js[name])

    # Fail closed if the public upstream itself no longer carries an asset.
    removed = module.ASSETS[0]
    (upstream / removed).unlink()
    git(upstream, "add", "-A")
    git(upstream, "commit", "-qm", "vendor bundle moved")
    changed_target = git(upstream, "rev-parse", "HEAD").stdout.strip()
    try:
        module.verify(local, upstream, changed_target)
    except ValueError as exc:
        assert "absent" in str(exc)
    else:
        raise AssertionError("Unreviewed public source structure was accepted")

    # Do not permit globbing, wildcard paths, or other source exceptions.
    for attack in (b"*.java -whitespace\n", b"app/src/main/assets/js/** -whitespace\n"):
        put(local, ".gitattributes", (ROOT / ".gitattributes").read_bytes() + attack)
        try:
            module.verify(local, upstream, target)
        except ValueError as exc:
            assert "exactly" in str(exc)
        else:
            raise AssertionError("Broader whitespace exception was accepted")
    put(local, ".gitattributes", (ROOT / ".gitattributes").read_bytes())

    # Unlisted files are not exempt even if they are also JS assets.
    put(local, "app/src/main/assets/js/extra-bundle.js", b"const extra = `data  \n`;\n")
    git(local, "add", "-A")
    assert "extra-bundle.js" in git(local, "diff", "--cached", "--check", allowed=True).stdout

workflow = (ROOT / ".github/workflows/manual-upstream-sync.yml").read_text(encoding="utf-8")
preview = workflow.index('if [[ "$BUILD_CANDIDATE" != "true" ]]')
for marker in ('git diff --check', 'git add -A', 'git diff --cached --check',
               'scripts/upstream/check_vendor_whitespace.py'):
    assert workflow.index(marker) < preview, f"Preview must run {marker} before exit"
assert workflow.index("git diff --check") < workflow.index("git add -A")
assert workflow.index("git add -A") < workflow.index("git diff --cached --check")
assert workflow.index('git commit -m "chore(upstream)') > preview
print("PASS four public JS blobs, real staged diff, Java whitespace, asset drift and scope rejection")
