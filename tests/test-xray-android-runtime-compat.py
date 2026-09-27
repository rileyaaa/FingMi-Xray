#!/usr/bin/env python3
"""Fail on Java APIs in :xray that can compile on Java 21 but break on older Android ART."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
XRAY = ROOT / "xray/src/main/java"

FORBIDDEN = [
    (re.compile(r"\.isBlank\s*\("), "String.isBlank"),
    (re.compile(r"\.repeat\s*\("), "String.repeat"),
    (re.compile(r"\b(?:Set|List|Map)\.of\s*\("), "Java collection factory"),
    (re.compile(r"\.strip(?:Leading|Trailing)?\s*\("), "String.strip"),
    (re.compile(r"\.formatted\s*\("), "String.formatted"),
    (re.compile(r"\bOptional\.isEmpty\s*\("), "Optional.isEmpty"),
    (re.compile(r"\bMath\.clamp\s*\("), "Math.clamp"),
]

URL_CHARSET = re.compile(
    r"(?:URLDecoder\.decode|URLEncoder\.encode)\s*\([^;]*?StandardCharsets\.UTF_8\s*\)",
    re.DOTALL,
)
STRING_BUILDER_DECL = re.compile(r"\bStringBuilder\s+([A-Za-z_$][A-Za-z0-9_$]*)\b")

APP_XRAY_FORBIDDEN = [
    (re.compile(r"\.isBlank\s*\("), "String.isBlank"),
    (re.compile(r"\.repeat\s*\("), "String.repeat"),
]

errors = []
for path in sorted(XRAY.rglob("*.java")):
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)

    for pattern, name in FORBIDDEN:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{rel}:{line}: forbidden runtime API: {name}")

    for match in URL_CHARSET.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        errors.append(
            f"{rel}:{line}: use the String charset-name overload for URLDecoder/URLEncoder"
        )

    for declaration in STRING_BUILDER_DECL.finditer(text):
        name = declaration.group(1)
        call = re.search(rf"\b{re.escape(name)}\.isEmpty\s*\(", text[declaration.end():])
        if call:
            offset = declaration.end() + call.start()
            line = text.count("\n", 0, offset) + 1
            errors.append(f"{rel}:{line}: StringBuilder.isEmpty is not safe on Android 12")


for path in sorted((ROOT / "app/src").rglob("*.java")):
    text = path.read_text(encoding="utf-8")
    if "com.fingmi.xray" not in text and "XrayImportEvent" not in text:
        continue
    rel = path.relative_to(ROOT)
    for pattern, name in APP_XRAY_FORBIDDEN:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{rel}:{line}: forbidden Xray integration runtime API: {name}")

proguard = (ROOT / "app/proguard-rules.pro").read_text(encoding="utf-8")
for keep_rule in ("-keep class libXray.** { *; }", "-keep class go.** { *; }"):
    if keep_rule not in proguard:
        errors.append(f"missing release JNI keep rule: {keep_rule}")


builder = ROOT / "scripts/build/build-published-libxray-aar.py"
if not builder.is_file():
    errors.append("missing published libXray binding/JNI builder")
else:
    builder_text = builder.read_text(encoding="utf-8")
    for required in (
        "libXray/AgeDecryptConfig.class",
        "libXray/GenerateAgeKeyPairResponse.class",
        "libXray/ProbeTLSCertificateRequest.class",
        "libXray/ProbeHysteria2CertificateRequest.class",
        "libXray/ProbeCertificateResponse.class",
    ):
        if required not in builder_text:
            errors.append(f"published libXray builder missing binding contract: {required}")

for workflow_name in (
    ".github/workflows/current-main-build.yml",
    ".github/workflows/publish-current-main-test-release.yml",
):
    workflow = ROOT / workflow_name
    workflow_text = workflow.read_text(encoding="utf-8")
    if "scripts/build/build-published-libxray-aar.py" not in workflow_text:
        errors.append(f"{workflow_name}: current build must rebuild matching libXray Java bindings and JNI")
    if "scripts/recovery/restore-published-libxrayjni.py" in workflow_text:
        errors.append(f"{workflow_name}: native-only libXray restore would recreate the gomobile binding mismatch")
    if "JADX_SHA256" not in workflow_text:
        errors.append(f"{workflow_name}: JADX input must be pinned for reproducible libXray binding recovery")

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: :xray source avoids known Java runtime APIs that are unsafe on older Android ART")
