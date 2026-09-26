import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile


spec = importlib.util.spec_from_file_location(
    "restore_libxrayjni", Path(__file__).resolve().parents[2] / "scripts/restore-published-libxrayjni.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RestoreLibXrayJniTest(unittest.TestCase):
    def test_exact_replacement_and_rejections(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            apk_paths = {}
            for abi in module.APK_SHA256:
                apk = base / f"{abi}.apk"
                with ZipFile(apk, "w") as archive:
                    archive.writestr(f"lib/{abi}/libgojni.so", f"published-{abi}".encode())
                apk_paths[abi] = apk
            pinned = dict(module.APK_SHA256)
            pinned_jni = dict(module.JNI_SHA256)
            try:
                module.APK_SHA256 = {
                    abi: module.digest(path.read_bytes()) for abi, path in apk_paths.items()
                }
                module.JNI_SHA256 = {
                    abi: module.digest(f"published-{abi}".encode()) for abi in apk_paths
                }
                aar = base / "official.aar"
                with ZipFile(aar, "w") as archive:
                    archive.writestr("classes.jar", b"classes")
                    for abi in module.APK_SHA256:
                        archive.writestr(f"jni/{abi}/libgojni.so", b"candidate")
                target = base / "restored.aar"
                hashes = module.restore(aar, apk_paths, target)
                with ZipFile(target) as archive:
                    self.assertEqual(archive.read("classes.jar"), b"classes")
                    for abi in module.APK_SHA256:
                        self.assertEqual(archive.read(f"jni/{abi}/libgojni.so"),
                                         f"published-{abi}".encode())
                        self.assertEqual(hashes[abi], module.digest(f"published-{abi}".encode()))
                with self.assertRaisesRegex(ValueError, "overwrite"):
                    module.restore(aar, apk_paths, target)
                module.JNI_SHA256["armeabi-v7a"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "Go JNI SHA-256"):
                    module.restore(aar, apk_paths, base / "wrong-native.aar")
                self.assertFalse((base / "wrong-native.aar").exists())
                module.JNI_SHA256["armeabi-v7a"] = module.digest(b"published-armeabi-v7a")
                with apk_paths["armeabi-v7a"].open("ab") as stream:
                    stream.write(b"tamper")
                with self.assertRaisesRegex(ValueError, "APK SHA-256"):
                    module.restore(aar, apk_paths, base / "bad.aar")
                self.assertFalse((base / "bad.aar").exists())
            finally:
                module.APK_SHA256 = pinned
                module.JNI_SHA256 = pinned_jni


if __name__ == "__main__":
    unittest.main()
