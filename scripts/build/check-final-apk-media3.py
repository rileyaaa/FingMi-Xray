#!/usr/bin/env python3
"""Check Media3 class linkage in every DEX of the actual packaged APK.

Local AAR files do not carry Gradle transitive dependencies. Compilation can
complete when javac does not resolve missing transitive classes and R8 warnings
are suppressed, while the installed APK lacks those classes. Read type_ids and
class_defs, not DEX strings: a reference is not a packaged implementation.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from zipfile import BadZipFile, ZipFile


MEDIA3 = "Landroidx/media3/"
# These public/JNI buffer classes have explicit keep rules in the application.
REQUIRED_DEFINITIONS = {
    MEDIA3 + "decoder/DecoderInputBuffer;",
    MEDIA3 + "decoder/SimpleDecoderOutputBuffer;",
    MEDIA3 + "decoder/VideoDecoderOutputBuffer;",
}
DEX_NAME = re.compile(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex")


def dex_types(data: bytes):
    if len(data) < 112 or not re.fullmatch(rb"dex\n0(?:3[5-9]|40)\x00", data[:8]):
        raise ValueError("invalid or unsupported DEX header (expected version 035–040)")

    def uint(offset):
        if offset < 0 or offset + 4 > len(data):
            raise ValueError("DEX integer is outside file bounds")
        return struct.unpack_from("<I", data, offset)[0]

    if uint(32) != len(data) or uint(36) != 112 or uint(40) != 0x12345678:
        raise ValueError("invalid DEX size, header size, or byte order")

    def table(header_offset, item_size):
        count, offset = uint(header_offset), uint(header_offset + 4)
        if count and (offset < 112 or offset + count * item_size > len(data)):
            raise ValueError("DEX table is outside file bounds")
        return [offset + i * item_size for i in range(count)]

    strings = table(56, 4)

    def descriptor(string_index):
        if string_index >= len(strings):
            raise ValueError("DEX type has an invalid string index")
        offset = uint(strings[string_index])
        # string_data starts with an unsigned LEB128 UTF-16 length.
        for _ in range(5):
            if offset >= len(data):
                raise ValueError("truncated DEX string length")
            byte = data[offset]
            offset += 1
            if not byte & 128:
                break
        else:
            raise ValueError("invalid DEX string length")
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError("unterminated DEX type descriptor")
        # All Media3 descriptors are ASCII. Replacement for unrelated modified
        # UTF-8 names does not affect the package whose closure is checked here.
        return data[offset:end].decode("utf-8", errors="replace")

    types = [descriptor(uint(offset)) for offset in table(64, 4)]
    definitions = set()
    for offset in table(96, 32):
        index = uint(offset)
        if index >= len(types):
            raise ValueError("DEX class has an invalid type index")
        name = types[index]
        if not name.startswith("L") or not name.endswith(";"):
            raise ValueError("invalid DEX class descriptor")
        if name in definitions:
            raise ValueError("duplicate DEX class definition: " + name)
        definitions.add(name)
    references = {name.lstrip("[") for name in types
                  if name.lstrip("[").startswith(MEDIA3)}
    return definitions, references


def analyze_apk(apk: Path):
    definitions, references = set(), set()
    dex_counts = {}
    with ZipFile(apk) as archive:
        names = [name for name in archive.namelist() if DEX_NAME.fullmatch(name)]
        if "classes.dex" not in names:
            raise ValueError("APK has no classes.dex")
        if len(names) != len(set(names)):
            raise ValueError("APK has duplicate DEX entries")
        for name in sorted(names):
            current, referenced = dex_types(archive.read(name))
            duplicates = definitions & current
            if duplicates:
                raise ValueError("duplicate APK class definitions: " + ", ".join(sorted(duplicates)))
            definitions.update(current)
            references.update(referenced)
            dex_counts[name] = len(current)
    return {
        "apk": str(apk),
        "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
        "dex_class_counts": dex_counts,
        "media3_referenced_types": len(references),
        "missing_referenced_types": sorted(references - definitions),
        "missing_required_definitions": sorted(REQUIRED_DEFINITIONS - definitions),
    }


def require_complete(report):
    missing = set(report["missing_referenced_types"]) | set(report["missing_required_definitions"])
    if missing:
        raise ValueError("Media3 types lack APK class definitions: " + ", ".join(sorted(missing)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, action="append", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    reports = []
    try:
        for apk in args.apk:
            reports.append(analyze_apk(apk))
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
        for report in reports:
            require_complete(report)
            print(f"PASS final Media3 DEX linkage: {report['apk']}; "
                  f"{len(report['dex_class_counts'])} DEX files; "
                  f"{report['media3_referenced_types']} Media3 types defined")
    except (OSError, BadZipFile, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
