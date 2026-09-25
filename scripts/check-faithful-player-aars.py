#!/usr/bin/env python3
"""Check the pinned FongMi player's non-Git AAR inputs before a build."""

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parent.parent
AARS = ROOT / "app" / "libs"
# Representative symbols referenced by FongMi 5.6.0 Java and not supplied by
# its version catalog. Passing these probes is only a dependency preflight;
# javac/Gradle must still check every method and binary API.
REQUIRED = (
    "androidx/media3/mpvplayer/MpvPlayer.class",
    "androidx/media3/exoplayer/trackselection/DecodeTrackSelector.class",
    "androidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier.class",
)


def classes_in_aar(path: Path) -> set[str]:
    result = set()
    with ZipFile(path) as bundle:
        for name in bundle.namelist():
            if name != "classes.jar" and not (name.startswith("libs/") and name.endswith(".jar")):
                continue
            with ZipFile(BytesIO(bundle.read(name))) as jar:
                result.update(symbol for symbol in REQUIRED if symbol in jar.namelist())
    return result


def main() -> int:
    supplied = sorted(AARS.glob("*.aar"))
    found = set()
    for aar in supplied:
        try:
            found.update(classes_in_aar(aar))
        except BadZipFile:
            print(f"Invalid AAR archive: {aar}")
            return 1
    missing = sorted(set(REQUIRED) - found)
    if missing:
        print("Pinned FongMi 5.6.0 player AAR prerequisites are missing:")
        for name in missing:
            print(f"  {name}")
        print(f"Checked {len(supplied)} AAR files in {AARS}.")
        print("Supply compatible upstream player lib-*.aar files before spending build/Actions time.")
        return 1
    print(f"Player AAR symbol preflight passed ({len(supplied)} archives checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
