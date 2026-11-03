#!/usr/bin/env python3
"""Fail fast when public FongMi/TV Java requires unavailable pinned Media3 APIs.

This is a narrow, evidence-backed blocker, not a promise that any other player
pin is compatible. 2026-11-03 full build #41606382989 reached javac only to
find the public FongMi/media@3c2cbe8 release-1.11.0-fongmi tree lacks these
imports. FongMi/TV issue #764 independently documents missing upstream media
source. No binary decompilation or synthetic player classes are permitted here.
"""

import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OLDER_PUBLIC_MEDIA = '3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d'
ISSUE = 'https://github.com/FongMi/TV/issues/764'

# Directly observed in javac's first 100 errors for official TV 5.8.7. The
# referenced source files/classes are absent at the pinned public media SHA.
# This is not a complete ABI listing; javac reported additional errors.
UNAVAILABLE_IMPORTS = frozenset('''
androidx.media3.common.DecoderMode
androidx.media3.common.DiscMenuController
androidx.media3.common.DiscMenuState
androidx.media3.common.VideoTransform
androidx.media3.common.audio.AudioChannelMode
androidx.media3.common.audio.AudioEffectParameters
androidx.media3.common.audio.AudioEffectProcessor
androidx.media3.common.text.SubtitleContent
androidx.media3.common.text.SubtitleOffsets
androidx.media3.common.text.SubtitleSelectionState
androidx.media3.common.util.LocalClearKeyLicense
androidx.media3.common.util.TrackSelectionUtil
androidx.media3.datasource.ProgressiveIsoCache
androidx.media3.effect.ColorToneAdjustEffect
androidx.media3.effect.DetailAdjustEffect
androidx.media3.effect.VideoAdjustment
androidx.media3.exoplayer.DecoderManager
androidx.media3.exoplayer.DecoderMode
androidx.media3.exoplayer.audio.AudioEqualizerController
androidx.media3.exoplayer.iso.IsoDiscPreparation
androidx.media3.exoplayer.iso.IsoNavigationPlayerController
androidx.media3.exoplayer.libass.LibassFontConfig
androidx.media3.exoplayer.source.ContentTypeResolvingMediaSource
androidx.media3.exoplayer.source.DefaultPositionMediaSource
androidx.media3.exoplayer.source.EndTrimMediaSource
androidx.media3.exoplayer.text.DefaultSubtitleContentLoader
androidx.media3.exoplayer.text.SubtitleTranscript
androidx.media3.exoplayer.text.SubtitleTranscriptParserFactory
androidx.media3.exoplayer.text.SubtitleTranscriptSession
androidx.media3.mpvplayer.MpvSubtitleContentLoader
'''.split())
assert len(UNAVAILABLE_IMPORTS) == 30
IMPORT = re.compile(r'^\s*import\s+(androidx\.media3\.[\w.]+)\s*;', re.MULTILINE)
SHA = re.compile(r'[0-9a-f]{40}\Z')


def pinned_media_revision(root: Path) -> str:
    script = (root / 'scripts/build/player_candidate.py').read_text(encoding='utf-8')
    pins = [node.value for node in ast.parse(script).body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == 'SOURCE_COMMIT']
    if len(pins) != 1:
        raise ValueError('Cannot identify exact source pin in player_candidate.py')
    pin = ast.literal_eval(pins[0])
    if not isinstance(pin, str) or not SHA.fullmatch(pin):
        raise ValueError('Invalid public Media3 source commit')
    builder = (root / 'scripts/build/build-player-aar-candidate.sh').read_text(encoding='utf-8')
    if not re.search(r'^SOURCE_COMMIT="' + pin + r'"\s*$', builder, re.MULTILINE):
        raise ValueError('Media3 candidate builder and verifier pin different public commits')
    return pin


def referenced_unavailable_imports(root: Path) -> list[str]:
    found = set()
    for subdir in ('app/src/main/java', 'app/src/leanback/java',
                   'catvod/src/main/java', 'catvod/src/leanback/java'):
        folder = root / subdir
        if not folder.is_dir():
            continue
        for path in folder.rglob('*.java'):
            found.update(IMPORT.findall(path.read_text(encoding='utf-8')))
    return sorted(found & UNAVAILABLE_IMPORTS)


def check(root: Path) -> list[str]:
    root = root.resolve()
    media_pin = pinned_media_revision(root)
    missing = referenced_unavailable_imports(root)
    if media_pin == OLDER_PUBLIC_MEDIA and missing:
        detail = '\n'.join('  - ' + name for name in missing)
        raise ValueError(
            f'BLOCKED: public FongMi/media@{media_pin[:12]} lacks {len(missing)} '
            'Media3 API imports required by the selected FongMi/TV source.\n'
            f'{detail}\n'
            f'Upstream source gap documented at {ISSUE}.\n'
            'Do not build APKs or synthesize placeholder classes. '
            'A source-verified compatible public Media3 revision is required.'
        )
    if media_pin != OLDER_PUBLIC_MEDIA and missing:
        print(f'NOTE: player pin {media_pin[:12]} differs from reviewed incompatible source; '
              'the actual Java/Media3 ABI remains unverified until compilation')
    else:
        print('PASS: selected source does not have the documented public Media3 source mismatch')
    return missing


def main() -> None:
    try:
        check(ROOT)
    except (OSError, SyntaxError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == '__main__':
    main()
