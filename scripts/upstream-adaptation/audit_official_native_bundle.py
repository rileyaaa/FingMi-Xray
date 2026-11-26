#!/usr/bin/env python3
"""Offline evidence gate for FongMi/mpv-android's public 2026-11 artifacts.

Exit 2 means verified partial evidence, NOT an installable/release candidate.
No dependency installation, download, APK extraction, or execution of native code.
"""
import hashlib
import io
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# Source: public runs 44885769496, 44040032853, 43415749605.
BUNDLES = {
    'mpv-native-14699804350': (43658512, 'f07422157e0f18409084e1bf50352f142d56fca2a7cf71802b6e95621cb9d4f4'),
    'renderer-sdk-14700635872': (14360945, 'd05798ac705e10172fd517b0d0ee718c9bb3e2a0073cd5f0d1baf807dbf8e010'),
    'bdj-14699869160': (2052197, '3730c648dcf2e6bfa69e59dda68e33414b9201d1485337f685f8571d713888cd'),
    'mpv-native-14310565120': (43575008, 'eb7ebb001bcf7fd2f70f6e8e06d7a109fb64b7daeb5700e05fec1f8ce73fb782'),
    'mpv-native-14032452811': (43545891, 'f573841e16ae8b15e3022008e5661ba2e149b3ab8354ca8b4f96f70b40b8c58c'),
}
ABIS = {'arm64-v8a': ('AArch64', 'ELF64'), 'armeabi-v7a': ('ARM', 'ELF32')}
LIBS = {'libffmpeg.so', 'libmpv.so', 'libplayer.so', 'libc++_shared.so'}
SYSTEM = set('libc.so libm.so libdl.so libz.so libandroid.so libmediandk.so liblog.so libvulkan.so libEGL.so libGLESv2.so libOpenSLES.so'.split())
MOTION = 'f964d1495355d5c6626df3de1d3eeb90ddee2aba'
FF_NAMES = re.compile(r'@LIB(?:AV|SW)\w+_\d+$')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def elf(path, flag):
    return subprocess.check_output(['readelf', flag, '-W', str(path)], text=True)


def entries(z):
    names = z.namelist()
    require(len(names) == len(set(names)), 'Duplicate ZIP members')
    return set(names)


def manifest(z, name, prefix=''):
    seen = set()
    for line in z.read(name).decode().splitlines():
        digest, rel = line.split(maxsplit=1)
        path = prefix + rel.removeprefix('./')
        require(path not in seen and sha(z.read(path)) == digest, 'Bad manifest: ' + path)
        seen.add(path)
    return seen


def properties(z, name):
    return dict(line.split('=', 1) for line in z.read(name).decode().splitlines() if line and not line.startswith('#'))


def symbols(path):
    rows = [line.split() for line in elf(path, '--dyn-syms').splitlines()]
    return ({r[7].replace('@@', '@') for r in rows if len(r) >= 8 and r[6] != 'UND' and r[0].endswith(':')},
            {r[7] for r in rows if len(r) >= 8 and r[6] == 'UND' and r[0].endswith(':')})


def check_native(z, tmp):
    require(entries(z) == {a + '/' + n for a in ABIS for n in LIBS}, 'Unexpected native file set')
    blocked = []
    for abi, (machine, klass) in ABIS.items():
        exports, imports = {}, {}
        for name in sorted(LIBS):
            data = z.read(abi + '/' + name)
            p = tmp / name
            p.write_bytes(data)
            header = elf(p, '-h')
            require(re.search(r'Machine:\s+' + machine + r'\s*$', header, re.M) and re.search(r'Class:\s+' + klass + r'\s*$', header, re.M) and 'DYN (Shared object file)' in header, 'Wrong ELF: ' + abi + '/' + name)
            dynamic = elf(p, '-d')
            needed = set(re.findall(r'\(NEEDED\).*?\[([^]]+)\]', dynamic))
            require(re.findall(r'\(SONAME\).*?\[([^]]+)\]', dynamic) == [name] and needed <= LIBS | SYSTEM and not re.search(r'\((RPATH|RUNPATH|TEXTREL)\)', dynamic), 'Bad dynamic contract: ' + name)
            if name in ('libmpv.so', 'libplayer.so'):
                require('libffmpeg.so' in needed, 'Not unified FFmpeg: ' + name)
            loads = [l.split() for l in elf(p, '-l').splitlines() if l.strip().startswith('LOAD ')]
            require(bool(loads), 'Missing PT_LOAD')
            good = all(int(l[-1], 16) >= 16384 and (int(l[1], 16) - int(l[2], 16)) % 16384 == 0 for l in loads)
            if not good:
                blocked.append(abi + '/' + name)
            exports[name], imports[name] = symbols(p)
            print('ELF', abi, name, len(data), sha(data), 'alignment', 'PASS' if good else 'FAIL', 'NEEDED', ','.join(sorted(needed)))
        ff = {s for s in exports['libffmpeg.so'] if FF_NAMES.search(s)}
        require(len(ff) == 1151, 'Unexpected FFmpeg export count')
        for n in ('libmpv.so', 'libplayer.so'):
            req = {s for s in imports[n] if FF_NAMES.search(s)}
            require(req and req <= ff, 'Unresolved versioned FFmpeg imports: ' + n)
            print('LINK', abi, n, len(req), 'versioned FFmpeg imports resolved')
        req = {s for s in imports['libplayer.so'] if s.startswith('mpv_')}
        require(req and req <= exports['libmpv.so'], 'Unresolved MPV bridge imports')
        jni = {s for s in exports['libplayer.so'] if s.startswith('Java_is_xyz_mpv_MPVLib_')}
        require(len(jni) == 24, 'Unexpected MPV JNI export count')
        print('LINK', abi, len(req), 'MPV imports resolved;', len(ff), 'FFmpeg exports;', len(jni), 'JNI exports (names only)')
    return blocked


