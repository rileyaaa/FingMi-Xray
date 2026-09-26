import hashlib
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/restore-published-libxrayjni.py"
spec = importlib.util.spec_from_file_location("restore_libxrayjni", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RestoreLibXrayJniTest(unittest.TestCase):
    ABIS = ("armeabi-v7a", "arm64-v8a")

    def official_aar(self, root):
        path = root / "official.aar"
        with ZipFile(path, "w") as archive:
            archive.writestr("classes.jar", b"classes")
            archive.writestr("AndroidManifest.xml", b"manifest")
            for abi in self.ABIS:
                archive.writestr(f"jni/{abi}/libgojni.so", b"official-" + abi.encode())
            archive.writestr("jni/x86/libgojni.so", b"official-x86")
            archive.writestr("jni/x86_64/libgojni.so", b"official-x86_64")
        return path

    def candidate_apks(self, root, payloads):
        result = {}
        for abi, payload in payloads.items():
            path = root / f"{abi}.apk"
            with ZipFile(path, "w") as archive:
                archive.writestr(f"lib/{abi}/libgojni.so", payload)
            result[abi] = path
        return result

    def candidate_jadx(self, root, payloads):
        result = {}
        for abi, payload in payloads.items():
            path = root / f"{abi}-jadx.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr(f"resources/lib/{abi}/libgojni.so", payload)
            result[abi] = path
        return result

    def assert_restored(self, official, target, payloads):
        with ZipFile(official) as source, ZipFile(target) as rebuilt:
            self.assertEqual(source.namelist(), rebuilt.namelist())
            for name in source.namelist():
                if name == "jni/armeabi-v7a/libgojni.so":
                    self.assertEqual(payloads["armeabi-v7a"], rebuilt.read(name))
                elif name == "jni/arm64-v8a/libgojni.so":
                    self.assertEqual(payloads["arm64-v8a"], rebuilt.read(name))
                else:
                    self.assertEqual(source.read(name), rebuilt.read(name))

    def test_apk_sources_replace_only_v7_v8_jni(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            official = self.official_aar(root)
            payloads = {abi: f"published-{abi}".encode() for abi in self.ABIS}
            sources = self.candidate_apks(root, payloads)
            target = root / "restored.aar"
            with patch.object(
                    module,
                    "OFFICIAL_AAR_SHA256",
                    module.digest(official.read_bytes())),                  patch.dict(
                    module.APK_SHA256,
                    {abi: module.digest(path.read_bytes()) for abi, path in sources.items()}),                  patch.dict(
                    module.JNI_SHA256,
                    {abi: module.digest(data) for abi, data in payloads.items()}):
                hashes = module.restore(
                    official, sources, {abi: "apk" for abi in self.ABIS}, target)
            self.assert_restored(official, target, payloads)
            self.assertEqual(
                hashes,
                {abi: module.digest(data) for abi, data in payloads.items()})

    def test_pinned_jadx_sources_replace_only_v7_v8_jni(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            official = self.official_aar(root)
            payloads = {abi: f"published-{abi}".encode() for abi in self.ABIS}
            sources = self.candidate_jadx(root, payloads)
            target = root / "restored.aar"
            with patch.object(
                    module,
                    "OFFICIAL_AAR_SHA256",
                    module.digest(official.read_bytes())),                  patch.dict(
                    module.JADX_SHA256,
                    {abi: module.digest(path.read_bytes()) for abi, path in sources.items()}),                  patch.dict(
                    module.JNI_SHA256,
                    {abi: module.digest(data) for abi, data in payloads.items()}):
                module.restore(
                    official, sources, {abi: "jadx" for abi in self.ABIS}, target)
            self.assert_restored(official, target, payloads)

    def test_rejects_wrong_official_aar_hash(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            official = self.official_aar(root)
            payloads = {abi: f"published-{abi}".encode() for abi in self.ABIS}
            sources = self.candidate_apks(root, payloads)
            with patch.object(module, "OFFICIAL_AAR_SHA256", "0" * 64):
                with self.assertRaisesRegex(
                        ValueError, "official libXray AAR SHA-256"):
                    module.restore(
                        official,
                        sources,
                        {abi: "apk" for abi in self.ABIS},
                        root / "bad.aar")


if __name__ == "__main__":
    unittest.main()
