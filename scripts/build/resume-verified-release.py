#!/usr/bin/env python3
"""Resume only an uploaded APK draft from a fully verified failed publish run.

The APK/source identity remains that of the original build, even when this
recovery workflow runs newer publication tooling. No compilation is performed.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ".github/workflows/02-正式APK构建与发布.yml"
LEGACY_WORKFLOW = ".github/workflows/publish-current-main-test-release.yml"
REPORT_NAME = "fingmi-xray-build-failure-reports"
PUBLISH_STEP = "Publish verified APKs"
REQUIRED_STEPS = (
    "Run fork source guards",
    "Prepare Android SDK 36 and 37",
    "Verify upstream Gradle daemon toolchain",
    "Verify persistent private-project release signing",
    "Rebuild and verify pinned player/native inputs",
    "Prepare public player and Xray native dependencies",
    "Verify current Xray chain against published v7 and arm64 native",
    "Build and import reconstructed Libass candidate",
    "Verify imported player startup",
    "Verify Xray artwork lifecycle",
    "Verify proxy policy host regression",
    "Compile current 5.6.3 Leanback source",
    "Assemble Android TV release APKs",
    "Verify MPEG-H survives final TV APK packaging",
    "Verify pinned native runtime survives final TV APK packaging",
    "Verify final Media3 DEX linkage",
    "Verify final Leanback manifest security contract",
    "Record build inputs and outputs",
    "Stage Android TV release APKs",
)

CURRENT_PUBLISH_STEP = "发布已验证的 APK"
CURRENT_REQUIRED_STEPS = (
    "按当前源码确定发布版本",
    "运行项目源码检查",
    "准备 Android SDK 36 与 37",
    "检查上游 Gradle 工具链",
    "检查项目固定签名配置",
    "重建并校验固定播放器及原生依赖",
    "准备公开播放器与 Xray 原生依赖",
    "对照已发布 v7 与 arm64 原生库验证 Xray",
    "Libass 前清理已验证的 Xray 临时文件",
    "重建并导入 Libass 兼容组件",
    "验证播放器组件启动",
    "验证 Xray 图片加载生命周期",
    "验证代理主机名崩溃回归",
    "编译当前 Leanback 源码",
    "打包 Android TV Release APK",
    "校验最终 APK 中的 MPEG-H",
    "校验最终 APK 中的原生运行库",
    "验证最终 Media3 DEX 依赖",
    "验证最终 Leanback Manifest 安全约束",
    "记录构建输入与输出",
    "暂存已验证的双 ABI APK",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive_id(value):
    return type(value) is int and value > 0


class GitHub:
    def __init__(self, repository):
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "Invalid repository")
        self.repository = repository

    def api(self, path):
        return json.loads(subprocess.check_output([
            "gh", "api", "repos/" + self.repository + "/" + path,
            "--method", "GET",
        ]))

    def pages(self, path, key):
        rows = []
        for page in range(1, 101):
            result = self.api(f"{path}?per_page=100&page={page}")[key]
            rows.extend(result)
            if len(result) < 100:
                return rows
        raise ValueError("Unexpected pagination limit: " + path)

    def download(self, path, target):
        # Always address the snapshotted asset ID, never a moving tag/URL.
        argv = ["gh", "api", "repos/" + self.repository + "/" + path,
                "--method", "GET"]
        if re.fullmatch(r"releases/assets/\d+", path):
            argv += ["-H", "Accept: application/octet-stream"]
        else:
            # Artifact ZIP is an API redirect endpoint: it requires JSON Accept,
            # unlike the release asset endpoint that negotiates binary content.
            require(re.fullmatch(r"actions/artifacts/\d+/zip", path), "Unexpected binary API endpoint")
        with target.open("wb") as output:
            subprocess.run(argv, stdout=output, check=True)


def verify_run(repository, run_id, run, workflow, jobs):
    require(run.get("id") == run_id and run.get("status") == "completed"
            and run.get("conclusion") == "failure"
            and run.get("event") == "workflow_dispatch"
            and run.get("head_branch") == "main", "Run is not a completed authorized main publication failure")
    repo, head = run.get("repository", {}), run.get("head_repository", {})
    require(repo.get("full_name") == repository and head.get("full_name") == repository
            and positive_id(repo.get("id")) and head.get("id") == repo["id"], "Run repository identity mismatch")
    require(workflow.get("path") in (WORKFLOW, LEGACY_WORKFLOW) and positive_id(workflow.get("id"))
            and run.get("workflow_id") == workflow["id"], "Run did not use the full publication workflow")
    require(re.fullmatch(r"[0-9a-f]{40}", run.get("head_sha", ""))
            and positive_id(run.get("run_attempt")), "Invalid original build identity")
    require(len(jobs) == 1, "Expected exactly one original build job")
    job = jobs[0]
    require(job.get("run_id") == run_id and job.get("head_sha") == run["head_sha"]
            and job.get("run_attempt") == run["run_attempt"] and job.get("name") == "build"
            and job.get("status") == "completed" and job.get("conclusion") == "failure",
            "Original build job identity mismatch")
    steps = job.get("steps", [])
    by_name = {}
    for step in steps:
        by_name.setdefault(step.get("name"), []).append(step)
    # Old GitHub workflow runs keep their original step labels after workflow
    # file renames; newer runs use the current localized labels.
    current = CURRENT_PUBLISH_STEP in by_name
    legacy = PUBLISH_STEP in by_name
    require(current != legacy, "Unknown or ambiguous original publication step")
    required_steps, publish_step = (
        (CURRENT_REQUIRED_STEPS, CURRENT_PUBLISH_STEP) if current
        else (REQUIRED_STEPS, PUBLISH_STEP)
    )
    required = [(name, "success") for name in required_steps] + [(publish_step, "failure")]
    for name, conclusion in required:
        matches = by_name.get(name, [])
        require(len(matches) == 1 and matches[0].get("status") == "completed"
                and matches[0].get("conclusion") == conclusion, "Original verification gate missing or failed: " + name)
    publish_number = by_name[publish_step][0]["number"]
    require(all(by_name[name][0]["number"] < publish_number for name in required_steps),
            "Verification occurred after the failed publication")
    require([step.get("name") for step in steps if step.get("conclusion") == "failure"] == [publish_step],
            "Original run failed outside publication")


def select_artifact(run, artifacts):
    matches = [a for a in artifacts if a.get("name") == REPORT_NAME]
    require(len(matches) == 1, "Expected one unambiguous original failure report artifact")
    artifact = matches[0]
    owner = artifact.get("workflow_run", {})
    require(positive_id(artifact.get("id")) and artifact.get("expired") is False
            and 0 < artifact.get("size_in_bytes", 0) <= 16 * 1024 * 1024
            and owner.get("id") == run["id"] and owner.get("head_sha") == run["head_sha"]
            and owner.get("repository_id") == run["repository"]["id"]
            and owner.get("head_repository_id") == run["repository"]["id"], "Failure report ownership/availability mismatch")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", artifact.get("digest") or ""), "Failure report lacks a verifiable digest")
    return artifact


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return "sha256:" + result.hexdigest()


def read_report(path, artifact):
    require(path.stat().st_size == artifact["size_in_bytes"] and digest(path) == artifact["digest"],
            "Downloaded failure report does not match its API digest/size")
    # Read only the single known JSON member; never extract arbitrary paths.
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if m.filename == "release/publication-result.json"]
        require(len(members) == 1 and members[0].file_size <= 1024 * 1024,
                "Missing, duplicate or oversized publication result")
        return json.loads(archive.read(members[0]))


def verify_report(run, report, tag):
    require(re.fullmatch(r"v\d+\.\d+\.\d+-xray\.\d+", tag), "Invalid formal release tag")
    require(report.get("source") == run["head_sha"] and report.get("release_tag") == tag
            and report.get("phase") in ("failed:uploading", "failed:staging_verified"),
            "Report is not a permitted pre-cutover failure for this source")
    stage_tag = f"stage-{tag}-{run['id']}-{run['run_attempt']}"
    staged = report.get("staged", {})
    stage_keys = {stage_tag}
    require(set(staged) == stage_keys and positive_id(staged.get(stage_tag)),
            "Unexpected staged release identity")
    expected = {f"FongMi-Xray-TV-{tag}-{abi}.apk" for abi in ("armeabi-v7a", "arm64-v8a")}
    assets = report.get("assets", [])
    require(len(assets) == 2 and {a.get("name") for a in assets} == expected, "Report must contain both exact APK names")
    for asset in assets:
        require(re.fullmatch(r"sha256:[0-9a-f]{64}", asset.get("digest", ""))
                and positive_id(asset.get("size")), "Invalid APK report digest/size")
    return stage_tag, staged[stage_tag]


def verify_stage(release, report, stage_tag, stage_id):
    require(release.get("id") == stage_id and release.get("tag_name") == stage_tag
            and release.get("draft") is True and release.get("prerelease") is False,
            "Uploaded APK stage is not the original unpublished draft")
    assets = release.get("assets", [])
    expected = {a["name"]: a for a in report["assets"]}
    require(len(assets) == 2 and {a.get("name") for a in assets} == set(expected), "Stage APK names mismatch")
    for asset in assets:
        match = expected[asset["name"]]
        require(positive_id(asset.get("id")) and asset.get("state") == "uploaded"
                and asset.get("digest") == match["digest"] and asset.get("size") == match["size"],
                "Stage APK digest/size/state mismatch: " + asset["name"])
    require(len({a["id"] for a in assets}) == 2, "Duplicate stage asset IDs")
    return assets


def verify_apk(path, asset, source):
    require(path.stat().st_size == asset["size"] and digest(path) == asset["digest"], "Downloaded APK bytes mismatch: " + path.name)
    with zipfile.ZipFile(path) as apk:
        name = "META-INF/version-control-info.textproto"
        require(apk.namelist().count(name) == 1, "APK has missing/ambiguous build revision")
        revisions = re.findall(r'revision:\s*"([^"]+)"', apk.read(name).decode())
        require(revisions == [source], "APK embedded source does not match verified run")


def source_identity(source):
    # Current verification scripts use the checkout's fixed key/version. Verify
    # those identities still match the original build before applying them.
    def version(text):
        return (re.search(r'versionName\s+"([^"]+)"', text).group(1),
                re.search(r"versionCode\s+(\d+)", text).group(1))
    original = subprocess.check_output(["git", "show", source + ":app/build.gradle"], text=True)
    require(version(original) == version((ROOT / "app/build.gradle").read_text()), "Original/current app versions differ")
    certificate = subprocess.check_output(["git", "show", source + ":signing/release-certificate.sha256"])
    require(certificate == (ROOT / "signing/release-certificate.sha256").read_bytes(), "Original/current signing pins differ")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verified-run-id", required=True, type=int)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--tag", default="v5.6.3-xray.1")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--prune-superseded", action="store_true")
    parser.add_argument("--rollback-tag", default="")
    parser.add_argument("--directory", type=Path, default=Path("release"))
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true", help="Perform every recovery verification without publishing")
    args = parser.parse_args()
    require(positive_id(args.verified_run_id), "Invalid original run ID")
    require(not args.directory.exists() or not any(args.directory.iterdir()), "Recovery directory must be empty; local APK reuse is forbidden")
    gh = GitHub(args.repository)
    run = gh.api(f"actions/runs/{args.verified_run_id}")
    workflow_id = run.get("workflow_id")
    require(positive_id(workflow_id), "Invalid original workflow ID")
    workflow = gh.api(f"actions/workflows/{workflow_id}")
    attempt = run.get("run_attempt")
    require(positive_id(attempt), "Invalid original run attempt")
    jobs = gh.pages(f"actions/runs/{args.verified_run_id}/attempts/{attempt}/jobs", "jobs")
    verify_run(args.repository, args.verified_run_id, run, workflow, jobs)
    artifact = select_artifact(run, gh.pages(f"actions/runs/{args.verified_run_id}/artifacts", "artifacts"))
    args.directory.mkdir(parents=True, exist_ok=True)
    archive = args.directory / "original-failure-reports.zip"
    gh.download(f"actions/artifacts/{artifact['id']}/zip", archive)
    report = read_report(archive, artifact)
    stage_tag, stage_id = verify_report(run, report, args.tag)
    assets = verify_stage(gh.api(f"releases/{stage_id}"), report, stage_tag, stage_id)
    source = run["head_sha"]
    ref = gh.api("git/ref/tags/" + stage_tag)
    require(ref.get("ref") == "refs/tags/" + stage_tag
            and ref.get("object", {}).get("type") == "commit"
            and ref["object"].get("sha") == source, "Original stage tag no longer identifies the verified source")
    subprocess.run(["git", "fetch", "--no-tags", "origin", source], check=True)
    source_identity(source)
    for asset in assets:
        apk = args.directory / asset["name"]
        gh.download(f"releases/assets/{asset['id']}", apk)
        verify_apk(apk, asset, source)
        subprocess.run([sys.executable, str(ROOT / "scripts/build/check-final-apk-media3.py"),
                        "--apk", str(apk)], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/build/check-release-signing.py"),
                        "--sdk", str(args.sdk), "--apk", str(apk), "--source-sha", source], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/build/check-final-apk-manifest.py"),
                        "--apkanalyzer", str(args.sdk / "cmdline-tools/latest/bin/apkanalyzer"),
                        "--apk", str(apk)], check=True)
    evidence = {"original_build_run": run["id"], "original_build_attempt": attempt,
                "source": source, "publication_tooling_source": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "resuming_workflow_run": os.environ.get("GITHUB_RUN_ID"),
                "stage_id": stage_id, "stage_tag": stage_tag, "report_artifact_id": artifact["id"],
                "assets": report["assets"], "phase": "all_recovery_checks_passed"}
    (args.directory / "resume-verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    if args.verify_only:
        return
    spec = importlib.util.spec_from_file_location("verified_release_publisher", ROOT / "scripts/build/publish-current-release.py")
    publisher = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = publisher
    spec.loader.exec_module(publisher)
    config = publisher.Config(args.repository, source, args.tag, str(run["id"]), str(attempt),
                              args.replace_existing, args.rollback_tag,
                              args.directory, resume_stage_id=stage_id, resume_stage_tag=stage_tag,
                              prune_superseded=args.prune_superseded)
    transaction = publisher.Publisher(config, publisher.GitHub(args.repository))
    try:
        result = transaction.run()
    except Exception as error:
        transaction.result["error"] = str(error)
        transaction.save("failed:" + transaction.result["phase"])
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
