#!/usr/bin/env python3
"""Apply only reviewed host edits to exact locked input blobs."""
import hashlib
import json
from pathlib import Path

PORTS = json.loads(Path(__file__).with_name("reviewed_recovery_host.json").read_text())
LIVE_PORTS = json.loads(Path(__file__).with_name("reviewed_live_host.json").read_text())
if PORTS.keys() & LIVE_PORTS.keys():
    raise RuntimeError("Duplicate reviewed host paths")
PORTS.update(LIVE_PORTS)
MEDIA_PORTS = json.loads(Path(__file__).with_name("reviewed_media_host.json").read_text())
if PORTS.keys() & MEDIA_PORTS.keys():
    raise RuntimeError("Duplicate reviewed media host paths")
PORTS.update(MEDIA_PORTS)


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def adapt_reviewed_host(row, fork, target):
    rule = PORTS[row["path"]]
    origin = rule["from"]
    if origin not in ("fork", "target") or rule["base"] != row[origin] or rule["resolved"] != row["resolved"]:
        raise RuntimeError("Review lock mismatch: " + row["path"])
    data = (fork if origin == "fork" else target).read_bytes()
    if git_blob(data) != rule["base"]:
        raise RuntimeError("Reviewed host source drift: " + row["path"])
    text = data.decode("utf-8")
    for before, after in rule["edits"]:
        if text.count(before) != 1:
            raise RuntimeError("Reviewed edit anchor drift: " + row["path"])
        text = text.replace(before, after)
    result = text.encode("utf-8")
    if git_blob(result) != rule["resolved"]:
        raise RuntimeError("Reviewed output mismatch: " + row["path"])
    return result
