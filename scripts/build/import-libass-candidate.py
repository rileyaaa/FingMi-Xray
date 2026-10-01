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
RECOVERY = ROOT / 'scripts/recovery'
sys.path.insert(0, str(RECOVERY))
from published_568_iso_contract import NATIVE_SHA256 as ISO_NATIVE_SHA256
spec = importlib.util.spec_from_file_location('libass_build', ROOT/'scripts/build/build-libass-candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
NAME = 'lib-exoplayer-libass-reconstructed.aar'
AAR_SHA256 = LIBASS_CANDIDATE_AAR_SHA256
ISO_NATIVE = {
    f'jni/{abi}/{soname}': digest
    for abi, libraries in ISO_NATIVE_SHA256.items()
    for soname, digest in libraries.items()
}

def merge_pinned_iso_native(extractor, restored_iso_extractor):
    """Merge only the immutable 5.6.8 libisoJNI payload into the Libass extractor."""
    with ZipFile(io.BytesIO(extractor)) as base, ZipFile(io.BytesIO(restored_iso_extractor)) as restored:
        base_names = base.namelist()
        restored_names = restored.namelist()
        if len(base_names) != len(set(base_names)) or len(restored_names) != len(set(restored_names)):
            raise ValueError('Extractor AAR contains duplicate ZIP entries')
        overlap = sorted(set(base_names) & set(ISO_NATIVE))
        if overlap:
            raise ValueError('Libass extractor unexpectedly already contains pinned ISO native entries: ' + ', '.join(overlap))
        missing = sorted(set(ISO_NATIVE) - set(restored_names))
        if missing:
            raise ValueError('Current extractor lacks pinned ISO native entries: ' + ', '.join(missing))
        for name, digest in ISO_NATIVE.items():
            actual = hashlib.sha256(restored.read(name)).hexdigest()
            if actual != digest:
                raise ValueError('Current extractor has unverified ISO native entry: ' + name)

        output = io.BytesIO()
        with ZipFile(output, 'w') as merged:
            for info in base.infolist():
                merged.writestr(info, base.read(info.filename))
            for name in sorted(ISO_NATIVE):
                merged.writestr(restored.getinfo(name), restored.read(name))
        return output.getvalue()


def check_combined_iso_contract(data):
    with tempfile.NamedTemporaryFile(suffix='.aar') as temporary:
        temporary.write(data)
        temporary.flush()
        subprocess.run(
            [
                'python3',
                str(RECOVERY / 'check-published-568-iso.py'),
                '--aar',
                temporary.name,
            ],
            check=True,
        )


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
    libass_candidate = build.checked(a.aar, AAR_SHA256)
    libass_extractor = build.checked(a.extractor, build.EXTRACTOR)
    container = build.checked(a.container, build.CONTAINER)
    # The candidate's own Java/native/public contract must pass before installation.
    subprocess.run(['python3', str(ROOT/'scripts/build/check-libass-contract.py'), '--aar', str(a.aar)], check=True)
    payload = {path.name: path.read_bytes() for path in a.libs.glob('*.aar')}
    if 'lib-extractor-release.aar' not in payload:
        p.error('Import the pinned player candidate before Libass')
    try:
        combined_extractor = merge_pinned_iso_native(
            libass_extractor, payload['lib-extractor-release.aar']
        )
        check_combined_iso_contract(combined_extractor)
    except (KeyError, ValueError) as error:
        p.error(str(error))
    updates = {
        NAME: libass_candidate,
        'lib-extractor-release.aar': combined_extractor,
        'media3-container-1.11.0.aar': container,
    }
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
    print('Combined extractor SHA256 '+hashlib.sha256(updates['lib-extractor-release.aar']).hexdigest())

if __name__ == '__main__':
    main()
