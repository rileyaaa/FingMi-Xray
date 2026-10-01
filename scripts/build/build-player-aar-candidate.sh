#!/usr/bin/env bash
set -euo pipefail

SOURCE_COMMIT="3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
DOLBY_OVERLAY_ID="fongmi-tv-5.6.8-dolby-release-overlay-v1"
MPV_OVERLAY_ID="fongmi-tv-5.6.8-mpv-bridge-v2"
ISO_OVERLAY_ID="fongmi-tv-5.6.8-iso-navigation-stream-overlay-v4"
WORKDIR=""
OUTPUT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workdir)
      WORKDIR="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "$WORKDIR" ] || [ -z "$OUTPUT" ]; then
  echo "usage: $0 --workdir DIR --output ZIP" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKDIR="$(mkdir -p "$WORKDIR" && cd "$WORKDIR" && pwd)"
OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"
SOURCE_DIR="$WORKDIR/media"
STAGE="$WORKDIR/player-aars"

rm -rf "$SOURCE_DIR" "$STAGE"
mkdir -p "$SOURCE_DIR" "$STAGE"

git -C "$SOURCE_DIR" init -q
git -C "$SOURCE_DIR" remote add origin https://github.com/FongMi/media.git
git -C "$SOURCE_DIR" fetch --depth=1 origin "$SOURCE_COMMIT"
git -C "$SOURCE_DIR" checkout -q --detach FETCH_HEAD

actual="$(git -C "$SOURCE_DIR" rev-parse HEAD)"
if [ "$actual" != "$SOURCE_COMMIT" ]; then
  echo "unexpected FongMi/media commit: $actual" >&2
  exit 1
fi

python3 "$ROOT/scripts/build/apply-media3-dolby568-overlay.py" --source "$SOURCE_DIR"
python3 "$ROOT/scripts/build/apply-media3-mpv568-overlay.py" --source "$SOURCE_DIR"
python3 "$ROOT/scripts/build/apply-media3-iso568-overlay.py" --source "$SOURCE_DIR"

(
  cd "$SOURCE_DIR"
  ./gradlew --no-daemon -PexternalBuildDir=buildout \
    :lib-mpvplayer:testDebugUnitTest \
    :lib-common:assembleRelease \
    :lib-database:assembleRelease \
    :lib-datasource:assembleRelease \
    :lib-datasource-okhttp:assembleRelease \
    :lib-extractor:assembleRelease \
    :lib-exoplayer:assembleRelease \
    :lib-exoplayer-rtsp:assembleRelease \
    :lib-exoplayer-hls:assembleRelease \
    :lib-exoplayer-dash:assembleRelease \
    :lib-exoplayer-smoothstreaming:assembleRelease \
    :lib-decoder-ffmpeg:assembleRelease \
    :lib-decoder-mpegh:assembleRelease \
    :lib-effect:assembleRelease \
    :lib-mpvplayer:assembleRelease \
    :lib-session:assembleRelease \
    :lib-ui:assembleRelease \
    :lib-ui-danmaku:assembleRelease
)

python3 - "$SOURCE_DIR" "$STAGE" "$OUTPUT" "$SOURCE_COMMIT" "$DOLBY_OVERLAY_ID" "$MPV_OVERLAY_ID" "$ISO_OVERLAY_ID" <<'PY'
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo
import hashlib
import shutil
import sys

source = Path(sys.argv[1])
stage = Path(sys.argv[2])
output = Path(sys.argv[3])
source_commit = sys.argv[4]
overlay_id = sys.argv[5]
mpv_overlay_id = sys.argv[6]
iso_overlay_id = sys.argv[7]

