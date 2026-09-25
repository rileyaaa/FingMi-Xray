#!/usr/bin/env python3
"""Pure-Python packaging test; synthetic fixtures are NOT published APK evidence."""

import hashlib
import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/restore-published-ffmpegjni.py"
SPEC = importlib.util.spec_from_file_location("restore_ffmpegjni", SCRIPT)
RESTORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESTORE)


class RestoreFfmpegJniTest(unittest.TestCase):
    def test_replaces_only_two_jni_entries_after_input_hash_checks(self):
        with tempfile.TemporaryDirectory() as location:
            root = Path(location)
            originals = {
                "armeabi-v7a": b"published-v7-jni",
                "arm64-v8a": b"published-v8-jni",
            }
            apks = {}
            for abi, payload in originals.items():
                path = root / f"{abi}.apk"
                with ZipFile(path, "w") as archive:
                    archive.writestr(f"lib/{abi}/libffmpegJNI.so", payload)
                apks[abi] = path

            aar_buffer = BytesIO()
            with ZipFile(aar_buffer, "w") as aar:
                for abi in originals:
                    aar.writestr(f"jni/{abi}/libffmpegJNI.so", b"candidate-" + abi.encode())
                aar.writestr("classes.jar", b"unchanged-classes")
            candidate = root / "candidate.zip"
            with ZipFile(candidate, "w") as outer:
                outer.writestr(RESTORE.NAME, aar_buffer.getvalue())

            destination = root / "new-decoder.aar"
            with patch.object(RESTORE, "V7_APK_SHA256",
                              hashlib.sha256(apks["armeabi-v7a"].read_bytes()).hexdigest()), \
                 patch.object(RESTORE, "V8_APK_SHA256",
                              hashlib.sha256(apks["arm64-v8a"].read_bytes()).hexdigest()), \
                 patch.dict(RESTORE.JNI_SHA256, {
                     abi: hashlib.sha256(payload).hexdigest()
                     for abi, payload in originals.items()
                 }), \
                 patch.object(RESTORE, "CANDIDATE_SHA256",
                              hashlib.sha256(candidate.read_bytes()).hexdigest()), \
                 patch.object(sys, "argv", [str(SCRIPT),
                                            "--candidate", str(candidate),
                                            "--v7-apk", str(apks["armeabi-v7a"]),
                                            "--v8-apk", str(apks["arm64-v8a"]),
                                            "--to", str(destination)]):
                RESTORE.main()

            with ZipFile(destination) as aar:
                self.assertEqual(b"unchanged-classes", aar.read("classes.jar"))
                for abi, payload in originals.items():
                    self.assertEqual(payload, aar.read(f"jni/{abi}/libffmpegJNI.so"))


if __name__ == "__main__":
    unittest.main()
