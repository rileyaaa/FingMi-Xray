#!/usr/bin/env python3
"""Fail on Java APIs which can compile on Java 21 but break on older Android ART."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
XRAY = ROOT / "xray/src/main/java"
RUNTIME_ROOTS = [
    ROOT / "app/src",
    ROOT / "xray/src/main/java",
    ROOT / "catvod/src/main/java",
    ROOT / "chaquo/src/main/java",
    ROOT / "quickjs/src/main/java",
    ROOT / "forcetech/src/main/java",
    ROOT / "hook/src/main/java",
    ROOT / "jianpian/src/main/java",
    ROOT / "thunder/src/main/java",
    ROOT / "tvbus/src/main/java",
    ROOT / "zlive/src/main/java",
]

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

GENERAL_FORBIDDEN = [
    (re.compile(r"\.isBlank\s*\("), "String.isBlank"),
    (re.compile(r"\.repeat\s*\("), "String.repeat"),
    (re.compile(r"\.strip(?:Leading|Trailing)?\s*\("), "String.strip"),
    (re.compile(r"\.formatted\s*\("), "String.formatted"),
    (re.compile(r"\bMath\.clamp\s*\("), "Math.clamp"),
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


seen = set()
for source_root in RUNTIME_ROOTS:
    if not source_root.exists():
        continue
    for path in sorted(source_root.rglob("*.java")):
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)

        for pattern, name in GENERAL_FORBIDDEN:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: forbidden old-Android runtime API: {name}")

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
                errors.append(f"{rel}:{line}: StringBuilder.isEmpty is not safe on older Android ART")

proguard = (ROOT / "app/proguard-rules.pro").read_text(encoding="utf-8")
for keep_rule in ("-keep class libXray.** { *; }", "-keep class go.** { *; }"):
    if keep_rule not in proguard:
        errors.append(f"missing release JNI keep rule: {keep_rule}")

if errors:
    raise SystemExit("\n".join(errors))

print("PASS: current Android runtime source avoids known Java APIs that are unsafe on older ART")
