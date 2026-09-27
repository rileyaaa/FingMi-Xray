#!/usr/bin/env python3
"""Compile real reconstructed library/track ownership with an instrumented JVM JNI boundary."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'compat/media3-libass/src/main/java/androidx/media3/exoplayer/libass'
tests=ROOT/'recovery/libass-tests/java'
with tempfile.TemporaryDirectory(prefix='libass-owners-') as td:
 files=[src/name for name in ['LibassConfiguration.java','LibassFrame.java','LibassFrameRenderer.java','LibassFrameSet.java','LibassImage.java','LibassMediaOwnership.java','LibassNativeLibrary.java','LibassStyleOverride.java','LibassTrack.java']]+list(tests.rglob('*.java'))
 subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-d',td,*map(str,files)],check=True)
 for name in ['NativeOwnershipTest','MediaOwnershipTest','FrameRendererTest']:
  subprocess.run(['java','-cp',td,'androidx.media3.exoplayer.libass.'+name],check=True,timeout=30)