def check_archive(z, name, machine, tmp):
    p = tmp / 'archive.a'
    data = z.read(name)
    require(data.startswith(b'!<arch>\n'), 'Not a regular archive: ' + name)
    p.write_bytes(data)
    machines = re.findall(r'Machine:\s+([^\n]+)', elf(p, '-h'))
    require(machines and all(x.strip() == machine for x in machines), 'Wrong archive object ABI: ' + name)
    print('ARCHIVE', name, len(machines), 'objects', sha(data))


def check_renderer(z, tmp):
    all_files = manifest(z, 'files.sha256')
    require(len(all_files) == 87 and all_files | {'files.sha256'} == entries(z), 'Incomplete renderer manifest')
    prop = properties(z, 'provenance.properties')
    expected = {'schema.version': '3', 'libplacebo.commit': 'dc98e2fceb82233b3bb75e9c6249e581c57f3f2d', 'libplacebo.api': '399', 'libplacebo.opengl': 'true', 'libplacebo.vulkan': 'true', 'mpv-motion.commit': MOTION, 'android.ndk.version': '30.0.16248370'}
    require(all(prop.get(k) == v for k, v in expected.items()), 'Renderer provenance mismatch')
    require(sha(z.read('LICENSE.mpv-motion')) == prop['mpv-motion.license.sha256'], 'Motion license hash mismatch')
    for abi, (machine, _) in ABIS.items():
        require(len(manifest(z, abi + '/headers.sha256', abi + '/include/')) == 36, 'Header manifest mismatch')
        build = properties(z, abi + '/motion-build.properties')
        for key, name in [('mpv-motion.header.sha256', 'include/mpv-motion/motion.h'), ('mpv-motion.archive.sha256', 'lib/libmpv-motion.a'), ('libplacebo.archive.sha256', 'lib/libplacebo.a'), ('libplacebo.headers.sha256', 'headers.sha256')]:
            require(build[key] == sha(z.read(abi + '/' + name)), 'Motion build mismatch: ' + key)
        for key in ('mpv-motion.commit', 'mpv-motion.source.sha256', 'mpv-motion.header.sha256'):
            require(build[key] == prop[key], 'Motion source pin mismatch: ' + key)
        for name in ('libmpv-motion.a', 'libplacebo.a', 'libshaderc.a'):
            check_archive(z, abi + '/lib/' + name, machine, tmp)
    print('RENDERER', len(all_files), 'manifest entries, 36 headers per ABI, motion source and license pins verified')


def check_bdj(z, tmp):
    jars = {'build/bdj/libbluray-' + n + '-1.4.1.jar' for n in ('j2se', 'awt-j2se')}
    archives = {'prefix/' + a + '/lib/' + n for a in ('arm64', 'armv7l') for n in ('libbluray.a', 'libfreetype.a')}
    require(entries(z) == jars | archives, 'Unexpected BD-J file set')
    for name in sorted(jars):
        with zipfile.ZipFile(io.BytesIO(z.read(name))) as jar:
            require(jar.testzip() is None and any(n.endswith('.class') for n in jar.namelist()), 'Bad jar: ' + name)
    for name in sorted(archives):
        check_archive(z, name, 'AArch64' if '/arm64/' in name else 'ARM', tmp)
    print('BDJ', len(jars), 'JARs and', len(archives), 'archives verified; not full runtime or isoJNI')


def main(directory):
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        blocked = []
        for label, (size, digest) in BUNDLES.items():
            p = directory / ('fongmi-' + label + '.zip')
            require(p.stat().st_size == size and sha(p.read_bytes()) == digest, 'Untrusted artifact: ' + label)
            with zipfile.ZipFile(p) as z:
                require(z.testzip() is None, 'CRC failure: ' + label)
                print('ARTIFACT', label, size, digest)
                if label.endswith('14699804350'):
                    blocked = check_native(z, tmp)
                elif label.startswith('renderer'):
                    check_renderer(z, tmp)
                elif label.startswith('bdj'):
                    check_bdj(z, tmp)
                else:
                    require(entries(z) == {a + '/' + n for a in ABIS for n in LIBS}, 'Historical file set mismatch')
                if label.startswith('mpv-native'):
                    for abi in ABIS:
                        print('PROVENANCE', label, abi, 'ffmpeg', blob(z.read(abi + '/libffmpeg.so')), 'mpv', blob(z.read(abi + '/libmpv.so')), 'player', blob(z.read(abi + '/libplayer.so')))
        require(set(blocked) == {'armeabi-v7a/libc++_shared.so', 'armeabi-v7a/libplayer.so'}, 'Unexpected alignment result')
        print('BLOCKED', ', '.join(blocked), '; consumer Java/JNI and complete license closure not established; no APK validation')
    return 2


if __name__ == '__main__':
    sys.exit(main(Path(sys.argv[1])))
