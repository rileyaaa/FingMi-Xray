#!/usr/bin/env python3
"""Capture/replay the actual pinned ARMv7 Android Go JNI Invoke dispatcher.

The supplied bridge must be built from recovery/native-tests/invoke_bridge.c
and dynamically link the exact absolute --jni path (verified using readelf).
This is native conversion evidence, not ART/JNI lifecycle or device playback QA.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

PIN = '6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e'


def capture(cases, jni, bridge, qemu, android_root, abi='armeabi-v7a'):
    pin = PIN if abi == 'armeabi-v7a' else '40b08a399871973ba6ad5898ca7097961337d7aeddb4b3378b153a66679eeece'
    if abi not in ('armeabi-v7a', 'arm64-v8a'): raise ValueError('Unsupported ABI')
    jni, bridge, qemu, android_root = map(Path, (jni, bridge, qemu, android_root))
    jni, bridge, qemu, android_root = (p.resolve() for p in (jni, bridge, qemu, android_root))
    if hashlib.sha256(jni.read_bytes()).hexdigest() != pin:
        raise ValueError('Refusing non-published JNI for selected ABI')
    dynamic = subprocess.check_output(['readelf', '-d', str(bridge)], text=True)
    if f'Shared library: [{jni}]' not in dynamic:
        raise ValueError('Bridge must link the exact absolute JNI path; rebuild it')
    ids = [c['id'] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate case IDs')
    with tempfile.TemporaryDirectory(prefix='published-converter-') as tmp:
        tmp = Path(tmp)
        with (tmp / 'input').open('wb') as f:
            for case in cases:
                request = case['request']
                raw = (request if isinstance(request, str) else json.dumps(request, ensure_ascii=True)).encode()
                f.write(struct.pack('<I', len(raw)) + raw)
        env = os.environ.copy()
        env['NATIVE_CAPTURE'] = str(tmp / 'output')
        command = ['sh', '-c', 'exec "$@" 3>"$NATIVE_CAPTURE"', 'sh', str(qemu),
                   '-L', str(android_root), '-E', 'LD_LIBRARY_PATH=' + str(android_root / 'system' / ('lib64' if abi == 'arm64-v8a' else 'lib')),
                   str(bridge)]
        with (tmp / 'input').open('rb') as inp, (tmp / 'stderr').open('wb') as err:
            result = subprocess.run(command, stdin=inp, stdout=subprocess.DEVNULL,
                                    stderr=err, env=env, timeout=90)
        if result.returncode:
            raise RuntimeError(f'Native bridge exited {result.returncode}: {(tmp / "stderr").read_text()}')
        data = (tmp / 'output').read_bytes()
        results = []
        for case in cases:
            if len(data) < 4:
                raise ValueError(f'Missing response for {case["id"]}')
            size = struct.unpack('<I', data[:4])[0]
            if size > len(data) - 4 or size & 1:
                raise ValueError('Truncated or malformed UTF-16 native response')
            raw = data[4:4 + size].decode('utf-16le')
            results.append({'id': case['id'], 'request': case['request'],
                            'response': json.loads(raw), 'raw_response': raw})
            data = data[4 + size:]
        if data:
            raise ValueError('Unexpected extra native responses')
    return {'schema': 1, 'evidence': {'kind': 'published-native-execution', 'abi': abi,
            'jni_sha256': pin, 'route': 'gomobile proxylibXray__Invoke -> libxray.Invoke',
            'runtime': 'QEMU user-mode ' + abi + ' + Android API24 Bionic',
            'limits': 'No ART, Java normalizer, certificate network probe or playback in this capture'},
            'cases': results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--abi', choices=['armeabi-v7a', 'arm64-v8a'], default='armeabi-v7a')
    p.add_argument('--cases', type=Path, required=True)
    p.add_argument('--jni', type=Path, required=True)
    p.add_argument('--bridge', type=Path, required=True)
    p.add_argument('--qemu', type=Path, required=True)
    p.add_argument('--android-root', type=Path, required=True)
    out = p.add_mutually_exclusive_group(required=True)
    out.add_argument('--capture', type=Path, help='Create a new oracle; refuses overwrite')
    out.add_argument('--expected', type=Path, help='Compare parsed responses, preserving array order')
    a = p.parse_args()
    observed = capture(json.loads(a.cases.read_text()), a.jni, a.bridge, a.qemu, a.android_root, a.abi)
    if a.capture:
        with a.capture.open('x') as f:
            json.dump(observed, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f'Captured {len(observed["cases"])} actual published native responses')
    else:
        expected = json.loads(a.expected.read_text())
        if expected['evidence']['jni_sha256'] != observed['evidence']['jni_sha256']:
            raise ValueError('Expected fixture is not pinned to this release')
        old, new = expected['cases'], observed['cases']
        if len(old) != len(new):
            raise AssertionError('Case count differs')
        failures = [b['id'] for a, b in zip(old, new)
                    if (a['id'], a['request'], a['response']) != (b['id'], b['request'], b['response'])]
        if failures:
            raise AssertionError(f'Native regression: {failures}')
        print(f'PASS: {len(new)} published native responses match frozen oracle')


if __name__ == '__main__':
    main()

