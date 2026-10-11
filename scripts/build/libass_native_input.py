#!/usr/bin/env python3
"""Extract only pinned Libass native bytes from a historical or retained APK.

The retained release is a container, not a source of Java/player behavior.
Whole APK digests are recorded; both native digests remain immutable gates.
"""
import argparse
import hashlib
import io
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from zipfile import ZipFile

APK = {
    "armeabi-v7a": "2859ebef12bf0fa0dfec023d410df478ac5e5a82a72ef2be48f6e4fa09a24761",
    "arm64-v8a": "948df594843e304c332476a380163dc1cc74f964be5ea1539ff0465a9dd936eb",
}
SO = {
    "armeabi-v7a": "58bc83730285c9a4ba40bf71d4deeea8be7e69dfb7d1a053f6a77aea006ad6ee",
    "arm64-v8a": "7e160faba4f64abb7551b48d07ae886af73464d3079978dcd55352e7b22bd6b3",
}
SOURCES = ("upstream-568", "retained-release")
RELEASE_VERSION = re.compile(r"v(\d+)\.(\d+)\.(\d+)-xray\.(\d+)")


def retained_version(release):
    tag = release.get("tag_name", "")
    match = RELEASE_VERSION.fullmatch(tag)
    if release.get("draft") is not False or not match or tag == "v5.6.0-xray.5":
        return None
    return tuple(map(int, match.groups()))


def select_retained_release(releases):
    # Release display flags do not change the pinned native bytes in an APK.
    # Choose the highest version first; an incomplete newest container must fail,
    # not silently fall back to another build with different provenance.
    candidates = [(retained_version(release), release) for release in releases]
    candidates = [(version, release) for version, release in candidates if version is not None]
    if not candidates:
        raise ValueError("No published FingMi-Xray APK container is available")
    latest = max(version for version, _ in candidates)
    matches = [release for version, release in candidates if version == latest]
    if len(matches) != 1:
        raise ValueError("Ambiguous highest FingMi-Xray APK container version")
    return matches[0]


def retained_assets(release):
    tag = release.get("tag_name", "")
    if (retained_version(release) is None or type(release.get("prerelease")) is not bool
            or type(release.get("id")) is not int or release["id"] <= 0):
        raise ValueError("Release is not a published FingMi-Xray APK container")
    assets = {}
    for abi in SO:
        name = "FongMi-Xray-TV-" + tag + "-" + abi + ".apk"
        matches = [asset for asset in release.get("assets", []) if asset.get("name") == name]
        if (len(matches) != 1 or matches[0].get("state") != "uploaded"
                or not isinstance(matches[0].get("id"), int) or matches[0]["id"] <= 0
                or matches[0].get("size", 0) <= 0):
            raise ValueError("Missing or ambiguous completed release asset: " + name)
        assets[abi] = matches[0]
    return assets


