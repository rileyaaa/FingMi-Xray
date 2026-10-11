#!/usr/bin/env python3
"""Regression cases for missing runtime dependencies in packaged DEX files."""

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import warnings
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("media3_dex", ROOT / "scripts/build/check-final-apk-media3.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)
BUFFER = "Landroidx/media3/decoder/DecoderInputBuffer;"
OUTPUT = "Landroidx/media3/decoder/SimpleDecoderOutputBuffer;"
VIDEO = "Landroidx/media3/decoder/VideoDecoderOutputBuffer;"


def dex(definitions=(), references=(), strings=()):
    """Build the DEX tables inspected by the gate, without fake class-name scans."""
    types = sorted(set(definitions) | set(references))
    text = sorted(set(types) | set(strings))
    data = bytearray(112 + 4 * len(text) + 4 * len(types) + 32 * len(definitions))

    def uint(offset, value):
        struct.pack_into("<I", data, offset, value)

    data[:8] = b"dex\n035\0"
    uint(36, 112)
    uint(40, 0x12345678)
    uint(56, len(text))
    uint(60, 112)
    uint(64, len(types))
    uint(68, 112 + 4 * len(text))
    uint(96, len(definitions))
    uint(100, 112 + 4 * len(text) + 4 * len(types))
    for i, value in enumerate(text):
        uint(112 + i * 4, len(data))
        encoded = value.encode()
        size = len(value)
        while size >= 128:
            data.append((size & 127) | 128)
            size >>= 7
        data.append(size)
        data.extend(encoded + b"\0")
    for i, value in enumerate(types):
        uint(112 + 4 * len(text) + i * 4, text.index(value))
    for i, value in enumerate(definitions):
        uint(112 + 4 * len(text) + 4 * len(types) + i * 32, types.index(value))
    uint(32, len(data))
    return bytes(data)


class Media3DexLinkageTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="media3-dex-")
        self.addCleanup(self.directory.cleanup)
        self.apk = Path(self.directory.name) / "candidate.apk"

    def analyze(self, *dex_files):
        with ZipFile(self.apk, "w") as archive:
            for i, data in enumerate(dex_files):
                archive.writestr("classes" + (str(i + 1) if i else "") + ".dex", data)
        return CHECK.analyze_apk(self.apk)

    def test_class_definition_is_required_even_when_name_is_referenced(self):
        report = self.analyze(dex([OUTPUT, VIDEO, "LRenderer;"], [BUFFER]))
        self.assertEqual(report["missing_referenced_types"], [BUFFER])
        with self.assertRaisesRegex(ValueError, "DecoderInputBuffer"):
            CHECK.require_complete(report)

    def test_definitions_can_be_in_another_dex(self):
        report = self.analyze(dex(["LRenderer;"], [BUFFER]), dex([BUFFER, OUTPUT, VIDEO]))
        CHECK.require_complete(report)
        self.assertEqual(report["dex_class_counts"], {"classes.dex": 1, "classes2.dex": 3})

    def test_array_types_require_their_component_definition(self):
        missing = "Landroidx/media3/decoder/Decoder$Callback;"
        report = self.analyze(dex([BUFFER, OUTPUT, VIDEO], ["[[" + missing]))
        self.assertEqual(report["missing_referenced_types"], [missing])
        with self.assertRaisesRegex(ValueError, "Callback"):
            CHECK.require_complete(report)

    def test_optional_reflection_strings_do_not_require_definitions(self):
        report = self.analyze(dex([BUFFER, OUTPUT, VIDEO], strings=[
            "Landroidx/media3/decoder/av1/Dav1dDecoder;",
            "androidx.media3.decoder.flac.LibflacAudioRenderer",
        ]))
        CHECK.require_complete(report)

    def test_all_media3_packages_checked_not_only_decoder(self):
        missing = "Landroidx/media3/exoplayer/ExoPlayer;"
        report = self.analyze(dex([BUFFER, OUTPUT, VIDEO], [missing]))
        self.assertEqual(report["missing_referenced_types"], [missing])

    def test_no_media3_apk_is_not_a_false_pass(self):
        report = self.analyze(dex(["LRenderer;"]))
        self.assertEqual(set(report["missing_required_definitions"]), {BUFFER, OUTPUT, VIDEO})
        with self.assertRaisesRegex(ValueError, "Media3 types"):
            CHECK.require_complete(report)

    def test_duplicate_definitions_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate APK class"):
            self.analyze(dex([BUFFER]), dex([BUFFER]))

    def test_duplicate_archive_entries_rejected(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(self.apk, "w") as archive:
                archive.writestr("classes.dex", dex([BUFFER]))
                archive.writestr("classes.dex", dex([BUFFER]))
        with self.assertRaisesRegex(ValueError, "duplicate DEX"):
            CHECK.analyze_apk(self.apk)

    def test_missing_dex_rejected(self):
        with ZipFile(self.apk, "w") as archive:
            archive.writestr("assets/decoder.txt", BUFFER)
        with self.assertRaisesRegex(ValueError, "no classes.dex"):
            CHECK.analyze_apk(self.apk)

    def test_malformed_table_rejected(self):
        damaged = bytearray(dex([BUFFER]))
        struct.pack_into("<I", damaged, 68, len(damaged))
        with self.assertRaisesRegex(ValueError, "outside file bounds"):
            CHECK.dex_types(bytes(damaged))

    def test_invalid_class_index_rejected(self):
        damaged = bytearray(dex([BUFFER]))
        class_offset = struct.unpack_from("<I", damaged, 100)[0]
        struct.pack_into("<I", damaged, class_offset, 123)
        with self.assertRaisesRegex(ValueError, "invalid type index"):
            CHECK.dex_types(bytes(damaged))

    def test_invalid_dex_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "DEX header"):
            CHECK.dex_types(b"DecoderInputBuffer")


if __name__ == "__main__":
    unittest.main()
