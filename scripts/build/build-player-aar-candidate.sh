#!/usr/bin/env bash
set -euo pipefail

SOURCE_COMMIT="3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d"
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

(
  cd "$SOURCE_DIR"
  ./gradlew --no-daemon -PexternalBuildDir=buildout \
    :lib-common:assembleRelease \
    :lib-database:assembleRelease \
    :lib-datasource:assembleRelease \
    :lib-datasource-okhttp:assembleRelease \
    :lib-decoder:assembleRelease \
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

python3 - "$SOURCE_DIR" "$STAGE" "$OUTPUT" "$SOURCE_COMMIT" <<'PY'
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

required = {
    "androidx/media3/mpvplayer/MpvPlayer.class",
    "androidx/media3/exoplayer/trackselection/DecodeTrackSelector.class",
    "androidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier.class",
    "androidx/media3/decoder/mpegh/MpeghAudioRenderer.class",
    "androidx/media3/decoder/DecoderInputBuffer.class",
}
found = set()
aars = sorted(set(
    source.glob("libraries/*/buildout/outputs/aar/*-release.aar")
) | set(
    source.glob("buildout/lib-*/outputs/aar/*-release.aar")
) | set(
    source.glob("libraries/*/build/outputs/aar/*-release.aar")
))
if len(aars) != 18:
    raise SystemExit(f"expected 18 release AARs, found {len(aars)}")

lines = [f"FongMi/media @ {source_commit}"]
for path in aars:
    target = stage / path.name
    shutil.copy2(path, target)
    data = target.read_bytes()
    with ZipFile(BytesIO(data)) as archive:
        classes = archive.read("classes.jar")
    with ZipFile(BytesIO(classes)) as jar:
        found.update(required.intersection(jar.namelist()))
    lines.append(f"{hashlib.sha256(data).hexdigest()}  {target.name}")

missing = required - found
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
