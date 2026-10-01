#!/usr/bin/env python3
"""Apply the scoped recovered share patch to its pinned upstream and compare real native fixtures.

This deliberately calls the conversion handler directly, not the still-official
API dispatcher. It does not claim to rebuild the complete published API v2 JNI.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / 'recovery/libxray'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workdir', type=Path, required=True)
    p.add_argument('--go', default='go', help='Go 1.26.3 executable')
    p.add_argument('--source-archive', type=Path)
    a = p.parse_args()
    a.workdir = a.workdir.resolve()
    a.workdir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((RECOVERY / 'upstream.json').read_text())
    version = subprocess.check_output([a.go, 'version'], text=True)
    assert 'go' + manifest['go_version'] + ' ' in version, version
    for filename, digest in manifest['fixtures'].items():
        f = ROOT / 'recovery/native-tests' / filename
        assert hashlib.sha256(f.read_bytes()).hexdigest() == digest, filename
    archive = a.source_archive or a.workdir / 'libxray-upstream.tar.gz'
    if not archive.exists():
        with urllib.request.urlopen(manifest['upstream_archive_url'], timeout=90) as r:
            archive.write_bytes(r.read())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['upstream_archive_sha256']
    env = os.environ.copy()
    env.setdefault('GOMODCACHE', str(a.workdir / 'gomod'))
    env.setdefault('GOCACHE', str(a.workdir / 'gocache'))
    go = str(Path(a.go).resolve()) if '/' in a.go else a.go
    with tempfile.TemporaryDirectory(prefix='recovered-libxray-', dir=a.workdir) as tmp:
        with tarfile.open(archive) as tar:
            tar.extractall(tmp, filter='data')
        children = list(Path(tmp).iterdir())
        assert len(children) == 1 and children[0].is_dir()
        source = children[0]
        with (RECOVERY / 'share-converter-recovery.patch').open('rb') as patch:
            subprocess.run(['patch', '-p1', '--batch', '--fuzz=0'], stdin=patch, cwd=source, check=True)
        shutil.copyfile(RECOVERY / 'recovered_native_test.go', source / 'recovered_native_test.go')
        subprocess.run([go, 'test', './share', '-count=1'], cwd=source, env=env, check=True)
        count = 0
        for filename in ['published-v7.json', 'published-v7-boundary.json', 'published-v7-chain.json']:
            fixture = ROOT / 'recovery/native-tests' / filename
            env['PUBLISHED_CONVERTER_FIXTURE'] = str(fixture)
            subprocess.run([go, 'test', '.', '-run', '^TestRecoveredPublishedConverter$', '-count=1'],
                           cwd=source, env=env, check=True)
            for row in json.loads(fixture.read_text())['cases']:
                req = row['request']
                count += isinstance(req, dict) and req.get('apiVersion') == 2 and req.get('method') == 'convertShareLinksToXrayJson'
        print(f'PASS: scoped Go recovery matches {count} actual published conversion responses; upstream share tests pass')


if __name__ == '__main__':
    main()