required = {
    "androidx/media3/mpvplayer/MpvPlayer.class",
    "androidx/media3/mpvplayer/nativebridge/MpvClient$LongResultCallback.class",
    "androidx/media3/mpvplayer/media/MpvIsoStream.class",
    "androidx/media3/mpvplayer/media/MpvIsoStreamManager.class",
    "androidx/media3/extractor/iso/udf/NativeUdfFileSystem.class",
    "androidx/media3/exoplayer/iso/IsoNavigationSession.class",
    "androidx/media3/exoplayer/source/iso/IsoNavigationDataSource.class",
    "androidx/media3/exoplayer/source/iso/IsoNavigationDataSource$Factory.class",
    "androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource.class",
    "androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource$Factory.class",
    "androidx/media3/exoplayer/source/iso/IsoNavigationMediaSource$NavigationTimeline.class",
    "androidx/media3/exoplayer/iso/IsoNavigationSession$DvdMenuHighlight.class",
    "androidx/media3/exoplayer/iso/IsoNavigationSession$HdmvMenuOverlay.class",
    "is/xyz/mpv/MPVLib$Stream.class",
    "is/xyz/mpv/MPVLib$StreamProvider.class",
    "androidx/media3/exoplayer/trackselection/DecodeTrackSelector.class",
    "androidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier.class",
    "androidx/media3/decoder/mpegh/MpeghAudioRenderer.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5MappingPolicy.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5Native.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5Renderer.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP5VideoSink.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP7Converter.class",
    "androidx/media3/decoder/ffmpeg/FfmpegDolbyVisionP7Converter$Factory.class",
    "androidx/media3/exoplayer/video/DolbyVisionP7Converter.class",
    "androidx/media3/exoplayer/video/DolbyVisionP7Converter$Factory.class",
}
found = set()
navigation_keep_found = False
navigation_timestamp_hook_found = False
aars = sorted(set(
    source.glob("libraries/*/buildout/outputs/aar/*-release.aar")
) | set(
    source.glob("buildout/lib-*/outputs/aar/*-release.aar")
) | set(
    source.glob("libraries/*/build/outputs/aar/*-release.aar")
))
if len(aars) != 17:
    raise SystemExit(f"expected 17 release AARs, found {len(aars)}")

lines = [
    f"FongMi/media @ {source_commit}",
    f"Dolby overlay: {overlay_id}",
    f"MPV overlay: {mpv_overlay_id}",
    f"ISO overlay: {iso_overlay_id}",
]
for path in aars:
    target = stage / path.name
    shutil.copy2(path, target)
    data = target.read_bytes()
    with ZipFile(BytesIO(data)) as archive:
        classes = archive.read("classes.jar")
        if target.name == "lib-exoplayer-release.aar":
            if "proguard.txt" not in archive.namelist():
                raise SystemExit("lib-exoplayer-release.aar lacks consumer ProGuard rules")
            navigation_keep_found = (
                b"-keep class androidx.media3.exoplayer.iso.IsoNavigationSession { *; }"
                in archive.read("proguard.txt")
            )
    with ZipFile(BytesIO(classes)) as jar:
        found.update(required.intersection(jar.namelist()))
        if target.name == "lib-extractor-release.aar":
            ts_class = jar.read("androidx/media3/extractor/ts/TsExtractor.class")
            bdmv_class = jar.read("androidx/media3/extractor/iso/bdmv/BdmvTsExtractor.class")
            navigation_timestamp_hook_found = (
                b"TimestampDiscontinuityProvider" in ts_class
                and b"pollTimestampOffsetUs" in ts_class
                and b"setTimestampDiscontinuityProvider" in bdmv_class
            )
    lines.append(f"{hashlib.sha256(data).hexdigest()}  {target.name}")

missing = required - found
if not navigation_keep_found:
    raise SystemExit("lib-exoplayer-release.aar lost IsoNavigationSession consumer keep rule")
if not navigation_timestamp_hook_found:
    raise SystemExit("lib-extractor-release.aar lost packet-level ISO navigation timestamp hook")
lines += ["", "Required classes found:"] + sorted(found)
lines += ["", "Required classes missing:"] + sorted(missing)
manifest = ("\n".join(lines) + "\n").encode()
(stage / "BUILD_MANIFEST.txt").write_bytes(manifest)
if missing:
    raise SystemExit("compiled output lacks player prerequisites: " + ", ".join(sorted(missing)))

output.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(output, "w", compression=ZIP_STORED) as bundle:
    for path in sorted(stage.iterdir(), key=lambda p: p.name):
        info = ZipInfo(path.name, (1980, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_STORED
        info.external_attr = 0o644 << 16
        bundle.writestr(info, path.read_bytes())

print((stage / "BUILD_MANIFEST.txt").read_text(), end="")
print(f"candidate_zip_sha256={hashlib.sha256(output.read_bytes()).hexdigest()}")
PY

python3 "$ROOT/scripts/build/player_candidate.py" "$OUTPUT"

# The FongMi/media checkout and Gradle buildout are only reconstruction scratch.
# Keeping them until the app Gradle build can exhaust GitHub-hosted runner disk.
rm -rf "$SOURCE_DIR" "$STAGE"
