#!/usr/bin/env python3
"""Failure-injection tests for release cutover; never contacts GitHub."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_publication", ROOT / "scripts/build/publish-current-release.py")
PUB = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PUB
SPEC.loader.exec_module(PUB)
OLD = "a" * 40
SOURCE = "b" * 40
PREVIOUS = "source-backup-2026-10-05-main-aaaaaaaa"
TAG = "v5.6.3-xray.1"


class FakeGitHub:
    def __init__(self):
        self.events = []
        self.refs = {TAG: self.make_ref(TAG, OLD), PREVIOUS: self.make_ref(PREVIOUS, OLD),
                     "v5.6.0-xray.5": self.make_ref("v5.6.0-xray.5", "c" * 40)}
        self.releases = {
            1: self.row(1, TAG, False),
            2: self.row(2, PREVIOUS, True),
            3: self.row(3, "v5.6.0-xray.5", False),
        }
        self.latest = 1
        self.uploads = 0
        self.fail_upload = 0
        self.bad_stage_digest = False
        self.bad_final_digest = False
        self.change_old_ref = False
        self.private = True

    @staticmethod
    def make_ref(tag, source):
        return {"ref": "refs/tags/" + tag, "object": {"type": "commit", "sha": source}}

    @staticmethod
    def row(identity, tag, prerelease):
        return {"id": identity, "tag_name": tag, "draft": False, "prerelease": prerelease,
                "immutable": False, "assets": [{"id": identity * 100, "name": "old-asset",
                "digest": "sha256:old", "size": 3, "state": "uploaded", "browser_download_url": "old-url"}]}

    def api(self, path, method="GET", data=None, optional=False):
        self.events.append((method, path, copy.deepcopy(data)))
        if method == "GET":
            if path == "":
                result = {"private": self.private}
            elif path == "releases/latest":
                result = self.releases[self.latest]
            elif path.startswith("releases/tags/"):
                tag = unquote(path.removeprefix("releases/tags/"))
                result = next((r for r in self.releases.values() if r["tag_name"] == tag), None)
            elif path.startswith("git/ref/tags/"):
                result = self.refs.get(unquote(path.removeprefix("git/ref/tags/")))
            else:
                raise AssertionError((method, path))
            if result is None and not optional:
                raise RuntimeError("missing fake resource")
            return copy.deepcopy(result)
        if path == "git/refs" and method == "POST":
            tag = data["ref"].removeprefix("refs/tags/")
            assert tag not in self.refs
            self.refs[tag] = self.make_ref(tag, data["sha"])
            return copy.deepcopy(self.refs[tag])
        if path.startswith("git/refs/tags/"):
            tag = unquote(path.removeprefix("git/refs/tags/"))
            if method == "PATCH":
                self.refs[tag] = self.make_ref(tag, data["sha"])
            elif method == "DELETE":
                del self.refs[tag]
            else:
                raise AssertionError((method, path))
            return None
        if path == "releases" and method == "POST":
            identity = max(self.releases) + 1
            self.releases[identity] = {"id": identity, "assets": [], **copy.deepcopy(data)}
            return copy.deepcopy(self.releases[identity])
        if path.startswith("releases/"):
            identity = int(path.split("/")[1])
            if method == "DELETE":
                del self.releases[identity]
            elif method == "PATCH":
                row = self.releases[identity]
                row.update(data)
                # GitHub's asset download URLs follow the release's new tag.
                for asset in row["assets"]:
                    asset["browser_download_url"] = "new-url/" + row["tag_name"]
                if data.get("make_latest") == "true":
                    self.latest = identity
                    if self.bad_final_digest:
                        row["assets"][0]["digest"] = "sha256:corrupted-after-promotion"
            else:
                raise AssertionError((method, path))
            return copy.deepcopy(self.releases.get(identity))
        raise AssertionError((method, path))

    def upload(self, tag, assets):
        self.uploads += 1
        self.events.append(("UPLOAD", tag, None))
        if self.uploads == self.fail_upload:
            raise RuntimeError("injected upload failure")
        row = next(r for r in self.releases.values() if r["tag_name"] == tag)
        row["assets"] = [{"id": row["id"] * 100 + i, "state": "uploaded", **asset.metadata()}
                         for i, asset in enumerate(assets)]
        if self.bad_stage_digest and self.uploads == 1:
            row["assets"][0]["digest"] = "sha256:wrong"
        if self.change_old_ref and self.uploads == 2:
            self.refs[TAG] = self.make_ref(TAG, "f" * 40)


class PublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="publication-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for abi in ("armeabi-v7a", "arm64-v8a"):
            (self.directory / f"FongMi-Xray-TV-{TAG}-{abi}.apk").write_bytes(("synthetic apk " + abi).encode())
        self.config = PUB.Config("private/project", SOURCE, TAG, "123", "1", PREVIOUS,
                                 True, "release-rollback-test", self.directory)
        self.github = FakeGitHub()
        self.original = copy.deepcopy(self.github.releases[1])

    def archive(self, config, tag):
        path = config.directory / f"FingMi-Xray-{tag}.zip"
        path.write_bytes(b"synthetic source archive")
        return PUB.Asset.read(path)

    def publisher(self, config=None):
        class TestedPublisher(PUB.Publisher):
            def source_version(self):
                return TAG, 563001
        return TestedPublisher(config or self.config, self.github, self.archive)

    def assert_old_preserved(self):
        self.assertEqual(self.github.releases[1], self.original)
        self.assertIn(2, self.github.releases)
        self.assertFalse(any(method == "DELETE" for method, _, _ in self.github.events))

    def test_each_upload_failure_preserves_current_publication(self):
        for upload in (1, 2):
            with self.subTest(upload=upload):
                self.github = FakeGitHub()
                self.github.fail_upload = upload
                with self.assertRaisesRegex(RuntimeError, "upload failure"):
                    self.publisher().run()
                self.assert_old_preserved()

    def test_wrong_remote_digest_prevents_retirement(self):
        self.github.bad_stage_digest = True
        with self.assertRaisesRegex(PUB.PublicationError, "asset verification"):
            self.publisher().run()
        self.assert_old_preserved()

    def test_final_verification_failure_keeps_rollback_and_old_backup(self):
        self.github.bad_final_digest = True
        with self.assertRaisesRegex(PUB.PublicationError, "asset verification"):
            self.publisher().run()
        rollback = self.github.releases[1]
        self.assertTrue(rollback["draft"])
        self.assertEqual(rollback["tag_name"], self.config.rollback_tag)
        self.assertEqual(PUB.Publisher.asset_fingerprint(rollback), PUB.Publisher.asset_fingerprint(self.original))
        self.assertEqual(self.github.refs[self.config.rollback_tag]["object"]["sha"], OLD)
        self.assertIn(2, self.github.releases)
        self.assertFalse(any(method == "DELETE" for method, _, _ in self.github.events))

    def test_concurrent_tag_change_aborts_before_retirement(self):
        self.github.change_old_ref = True
        with self.assertRaisesRegex(PUB.PublicationError, "changed during staging"):
            self.publisher().run()
        self.assert_old_preserved()

    def test_private_repository_and_explicit_replacement_are_required(self):
        self.github.private = False
        with self.assertRaisesRegex(PUB.PublicationError, "private project"):
            self.publisher().run()
        self.assertEqual(self.github.uploads, 0)
        self.github.private = True
        from dataclasses import replace
        with self.assertRaisesRegex(PUB.PublicationError, "ALLOW_EXISTING_RELEASE"):
            self.publisher(replace(self.config, allow_existing=False)).run()
        self.assert_old_preserved()

    def test_github_repository_endpoint_has_no_trailing_slash(self):
        response = subprocess.CompletedProcess([], 0, b'{"private":true}', b"")
        with mock.patch.object(PUB.subprocess, "run", return_value=response) as runner:
            client = PUB.GitHub("private/project")
            self.assertTrue(client.api("")["private"])
            self.assertEqual(runner.call_args.args[0], ["gh", "api", "repos/private/project", "--method", "GET"])
            client.api("releases", "POST", {"draft": True})
            self.assertEqual(runner.call_args.args[0][2], "repos/private/project/releases")
            self.assertEqual(json.loads(runner.call_args.kwargs["input"]), {"draft": True})

    def test_optional_lookup_does_not_hide_permission_errors(self):
        client = PUB.GitHub("private/project")
        with mock.patch.object(PUB.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"gh: Not Found (HTTP 404)")):
            self.assertIsNone(client.api("releases/tags/missing", optional=True))
        with mock.patch.object(PUB.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"gh: Forbidden (HTTP 403)")):
            with self.assertRaisesRegex(PUB.PublicationError, "HTTP 403"):
                client.api("releases/tags/private", optional=True)

    def test_success_cleans_only_after_both_final_publications_verify(self):
        # A precreated rollback tag is accepted only at the old source.
        self.github.refs[self.config.rollback_tag] = self.github.make_ref(self.config.rollback_tag, OLD)
        result = self.publisher().run()
        self.assertEqual(result["phase"], "complete")
        self.assertEqual(self.github.refs[TAG]["object"]["sha"], SOURCE)
        self.assertNotIn(1, self.github.releases)
        self.assertNotIn(2, self.github.releases)
        self.assertIn(3, self.github.releases)
        self.assertNotIn(PREVIOUS, self.github.refs)
        self.assertFalse(any(tag.startswith(("stage-", "release-rollback-")) for tag in self.github.refs))
        actions = self.github.events
        retired = next(i for i, (m, p, d) in enumerate(actions) if m == "PATCH" and p == "releases/1")
        uploads = [i for i, (m, _, _) in enumerate(actions) if m == "UPLOAD"]
        self.assertGreater(retired, max(uploads))
        latest_check = max(i for i, (m, p, _) in enumerate(actions) if m == "GET" and p == "releases/latest")
        deletions = [i for i, (m, _, _) in enumerate(actions) if m == "DELETE"]
        self.assertTrue(deletions and min(deletions) > latest_check)
        before = json.loads((self.directory / "publication-before.json").read_text())
        self.assertEqual(before["release"]["id"], 1)
        self.assertEqual(json.loads((self.directory / "publication-result.json").read_text())["phase"], "complete")

    def test_source_archive_restores_exact_committed_signing_and_source_bytes(self):
        repository = self.directory / "repository"
        repository.mkdir()
        previous_cwd = Path.cwd()
        try:
            os.chdir(repository)
            def git(*args):
                return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)
            git("init", "--quiet")
            git("config", "user.name", "Archive test")
            git("config", "user.email", "archive@example.invalid")
            Path("signing").mkdir()
            for name in ("fingmi-xray-release.p12", "release-signing.properties", "release-certificate.sha256"):
                (Path("signing") / name).write_bytes(b"synthetic signing fixture")
            Path("source.java").write_bytes(b"committed source\n")
            Path("app").mkdir()
            Path("app/build.gradle").write_text(f'versionName "{TAG}"\nversionCode 563001\n')
            git("add", ".")
            git("commit", "--quiet", "-m", "archive fixture")
            source = git("rev-parse", "HEAD").decode().strip()
            Path("source.java").write_bytes(b"uncommitted dirty bytes must not enter archive\n")
            from dataclasses import replace
            source_config = replace(self.config, source=source)
            self.assertEqual(PUB.Publisher(source_config, None).source_version(), (TAG, 563001))
            asset = PUB.source_archive(source_config, "source-backup-test")
            import zipfile
            with zipfile.ZipFile(asset.path) as archive:
                self.assertEqual(archive.read("FingMi-Xray/source.java"), b"committed source\n")
                self.assertEqual(len([i for i in archive.infolist() if not i.is_dir()]), 5)
        finally:
            os.chdir(previous_cwd)


if __name__ == "__main__":
    unittest.main(verbosity=2)
