#!/usr/bin/env python3
"""Import the real historical Libass artifact; this is not the complete 5.6.3 API."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ZIP_SHA = '8cc91dae9c7d6770033bfe72e505b9455136c3f85e77d9ddec1f844335afa0d8'
AAR_SHA = '3b2326d98e1339f3ca4d1763e3a3028de20a5dd62cc738875af51b6329fe2571'
NAME = 'lib-exoplayer-libass-release.aar'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path, help='FongMi/media run 31571172760 artifact 9131565941 ZIP')
    parser.add_argument('--dest', type=Path, default=ROOT / 'app/libs')
    args = parser.parse_args()
    data = args.artifact.read_bytes()
    if hashlib.sha256(data).hexdigest() != ZIP_SHA:
        parser.error('Libass artifact SHA mismatch')
    with ZipFile(BytesIO(data)) as bundle:
        if bundle.namelist() != [NAME]:
            parser.error('Unexpected artifact entries')
        aar = bundle.read(NAME)
    if hashlib.sha256(aar).hexdigest() != AAR_SHA:
        parser.error('Libass AAR SHA mismatch')
    with ZipFile(BytesIO(aar)) as archive:
        for abi, machine in [('armeabi-v7a', 40), ('arm64-v8a', 183)]:
            elf = archive.read(f'jni/{abi}/libmedia3ass.so')
            if elf[:4] != b'\x7fELF' or int.from_bytes(elf[18:20], 'little') != machine:
                parser.error('Unexpected Libass JNI architecture')
        with ZipFile(BytesIO(archive.read('classes.jar'))) as classes:
            if 'androidx/media3/exoplayer/libass/LibassPlaybackSession.class' not in classes.namelist():
                parser.error('Missing real playback session')
    args.dest.mkdir(parents=True, exist_ok=True)
    target = args.dest / NAME
    if target.exists() and target.read_bytes() != aar:
        parser.error('Refusing to replace a different Libass AAR')
    target.write_bytes(aar)
    print(f'Imported verified upstream Libass Java + v7/arm64 JNI: {target}')
    print('Historical API: 5.6.3 LibassConfiguration/SubtitleController and SecondaryText still require recovery.')


if __name__ == '__main__':
    main()
