#!/usr/bin/env python3
"""Validate and import reconstructed Libass and its extractor/container dependencies.

Run import-player-aar-candidate.py first. This does not certify exact5.6.3 provenance.
All validation finishes before any destination file is replaced.
"""
import argparse
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import subprocess
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/build'))
from libass_build_contract import LIBASS_CANDIDATE_AAR_SHA256
spec = importlib.util.spec_from_file_location('libass_build', ROOT/'scripts/build/build-libass-candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
NAME = 'lib-exoplayer-libass-reconstructed.aar'
AAR_SHA256 = LIBASS_CANDIDATE_AAR_SHA256
ORIGINAL_EXTRACTOR = '9f5d306cabf3118ae26417c02870200dd245da853f980cdc8d51b27db34accd9'

def inventory(payload):
    owners = {}
    native_owners = {}
    for filename, data in sorted(payload.items()):
        with ZipFile(io.BytesIO(data)) as aar:
            names = aar.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate ZIP entries in '+filename)
            for name in names:
                if name.startswith('jni/') and name.endswith('.so'):
                    if name in native_owners:
                        raise ValueError('Duplicate native library '+name)
                    native_owners[name] = filename
                if name != 'classes.jar' and not (name.startswith('libs/') and name.endswith('.jar')):
                    continue
                with ZipFile(io.BytesIO(aar.read(name))) as jar:
                    for cls in jar.namelist():
                        if not cls.endswith('.class') or cls.endswith('module-info.class'):
                            continue
                        if cls in owners:
                            raise ValueError('Duplicate class '+cls+' in '+filename+' and '+owners[cls])
                        if cls.startswith(('androidx/media3/exoplayer/trackselection/SecondaryTextTrackSelector',
                                           'androidx/media3/exoplayer/text/SecondaryTextOutput')):
                            raise ValueError('AAR contains app-owned SecondaryText class: '+cls)
                        if cls.startswith(build.PREFIX) and filename != NAME:
                            raise ValueError('Another AAR owns Libass: '+filename)
                        owners[cls] = filename
    return owners

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ['aar', 'extractor', 'container']:
        p.add_argument('--'+arg, type=Path, required=True)
    p.add_argument('--libs', type=Path, default=ROOT/'app/libs')
    a = p.parse_args()
    updates = {NAME: build.checked(a.aar, AAR_SHA256),
               'lib-extractor-release.aar': build.checked(a.extractor, build.EXTRACTOR),
               'media3-container-1.11.0.aar': build.checked(a.container, build.CONTAINER)}
    # The candidate's own Java/native/public contract must pass before installation.
    subprocess.run(['python3', str(ROOT/'scripts/build/check-libass-contract.py'), '--aar', str(a.aar)], check=True)
    payload = {path.name: path.read_bytes() for path in a.libs.glob('*.aar')}
    if 'lib-extractor-release.aar' not in payload:
        p.error('Import the pinned player candidate before Libass')
    if build.sha(payload['lib-extractor-release.aar']) not in (ORIGINAL_EXTRACTOR, build.EXTRACTOR):
        p.error('Refusing to replace an unknown extractor AAR')
    for filename in (NAME, 'media3-container-1.11.0.aar'):
        if filename in payload and payload[filename] != updates[filename]:
            p.error('Refusing to replace a different existing '+filename)
    payload.update(updates)
    owners = inventory(payload)
    for filename, data in updates.items():
        with tempfile.NamedTemporaryFile(dir=a.libs, prefix='.libass-', delete=False) as f:
            temporary = Path(f.name)
            f.write(data)
        try:
            os.replace(temporary, a.libs/filename)
        finally:
            temporary.unlink(missing_ok=True)
    print('PASS: imported3 AARs; '+str(len(owners))+' unique dependency classes; no app-owned SecondaryText copies')
    print('Libass SHA256 '+hashlib.sha256(updates[NAME]).hexdigest())

if __name__ == '__main__':
    main()
