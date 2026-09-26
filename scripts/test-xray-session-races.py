#!/usr/bin/env python3
"""Deterministic JVM tests of real controller; Android queue/Binder/config are test doubles."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'xray/src/main/java/com/fingmi/xray'
files = [source / 'session' / name for name in ('XraySessionController.java', 'XrayResult.java', 'XrayOperationIds.java', 'XraySessionListener.java')]
files += [source / 'service/XrayOperation.java', source / 'util/XrayErrorSanitizer.java']
files += sorted((ROOT / 'recovery/session-tests').rglob('*.java'))
with tempfile.TemporaryDirectory(prefix='xray-races-') as directory:
    subprocess.run(['java', 'com.sun.tools.javac.Main', '--release', '17', '-d', directory] + [str(p) for p in files], check=True)
    subprocess.run(['java', '-cp', directory, 'com.fingmi.xray.session.SessionRaceTest'], check=True)
