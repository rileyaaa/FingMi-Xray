#!/usr/bin/env python3
"""Verify that a restored decoder cannot silently change playback Java/native code."""

import hashlib
import importlib.util
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/import-player-aar-candidate.py"
SPEC = importlib.util.spec_from_file_location("import_player", SCRIPT)
IMPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORT)


def aar(entries):
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return output.getvalue()


class ImportRestoredDecoderTest(unittest.TestCase):
    def test_only_verified_jni_may_change(self):
        original = [
            ("jni/armeabi-v7a/libffmpegJNI.so", b"candidate-v7"),
            ("jni/arm64-v8a/libffmpegJNI.so", b"candidate-v8"),
            ("classes.jar", b"original-class-bytecode"),
        ]
        restored = [
            (original[0][0], b"published-v7"),
            (original[1][0], b"published-v8"),
            original[2],
        ]
        hashes = {name: hashlib.sha256(data).hexdigest()
                  for name, data in restored[:2]}
        with patch.dict(IMPORT.PUBLISHED_JNI, hashes):
            self.assertEqual(
                aar(restored), IMPORT.verified_decoder_replacement(
                    aar(original), aar(restored)))
            tampered = restored[:2] + [("classes.jar", b"changed-class-bytecode")]
            with self.assertRaisesRegex(ValueError, "changed another entry"):
                IMPORT.verified_decoder_replacement(aar(original), aar(tampered))
            with self.assertRaisesRegex(ValueError, "unverified published JNI"):
                IMPORT.verified_decoder_replacement(
                    aar(original), aar([(original[0][0], b"wrong-v7")] + restored[1:]))
            with self.assertRaisesRegex(ValueError, "names/order differ"):
                IMPORT.verified_decoder_replacement(
                    aar(original), aar(restored + [("extra", b"unexpected")]))


if __name__ == "__main__":
    unittest.main()
