#!/usr/bin/env python3
"""Compile current app's Libass/Media3 call-site witness using the packaged AAR.

This is not compilation of ExoPlayerSession/ExoSubtitleController or an Android
Gradle task. It checks actual package access, generic/public types and overrides.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('candidate', ROOT/'scripts/build/build-libass-candidate.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--libs', type=Path, required=True)
    p.add_argument('--android-jar', type=Path, required=True)
    p.add_argument('--local-repository', type=Path, default=Path.home()/'.m2/repository')
    a = p.parse_args()
    candidate.checked(a.android_jar, candidate.ANDROID)
    dependencies = []
    for path, digest in candidate.DEPS.items():
        jar = a.local_repository/path
        candidate.checked(jar, digest)
        dependencies.append(jar)
    with tempfile.TemporaryDirectory(prefix='libass-app-contract-') as directory:
        work = Path(directory)
        for aar in sorted(a.libs.glob('*.aar')):
            with ZipFile(aar) as z:
                for entry in z.namelist():
                    if entry == 'classes.jar' or entry.startswith('libs/') and entry.endswith('.jar'):
                        jar = work/(aar.stem+'-'+entry.replace('/', '-'))
                        jar.write_bytes(z.read(entry))
                        dependencies.append(jar)
        output = work/'classes'
        output.mkdir()
        sources = [ROOT/'recovery/libass-tests/AppCallSiteContract.java']
        sources += [ROOT/'app/src/main/java/androidx/media3/exoplayer'/path for path in
                    ['trackselection/SecondaryTextTrackSelector.java', 'text/SecondaryTextOutput.java']]
        subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '17', '-d', str(output),
                        '-cp', os.pathsep.join(map(str, [a.android_jar, *dependencies])),
                        *map(str, sources)], check=True)
    print('PASS: app-facing Libass/Media3 call-site witness and actual SecondaryText source compile against packaged AARs')
    print('Not a complete app source, Android Gradle, resource, D8, assemble or runtime test')

if __name__ == '__main__':
    main()
