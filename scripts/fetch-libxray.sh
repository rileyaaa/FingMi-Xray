#!/usr/bin/env bash
set -euo pipefail

VERSION="26.7.28"
EXPECTED_SHA256="28b7dc9d6cc8455fcca5cbd56e387003a7bfb558128651a64899dc3a8ccff666"
URL="https://github.com/XTLS/libXray/releases/download/v${VERSION}/libxray-android.zip"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/xray/libs"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$DEST"

curl -fL --retry 3 --retry-delay 2 "$URL" -o "$TMP/libxray-android.zip"
echo "$EXPECTED_SHA256  $TMP/libxray-android.zip" | sha256sum -c -

AAR_PATH="$(unzip -Z1 "$TMP/libxray-android.zip" | grep -E '(^|/)libXray\.aar$' | head -n 1)"
if [ -z "$AAR_PATH" ]; then
  echo "libXray.aar not found in official archive" >&2
  exit 1
fi

unzip -p "$TMP/libxray-android.zip" "$AAR_PATH" > "$DEST/libXray.aar"
echo "Installed libXray v$VERSION -> $DEST/libXray.aar"
