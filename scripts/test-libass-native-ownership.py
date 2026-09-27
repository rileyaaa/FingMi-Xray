#!/usr/bin/env python3
"""Compile real reconstructed library/track ownership with an instrumented JVM JNI boundary."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'recovery/media3-libass/src/main/java/androidx/media3/exoplayer/libass'
tests=ROOT/'recovery/libass-tests/java'
with tempfile.TemporaryDirectory(prefix='libass-owners-') as td:
 files=[p for p in src.glob('*.java') if p.name!='LibassNative.java']+list(tests.rglob('*.java'))
 subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-d',td,*map(str,files)],check=True)
 subprocess.run(['java','-cp',td,'androidx.media3.exoplayer.libass.NativeOwnershipTest'],check=True,timeout=30)
