#!/usr/bin/env python3
"""Compile actual GLES implementation against Android API; test resource calls with a recording API."""
import argparse,hashlib,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--android-jar',type=Path,required=True)
a=p.parse_args()
# Maven Central com.google.android:android:4.1.1.4, checked against its published SHA1 on download.
assert hashlib.sha256(a.android_jar.read_bytes()).hexdigest()=='84072541cbb711eff89f7277100ff854929a446dba7ceb1b195c340e0b4fd3cb'
src=ROOT/'compat/media3-libass/src/main/java/androidx/media3/exoplayer/libass'
with tempfile.TemporaryDirectory(prefix='libass-gl-') as td:
 td=Path(td)
 sources=[src/name for name in ['LibassFrame.java','LibassImage.java','LibassFrameSet.java','LibassFrameRenderer.java','LibassGlTextures.java']]
 subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-cp',str(a.android_jar),'-d',str(td/'api'),*map(str,sources)],check=True)
 sources=[src/n for n in ['LibassFrame.java','LibassImage.java','LibassFrameSet.java','LibassFrameRenderer.java','LibassGlTextures.java']]
 sources+=list((ROOT/'recovery/libass-tests/gl-java').rglob('*.java'))
 subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-d',str(td/'test'),*map(str,sources)],check=True)
 subprocess.run(['java','-cp',str(td/'test'),'androidx.media3.exoplayer.libass.GlTexturesTest'],check=True)
print('PASS Android API source compile (recovered subset only, not full Media3/app build)')
