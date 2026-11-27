#!/usr/bin/env python3
"""Generate only reviewed-rule additions in a new directory; never push or mutate a checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'a02429c0e06f07a667fcee5e698bd22adb241a48'
BASE_TREE = '46ce297ec3504d175cfe5bdec0a7c2fb8bae8f8f'
TV = 'd3a0b84b24cf6628d72a4dbc2be453875b005536'
TV_TREE = '82953e314d3009f039bb220db05ca537e0eadc92'
PREFIX = 'scripts/upstream-adaptation/'
PINS = {
    'reviewed_media_host.json': ('e49f88b9e61daa6986a27b7bde92f5f8deb709d0', '619041c80076a6c7b2c6e17577902433b88ea361'),
    'reviewed_live_host.json': ('9fde26c6e9d5073dbe098c3d9f2c8da993558c88', 'a0c87206a9a73171906524c01aa6a2e5d63a519a'),
    'lock.json': ('d33ade8301812e7964edf16b07fe9437ff83e791', '02883814ff3af42a7388d080ef5e20c7bbdbcb79'),
}


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def apply(source, edits):
    for before, after in edits:
        if source.count(before) != 1:
            raise RuntimeError('review anchor drift')
        source = source.replace(before, after)
    return source


def main():
    assert __debug__
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('dev', 'tv', 'out'):
        ap.add_argument('--' + name, required=True, type=Path)
    a = ap.parse_args()
    for path, ref, tree in ((a.dev, BASE, BASE_TREE), (a.tv, TV, TV_TREE)):
        assert git(path, 'rev-parse', 'HEAD').decode().strip() == ref
        assert git(path, 'rev-parse', 'HEAD^{tree}').decode().strip() == tree
    assert not a.out.exists()
    assert not a.out.resolve().is_relative_to(a.dev.resolve())
    assert not a.out.resolve().is_relative_to(a.tv.resolve())
    plan = json.loads(Path(__file__).with_name('epg-review-edits.json').read_text())
    assert len(plan) == 4
    files = {}
    for name, (old, _) in PINS.items():
        data = git(a.dev, 'show', BASE + ':' + PREFIX + name)
        assert blob(data) == old, name
        files[name] = json.loads(data)
    lock = files['lock.json']
    assert len(lock['fork_scope']) == 110
    assert sum(r['strategy'] == 'old-media-compat-review' for r in lock['fork_scope']) == 5
    for path, change in plan.items():
        name = 'reviewed_live_host.json' if path.endswith('/LiveActivity.java') else 'reviewed_media_host.json'
        rule = files[name][path]
        row, = (r for r in lock['fork_scope'] if r['path'] == path)
        assert row['strategy'] == name.removesuffix('.json').replace('_', '-') and rule['from'] == 'target'
        raw = git(a.tv, 'show', TV + ':' + path)
        assert blob(raw) == row['target'] == rule['base']
        assert blob(git(a.dev, 'show', BASE + ':' + path)) == row['fork']
        text = apply(raw.decode('utf-8'), rule['edits'])
        assert blob(text.encode()) == rule['resolved'] == row['resolved'] == change['old_resolved']
        result = apply(text, change['edits'])
        assert blob(result.encode()) == change['resolved']
        rule['edits'].extend(change['edits'])
        rule['resolved'] = row['resolved'] = change['resolved']
        assert apply(raw.decode('utf-8'), rule['edits']) == result
        print('REPLAY', path, change['resolved'])
    outputs = {}
    for name, (_, new) in PINS.items():
        data = (json.dumps(files[name], indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        assert blob(data) == new, name
        outputs[name] = data
    a.out.mkdir(parents=True)
    for name, data in outputs.items():
        (a.out / name).write_bytes(data)
        print('REVIEW_OUTPUT', name, blob(data), hashlib.sha256(data).hexdigest(), len(data))


if __name__ == '__main__':
    main()
