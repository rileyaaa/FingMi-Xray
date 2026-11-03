#!/usr/bin/env python3
"""Offline fixtures: source/media ABI blocker must fail early, never suppress APIs."""
from pathlib import Path
import importlib.util
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'media3_source_contract', ROOT / 'scripts/upstream/check_media3_source_contract.py')
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


with tempfile.TemporaryDirectory(prefix='fingmi-media3-public-source-') as tmp:
    root = Path(tmp)
    script = 'scripts/build/player_candidate.py'
    builder = 'scripts/build/build-player-aar-candidate.sh'
    app = 'app/src/main/java/com/fongmi/android/tv/setting/DecodeSetting.java'
    def pin(sha):
        write(root, script, 'SOURCE_COMMIT = "' + sha + '"\n')
        write(root, builder, '#!/bin/sh\nSOURCE_COMMIT="' + sha + '"\n')
    pin(contract.OLDER_PUBLIC_MEDIA)
    write(root, app, 'package com.fongmi;\nimport androidx.media3.common.Player;\n')
    assert contract.check(root) == [], 'Existing 5.6.3-style source should not be blocked'
    write(root, app, 'package com.fongmi;\nimport androidx.media3.common.DecoderMode;\n'
                     'import androidx.media3.common.text.SubtitleOffsets;\n')
    try:
        contract.check(root)
    except ValueError as exc:
        assert 'BLOCKED:' in str(exc)
        assert '2 Media3 API imports' in str(exc)
        assert 'DecoderMode' in str(exc) and 'SubtitleOffsets' in str(exc)
        assert contract.ISSUE in str(exc)
    else:
        raise AssertionError('Known unbuildable public Media3 pin was accepted')
    # New gap types were verified separately, beyond the first 100 javac errors.
    assert len(contract.UNAVAILABLE_IMPORTS) == 44
    write(root, app, 'package com.fongmi;\n'
                     'import androidx.media3.exoplayer.libass.LibassPlaybackSession;\n'
                     'import androidx.media3.mpvplayer.media.MpvDrmSupport;\n')
    try:
        contract.check(root)
    except ValueError as exc:
        assert 'BLOCKED:' in str(exc)
        assert '2 Media3 API imports' in str(exc)
        assert 'LibassPlaybackSession' in str(exc)
        assert 'MpvDrmSupport' in str(exc)
    else:
        raise AssertionError('Additional confirmed missing APIs bypassed the source guard')
    write(root, app, 'package com.fongmi;\n'
                     'import androidx.media3.common.audio.AudioChannelMix;\n')
    try:
        contract.check(root)
    except ValueError as exc:
        assert '1 Media3 API imports' in str(exc)
        assert 'AudioChannelMix' in str(exc)
    else:
        raise AssertionError('Audio-channel extension must not bypass the guard')
    write(root, app, 'package com.fongmi;\n'
                     'import androidx.media3.common.DecoderMode;\n'
                     'import androidx.media3.common.text.SubtitleOffsets;\n')
    # A changed public source commit is not claimed compatible; Gradle must decide.
    pin('a' * 40)
    assert len(contract.check(root)) == 2
    write(root, builder, '#!/bin/sh\nSOURCE_COMMIT="' + contract.OLDER_PUBLIC_MEDIA + '"\n')
    try:
        contract.check(root)
    except ValueError as exc:
        assert 'pin different' in str(exc)
    else:
        raise AssertionError('Inconsistent player rebuild/validator source was accepted')
    pin(contract.OLDER_PUBLIC_MEDIA)
    write(root, app, 'package com.fongmi;\nimport androidx.media3.common.DecoderMode;\n')
    assert contract.referenced_unavailable_imports(root) == ['androidx.media3.common.DecoderMode']

print('PASS: incompatible public Media3 commit blocked; older source and future new pins treated accurately')
