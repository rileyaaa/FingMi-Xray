import importlib.util
from io import BytesIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile


spec = importlib.util.spec_from_file_location(
    "check_libxray", Path(__file__).resolve().parents[2] / "scripts/check-libxray-gojni.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LibXrayGateTest(unittest.TestCase):
    def test_published_jni_and_java_method(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "libXray/LibXray.java"
            src.parent.mkdir()
            src.write_text("package libXray; public class LibXray { "
                           "public static String invoke(String s){return s;} }")
            subprocess.run(["java", "com.sun.tools.javac.Main", "-d", str(root), str(src)],
                           check=True)
            classes = BytesIO()
            with ZipFile(classes, "w") as jar:
                jar.writestr("libXray/LibXray.class",
                             (root / "libXray/LibXray.class").read_bytes())
            aar = root / "libXray.aar"
            values = {abi: f"native-{abi}".encode() for abi in module.PUBLISHED}
            with ZipFile(aar, "w") as archive:
                archive.writestr("classes.jar", classes.getvalue())
                for abi, data in values.items():
                    archive.writestr(f"jni/{abi}/libgojni.so", data)
            expected = {abi: module.hashlib.sha256(data).hexdigest()
                        for abi, data in values.items()}
            with patch.dict(module.PUBLISHED, expected):
                module.check(aar)
                module.PUBLISHED["armeabi-v7a"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "Go JNI SHA-256 differs"):
                    module.check(aar)


if __name__ == "__main__":
    unittest.main()
