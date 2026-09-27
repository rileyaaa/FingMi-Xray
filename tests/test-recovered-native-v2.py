#!/usr/bin/env python3
"""Run targeted native recovery tests; does not rerun the converter matrix."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--go', default='go')
    parser.add_argument('--run', default='^TestPublished')
    args = parser.parse_args()
    assert hashlib.sha256(args.source_archive.read_bytes()).hexdigest() == '1596603887679f7ac6cca99eb27ecb9153fb4ccc7828c1eacd4d07bcb6d94998'
    go = str(Path(args.go).resolve()) if '/' in args.go else args.go
    assert 'go1.26.3 ' in subprocess.check_output([go, 'version'], text=True)
    with tempfile.TemporaryDirectory(prefix='native-v2-') as directory:
        with tarfile.open(args.source_archive) as archive:
            archive.extractall(directory, filter='data')
        source, = Path(directory).iterdir()
        for name in ('share-converter-recovery.patch', 'native-v2-recovery.patch', 'native-age-errors.patch'):
            with (ROOT / 'recovery/libxray' / name).open('rb') as patch:
                subprocess.run(['patch', '-p1', '--batch', '--fuzz=0'], stdin=patch,
                               cwd=source, check=True, stdout=subprocess.DEVNULL)
        for test in (ROOT / 'recovery/libxray').glob('recovered_*_test.go'):
            shutil.copyfile(test, source / test.name)
        subprocess.run([go, 'test', '.', './xray', './share', '-run', args.run, '-count=1'],
                       cwd=source, check=True, env=dict(os.environ, PUBLISHED_AGE_FIXTURE=str(ROOT / 'recovery/native-tests/published-v7-age-matrix.json')))


if __name__ == '__main__':
    main()
