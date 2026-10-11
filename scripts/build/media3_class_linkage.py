#!/usr/bin/env python3
"""Validate Media3 symbolic class dependencies in a set of unshrunk AARs.

This reads class-file type/descriptor references, not arbitrary UTF-8 strings.
Android R classes are accounted for only when the owning AAR manifest and R.txt
declare their namespace/resource type. Other Android/Maven packages are outside
this Media3-local check; the final APK DEX verifier checks the packaged result.
"""

from io import BytesIO
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

PREFIX = "androidx/media3/"


def class_links(data: bytes) -> tuple[str, set[str]]:
    """Return this class and symbolic classes from its constant pool/signatures."""
    position = 0

    def take(size):
        nonlocal position
        value = data[position:position + size]
        if len(value) != size:
            raise ValueError("truncated class file")
        position += size
        return value

    def uint(size):
        return int.from_bytes(take(size), "big")

    if take(4) != b"\xca\xfe\xba\xbe":
        raise ValueError("invalid class magic")
    take(4)
    pool = [None] * uint(2)
    index = 1
    while index < len(pool):
        tag = uint(1)
        if tag == 1:
            # Modified UTF-8 strings may contain Java's surrogate encoding.
            # Relevant JVM internal names/descriptors are ASCII in this input.
            value = take(uint(2)).decode("utf-8", errors="replace")
        elif tag in (7, 8, 16, 19, 20):
            value = uint(2)
        elif tag in (9, 10, 11, 12, 17, 18):
            value = (uint(2), uint(2))
        elif tag in (3, 4):
            value = take(4)
        elif tag in (5, 6):
            value = take(8)
        elif tag == 15:
            value = (uint(1), uint(2))
        else:
            raise ValueError(f"unsupported class constant tag {tag}")
        pool[index] = (tag, value)
        index += 2 if tag in (5, 6) else 1

    def entry(index, tag):
        if not 0 < index < len(pool) or not pool[index] or pool[index][0] != tag:
            raise ValueError(f"invalid class constant index {index} for tag {tag}")
        return pool[index][1]

    references = set()

    def descriptor(value):
        references.update(re.findall(r"L([^;]+);", value))

    for constant in pool:
        if constant is None:
            continue
        tag, value = constant
        if tag == 7:
            name = entry(value, 1)
            if name.startswith("["):
                descriptor(name)
            else:
                references.add(name)
        elif tag == 12:
            descriptor(entry(value[1], 1))
        elif tag == 16:
            descriptor(entry(value, 1))

    take(2)  # access flags
    name = entry(entry(uint(2), 7), 1)
    take(2)  # superclass is already a CONSTANT_Class reference
    take(2 * uint(2))  # interfaces, likewise
    for _ in range(2):  # fields, then methods
        for _ in range(uint(2)):
            take(4)  # access flags and name
            descriptor(entry(uint(2), 1))
            for _ in range(uint(2)):
                take(2)
                take(uint(4))
    return name, {reference for reference in references if reference.startswith(PREFIX)}


def verify_media3_linkage(payload: dict[str, bytes], *, external_container=False) -> dict:
    owners = {}
    references = {}
    generated = set()
    for filename, content in sorted(payload.items()):
        with ZipFile(BytesIO(content)) as aar:
            try:
                manifest = ET.fromstring(aar.read("AndroidManifest.xml"))
            except ET.ParseError as error:
                raise ValueError(f"invalid AAR manifest: {filename}: {error}") from error
            namespace = manifest.get("package", "").replace(".", "/")
            if namespace.startswith(PREFIX) and "R.txt" in aar.namelist():
                generated.add(namespace + "/R")
                for line in aar.read("R.txt").decode().splitlines():
                    fields = line.split()
                    if len(fields) >= 3:
                        generated.add(namespace + "/R$" + fields[1])
            for jarname in aar.namelist():
                if jarname != "classes.jar" and not (jarname.startswith("libs/") and jarname.endswith(".jar")):
                    continue
                with ZipFile(BytesIO(aar.read(jarname))) as jar:
                    for path in jar.namelist():
                        if not (path.startswith(PREFIX) and path.endswith(".class")):
                            continue
                        name, links = class_links(jar.read(path))
                        if name + ".class" != path:
                            raise ValueError(f"class name disagrees with archive path: {filename}: {path}")
                        if name in owners:
                            raise ValueError(f"duplicate Media3 class {name}: {owners[name]}, {filename}")
                        owners[name] = filename
                        references[name] = links
    missing = {}
    for name, links in references.items():
        for reference in links - owners.keys() - generated:
            if external_container and reference.startswith(PREFIX + "container/"):
                continue
            missing.setdefault(reference, []).append(name)
    if missing:
        detail = "; ".join(f"{name} (from {sorted(users)[0]})" for name, users in sorted(missing.items()))
        raise ValueError("missing Media3 bytecode dependencies: " + detail)
    return {"classes": len(owners), "symbolic_references": sum(map(len, references.values())),
            "external_container": external_container}
