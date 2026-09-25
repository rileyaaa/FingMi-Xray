#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM_COMMIT="1a19fee278fa2234da725d61a53bf59b69fe9127"
WORK_DIR="${FINGMI_LEGACY_WORK_DIR:-$ROOT/recovery/work/fingmi-faithful-5.6.0}"
OVERLAY="$ROOT/recovery/legacy-src/upstream"
SOURCE_ONLY="${FINGMI_LEGACY_SOURCE_ONLY:-0}"
UPSTREAM_GIT_DIR="${FINGMI_LEGACY_UPSTREAM_GIT_DIR:-}"

command -v git >/dev/null 2>&1 || {
  echo "git is required" >&2
  exit 1
}

if [ "$SOURCE_ONLY" != 1 ] && [ ! -f "$ROOT/libxray/libs/libXray.aar" ]; then
  echo "libXray.aar is missing; fetching the pinned official build..."
  bash "$ROOT/scripts/fetch-libxray.sh"
fi

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

if [ -n "$UPSTREAM_GIT_DIR" ]; then
  # The object store can be reused offline, but only for the exact upstream
  # commit. Never use an arbitrary working tree containing previous overlays.
  if [ "$(git --git-dir="$UPSTREAM_GIT_DIR" cat-file -t "$UPSTREAM_COMMIT" 2>/dev/null)" != commit ]; then
    echo "Local upstream Git object store lacks $UPSTREAM_COMMIT: $UPSTREAM_GIT_DIR" >&2
    exit 1
  fi
  git --git-dir="$UPSTREAM_GIT_DIR" archive "$UPSTREAM_COMMIT" | tar -x -C "$WORK_DIR"
else
  git -C "$WORK_DIR" init -q
  git -C "$WORK_DIR" remote add origin https://github.com/FongMi/TV.git
  git -C "$WORK_DIR" fetch -q --depth=1 origin "$UPSTREAM_COMMIT"
  git -C "$WORK_DIR" checkout -q --detach FETCH_HEAD
  rm -rf "$WORK_DIR/.git"
fi

# Overlay every FongMi source/resource/build file whose final APK behavior was
# reconstructed from v5.6.0-xray.5.
cp -a "$OVERLAY/." "$WORK_DIR/"

# FongMi keeps its custom player lib-*.aar files out of Git. When a developer
# supplies the matching binaries locally, retain them in the disposable
# faithful workspace; the upstream checkout cannot provide them by itself.
for player_aar in "$ROOT"/app/libs/lib-*.aar; do
  [ -f "$player_aar" ] || continue
  mkdir -p "$WORK_DIR/app/libs"
  cp -a "$player_aar" "$WORK_DIR/app/libs/"
done

# The readable legacy Xray implementation itself is deliberately kept outside
# the upstream-shaped overlay. Install it into the original app package only
# for the faithful build workspace.
mkdir -p "$WORK_DIR/app/src/main/java/com/fongmi/android/tv/xray"
cp -a   "$ROOT/recovery/legacy-src/com/fongmi/android/tv/xray/."   "$WORK_DIR/app/src/main/java/com/fongmi/android/tv/xray/"

mkdir -p "$WORK_DIR/app/src/main/aidl"
cp -a   "$ROOT/recovery/legacy-src/aidl/."   "$WORK_DIR/app/src/main/aidl/"

if [ -f "$ROOT/libxray/libs/libXray.aar" ]; then
  mkdir -p "$WORK_DIR/libxray/libs"
  cp "$ROOT/libxray/libs/libXray.aar" "$WORK_DIR/libxray/libs/libXray.aar"
fi

# app/build.gradle reads signing keys from local.properties even for a debug
# configuration. Preserve a developer's SDK settings when available, while
# providing harmless placeholders for release-only signing fields.
if [ -f "$ROOT/local.properties" ]; then
  cp "$ROOT/local.properties" "$WORK_DIR/local.properties"
else
  : > "$WORK_DIR/local.properties"
fi

ensure_property() {
  local key="$1"
  local value="$2"
  if ! grep -q "^$key=" "$WORK_DIR/local.properties" 2>/dev/null; then
    printf '%s=%s\n' "$key" "$value" >> "$WORK_DIR/local.properties"
  fi
}

ensure_property storeFile /tmp/fingmi-recovery-placeholder.jks
ensure_property keyAlias placeholder
ensure_property storePassword placeholder

chmod +x "$WORK_DIR/gradlew"

cat <<EOF
Prepared faithful recovery workspace:
  $WORK_DIR

Upstream:
  FongMi/TV@$UPSTREAM_COMMIT

Recovered APK identity:
  versionCode 56005
  versionName 5.6.0-xray.5

No files under the normal app/:xray refactor tree were modified.
EOF

if [ "$SOURCE_ONLY" = 1 ]; then
  echo "Source-only review: no Gradle task ran and missing AAR files were not fetched."
fi
