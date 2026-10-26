#!/usr/bin/env python3
"""Stage verified APKs and an exact source archive before retiring a release."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote
import zipfile


class PublicationError(RuntimeError):
    pass


def command(argv):
    return subprocess.check_output(argv)


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
    previous_backup: str
    allow_existing: bool
    rollback_tag: str = ""
    directory: Path = Path("release")
    resume_stage_id: int = 0
    resume_stage_tag: str = ""
    prune_superseded: bool = False

    @classmethod
    def environment(cls):
        required = ["GITHUB_REPOSITORY", "BUILD_SOURCE_SHA", "RELEASE_TAG", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "PREVIOUS_BACKUP_TAG"]
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
                   values[required[3]], values[required[4]], values[required[5]],
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
        if self.previous_backup and not self.previous_backup.startswith("source-backup-"):
            raise PublicationError("Only a named source-backup tag may be retired")
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
            # Do not echo request bodies: the private archive contains signing material.
            raise PublicationError(f"GitHub {method} {path} failed: {result.stderr.decode(errors='replace').strip()}")
        return json.loads(result.stdout) if result.stdout.strip() else None

    def upload(self, tag, assets):
        subprocess.run(["gh", "release", "upload", tag, "--repo", self.repository,
                        *[str(asset.path) for asset in assets]], check=True)


def source_archive(config, backup_tag):
    """Verify every archived tracked blob, including the fixed signing files."""
    output = config.directory / f"FingMi-Xray-{backup_tag}.zip"
    command(["git", "cat-file", "-e", config.source + "^{commit}"])
    command(["git", "archive", "--format=zip", "--prefix=FingMi-Xray/",
             "--output=" + str(output), config.source])
    object_format = command(["git", "rev-parse", "--show-object-format"]).decode().strip()
    records = command(["git", "ls-tree", "-rz", "--full-tree", config.source]).split(b"\0")
    expected = {}
    for record in records:
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        _, kind, oid = metadata.decode().split()
        if kind != "blob":
            raise PublicationError("Source backup cannot silently omit submodule contents")
        expected["FingMi-Xray/" + name.decode()] = oid
    for name in ("signing/fingmi-xray-release.p12", "signing/release-signing.properties", "signing/release-certificate.sha256"):
        if "FingMi-Xray/" + name not in expected:
            raise PublicationError("Source commit lacks fixed signing recovery files")
    with zipfile.ZipFile(output) as archive:
        members = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
        if len(members) != len(expected) or set(members) != set(expected):
            raise PublicationError("Source archive does not contain exactly the tracked files")
        for name in members:
            data = archive.read(name)
            oid = hashlib.new(object_format, b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if oid != expected[name]:
                raise PublicationError(f"Archived tracked bytes differ: {name}")
    return Asset.read(output)


class Publisher:
    def __init__(self, config, github, archive_factory=source_archive):
        self.c = config
        self.gh = github
        self.archive_factory = archive_factory
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
            self.gh.api("git/refs/tags/" + quote(tag, safe=""), "DELETE")

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
            raise PublicationError("Signing recovery archive may only be uploaded to the private project")
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
        if old_ref and old_source != self.c.source and not self.c.allow_existing:
            raise PublicationError("Existing tag replacement requires explicit authorization")
        previous = self.release(self.c.previous_backup) if self.c.previous_backup else None
        previous_ref = self.ref(self.c.previous_backup) if self.c.previous_backup else None
        backup_tag = "source-backup-" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "-main-" + self.c.source[:8]
        backup = self.archive_factory(self.c, backup_tag)
        token = self.c.run_id + "-" + self.c.attempt
        attempt_stage_tag = "stage-" + self.c.tag + "-" + token
        stage_tag = self.c.resume_stage_tag or attempt_stage_tag
        backup_stage_tag = attempt_stage_tag + "-backup"
        rollback_tag = self.c.rollback_tag or "rollback-" + self.c.tag + "-" + token
        self.result.update({"backup_tag": backup_tag, "rollback_tag": rollback_tag if old else None,
                            "assets": [a.metadata() for a in apks], "backup_asset": backup.metadata()})
        before = {"release": old, "ref": old_ref, "previous_backup": previous, "previous_backup_ref": previous_ref}
        (self.c.directory / "publication-before.json").write_text(json.dumps(before, indent=2) + "\n")
        self.save("prepared")
        version_name, version_code = self.source_version()
        notes = (f"{self.c.tag} 正式版\n\nAPK 构建源码：`{self.c.source}`\n"
                 f"Actions run：{self.c.run_id} / attempt {self.c.attempt}\n\n"
                 "应用显示名称改为 FongMi-Xray，包名与固定签名保持不变，可从此前同签名版本覆盖升级。"
                 "Xray 设置在 UDP 下增加默认关闭的 TLS 分片开关，预设 tlshello / 80–120 字节 / 5–10 毫秒；"
                 "测试连接与实际播放均传递对应设置，Hysteria2、KCP、QUIC、无 TLS 与 XHTTP 仅 H3 等不适用配置自动跳过。"
                 "该选项用于部分网络的握手兼容，不保证普遍提速，也不能修正节点域名 DNS 污染。"
                 "保留此前退出清理、主机名崩溃与 decoder 依赖修复；不升级 Xray 核心或公开 FongMi 基线。"
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
        has_marker = subprocess.run(
            ["git", "cat-file", "-e", self.c.source + ":.github/.trigger-publish-current-main-test"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        trigger_note = ("本归档保留构建时的临时 push trigger/marker；恢复使用前删除 "
                        "`.github/.trigger-publish-current-main-test`，并将发布 workflow 的 on 还原为仅 workflow_dispatch。"
                        "当前 main 在整个发布 run 完成后也会执行此还原。\n\n") if has_marker else ""
        backup_notes = (f"完整 tracked 源码归档：`{self.c.source}`。包含固定签名及私有恢复配置，"
                        "不包含 Git 历史、ignored AAR 或构建缓存；所有归档文件与该 commit 的 blob 字节核对。\n\n"
                        + trigger_note +
                        f"{backup.path.name}: `{backup.digest}` ({backup.size} bytes)")
        stage = self.resume_stage(apks) if self.c.resume_stage_id else self.stage(stage_tag, apks, False, notes)
        existing_backup = self.find_release(backup_tag)
        if existing_backup:
            self.verify(backup_tag, [backup], False, True, self.c.source)
            backup_stage = None
        else:
            backup_stage = self.stage(backup_stage_tag, [backup], True, backup_notes)
        self.save("both_uploads_verified")
        if backup_stage:
            self.ensure_tag(backup_tag, self.c.source)
            self.gh.api(f"releases/{backup_stage['id']}", "PATCH", {
                "tag_name": backup_tag, "name": backup_tag, "body": backup_notes,
                "target_commitish": self.c.source, "draft": False,
                "prerelease": True, "make_latest": "false",
            })
        published_backup = self.verify(backup_tag, [backup], False, True, self.c.source)
        self.result["backup_release_id"] = published_backup["id"]
        self.save("backup_published")
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
        if old_ref:
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
        self.verify(backup_tag, [backup], False, True, self.c.source)
        if self.gh.api("releases/latest")["id"] != current["id"]:
            raise PublicationError("Formal release is not latest")
        self.result["release_id"] = current["id"]
        self.save("final_verified")
        # Destructive cleanup is strictly after both final publications verify.
        if self.c.previous_backup and self.c.previous_backup != backup_tag:
            if self.fingerprint(self.release(self.c.previous_backup)) != self.fingerprint(previous) or self.ref(self.c.previous_backup) != previous_ref:
                raise PublicationError("Previous backup changed; refusing cleanup")
            if previous:
                self.gh.api(f"releases/{previous['id']}", "DELETE")
            if previous_ref:
                self.delete_tag(self.c.previous_backup, self.commit(previous_ref))
        if old:
            self.gh.api(f"releases/{old['id']}", "DELETE")
            self.delete_tag(rollback_tag, old_source)
        self.delete_tag(stage_tag, self.c.source)
        if backup_stage:
            self.delete_tag(backup_stage_tag, self.c.source)
        if self.c.prune_superseded:
            self.prune_superseded()
        self.save("complete")
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
