#!/usr/bin/env python3
"""Recovery Java -> actual published converter -> runtime -> native testXray.

Synthetic certificate probe and memory store; no Android Keystore, ART, network
certificate handshake or playback assertions. Expected native responses are
frozen independently. Current Java runtime output is never promoted to expected.
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
    'json.jar': ('https://repo.maven.apache.org/maven2/org/json/json/20240303/json-20240303.jar',
                 '3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'),
    'ecj.jar': ('https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.40.0/ecj-3.40.0.jar',
                '05cc22a24e7982970f63a405fc6c820bc80b806f27f3c5a6236fc475f8f7152b'),
}


def compare(expected, observed):
    old, new = expected['cases'], observed['cases']
    assert len(old) == len(new), 'native case count changed'
    for a, b in zip(old, new):
        assert (a['id'], a['request'], a['response']) == (b['id'], b['request'], b['response']), b['id']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('workdir', 'jni', 'bridge', 'qemu', 'android-root'):
        p.add_argument('--' + arg, type=Path, required=True)
    a = p.parse_args()
    a.workdir.mkdir(parents=True, exist_ok=True)
    jars = {}
    for name, (url, digest) in JARS.items():
        path = a.workdir / name
        if not path.exists():
            with urllib.request.urlopen(url, timeout=90) as r:
                path.write_bytes(r.read())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        jars[name] = str(path.resolve())
    spec = importlib.util.spec_from_file_location('published_native', ROOT / 'scripts/recovery/run-published-libxray-converter.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    with tempfile.TemporaryDirectory(prefix='native-share-chain-', dir=a.workdir) as tmp:
        tmp = Path(tmp).resolve()
        classes = tmp / 'classes'
        classes.mkdir()
        legacy = ROOT / 'recovery/legacy-src/com/fongmi/android/tv/xray/legacy'
        sources = list((FIXTURES / 'java').rglob('*.java')) + [legacy / (n + '.java') for n in (
            'LegacyLibXrayApi', 'LegacyXrayProbeApi', 'LegacyXrayShareLinkNormalizer',
            'LegacyXrayTransportSecurity', 'LegacyXrayRuntimeConfigFactory')]
        subprocess.run(['java', '-jar', jars['ecj.jar'], '-17', '-cp', jars['json.jar'], '-d', str(classes),
                        *map(str, sources)], check=True)
        command = ['java', '-cp', jars['json.jar'] + ':' + str(classes), 'NativeChain']
        inputs = str(FIXTURES / 'chain-inputs.json')
        normalized = tmp / 'normalized.json'
        subprocess.run(command + ['normalize', inputs, str(normalized)], check=True)
        conversion = native.capture(json.loads(normalized.read_text()), a.jni, a.bridge, a.qemu, a.android_root)
        compare(json.loads((FIXTURES / 'published-v7-chain.json').read_text()), conversion)
        actual = tmp / 'native.json'
        actual.write_text(json.dumps(conversion))
        runtime = tmp / 'runtime.json'
        subprocess.run(command + ['runtime', inputs, str(actual), str(runtime)], check=True)
        validation = native.capture(json.loads(runtime.read_text()), a.jni, a.bridge, a.qemu, a.android_root)
        compare(json.loads((FIXTURES / 'published-v7-runtime-validation.json').read_text()), validation)
        assert all(c['response']['success'] for c in validation['cases']), 'native testXray rejected runtime'
        print(f'PASS: {len(conversion["cases"])} Java/native/runtime chains and inline native testXray validations')


if __name__ == '__main__':
    main()
