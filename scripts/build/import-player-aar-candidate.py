#!/usr/bin/env python3
"""Import the locally rebuilt pinned FongMi/media player AAR bundle into app/libs."""

import argparse
from pathlib import Path
import sys
from zipfile import BadZipFile

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from player_candidate import SOURCE_COMMIT, read_verified_candidate  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifact",
        type=Path,
        help=f"candidate ZIP rebuilt from FongMi/media@{SOURCE_COMMIT}",
    )
    args = parser.parse_args()

    try:
        payload = read_verified_candidate(args.artifact)
    except (BadZipFile, KeyError, ValueError, OSError) as error:
        parser.error(str(error))

    dest = ROOT / "app" / "libs"
    dest.mkdir(parents=True, exist_ok=True)
    for filename, data in payload.items():
        (dest / filename).write_bytes(data)

    print(
        f"Imported {len(payload)} verified FongMi/media@{SOURCE_COMMIT} "
        f"candidate AARs to {dest}"
    )


if __name__ == "__main__":
    main()
