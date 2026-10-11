#!/usr/bin/env python3
"""Check the pinned Libass extraction boundary and retained-release handoff."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/build"))
import libass_native_input as native


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apk(entries):
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return output.getvalue()


class NativeInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="libass-input-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.libraries = {abi: b"test-native-" + abi.encode() for abi in native.SO}
        self.containers = {
            abi: apk([("lib/" + abi + "/libmedia3ass.so", data), ("classes.dex", b"not imported")])
            for abi, data in self.libraries.items()
        }
        self.paths = {abi: self.root / (abi + ".apk") for abi in native.SO}
        for abi, data in self.containers.items():
            self.paths[abi].write_bytes(data)
        # Tiny deterministic fixtures test gates, not production native compatibility.
        self.addCleanup(patch.stopall)
        patch.object(native, "SO", {abi: digest(data) for abi, data in self.libraries.items()}).start()
        patch.object(native, "APK", {abi: digest(data) for abi, data in self.containers.items()}).start()
        self.release = {"id": 7, "tag_name": "v5.6.3-xray.2", "draft": False,
                        "prerelease": False, "target_commitish": "a" * 40, "assets": []}
        for index, (abi, data) in enumerate(self.containers.items(), 40):
            self.release["assets"].append({
                "id": index, "name": "FongMi-Xray-TV-v5.6.3-xray.2-" + abi + ".apk",
                "state": "uploaded", "size": len(data), "digest": "sha256:" + digest(data),
            })

    def read(self, source="retained-release"):
        return native.read_native_inputs(self.paths["armeabi-v7a"], self.paths["arm64-v8a"], source)

    def test_historical_default_and_retained_extract_identical_bytes(self):
        retained = self.read()
        historical = native.read_native_inputs(self.paths["armeabi-v7a"], self.paths["arm64-v8a"])
        self.assertEqual(historical, retained)
        self.assertEqual(set(retained[0]), {"jni/" + abi + "/libmedia3ass.so" for abi in native.SO})

    def test_apk_classes_do_not_change_extracted_native(self):
        before, digests = self.read()
        abi = "armeabi-v7a"
        self.paths[abi].write_bytes(apk([
            ("lib/" + abi + "/libmedia3ass.so", self.libraries[abi]),
            ("classes.dex", b"different application"), ("classes.jar", b"not a jar"),
            ("assets/unused", b"arbitrary container change"),
        ]))
        after, changed = self.read()
        self.assertEqual(before, after)
        self.assertNotEqual(digests[abi], changed[abi])
        with self.assertRaisesRegex(ValueError, "Unpinned historical APK"):
            self.read("upstream-568")

    def test_changed_native_is_rejected(self):
        self.paths["armeabi-v7a"].write_bytes(apk([
            ("lib/armeabi-v7a/libmedia3ass.so", b"changed"),
        ]))
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            self.read()

    def test_missing_or_wrong_abi_is_rejected(self):
        for entries in ([('classes.dex', b"no native")],
                        [("lib/arm64-v8a/libmedia3ass.so", self.libraries["arm64-v8a"])]):
            with self.subTest(entries=entries):
                self.paths["armeabi-v7a"].write_bytes(apk(entries))
                with self.assertRaisesRegex(ValueError, "exactly one"):
                    self.read()
        self.paths["armeabi-v7a"].write_bytes(apk([
            ("lib/armeabi-v7a/libmedia3ass.so", self.libraries["arm64-v8a"]),
        ]))
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            self.read()

    def test_duplicate_native_entry_is_rejected(self):
        entry = ("lib/armeabi-v7a/libmedia3ass.so", self.libraries["armeabi-v7a"])
        with self.assertWarns(UserWarning):
            self.paths["armeabi-v7a"].write_bytes(apk([entry, entry]))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.read()

    def test_unknown_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            self.read("unverified")

    def test_published_normal_version_container_accepts_prerelease_flag(self):
        self.assertEqual(len(native.retained_assets(self.release)), 2)
        self.assertEqual(len(native.retained_assets({**self.release, "prerelease": True})), 2)
        for update in ({"draft": True}, {"prerelease": None}, {"tag_name": "v5.6.0-xray.5"},
                       {"id": None}, {"tag_name": "source-backup-example"},
                       {"tag_name": "v5.6.3-xray.test.7"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                native.retained_assets({**self.release, **update})

    def test_missing_ambiguous_or_incomplete_asset_is_rejected(self):
        for mode in ("missing", "duplicate", "pending", "wrong-name"):
            release = copy.deepcopy(self.release)
            if mode == "missing":
                release["assets"].pop()
            elif mode == "duplicate":
                release["assets"].append(release["assets"][0])
            elif mode == "pending":
                release["assets"][0]["state"] = "starter"
            else:
                release["assets"][0]["name"] = "wrong.apk"
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                native.retained_assets(release)

    def download(self, metadata=None, fail=False, fail_first=False, pages=None, annotated=False):
        payload = {asset["id"]: self.containers[abi]
                   for abi, asset in native.retained_assets(self.release).items()}
        calls = []

        def run(command, stdout):
            calls.append(command)
            asset_id = int(command[2].rsplit("/", 1)[1])
            stdout.write(payload[asset_id])
            return subprocess.CompletedProcess(command, 1 if fail or (fail_first and len(calls) == 1) else 0)

        selected = metadata or self.release
        snapshot = [[selected]] if pages is None else pages
        source = "a" * 40

        def lookup_result(command, text):
            path = command[2]
            if path == "repos/owner/repo/releases?per_page=100":
                return "\n".join(json.dumps(page) for page in snapshot)
            if path == "repos/owner/repo/git/ref/tags/" + selected["tag_name"]:
                return json.dumps({"ref": "refs/tags/" + selected["tag_name"], "object": {
                    "type": "tag" if annotated else "commit", "sha": "b" * 40 if annotated else source}})
            if annotated and path == "repos/owner/repo/git/tags/" + "b" * 40:
                return json.dumps({"object": {"type": "commit", "sha": source}})
            raise AssertionError("Unexpected metadata lookup: " + path)

        with patch.object(native.subprocess, "check_output", side_effect=lookup_result) as lookup, \
                patch.object(native.subprocess, "run", side_effect=run), patch.object(native.time, "sleep"):
            result = native.fetch_retained_inputs("owner/repo", self.root / "download")
            listing = [call for call in lookup.call_args_list
                       if call.args[0][2] == "repos/owner/repo/releases?per_page=100"]
            self.assertEqual(len(listing), 1)
            self.assertEqual(listing[0].args[0], [
                "gh", "api", "repos/owner/repo/releases?per_page=100", "--method", "GET",
                "--paginate",
            ])
            self.assertEqual(lookup.call_count, 3 if annotated else 2)
        return result, calls

    def test_release_snapshot_downloads_asset_ids_and_records_provenance(self):
        result, calls = self.download()
        self.assertEqual(len(calls), 2)
        self.assertEqual({call[2] for call in calls}, {
            "repos/owner/repo/releases/assets/40", "repos/owner/repo/releases/assets/41",
        })
        self.assertEqual(result["tag"], "v5.6.3-xray.2")
        self.assertEqual(result["release_id"], 7)
        self.assertFalse(result["prerelease"])
        self.assertEqual(result["tag_source_commit"], "a" * 40)
        self.assertEqual(result["target_commitish"], "a" * 40)
        self.assertEqual(result["apk_sha256"], native.APK)
        self.assertEqual((self.root / "download/libass-source-v7.apk").read_bytes(),
                         self.containers["armeabi-v7a"])

    def test_latest_golden_display_and_other_release_types_do_not_hide_prerelease(self):
        preview = {**self.release, "prerelease": True}
        ignored = [
            {**self.release, "tag_name": "v5.6.0-xray.5"},
            {**self.release, "tag_name": "source-backup-2026-10-11-main-6172516b"},
            {**self.release, "tag_name": "v5.6.3-xray.99", "draft": True},
            {**self.release, "tag_name": "v5.6.3-xray.test.7"},
        ]
        before = copy.deepcopy(ignored + [preview])
        result, calls = self.download(metadata=preview, pages=[ignored, [preview]])
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["tag"], preview["tag_name"])
        self.assertTrue(result["prerelease"])
        self.assertEqual(ignored + [preview], before)

    def test_pagination_and_numeric_version_order_choose_highest(self):
        highest = copy.deepcopy(self.release)
        highest["tag_name"] = "v5.6.3-xray.10"
        for abi, asset in zip(native.SO, highest["assets"]):
            asset["name"] = "FongMi-Xray-TV-" + highest["tag_name"] + "-" + abi + ".apk"
        result, _ = self.download(metadata=highest, pages=[[self.release], [highest]])
        self.assertEqual(result["tag"], "v5.6.3-xray.10")
        newer_upstream = {**highest, "tag_name": "v5.6.10-xray.1"}
        self.assertIs(native.select_retained_release([highest, newer_upstream]), newer_upstream)
        newer_major = {**highest, "tag_name": "v10.0.0-xray.1"}
        self.assertIs(native.select_retained_release([newer_upstream, newer_major]), newer_major)

    def test_highest_incomplete_container_fails_without_downloading_older_release(self):
        for count in (0, 1):
            highest = copy.deepcopy(self.release)
            highest["tag_name"] = "v5.6.3-xray.3"
            highest["assets"] = highest["assets"][:count]
            for asset in highest["assets"]:
                asset["name"] = asset["name"].replace("v5.6.3-xray.2", "v5.6.3-xray.3")
            pages = json.dumps([self.release]) + "\n" + json.dumps([highest])
            with self.subTest(available_abis=count), \
                    patch.object(native.subprocess, "check_output", return_value=pages), \
                    patch.object(native.subprocess, "run") as download:
                with self.assertRaisesRegex(ValueError, "Missing or ambiguous"):
                    native.fetch_retained_inputs("owner/repo", self.root / "download")
                download.assert_not_called()

    def test_no_eligible_or_ambiguous_highest_container_is_rejected(self):
        for releases in ([], [{**self.release, "tag_name": "v5.6.0-xray.5"}],
                         [{**self.release, "draft": True}]):
            with self.subTest(releases=releases), self.assertRaisesRegex(ValueError, "No published"):
                native.select_retained_release(releases)
        with self.assertRaisesRegex(ValueError, "Ambiguous highest"):
            native.select_retained_release([self.release, copy.deepcopy(self.release)])
        with self.assertRaisesRegex(ValueError, "Ambiguous highest"):
            native.select_retained_release([self.release, {**self.release, "tag_name": "v05.6.3-xray.2"}])

    def test_annotated_container_tag_records_commit_source(self):
        result, _ = self.download(annotated=True)
        self.assertEqual(result["tag_source_commit"], "a" * 40)

    def test_download_failure_and_metadata_mismatch_never_publish_inputs(self):
        with self.assertRaises(RuntimeError):
            self.download(fail=True)
        for key, value in (("size", 1), ("digest", "sha256:" + "0" * 64)):
            metadata = copy.deepcopy(self.release)
            metadata["assets"][0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "mismatch"):
                self.download(metadata=metadata)
        self.assertFalse(list((self.root / "download").glob("*.apk")))

    def test_missing_api_digest_still_records_actual_apk_digest(self):
        metadata = copy.deepcopy(self.release)
        del metadata["assets"][0]["digest"]
        metadata["assets"][1]["digest"] = None
        result, _ = self.download(metadata=metadata)
        self.assertEqual(result["apk_sha256"], native.APK)
        self.assertEqual(result["so_sha256"], native.SO)

    def test_retry_keeps_same_asset_id_and_single_metadata_snapshot(self):
        _, calls = self.download(fail_first=True)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0], calls[1])
        self.assertTrue(calls[1][2].endswith("/40"))
        self.assertTrue(calls[2][2].endswith("/41"))

    def test_second_abi_native_failure_preserves_both_previous_inputs(self):
        directory = self.root / "download"
        directory.mkdir()
        names = ("libass-source-v7.apk", "libass-source-v8.apk")
        for name in names:
            (directory / name).write_bytes(b"previous-" + name.encode())
        abi = "arm64-v8a"
        self.containers[abi] = apk([("lib/" + abi + "/libmedia3ass.so", b"changed native")])
        self.release["assets"][1]["size"] = len(self.containers[abi])
        self.release["assets"][1]["digest"] = "sha256:" + digest(self.containers[abi])
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            self.download()
        for name in names:
            self.assertEqual((directory / name).read_bytes(), b"previous-" + name.encode())


if __name__ == "__main__":
    unittest.main()
