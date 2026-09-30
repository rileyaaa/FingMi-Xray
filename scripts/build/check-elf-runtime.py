#!/usr/bin/env python3
"""Compare ELF runtime load images while ignoring strip-only section metadata."""

import argparse
import hashlib
import json
import struct
from pathlib import Path

PT_LOAD = 1
MAX_BYTES = 512 * 1024 * 1024


def _fingerprint_bytes(data: bytes):
    if not data or len(data) > MAX_BYTES:
        raise ValueError(f"invalid ELF size: {len(data)}")
    if data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")

    elf_class = data[4]
    elf_data = data[5]
    if elf_class not in (1, 2) or elf_data != 1:
        raise ValueError(f"unsupported ELF class/data: {elf_class}/{elf_data}")

    machine = struct.unpack_from("<H", data, 18)[0]
    if elf_class == 1:
        phoff = struct.unpack_from("<I", data, 28)[0]
        phentsize = struct.unpack_from("<H", data, 42)[0]
        phnum = struct.unpack_from("<H", data, 44)[0]
        minimum_phentsize = 32
        section_metadata = ((32, 36), (46, 52))
    else:
        phoff = struct.unpack_from("<Q", data, 32)[0]
        phentsize = struct.unpack_from("<H", data, 54)[0]
        phnum = struct.unpack_from("<H", data, 56)[0]
        minimum_phentsize = 56
        section_metadata = ((40, 48), (58, 64))

    if (
        phentsize < minimum_phentsize
        or phnum == 0
        or phoff + phentsize * phnum > len(data)
    ):
        raise ValueError("invalid ELF program header table")

    segments = []
    for index in range(phnum):
        offset = phoff + index * phentsize
        if elf_class == 1:
            (
                p_type,
                p_offset,
                p_vaddr,
                _p_paddr,
                p_filesz,
                p_memsz,
                p_flags,
                p_align,
            ) = struct.unpack_from("<IIIIIIII", data, offset)
        else:
            (
                p_type,
                p_flags,
                p_offset,
                p_vaddr,
                _p_paddr,
                p_filesz,
                p_memsz,
                p_align,
            ) = struct.unpack_from("<IIQQQQQQ", data, offset)

        if p_type != PT_LOAD:
            continue
        end = p_offset + p_filesz
        if end > len(data):
            raise ValueError(f"PT_LOAD {index} exceeds file")

        payload = bytearray(data[p_offset:end])

        # Android Gradle packaging may strip section tables. strip/llvm-strip
        # updates e_shoff/e_shentsize/e_shnum/e_shstrndx in the ELF header,
        # which lives inside the first PT_LOAD, without changing the runtime
        # memory image. Normalize only those non-runtime section-table fields.
        if p_offset == 0:
            for lo, hi in section_metadata:
                if hi <= len(payload):
                    payload[lo:hi] = b"\0" * (hi - lo)

        segments.append(
            {
                "vaddr": p_vaddr,
                "filesz": p_filesz,
                "memsz": p_memsz,
                "flags": p_flags,
                "align": p_align,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    if not segments:
        raise ValueError("ELF has no PT_LOAD segments")

    return {
        "elf_class": 32 if elf_class == 1 else 64,
        "machine": machine,
        "segments": segments,
    }


def fingerprint(path: Path):
    return _fingerprint_bytes(path.read_bytes())


def self_test():
    data = bytearray(512)
    data[:4] = b"\x7fELF"
    data[4] = 2
    data[5] = 1
    struct.pack_into("<H", data, 18, 183)
    struct.pack_into("<Q", data, 32, 64)
    struct.pack_into("<Q", data, 40, 400)
    struct.pack_into("<H", data, 54, 56)
    struct.pack_into("<H", data, 56, 1)
    struct.pack_into("<H", data, 58, 64)
    struct.pack_into("<H", data, 60, 3)
    struct.pack_into("<H", data, 62, 2)
    struct.pack_into("<IIQQQQQQ", data, 64, PT_LOAD, 5, 0, 0, 0, 256, 256, 4096)
    data[192:256] = bytes(range(64))

    stripped = bytearray(data)
    struct.pack_into("<Q", stripped, 40, 0)
    struct.pack_into("<H", stripped, 58, 0)
    struct.pack_into("<H", stripped, 60, 0)
    struct.pack_into("<H", stripped, 62, 0)

    if _fingerprint_bytes(bytes(data)) != _fingerprint_bytes(bytes(stripped)):
        raise AssertionError("section-table metadata normalization failed")

    changed = bytearray(stripped)
    changed[220] ^= 1
    if _fingerprint_bytes(bytes(data)) == _fingerprint_bytes(bytes(changed)):
        raise AssertionError("runtime PT_LOAD mutation was not detected")

    print("PASS ELF runtime fingerprint self-test")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--label", default="ELF")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        if args.reference or args.candidate:
            parser.error("--self-test cannot be combined with file inputs")
        self_test()
        return

    if not args.reference or not args.candidate:
        parser.error("--reference and --candidate are required")

    try:
        reference = fingerprint(args.reference)
        candidate = fingerprint(args.candidate)
    except (OSError, ValueError, struct.error) as error:
        parser.error(str(error))

    if reference != candidate:
        print(
            json.dumps(
                {"label": args.label, "reference": reference, "candidate": candidate},
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(f"{args.label}: runtime PT_LOAD fingerprint mismatch")

    print(
        f"PASS {args.label}: runtime PT_LOAD fingerprint matches "
        f"({len(reference['segments'])} load segments)"
    )


if __name__ == "__main__":
    main()
