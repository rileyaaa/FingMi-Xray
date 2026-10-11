#!/usr/bin/env python3
"""Compile real class fixtures and reject missing Media3 runtime dependencies."""

from io import BytesIO
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/build"))
from media3_class_linkage import class_links, verify_media3_linkage
from player_candidate import REQUIRED_AARS, SOURCE_COMMIT, read_verified_candidate


def aar(classes, namespace="androidx.media3.exoplayer", resources=b""):
    jar_data = BytesIO()
    with ZipFile(jar_data, "w") as jar:
        for name, data in classes.items():
            jar.writestr(name + ".class", data)
    result = BytesIO()
    with ZipFile(result, "w") as bundle:
        bundle.writestr("classes.jar", jar_data.getvalue())
        bundle.writestr("AndroidManifest.xml", f'<manifest package="{namespace}"/>')
        bundle.writestr("R.txt", resources)
    return result.getvalue()


class LinkageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="media3-class-linkage-")
        work = Path(cls.temporary.name)
        sources = {
            "decoder/DecoderInputBuffer": "public class DecoderInputBuffer {}",
            "decoder/CryptoInfo": "public class CryptoInfo {}",
            "container/Mp4Box": "public class Mp4Box {}",
            "mpvplayer/MpvPlayer": "public class MpvPlayer {}",
            "exoplayer/trackselection/DecodeTrackSelector": "public class DecodeTrackSelector {}",
            "exoplayer/source/preload/MediaSourceFactorySupplier": "public class MediaSourceFactorySupplier {}",
            "decoder/mpegh/MpeghAudioRenderer": "public class MpeghAudioRenderer {}",
            "exoplayer/R": "public class R { public static class raw { public static int shader; } }",
            "exoplayer/Player": """public class Player {
                public androidx.media3.decoder.DecoderInputBuffer buffer =
                    new androidx.media3.decoder.DecoderInputBuffer();
                public androidx.media3.decoder.CryptoInfo[] crypto;
                public androidx.media3.container.Mp4Box box;
                public int shader() { return R.raw.shader; }
                public String optional() { return "androidx/media3/optional/NotInstalled"; }
            }""",
        }
        paths = []
        for name, body in sources.items():
            source = work / (name + ".java")
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("package androidx.media3." + name.rsplit("/", 1)[0].replace("/", ".") + "; " + body)
            paths.append(str(source))
        subprocess.run([shutil.which("javac") or "javac", "--release", "17", "-d", str(work / "classes"), *paths], check=True)
        cls.classes = {str(path.relative_to(work / "classes"))[:-6]: path.read_bytes()
                       for path in (work / "classes").rglob("*.class")}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def payload(self, missing=()):
        classes = {name: data for name, data in self.classes.items() if name not in missing}
        return {"player.aar": aar(classes)}

    def test_complete_real_classfiles_and_string_literal(self):
        report = verify_media3_linkage(self.payload())
        self.assertEqual(len(self.classes), report["classes"])

    def test_actual_decoder_class_must_exist(self):
        with self.assertRaisesRegex(ValueError, "missing Media3.*DecoderInputBuffer"):
            verify_media3_linkage(self.payload(("androidx/media3/decoder/DecoderInputBuffer",)))

    def test_field_only_array_dependency_must_exist(self):
        with self.assertRaisesRegex(ValueError, "missing Media3.*CryptoInfo"):
            verify_media3_linkage(self.payload(("androidx/media3/decoder/CryptoInfo",)))

    def test_documented_container_boundary_only_when_explicit(self):
        payload = self.payload(("androidx/media3/container/Mp4Box",))
        with self.assertRaisesRegex(ValueError, "missing Media3.*Mp4Box"):
            verify_media3_linkage(payload)
        verify_media3_linkage(payload, external_container=True)
        with self.assertRaisesRegex(ValueError, "missing Media3.*DecoderInputBuffer"):
            verify_media3_linkage(self.payload(("androidx/media3/decoder/DecoderInputBuffer",)), external_container=True)

    def test_only_owned_android_resource_types_are_generated(self):
        classes = {name: data for name, data in self.classes.items()
                   if name not in ("androidx/media3/exoplayer/R", "androidx/media3/exoplayer/R$raw")}
        with self.assertRaisesRegex(ValueError, r"missing Media3.*R\$raw"):
            verify_media3_linkage({"player.aar": aar(classes)})
        verify_media3_linkage({"player.aar": aar(classes, resources=b"int raw shader 0x0\n")})
        with self.assertRaisesRegex(ValueError, r"missing Media3.*R\$raw"):
            verify_media3_linkage({"player.aar": aar(classes, namespace="androidx.media3.other", resources=b"int raw shader 0x0\n")})

    def test_duplicate_class_owners_rejected(self):
        payload = self.payload()
        payload["duplicate.aar"] = payload["player.aar"]
        with self.assertRaisesRegex(ValueError, "duplicate Media3 class"):
            verify_media3_linkage(payload)

    def test_class_path_disagreement_rejected(self):
        with self.assertRaisesRegex(ValueError, "class name disagrees"):
            verify_media3_linkage({"bad.aar": aar({"androidx/media3/Wrong": next(iter(self.classes.values()))})})

    def test_truncated_class_rejected(self):
        with self.assertRaisesRegex(ValueError, "truncated class"):
            class_links(next(iter(self.classes.values()))[:19])

    def test_candidate_entry_point_checks_all_links_after_count_and_hashes(self):
        def candidate(classes, path):
            payload = {name: aar({}) for name in REQUIRED_AARS}
            payload["lib-common-release.aar"] = aar(classes)
            lines = [f"FongMi/media @ {SOURCE_COMMIT}"]
            lines.extend(f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in sorted(payload.items()))
            with ZipFile(path, "w") as bundle:
                bundle.writestr("BUILD_MANIFEST.txt", "\n".join(lines) + "\n")
                for name, data in payload.items():
                    bundle.writestr(name, data)

        path = Path(self.temporary.name) / "candidate.zip"
        candidate(self.classes, path)
        self.assertEqual(18, len(read_verified_candidate(path)))
        # Count, filenames, source, manifest digests and every anchor still pass.
        # Only checking actual cross-class links can reject this missing type.
        candidate({name: data for name, data in self.classes.items()
                   if name != "androidx/media3/decoder/CryptoInfo"}, path)
        with self.assertRaisesRegex(ValueError, "missing Media3.*CryptoInfo"):
            read_verified_candidate(path)


if __name__ == "__main__":
    unittest.main()