def fetch_retained_inputs(repository: str, directory: Path):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid GitHub repository")
    # One paginated snapshot, independent of GitHub's Latest/prerelease display.
    # Asset IDs do not silently switch when the same tag is replaced.
    output = subprocess.check_output([
        "gh", "api", "repos/" + repository + "/releases?per_page=100", "--method", "GET",
        "--paginate",
    ], text=True)
    # gh 2.46 supports --paginate but not --slurp; decode each returned page.
    releases, decoder = [], json.JSONDecoder()
    while output.strip():
        page, end = decoder.raw_decode(output.lstrip())
        if not isinstance(page, list):
            raise ValueError("Unexpected GitHub release listing page")
        releases.extend(page)
        output = output.lstrip()[end:]
    release = select_retained_release(releases)
    assets = retained_assets(release)
    tag = release["tag_name"]
    ref = json.loads(subprocess.check_output([
        "gh", "api", "repos/" + repository + "/git/ref/tags/" + tag, "--method", "GET",
    ], text=True))
    if ref.get("ref") != "refs/tags/" + tag:
        raise ValueError("Retained APK container tag identity mismatch")
    obj = ref.get("object", {})
    for _ in range(5):
        if not re.fullmatch(r"[0-9a-f]{40}", obj.get("sha", "")):
            raise ValueError("Invalid retained APK container source")
        if obj.get("type") == "commit":
            break
        if obj.get("type") != "tag":
            raise ValueError("Retained APK container tag does not identify a commit")
        annotated = json.loads(subprocess.check_output([
            "gh", "api", "repos/" + repository + "/git/tags/" + obj["sha"], "--method", "GET",
        ], text=True))
        obj = annotated.get("object", {})
    else:
        raise ValueError("Retained APK container tag nesting is too deep")
    directory.mkdir(parents=True, exist_ok=True)
    names = {"armeabi-v7a": "libass-source-v7.apk", "arm64-v8a": "libass-source-v8.apk"}
    with tempfile.TemporaryDirectory(prefix="libass-download-", dir=directory) as temporary:
        work = Path(temporary)
        for abi, asset in assets.items():
            path = work / names[abi]
            for attempt in range(3):
                with path.open("wb") as target:
                    result = subprocess.run([
                        "gh", "api", "repos/" + repository + "/releases/assets/" + str(asset["id"]),
                        "--method", "GET", "-H", "Accept: application/octet-stream",
                    ], stdout=target)
                if result.returncode == 0:
                    break
                if attempt == 2:
                    raise RuntimeError("Cannot download retained release asset " + str(asset["id"]))
                time.sleep(attempt + 1)
            data = path.read_bytes()
            if len(data) != asset["size"]:
                raise ValueError("Retained release asset size mismatch: " + asset["name"])
            digest = asset.get("digest")
            # Older GitHub assets may have no API digest. In every case record
            # the actual APK hash and require both immutable native hashes below.
            if digest and digest != "sha256:" + hashlib.sha256(data).hexdigest():
                raise ValueError("Retained release asset digest mismatch: " + asset["name"])
        _, apk_digests = read_native_inputs(work / names["armeabi-v7a"],
                                           work / names["arm64-v8a"], "retained-release")
        report = {
            "native_source": "retained-release", "repository": repository,
            "release_id": release["id"], "tag": release["tag_name"],
            # This records tag provenance, not a claim about APK Java contents.
            "prerelease": release["prerelease"], "tag_source_commit": obj["sha"],
            "target_commitish": release.get("target_commitish"),
            "assets": {abi: {key: asset.get(key) for key in ("id", "name", "size", "digest")}
                       for abi, asset in assets.items()},
            "apk_sha256": apk_digests, "so_sha256": SO,
            "extracted": "libmedia3ass.so only; no APK Java or DEX",
        }
        for name in names.values():
            (work / name).replace(directory / name)
    return report


def read_native_inputs(v7_apk: Path, v8_apk: Path, source: str = "upstream-568"):
    if source not in SOURCES:
        raise ValueError("Unknown Libass native source: " + source)
    native, apk_digests = {}, {}
    for abi, path in (("armeabi-v7a", v7_apk), ("arm64-v8a", v8_apk)):
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if source == "upstream-568" and digest != APK[abi]:
            raise ValueError("Unpinned historical APK: " + str(path))
        entry = "lib/" + abi + "/libmedia3ass.so"
        with ZipFile(io.BytesIO(data)) as apk:
            if apk.namelist().count(entry) != 1:
                raise ValueError("Expected exactly one " + entry + " in " + str(path))
            library = apk.read(entry)
        observed = hashlib.sha256(library).hexdigest()
        if observed != SO[abi]:
            raise ValueError("libmedia3ass.so SHA mismatch for " + abi
                             + ": expected " + SO[abi] + ", got " + observed)
        native["jni/" + abi + "/libmedia3ass.so"] = library
        apk_digests[abi] = digest
    return native, apk_digests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v7-apk", type=Path)
    parser.add_argument("--v8-apk", type=Path)
    parser.add_argument("--native-source", choices=SOURCES, default="upstream-568")
    parser.add_argument("--fetch-retained", metavar="OWNER/REPO")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.fetch_retained:
        if not args.output_dir or args.v7_apk or args.v8_apk:
            parser.error("--fetch-retained requires --output-dir, without APK arguments")
        report = fetch_retained_inputs(args.fetch_retained, args.output_dir)
    else:
        if not args.v7_apk or not args.v8_apk or args.output_dir:
            parser.error("Verification requires --v7-apk and --v8-apk, without --output-dir")
        _, apk_digests = read_native_inputs(args.v7_apk, args.v8_apk, args.native_source)
        report = {"native_source": args.native_source, "apk_sha256": apk_digests,
                  "so_sha256": SO, "extracted": "libmedia3ass.so only; no APK Java or DEX"}
    output = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
