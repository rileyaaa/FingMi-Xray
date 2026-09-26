#!/usr/bin/env python3
"""Prepare an isolated Linux x86_64 -> Android ARMv7/arm64 Invoke harness (separate workdir per ABI).

No root, emulator boot, APK build, repository binary commit or JNI modification.
Requires python3, curl, dpkg-deb, debugfs, readelf and ordinary host GCC runtime libs.
All third-party downloads are immutable inputs checked with SHA-256.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

DEB = 'https://deb.debian.org/debian/pool/main/'
INPUTS = {
    'qemu.deb': (DEB + 'q/qemu/qemu-user-static_7.2+dfsg-7+deb12u18+b3_amd64.deb', 'c3e3ba2bd87f8c5b9a5da5ef21b5a3b82d7c63b89dd448d9ddaa4eabc5b6e402'),
    'gcc.deb': (DEB + 'g/gcc-12-cross/gcc-12-arm-linux-gnueabi_12.2.0-14cross1_amd64.deb', '008aa0c2c881ccbb17df94f77a905bc4fbfbb2d71ddeca2069f8bd4ce9da2870'),
    'cpp.deb': (DEB + 'g/gcc-12-cross/cpp-12-arm-linux-gnueabi_12.2.0-14cross1_amd64.deb', '834c4b0abbcb473cc48c28a3e12f9c54a0174a606b7bbd38b61af9780dd3da10'),
    'binutils.deb': (DEB + 'b/binutils/binutils-arm-linux-gnueabi_2.40-2_amd64.deb', 'febda98ec85a9b1b99a3521326ed8fce15a6d1848435d52d432ab43fc9dab570'),
    'libbinutils.deb': (DEB + 'b/binutils/libbinutils_2.40-2_amd64.deb', 'fcf55b99e5f8a78f3c8ce9b6957f1024f394cf20c196b100d308a57e43547710'),
    'android-arm24.zip': ('https://dl.google.com/android/repository/sys-img/android/armeabi-v7a-24_r07.zip', '42690977fe4b97b0643da11a2b42742b2e3d5b8849dcdd6893e0b92d6618c91d'),
}
JNI_SHA = '6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e'
ARM64_INPUTS = dict(INPUTS, **{
    'gcc.deb': (DEB + 'g/gcc-12-cross/gcc-12-aarch64-linux-gnu_12.2.0-14cross1_amd64.deb', '43747bbcd46a4062e66e855090b8ed9c2e06a93ae5a69fb304beebbc8c36d11f'),
    'cpp.deb': (DEB + 'g/gcc-12-cross/cpp-12-aarch64-linux-gnu_12.2.0-14cross1_amd64.deb', '5921df4ad56e34e6257a1caf862474845aab6548ba7ae7852e8cdd7cb622394e'),
    'binutils.deb': (DEB + 'b/binutils/binutils-aarch64-linux-gnu_2.40-2_amd64.deb', '3d6f64a7a4ed6d73719f8fa2e85fd896f58ff7f211a6683942ba93de690aaa66'),
})
ARM64_INPUTS.pop('android-arm24.zip')
ARM64_INPUTS['android-arm64-24.zip'] = ('https://dl.google.com/android/repository/sys-img/android/arm64-v8a-24_r09.zip', '3c3a70dcffe8c162984ec190fc3388bf237b241b3ba80bf7aa5c86e130d8f59b')
ARM64_JNI_SHA = '40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece'
JADX_SHA = '7aab8c3419717516167eba7cf6a6f320df894b9ef554761c0cfc98d90c580e8d'


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--abi', choices=['armeabi-v7a', 'arm64-v8a'], default='armeabi-v7a')
    p.add_argument('--workdir', type=Path, required=True)
    p.add_argument('--parallel', action='store_true', help='Build barrier-synchronized Invoke group harness')
    inp = p.add_mutually_exclusive_group(required=True)
    inp.add_argument('--jni', type=Path)
    inp.add_argument('--v7-jadx', type=Path)
    a = p.parse_args()
    arm64 = a.abi == 'arm64-v8a'
    if arm64 and a.v7_jadx:
        p.error('arm64 requires --jni; the v7 JADX artifact is a different ABI')
    work = a.workdir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    if a.v7_jadx:
        if digest(a.v7_jadx) != JADX_SHA:
            raise ValueError('Not the pinned v7 JADX evidence archive')
        jni = work / 'published-v7-libgojni.so'
        with ZipFile(a.v7_jadx) as z:
            jni.write_bytes(z.read('resources/lib/armeabi-v7a/libgojni.so'))
    else:
        jni = a.jni.resolve()
    if digest(jni) != (ARM64_JNI_SHA if arm64 else JNI_SHA):
        raise ValueError('Not the pinned published JNI for selected ABI')
    for name, (url, sha) in (ARM64_INPUTS if arm64 else INPUTS).items():
        path = work / name
        if not path.exists():
            partial = path.with_suffix(path.suffix + '.partial')
            subprocess.run(['curl', '-fL', '--retry', '2', '--max-time', '300', url, '-o', str(partial)], check=True)
            if digest(partial) != sha:
                raise ValueError(f'Download SHA mismatch: {name}')
            partial.replace(path)
        if digest(path) != sha:
            raise ValueError(f'Cached input SHA mismatch: {name}')
        if name.endswith('.deb'):
            subprocess.run(['dpkg-deb', '-x', str(path), str(work / ('qemu' if name == 'qemu.deb' else 'cross'))], check=True)
    image_name = a.abi + '/system.img'
    image = work / 'android' / image_name
    with ZipFile(work / ('android-arm64-24.zip' if arm64 else 'android-arm24.zip')) as z:
        z.extract(image_name, work / 'android')
    root = work / 'android/root'
    # Re-extract from the checked image, never silently trust a modified runtime.
    if root.exists():
        shutil.rmtree(root)
    (root / 'system/bin').mkdir(parents=True)
    libdir = 'lib64' if arm64 else 'lib'
    linker = 'linker64' if arm64 else 'linker'
    subprocess.run(['debugfs', '-R', f'rdump /{libdir} "{root / "system"}"', str(image)], check=True)
    subprocess.run(['debugfs', '-R', f'dump /bin/{linker} "{root / "system/bin" / linker}"', str(image)], check=True)
    (root / 'system/bin' / linker).chmod(0o755)
    ccdir = work / 'cross/usr/bin'
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(work / 'cross/usr/lib/x86_64-linux-gnu')
    source = Path(__file__).resolve().parents[1] / 'recovery/native-tests' / ('invoke_parallel_bridge.c' if a.parallel else 'invoke_bridge.c')
    bridge = work / ('invoke-parallel-bridge' if a.parallel else 'invoke-bridge')
    subprocess.run([str(ccdir / ('aarch64-linux-gnu-gcc-12' if arm64 else 'arm-linux-gnueabi-gcc-12')), '-B', str(ccdir) + '/',
                    '-nostdlib', '-fPIC', '-fno-stack-protector', '-pie', '-Wl,-e,_start',
                    '-Wl,--dynamic-linker=/system/bin/' + linker, '-Wl,--hash-style=sysv',
                    '-Wl,--allow-shlib-undefined', '-o', str(bridge),
                    str(source), str(jni), str(root / 'system' / libdir / 'libc.so')], env=env, check=True)
    print('JNI:', jni)
    print('Bridge:', bridge)
    print('QEMU:', work / ('qemu/usr/bin/qemu-aarch64-static' if arm64 else 'qemu/usr/bin/qemu-arm-static'))
    print('Android root:', root)


if __name__ == '__main__':
    main()
