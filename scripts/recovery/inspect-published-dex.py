#!/usr/bin/env python3
"""Print raw DEX code units around a string reference in one class method.

Inspection aid only: DEX code units are not fully disassembled. Branch target
arithmetic is in 16-bit code units; inspect opcode widths before conclusions.
"""

import argparse
import hashlib
import struct
import zipfile


def u16(data, pos):
    return struct.unpack_from('<H', data, pos)[0]


def u32(data, pos):
    return struct.unpack_from('<I', data, pos)[0]


def leb(data, pos):
    result = 0
    for shift in range(0, 35, 7):
        value = data[pos]
        pos += 1
        result |= (value & 0x7f) << shift
        if not value & 0x80:
            return result, pos
    raise ValueError('invalid ULEB128')


def read_dex(archive, member):
    with zipfile.ZipFile(archive) as contents:
        return contents.read(member)


def strings(data):
    count, offset = u32(data, 56), u32(data, 60)
    values = []
    for index in range(count):
        pos = u32(data, offset + 4 * index)
        _, pos = leb(data, pos)
        end = data.index(b'\x00', pos)
        values.append(data[pos:end].decode('utf-8', 'replace'))
    return values


def methods_in_class(data, values, descriptor):
    type_count, type_off = u32(data, 64), u32(data, 68)
    types = [values[u32(data, type_off + i * 4)] for i in range(type_count)]
    method_count, method_off = u32(data, 88), u32(data, 92)
    methods = [(u16(data, method_off + i * 8),
                values[u32(data, method_off + i * 8 + 4)])
               for i in range(method_count)]
    count, offset = u32(data, 96), u32(data, 100)
    for i in range(count):
        pos = offset + 32 * i
        if types[u32(data, pos)] != descriptor:
            continue
        pos = u32(data, pos + 24)
        sizes = []
        for _ in range(4):
            size, pos = leb(data, pos)
            sizes.append(size)
        for _ in range(sizes[0] + sizes[1]):
            _, pos = leb(data, pos)
            _, pos = leb(data, pos)
        for size in sizes[2:]:
            method_id = 0
            for _ in range(size):
                delta, pos = leb(data, pos)
                method_id += delta
                _, pos = leb(data, pos)
                code_off, pos = leb(data, pos)
                yield methods[method_id][1], code_off
        return
    raise ValueError(f'class not found: {descriptor}')


def method_refs(data, values):
    type_count, type_off = u32(data, 64), u32(data, 68)
    types = [values[u32(data, type_off + i * 4)] for i in range(type_count)]
    count, offset = u32(data, 88), u32(data, 92)
    return [types[u16(data, offset + i * 8)] + '->' +
            values[u32(data, offset + i * 8 + 4)] for i in range(count)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', help='published v7/v8 DEX artifact ZIP')
    parser.add_argument('member', help='e.g. v7-dex/classes.dex')
    parser.add_argument('descriptor', help='e.g. Lcom/fongmi/android/tv/xray/XrayService;')
    parser.add_argument('method', help='method name as recorded in the DEX')
    parser.add_argument('needle', help='literal string to find references to')
    parser.add_argument('--at', type=lambda s: int(s, 0),
                        help='print 80 code units centered at this offset')
    parser.add_argument('--decode-from', type=lambda s: int(s, 0))
    parser.add_argument('--decode-to', type=lambda s: int(s, 0))
    args = parser.parse_args()
    data = read_dex(args.archive, args.member)
    print('sha256', hashlib.sha256(data).hexdigest())
    values = strings(data)
    matches = {i for i, s in enumerate(values) if args.needle in s}
    for name, pos in methods_in_class(data, values, args.descriptor):
        if args.method == '*':
            print(name, pos)
            continue
        if name != args.method or not pos:
            continue
        size = u32(data, pos + 12)
        units = [u16(data, pos + 16 + i * 2) for i in range(size)]
        print('code_off', pos, 'insns_size', size)
        if args.decode_from is not None:
            refs = method_refs(data, values)
            i = args.decode_from
            end = min(args.decode_to or i + 60, size)
            while i < end:
                op = units[i] & 0xff
                width = (3 if op in (0x6e, 0x6f, 0x70, 0x71, 0x72,
                                      0x74, 0x75, 0x76, 0x77, 0x78, 0x1b)
                         else 2 if op in (0x1a, 0x13, 0x29, 0x08,
                                           0x22, 0x52, 0x54, 0x56,
                                           0x62, 0x6a, 0x1c) or 0x32 <= op <= 0x3d
                         else 1)
                detail = ''
                if op in (0x6e, 0x6f, 0x70, 0x71, 0x72,
                          0x74, 0x75, 0x76, 0x77, 0x78):
                    detail = refs[units[i + 1]]
                elif op == 0x1a:
                    detail = repr(values[units[i + 1]])
                elif 0x32 <= op <= 0x3d or op == 0x29:
                    delta = struct.unpack('<h', struct.pack('<H', units[i + 1]))[0]
                    detail = f'-> {i + delta:04x}'
                    if op == 0x33:
                        detail = 'if-ne ' + detail
                    elif op == 0x38:
                        detail = 'if-eqz ' + detail
                elif op == 0x12:
                    register = units[i] >> 8 & 0xf
                    literal = units[i] >> 12
                    detail = f'const/4 v{register}, #{literal if literal < 8 else literal - 16}'
                elif op == 0x28:
                    delta = units[i] >> 8
                    detail = f'-> {i + (delta if delta < 128 else delta - 256):04x}'
                print(f'  {i:04x}: ' + ' '.join(f'{v:04x}' for v in units[i:i + width]) +
                      ('  ' + detail if detail else ''))
                i += width
            continue
        if args.at is not None:
            for j in range(max(0, args.at - 60), min(size, args.at + 20)):
                print(f'  {j:04x}: {units[j]:04x}')
            continue
        for i, op in enumerate(units[:-1]):
            if op & 0xff == 0x1a and units[i + 1] in matches:
                print('string', repr(values[units[i + 1]]), 'offset', hex(i))
            elif op & 0xff == 0x1b and i + 2 < size:
                index = units[i + 1] | units[i + 2] << 16
                if index in matches:
                    print('string', repr(values[index]), 'offset', hex(i))
            else:
                continue
            for j in range(max(0, i - 32), min(size, i + 6)):
                print(f'  {j:04x}: {units[j]:04x}')


if __name__ == '__main__':
    main()
