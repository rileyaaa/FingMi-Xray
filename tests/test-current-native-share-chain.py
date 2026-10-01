#!/usr/bin/env python3
"""Current Java -> published JNI -> current runtime -> published testXray parity.

This executes an exact pinned v7 or arm64 converter/testXray native binary.
Certificate probes and pin persistence are the only deterministic test
boundaries. Both ABIs are compared to the frozen v7 legacy-chain oracle.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'recovery/native-tests'
JARS = {
    'json.jar': (
        'https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar',
        '3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed',
    ),
    'ecj.jar': (
        'https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.40.0/ecj-3.40.0.jar',
        '05cc22a24e7982970f63a405fc6c820bc80b806f27f3c5a6236fc475f8f7152b',
    ),
}


def compare(expected, observed):
    old, new = expected['cases'], observed['cases']
    assert len(old) == len(new), 'native case count changed'
    for a, b in zip(old, new):
        assert (a['id'], a['request'], a['response']) == (
            b['id'], b['request'], b['response']
        ), b['id']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--abi',
        choices=['armeabi-v7a', 'arm64-v8a'],
        default='armeabi-v7a',
    )
    for arg in ('workdir', 'jni', 'bridge', 'qemu', 'android-root'):
        parser.add_argument('--' + arg, type=Path, required=True)
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)

    jars = {}
    for name, (url, digest) in JARS.items():
        path = args.workdir / name
        if not path.exists():
            with urllib.request.urlopen(url, timeout=90) as response:
                path.write_bytes(response.read())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        jars[name] = str(path.resolve())

    spec = importlib.util.spec_from_file_location(
        'published_native',
        ROOT / 'scripts/recovery/run-published-libxray-converter.py',
    )
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)

    with tempfile.TemporaryDirectory(
        prefix='current-native-share-chain-',
        dir=args.workdir,
    ) as directory:
        tmp = Path(directory).resolve()
        classes = tmp / 'classes'
        classes.mkdir()

        current = ROOT / 'xray/src/main/java/com/fingmi/xray'
        support = ROOT / 'tests/xray-current-chain'
        sources = [
            support / 'CurrentNativeChain.java',
            support / 'libXray/LibXray.java',
            support / 'com/fingmi/xray/security/XrayCertificatePins.java',
            current / 'config/XrayShareLinkNormalizer.java',
            current / 'config/XrayConfigFactory.java',
            current / 'core/LibXrayBridge.java',
            current / 'security/XrayShareLinkSecurity.java',
        ]

        subprocess.run(
            [
                'java',
                '-jar',
                jars['ecj.jar'],
                '-17',
                '-cp',
                jars['json.jar'],
                '-d',
                str(classes),
                *map(str, sources),
            ],
            check=True,
        )

        command = [
            'java',
            '-cp',
            jars['json.jar'] + ':' + str(classes),
            'CurrentNativeChain',
        ]
        inputs = str(FIXTURES / 'chain-inputs.json')

        normalized = tmp / 'normalized.json'
        subprocess.run(
            command + ['normalize', inputs, str(normalized)],
            check=True,
        )

        conversion = native.capture(
            json.loads(normalized.read_text()),
            args.jni,
            args.bridge,
            args.qemu,
            args.android_root,
            args.abi,
        )
        compare(
            json.loads((FIXTURES / 'published-v7-chain.json').read_text()),
            conversion,
        )

        actual = tmp / 'native.json'
        actual.write_text(json.dumps(conversion))

        runtime = tmp / 'runtime.json'
        subprocess.run(
            command + ['runtime', inputs, str(actual), str(runtime)],
            check=True,
        )

        validation = native.capture(
            json.loads(runtime.read_text()),
            args.jni,
            args.bridge,
            args.qemu,
            args.android_root,
            args.abi,
        )
        compare(
            json.loads(
                (FIXTURES / 'published-v7-runtime-validation.json').read_text()
            ),
            validation,
        )
        assert all(
            case['response']['success'] for case in validation['cases']
        ), 'published native testXray rejected current runtime config'

        kcp = [
            row
            for row in json.loads((FIXTURES / 'chain-inputs.json').read_text())
            if '-kcp-' in row['id']
        ]
        assert len(kcp) == 6, 'KCP golden chain coverage changed'
        print(
            'PASS: current Java chain '
            f'({args.abi}) matches {len(conversion["cases"])} published v7 '
            'conversion/runtime oracles; '
            f'{len(kcp)} KCP golden cases validated by published testXray'
        )


if __name__ == '__main__':
    main()
