#!/usr/bin/env python3
"""Stage verified APKs before retiring a release."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote


class PublicationError(RuntimeError):
    pass


def command(argv):
    return subprocess.check_output(argv)



def upstream_release_note(version_name: str) -> str:
    """Describe the selected public FongMi baseline, never the previous release."""
    match = re.fullmatch(r"v(\d+\.\d+\.\d+)-xray\.\d+", version_name)
    if match is None:
        raise PublicationError("Invalid app version for release notes")
    return (f"本版采用公开 FongMi/TV {match.group(1)} 源码基线；"
            "Xray 核心保持既有固定版本。")


@dataclass(frozen=True)
class Asset:
    path: Path
    digest: str
    size: int

    @classmethod
    def read(cls, path):
        path = Path(path)
        if not path.is_file() or path.stat().st_size == 0:
            raise PublicationError(f"Missing or empty publication asset: {path.name}")
        return cls(path, "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size)

    def metadata(self):
        return {"name": self.path.name, "digest": self.digest, "size": self.size}


@dataclass(frozen=True)
class Config:
    repository: str
    source: str
    tag: str
    run_id: str
    attempt: str
    allow_existing: bool
    rollback_tag: str = ""
    directory: Path = Path("release")
    resume_stage_id: int = 0
    resume_stage_tag: str = ""
    prune_superseded: bool = False

    @classmethod
    def environment(cls):
        required = ["GITHUB_REPOSITORY", "BUILD_SOURCE_SHA", "RELEASE_TAG", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"]
        values = {key: os.environ[key] for key in required}
        allow = os.environ.get("ALLOW_EXISTING_RELEASE", "false")
        if allow not in ("true", "false"):
            raise PublicationError("ALLOW_EXISTING_RELEASE must be true or false")
        prune = os.environ.get("PRUNE_SUPERSEDED", "false")
        if prune not in ("true", "false"):
            raise PublicationError("PRUNE_SUPERSEDED must be true or false")
        resume_id = os.environ.get("RESUME_STAGE_ID", "")
        if resume_id and (not resume_id.isdigit() or int(resume_id) <= 0):
            raise PublicationError("RESUME_STAGE_ID must be a positive release ID")
        return cls(values[required[0]], values[required[1]], values[required[2]],
                   values[required[3]], values[required[4]],
                   allow == "true", os.environ.get("ROLLBACK_TAG", ""),
                   resume_stage_id=int(resume_id) if resume_id else 0,
                   resume_stage_tag=os.environ.get("RESUME_STAGE_TAG", ""),
                   prune_superseded=(prune == "true"))

    def validate(self):
        if not re.fullmatch(r"[^/\s]+/[^/\s]+", self.repository):
            raise PublicationError("Invalid repository")
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", self.source):
            raise PublicationError("BUILD_SOURCE_SHA must be a full commit hash")
        if not re.fullmatch(r"v\d+\.\d+\.\d+-xray\.\d+", self.tag):
            raise PublicationError("Invalid formal release tag")
        if not self.run_id.isdigit() or not self.attempt.isdigit():
            raise PublicationError("Invalid workflow run identity")
        if self.rollback_tag and not self.rollback_tag.startswith(("rollback-", "release-rollback-")):
            raise PublicationError("ROLLBACK_TAG must use a rollback prefix")
        if bool(self.resume_stage_id) != bool(self.resume_stage_tag):
            raise PublicationError("RESUME_STAGE_ID and RESUME_STAGE_TAG must be supplied together")
        if self.resume_stage_id and (type(self.resume_stage_id) is not int or self.resume_stage_id <= 0
                                    or not re.fullmatch("stage-" + re.escape(self.tag) + r"-\d+-\d+", self.resume_stage_tag)):
            raise PublicationError("Invalid explicitly resumed APK staging identity")


class GitHub:
    def __init__(self, repository):
        self.repository = repository

    def api(self, path, method="GET", data=None, optional=False):
        endpoint = f"repos/{self.repository}" + ("/" + path if path else "")
        argv = ["gh", "api", endpoint, "--method", method]
        payload = None
        if data is not None:
            argv += ["--input", "-"]
            payload = json.dumps(data).encode()
        result = subprocess.run(argv, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            if optional and "(HTTP 404)" in result.stderr.decode(errors="replace"):
                return None
            # Do not echo request bodies: request bodies may contain private release metadata.
            raise PublicationError(f"GitHub {method} {path} failed: {result.stderr.decode(errors='replace').strip()}")
        return json.loads(result.stdout) if result.stdout.strip() else None

    def upload(self, tag, assets):
        subprocess.run(["gh", "release", "upload", tag, "--repo", self.repository,
                        *[str(asset.path) for asset in assets]], check=True)


class Publisher:
    def __init__(self, config, github):
        self.c = config
        self.gh = github
        self.result = {"source": config.source, "release_tag": config.tag, "phase": "preflight"}

    def save(self, phase):
        self.result["phase"] = phase
        self.c.directory.mkdir(parents=True, exist_ok=True)
        (self.c.directory / "publication-result.json").write_text(json.dumps(self.result, indent=2) + "\n")

    def ref(self, tag):
        return self.gh.api("git/ref/tags/" + quote(tag, safe=""), optional=True)

    def release(self, tag):
        return self.gh.api("releases/tags/" + quote(tag, safe=""), optional=True)

    def find_release(self, tag):
        """The tag endpoint excludes drafts; include them in collision checks."""
        published = self.release(tag)
        if published:
            return published
        page = 1
        while True:
            rows = self.gh.api(f"releases?per_page=100&page={page}")
            for row in rows:
                if row.get("tag_name") == tag:
                    return row
            if len(rows) < 100:
                return None
            page += 1

    def commit(self, ref):
        obj = ref["object"] if ref else None
        for _ in range(10):
            if obj is None:
                return None
            if obj["type"] == "commit":
                return obj["sha"]
            if obj["type"] != "tag":
                break
            obj = self.gh.api("git/tags/" + obj["sha"])["object"]
        raise PublicationError("Tag does not resolve to a commit")

    def ensure_tag(self, tag, source):
        current = self.ref(tag)
        if current:
            if self.commit(current) != source:
                raise PublicationError(f"Tag already points elsewhere: {tag}")
        else:
            self.gh.api("git/refs", "POST", {"ref": "refs/tags/" + tag, "sha": source})

    def verify(self, tag, assets, draft, prerelease, source, release_id=None):
        # Known draft releases must be read by ID. GitHub's by-tag endpoint is
        # for published releases, even when the caller created the draft.
        release = self.gh.api(f"releases/{release_id}") if release_id is not None else self.release(tag)
        if (not release or release.get("tag_name") != tag or release.get("draft") != draft
                or release.get("prerelease") != prerelease
                or (release_id is not None and release.get("id") != release_id)):
            raise PublicationError(f"Release state mismatch: {tag}")
        actual = release.get("assets", [])
        expected = {a.path.name: a for a in assets}
        if len(actual) != len(expected) or {a["name"] for a in actual} != set(expected):
            raise PublicationError(f"Release asset names mismatch: {tag}")
        for row in actual:
            asset = expected[row["name"]]
            if row.get("digest") != asset.digest or row.get("size") != asset.size or row.get("state") != "uploaded":
                raise PublicationError(f"Release asset verification failed: {row['name']}")
        if self.commit(self.ref(tag)) != source:
            raise PublicationError(f"Release source tag mismatch: {tag}")
        return release

    def stage(self, tag, assets, prerelease, notes):
        if self.find_release(tag) or self.ref(tag):
            raise PublicationError(f"Staging identity already exists; inspect before retry: {tag}")
        self.ensure_tag(tag, self.c.source)
        release = self.gh.api("releases", "POST", {
            "tag_name": tag, "target_commitish": self.c.source,
            "name": tag, "body": notes, "draft": True, "prerelease": prerelease,
        })
        self.result.setdefault("staged", {})[tag] = release["id"]
        self.save("uploading")
        self.gh.upload(tag, assets)
        return self.verify(tag, assets, True, prerelease, self.c.source, release["id"])

    def resume_stage(self, assets):
        release = self.verify(self.c.resume_stage_tag, assets, True, False,
                              self.c.source, self.c.resume_stage_id)
        self.result.setdefault("staged", {})[self.c.resume_stage_tag] = release["id"]
        self.result["resumed_stage"] = {"id": release["id"], "tag_name": self.c.resume_stage_tag}
        self.save("staging_resumed")
        return release

    @staticmethod
    def asset_fingerprint(release):
        return sorted((a["id"], a["name"], a["size"], a.get("digest"), a.get("state"))
                      for a in release.get("assets", []))

    @classmethod
    def fingerprint(cls, release):
        if release is None:
            return None
        return (release["id"], release["tag_name"], release["draft"], release["prerelease"],
                cls.asset_fingerprint(release))

    def delete_tag(self, tag, expected_source):
        ref = self.ref(tag)
        if ref:
            if self.commit(ref) != expected_source:
                raise PublicationError(f"Ref changed; refusing cleanup: {tag}")
            try:
                self.gh.api("git/refs/tags/" + quote(tag, safe=""), "DELETE")
            except PublicationError as error:
                # GITHUB_TOKEN can publish verified Release assets but may be
                # forbidden from deleting refs. Never hide an uncompleted tag
                # deletion or let it erase a successful, verified APK cutover.
                if "(HTTP 403)" not in str(error):
                    raise
                pending = self.result.setdefault("pending_tag_cleanup", [])
                pending.append({"tag": tag, "expected_commit": expected_source,
                                "reason": "GitHub Actions token refused tag DELETE (HTTP 403)"})
                self.save("tag_cleanup_requires_owner")

    def prune_superseded(self):
        """Owner-authorized one-time cleanup, only after verified new publication.

        Golden APKs and the exact current source/asset set are protected. Every
        other Release (including transient source backups) is retired only after
        the complete new APK release was verified and became Latest.
        """
        keep = {"v5.6.0-xray.5", self.c.tag}
        expected = [Asset.read(self.c.directory / f"FongMi-Xray-TV-{self.c.tag}-{abi}.apk")
                    for abi in ("armeabi-v7a", "arm64-v8a")]
        current = self.verify(self.c.tag, expected, False, False, self.c.source)
        golden = self.release("v5.6.0-xray.5")
        if (not golden or golden.get("draft") or golden.get("prerelease")
                or not self.ref("v5.6.0-xray.5")):
            raise PublicationError("Golden release/reference unavailable; refusing cleanup")
        if self.gh.api("releases/latest")["id"] != current["id"]:
            raise PublicationError("Current release is not Latest; refusing cleanup")

        rows = []
        for page in range(1, 100):
            batch = self.gh.api(f"releases?per_page=100&page={page}")
            if not isinstance(batch, list):
                raise PublicationError("Invalid release listing; refusing cleanup")
            rows.extend(batch)
            if len(batch) < 100:
                break
        else:
            raise PublicationError("Release listing too large; refusing cleanup")
        by_tag = {}
        for row in rows:
            tag = row.get("tag_name")
            if not tag or tag in by_tag:
                raise PublicationError("Duplicate/empty release tag; refusing cleanup")
            by_tag[tag] = row
        if not keep.issubset(by_tag):
            raise PublicationError("Protected release missing; refusing cleanup")
        if (self.fingerprint(by_tag[self.c.tag]) != self.fingerprint(current)
                or self.fingerprint(by_tag["v5.6.0-xray.5"]) != self.fingerprint(golden)):
            raise PublicationError("Protected release changed; refusing cleanup")

        retire = []
        for tag, row in by_tag.items():
            if tag in keep:
                continue
            ref = self.ref(tag)
            retire.append((tag, row, ref, self.commit(ref)))

        for tag, row, ref, source in retire:
            if (self.fingerprint(self.gh.api(f"releases/{row['id']}")) != self.fingerprint(row)
                    or self.ref(tag) != ref):
                raise PublicationError(f"Release changed during cleanup: {tag}")
            self.gh.api(f"releases/{row['id']}", "DELETE")
            if ref:
                self.delete_tag(tag, source)
            self.result.setdefault("pruned_releases", []).append(tag)
            self.save("pruning_superseded")

        remaining = self.gh.api("releases?per_page=100&page=1")
        if len(remaining) != 2 or {r.get("tag_name") for r in remaining} != keep:
            raise PublicationError("Post-cleanup release set does not match requested two tags")
        self.save("superseded_pruned")

    def source_version(self):
        gradle = command(["git", "show", self.c.source + ":app/build.gradle"]).decode()
        name = re.search(r'versionName\s+"([^"]+)"', gradle)
        code = re.search(r"versionCode\s+(\d+)", gradle)
        if not name or not code or name.group(1) != self.c.tag:
            raise PublicationError("Source app version does not match the publication tag")
        return name.group(1), int(code.group(1))

    def run(self):
        self.c.validate()
        if self.gh.api("").get("private") is not True:
            raise PublicationError("Publication is restricted to the private project")
        self.c.directory.mkdir(parents=True, exist_ok=True)
        apks = [Asset.read(self.c.directory / f"FongMi-Xray-TV-{self.c.tag}-{abi}.apk")
                for abi in ("armeabi-v7a", "arm64-v8a")]
        if set(self.c.directory.glob("*.apk")) != {a.path for a in apks}:
            raise PublicationError("Publication directory must contain exactly the two named APKs")
        old = self.find_release(self.c.tag)
        old_ref = self.ref(self.c.tag)
        old_source = self.commit(old_ref)
        if old and not self.c.allow_existing:
            raise PublicationError("Existing release replacement requires ALLOW_EXISTING_RELEASE=true")
        if old and (old.get("immutable") or old.get("draft") or not old_source):
            raise PublicationError("Existing release is not a replaceable formal release")
        if old and old_source == self.c.source and self.c.resume_stage_id:
            raise PublicationError("Prepositioned tag still belongs to an existing old release; refusing ambiguous cutover")
        if old_ref and old_source != self.c.source and not self.c.allow_existing:
            raise PublicationError("Existing tag replacement requires explicit authorization")
        token = self.c.run_id + "-" + self.c.attempt
        attempt_stage_tag = "stage-" + self.c.tag + "-" + token
        stage_tag = self.c.resume_stage_tag or attempt_stage_tag
        rollback_tag = self.c.rollback_tag or "rollback-" + self.c.tag + "-" + token
        self.result.update({"rollback_tag": rollback_tag if old else None,
                            "assets": [a.metadata() for a in apks]})
        before = {"release": old, "ref": old_ref}
        (self.c.directory / "publication-before.json").write_text(json.dumps(before, indent=2) + "\n")
        self.save("prepared")
        version_name, version_code = self.source_version()
        notes = (f"{self.c.tag} 正式版\n\nAPK 构建源码：`{self.c.source}`\n"
                 f"Actions run：{self.c.run_id} / attempt {self.c.attempt}\n\n"
                 "应用显示名称改为 FongMi-Xray，包名与固定签名保持不变，可从此前同签名版本覆盖升级。"
                 "Xray 设置在 UDP 下增加默认关闭的 TLS 分片开关，预设 tlshello / 80–120 字节 / 5–10 毫秒；"
                 "测试连接与实际播放均传递对应设置，Hysteria2、KCP、QUIC、无 TLS 与 XHTTP 仅 H3 等不适用配置自动跳过。"
                 "该选项用于部分网络的握手兼容，不保证普遍提速，也不能修正节点域名 DNS 污染。"
                 f"{upstream_release_note(version_name)}"
                 "源码、单元、双 ABI native、Release 编译与签名校验已执行；电视真机行为尚未验收。\n\n")
        if old:
            notes += ("本次按用户明确要求同名替换，为一次性版本规则例外；"
                      f"{version_name} / versionCode {version_code} 保持不变。"
                      "同签名包可手动覆盖安装，但这不是递增版本的新版本检测；安装器行为需设备验证。"
                      "后续正常发布仍递增修订号及 versionCode。\n\n")
            if self.c.tag == "v5.6.3-xray.1":
                notes += ("注意：此前 .2/.3/.4 安装包的 versionCode 高于此 .1 同名替换版，"
                          "Android 通常不允许直接降级覆盖；请先备份应用配置再决定是否卸载重装。\n\n")
        notes += "\n".join(f"{a.path.name}: `{a.digest}` ({a.size} bytes)" for a in apks)
        stage = self.resume_stage(apks) if self.c.resume_stage_id else self.stage(stage_tag, apks, False, notes)
        self.save("staging_verified")
        if self.fingerprint(self.release(self.c.tag)) != self.fingerprint(old) or self.ref(self.c.tag) != old_ref:
            raise PublicationError("Old publication changed during staging; refusing cutover")
        if old:
            if self.find_release(rollback_tag):
                raise PublicationError("Rollback release already exists; inspect before cutover")
            self.ensure_tag(rollback_tag, old_source)
            self.gh.api(f"releases/{old['id']}", "PATCH", {
                "tag_name": rollback_tag, "draft": True, "make_latest": "false",
            })
            rollback = self.gh.api(f"releases/{old['id']}")
            if (not rollback or rollback["id"] != old["id"] or rollback.get("tag_name") != rollback_tag
                    or not rollback["draft"] or rollback.get("prerelease") != old.get("prerelease")
                    or self.asset_fingerprint(rollback) != self.asset_fingerprint(old)
                    or self.commit(self.ref(rollback_tag)) != old_source):
                raise PublicationError("Rollback publication was not preserved")
            self.result["rollback_release_id"] = old["id"]
        self.save("rollback_preserved")
        if old_ref and old_source == self.c.source:
            # The owner has moved the tag to the exact verified build before
            # the resume run. GitHub Actions cannot force-update this tag (403).
            # The unchanged ref was checked immediately before this cutover.
            self.result["prepositioned_owner_tag"] = self.c.tag
        elif old_ref:
            self.gh.api("git/refs/tags/" + quote(self.c.tag, safe=""), "PATCH", {"sha": self.c.source, "force": True})
        else:
            self.ensure_tag(self.c.tag, self.c.source)
        self.gh.api(f"releases/{stage['id']}", "PATCH", {
            "tag_name": self.c.tag, "name": self.c.tag, "body": notes,
            "target_commitish": self.c.source, "draft": False,
            "prerelease": False, "make_latest": "true",
        })
        self.save("cutover_published")
        current = self.verify(self.c.tag, apks, False, False, self.c.source)
        if self.gh.api("releases/latest")["id"] != current["id"]:
            raise PublicationError("Formal release is not latest")
        self.result["release_id"] = current["id"]
        self.save("final_verified")
        # Retire old assets only after exact APK/source/latest verification.
        if old:
            self.gh.api(f"releases/{old['id']}", "DELETE")
            self.delete_tag(rollback_tag, old_source)
        self.delete_tag(stage_tag, self.c.source)
        if self.c.prune_superseded:
            self.prune_superseded()
        self.save("complete_pending_tag_cleanup" if self.result.get("pending_tag_cleanup") else "complete")
        return self.result


def main():
    config = Config.environment()
    publisher = Publisher(config, GitHub(config.repository))
    try:
        result = publisher.run()
    except Exception as error:
        publisher.result["error"] = str(error)
        publisher.save("failed:" + publisher.result["phase"])
        raise
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
