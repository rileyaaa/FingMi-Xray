#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK_DIR="${FINGMI_LEGACY_WORK_DIR:-$ROOT/recovery/work/fingmi-faithful-5.6.0}"
TASK="${FINGMI_LEGACY_GRADLE_TASK:-:app:assembleLeanbackArmeabi_v7aDebug}"

if [ "${FINGMI_LEGACY_SOURCE_ONLY:-0}" = 1 ]; then
  echo "FINGMI_LEGACY_SOURCE_ONLY=1 prepares sources for review; it cannot be used for a build." >&2
  exit 1
fi

python3 "$ROOT/scripts/recovery/check-faithful-player-aars.py"
python3 "$ROOT/scripts/recovery/check-player-ffmpegjni-against-published.py" --aar-dir "$ROOT/app/libs"
python3 "$ROOT/scripts/recovery/check-libxray-gojni.py" --aar "$ROOT/libxray/libs/libXray.aar"
bash "$ROOT/scripts/recovery/prepare-legacy-faithful.sh"

echo "Compiling recovered TV source with:"
echo "  $TASK"

cd "$WORK_DIR"
./gradlew "$TASK" --stacktrace
