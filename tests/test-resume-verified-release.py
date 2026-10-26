#!/usr/bin/env python3
"""Fail-closed recovery tests; synthetic APKs/reports, no GitHub mutations."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("resume_verified_release", ROOT / "scripts/build/resume-verified-release.py")
RESUME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESUME)
REPOSITORY = "test/project"
SOURCE = "a" * 40
TAG = "v5.6.3-xray.1"
RUN_ID = 123
STAGE_TAG = "stage-" + TAG + "-123-1"


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.run = {"id": RUN_ID, "status": "completed", "conclusion": "failure", "event": "workflow_dispatch",
                    "head_branch": "main", "repository": {"id": 10, "full_name": REPOSITORY},
                    "head_repository": {"id": 10, "full_name": REPOSITORY}, "head_sha": SOURCE,
                    "run_attempt": 1, "workflow_id": 20}
        self.workflow = {"id": 20, "path": RESUME.WORKFLOW}
        steps = [{"name": name, "status": "completed", "conclusion": "success", "number": number}
                 for number, name in enumerate(RESUME.REQUIRED_STEPS, 1)]
        steps.append({"name": RESUME.PUBLISH_STEP, "status": "completed", "conclusion": "failure", "number": 99})
        self.jobs = [{"name": "build", "run_id": RUN_ID, "run_attempt": 1, "head_sha": SOURCE,
                      "status": "completed", "conclusion": "failure", "steps": steps}]
        self.assets = [{"name": f"FongMi-Xray-TV-{TAG}-{abi}.apk", "digest": "sha256:" + char * 64, "size": 100 + index}
                       for index, (abi, char) in enumerate((("armeabi-v7a", "b"), ("arm64-v8a", "c")))]
        self.report = {"source": SOURCE, "release_tag": TAG, "phase": "failed:uploading",
                       "staged": {STAGE_TAG: 30}, "assets": self.assets}
        self.stage = {"id": 30, "tag_name": STAGE_TAG, "draft": True, "prerelease": False,
                      "assets": [{"id": 100 + i, "state": "uploaded", **a} for i, a in enumerate(self.assets)]}
        self.artifact = {"id": 40, "name": RESUME.REPORT_NAME, "expired": False, "size_in_bytes": 100,
                         "digest": "sha256:" + "e" * 64,
                         "workflow_run": {"id": RUN_ID, "head_sha": SOURCE, "repository_id": 10, "head_repository_id": 10}}

    def check_run(self):
        RESUME.verify_run(REPOSITORY, RUN_ID, self.run, self.workflow, self.jobs)

    def test_accepts_only_complete_original_evidence(self):
        self.check_run()
        self.assertEqual(RESUME.select_artifact(self.run, [self.artifact])["id"], 40)
        self.assertEqual(RESUME.verify_report(self.run, self.report, TAG), (STAGE_TAG, 30))
        self.assertEqual(len(RESUME.verify_stage(self.stage, self.report, STAGE_TAG, 30)), 2)

    def test_authorized_marker_push_must_have_matching_successful_source_guard(self):
        self.run["event"] = "push"
        self.run["head_commit"] = {
            "id": SOURCE, "message": "ci: trigger authorized v5.6.3-xray.1 release"}
        guard = {"name": "Verify temporary push trigger source",
                 "status": "completed", "conclusion": "success", "number": 0}
        self.jobs[0]["steps"].insert(0, guard)
        self.check_run()
        for bad in ("unexpected", "ci: trigger authorized v5.6.3-xray.2 release"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.run["head_commit"]["message"] = bad
                self.check_run()
        self.run["head_commit"]["message"] = "ci: trigger authorized v5.6.3-xray.1 release"
        for bad in ("failure", "skipped"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                guard["conclusion"] = bad
                self.check_run()
        guard["conclusion"] = "success"
        guard["name"] = "different guard"
        with self.assertRaises(ValueError):
            self.check_run()

    def test_accepts_only_the_identified_backup_published_stage(self):
        backup_tag = "source-backup-2026-10-26-main-" + SOURCE[:8]
        backup_stage_tag = STAGE_TAG + "-backup"
        backup_asset = {"name": "FingMi-Xray-" + backup_tag + ".zip",
                        "digest": "sha256:" + "d" * 64, "size": 110}
        self.report.update(phase="failed:backup_published",
                           staged={STAGE_TAG: 30, backup_stage_tag: 31},
                           backup_tag=backup_tag, backup_release_id=31,
                           backup_asset=backup_asset)
        self.assertEqual(RESUME.verify_report(self.run, self.report, TAG),
                         (STAGE_TAG, 30))
        release = {"id": 31, "tag_name": backup_tag,
                   "draft": False, "prerelease": True,
                   "assets": [{"id": 111, "state": "uploaded", **backup_asset}]}
        ref = {"ref": "refs/tags/" + backup_tag,
               "object": {"type": "commit", "sha": SOURCE}}
        gh = mock.Mock()
        gh.api.side_effect = lambda name: {
            "releases/31": release, "git/ref/tags/" + backup_tag: ref
        }[name]
        RESUME.verify_completed_backup(gh, self.run, self.report)
        for field, bad in (("digest", "sha256:" + "f" * 64), ("state", "uploading")):
            actual = release["assets"][0][field]
            release["assets"][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                RESUME.verify_completed_backup(gh, self.run, self.report)
            release["assets"][0][field] = actual
        for mutation in (
            {"phase": "failed:rollback_preserved"},
            {"backup_release_id": 0},
            {"backup_tag": "source-backup-2026-10-26-main-bad00000"},
            {"staged": {STAGE_TAG: 30}},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                RESUME.verify_report(self.run, {**self.report, **mutation}, TAG)

    def test_binary_api_media_types_follow_each_endpoint_contract(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(RESUME.subprocess, "run") as command:
            gh = RESUME.GitHub(REPOSITORY)
            gh.download("actions/artifacts/40/zip", Path(directory) / "report.zip")
            self.assertEqual(command.call_args.args[0],
                             ["gh", "api", "repos/test/project/actions/artifacts/40/zip", "--method", "GET"])
            gh.download("releases/assets/100", Path(directory) / "app.apk")
            self.assertEqual(command.call_args.args[0],
                             ["gh", "api", "repos/test/project/releases/assets/100", "--method", "GET",
                              "-H", "Accept: application/octet-stream"])
            with self.assertRaises(ValueError):
                gh.download("releases/latest", Path(directory) / "invalid")

    def test_rejects_untrusted_run_identity(self):
        for field, value in (("id", 321), ("status", "in_progress"), ("conclusion", "success"),
                             ("event", "pull_request"), ("head_branch", "fork"), ("head_sha", "bad"),
                             ("run_attempt", 0), ("workflow_id", 99)):
            original = self.run[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.run[field] = value
                self.check_run()
            self.run[field] = original
        for repo in ("repository", "head_repository"):
            original = copy.deepcopy(self.run[repo])
            for field, value in (("id", 999), ("full_name", "fork/project")):
                with self.subTest(repo=repo, field=field), self.assertRaises(ValueError):
                    self.run[repo][field] = value
                    self.check_run()
                self.run[repo] = copy.deepcopy(original)
        self.workflow["path"] = ".github/workflows/resume-verified-release.yml"
        with self.assertRaises(ValueError):
            self.check_run()

    def test_every_gate_must_pass_before_publication(self):
        for step in self.jobs[0]["steps"][:-1]:
            for conclusion in ("failure", "skipped", "cancelled"):
                with self.subTest(gate=step["name"], conclusion=conclusion), self.assertRaises(ValueError):
                    step["conclusion"] = conclusion
                    self.check_run()
                step["conclusion"] = "success"
            original = step["number"]
            step["number"] = 100
            with self.assertRaises(ValueError):
                self.check_run()
            step["number"] = original
        self.jobs[0]["steps"].append(copy.deepcopy(self.jobs[0]["steps"][0]))
        with self.assertRaises(ValueError):
            self.check_run()

    def test_rejects_job_from_other_attempt_and_extra_failures(self):
        self.jobs[0]["run_attempt"] = 2
        with self.assertRaises(ValueError):
            self.check_run()
        self.jobs[0]["run_attempt"] = 1
        self.jobs[0]["steps"].append({"name": "Post verification", "conclusion": "failure"})
        with self.assertRaises(ValueError):
            self.check_run()

    def test_cannot_resume_without_new_crash_regressions(self):
        original = copy.deepcopy(self.jobs)
        for gate in ("Verify Xray artwork lifecycle", "Verify proxy policy host regression"):
            self.assertIn(gate, RESUME.REQUIRED_STEPS)
            for mutation in ("missing", "skipped", "duplicated"):
                with self.subTest(gate=gate, mutation=mutation):
                    self.jobs = copy.deepcopy(original)
                    steps = self.jobs[0]["steps"]
                    step = next(step for step in steps if step["name"] == gate)
                    if mutation == "missing":
                        steps.remove(step)
                    elif mutation == "skipped":
                        step["conclusion"] = "skipped"
                    else:
                        steps.append(copy.deepcopy(step))
                    with self.assertRaisesRegex(ValueError, gate):
                        self.check_run()
        self.jobs = original

    def test_rejects_missing_expired_and_wrong_report_owners(self):
        for rows in ([], [self.artifact, self.artifact]):
            with self.assertRaises(ValueError):
                RESUME.select_artifact(self.run, rows)
        for field, value in (("id", False), ("expired", True), ("digest", None), ("size_in_bytes", 32 * 1024 * 1024)):
            invalid = copy.deepcopy(self.artifact)
            invalid[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                RESUME.select_artifact(self.run, [invalid])
        for field in ("id", "head_sha", "repository_id", "head_repository_id"):
            invalid = copy.deepcopy(self.artifact)
            invalid["workflow_run"][field] = "unrelated"
            with self.subTest(field=field), self.assertRaises(ValueError):
                RESUME.select_artifact(self.run, [invalid])

    def test_report_hash_and_exact_member_required(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "report.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("release/publication-result.json", json.dumps(self.report))
                z.writestr("../../not-extracted", "irrelevant")
            artifact = {**self.artifact, "size_in_bytes": archive.stat().st_size, "digest": RESUME.digest(archive)}
            self.assertEqual(RESUME.read_report(archive, artifact), self.report)
            self.assertEqual([p.name for p in Path(directory).iterdir()], ["report.zip"])
            artifact["digest"] = "sha256:" + "0" * 64
            with self.assertRaises(ValueError):
                RESUME.read_report(archive, artifact)
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("other/publication-result.json", json.dumps(self.report))
            artifact.update(size_in_bytes=archive.stat().st_size, digest=RESUME.digest(archive))
            with self.assertRaises(ValueError):
                RESUME.read_report(archive, artifact)

    def test_refuses_cutover_or_wrong_run_report(self):
        for field, value in (("phase", "failed:cutover_published"), ("source", "b" * 40),
                             ("release_tag", "v5.6.3-xray.2"), ("staged", {STAGE_TAG + "-backup": 30}),
                             ("staged", {STAGE_TAG: 30, STAGE_TAG + "-backup": 31}),
                             ("staged", {STAGE_TAG.replace("-123-1", "-123-2"): 30}),
                             ("assets", self.assets[:1])):
            report = {**self.report, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                RESUME.verify_report(self.run, report, TAG)

    def test_refuses_changed_draft_or_assets(self):
        for field, value in (("id", 31), ("tag_name", TAG), ("draft", False), ("prerelease", True)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                RESUME.verify_stage({**self.stage, field: value}, self.report, STAGE_TAG, 30)
        for field, value in (("id", 0), ("state", "new"), ("digest", "sha256:" + "f" * 64),
                             ("size", 999), ("name", "../../replace.apk")):
            stage = copy.deepcopy(self.stage)
            stage["assets"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                RESUME.verify_stage(stage, self.report, STAGE_TAG, 30)

    def test_downloaded_apk_must_match_digest_and_original_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "fixture.apk"
            for revision in (SOURCE, "b" * 40):
                with zipfile.ZipFile(apk, "w") as z:
                    z.writestr("META-INF/version-control-info.textproto", f'revision: "{revision}"\n')
                asset = {"size": apk.stat().st_size, "digest": RESUME.digest(apk)}
                if revision == SOURCE:
                    RESUME.verify_apk(apk, asset, SOURCE)
                    asset["digest"] = "sha256:" + "f" * 64
                with self.assertRaises(ValueError):
                    RESUME.verify_apk(apk, asset, SOURCE)

    def test_verify_only_downloads_original_assets_and_runs_apk_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            binaries = {}
            for index, asset in enumerate(self.assets):
                apk = directory / asset["name"]
                with zipfile.ZipFile(apk, "w") as z:
                    z.writestr("META-INF/version-control-info.textproto", f'revision: "{SOURCE}"\n')
                    z.writestr("fixture-abi", str(index))
                asset.update(size=apk.stat().st_size, digest=RESUME.digest(apk))
                self.stage["assets"][index].update(asset)
                binaries[f"releases/assets/{100 + index}"] = apk.read_bytes()
            archive = directory / "reports.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("release/publication-result.json", json.dumps(self.report))
            self.artifact.update(size_in_bytes=archive.stat().st_size, digest=RESUME.digest(archive))
            binaries["actions/artifacts/40/zip"] = archive.read_bytes()
            responses = {"actions/runs/123": self.run,
                         "actions/workflows/publish-current-main-test-release.yml": self.workflow,
                         "releases/30": self.stage,
                         "git/ref/tags/" + STAGE_TAG: {"ref": "refs/tags/" + STAGE_TAG,
                                                     "object": {"type": "commit", "sha": SOURCE}}}
            gh = mock.Mock()
            gh.api.side_effect = lambda path: responses[path]
            gh.pages.side_effect = lambda path, key: self.jobs if key == "jobs" else [self.artifact]
            gh.download.side_effect = lambda path, target: target.write_bytes(binaries[path])
            output = directory / "recovered"
            argv = ["resume", "--verified-run-id", "123", "--repository", REPOSITORY,
                    "--directory", str(output), "--sdk", "/sdk", "--tag", TAG, "--verify-only"]
            with mock.patch.object(RESUME.sys, "argv", argv), mock.patch.object(RESUME, "GitHub", return_value=gh), \
                    mock.patch.object(RESUME, "source_identity") as identity, \
                    mock.patch.object(RESUME.subprocess, "run") as commands, \
                    mock.patch.object(RESUME.subprocess, "check_output", return_value="d" * 40), \
                    mock.patch("builtins.print"):
                RESUME.main()
            identity.assert_called_once_with(SOURCE)
            self.assertEqual(gh.download.call_args_list[0].args[0], "actions/artifacts/40/zip")
            self.assertEqual({c.args[0] for c in gh.download.call_args_list[1:]},
                             {"releases/assets/100", "releases/assets/101"})
            executed = [c.args[0] for c in commands.call_args_list]
            self.assertEqual(executed[0], ["git", "fetch", "--no-tags", "origin", SOURCE])
            self.assertEqual(len(executed), 7)
            self.assertEqual(sum("check-release-signing.py" in c[1] for c in executed[1:]), 2)
            self.assertEqual(sum("check-final-apk-manifest.py" in c[1] for c in executed[1:]), 2)
            self.assertEqual(sum("check-final-apk-media3.py" in c[1] for c in executed[1:]), 2)
            evidence = json.loads((output / "resume-verification.json").read_text())
            self.assertEqual(evidence["source"], SOURCE)
            self.assertEqual(evidence["publication_tooling_source"], "d" * 40)
            # Already-downloaded local files are never accepted as fresh proof.
            with mock.patch.object(RESUME.sys, "argv", argv), self.assertRaisesRegex(ValueError, "empty"):
                RESUME.main()


if __name__ == "__main__":
    unittest.main()
