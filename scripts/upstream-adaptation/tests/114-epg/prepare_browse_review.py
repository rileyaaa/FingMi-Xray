#!/usr/bin/env python3
"""Extend the frozen P2 review plan using exact Browse diff; local output only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

BASE = 'a02429c0e06f07a667fcee5e698bd22adb241a48'
TV = 'd3a0b84b24cf6628d72a4dbc2be453875b005536'
OLD = 'c616c0aa3613e87529791587a9f71b78c278c991'
PREFIX = 'app/src/main/java/com/fongmi/android/tv/'
RULE_DIR = 'scripts/upstream-adaptation/'
PINS = {
    PREFIX+'browse/BrowseTree.java': ('b3f097c47c75220ab84972d78fd0d5f483d9f469','b907ff3702d0afe6854e8ad040769d84aa0654c8','634d79b333f288334bebbe2f712bdce7ebaec58a'),
    PREFIX+'browse/LiveBrowse.java': ('04c4faebc844a9a6d5a52ad3bc80b59ae5486143','3d6c8646c2565f1e5f6deef7f269750c8498cdff','82a6ad25e4ef3e33c04ad31e225fb94fa7407992'),
    PREFIX+'service/LiveMetadata.java': (None,'43b908e5ca364d132dc10e87aa6f7064be54fe7d','f106d211ef63070db9b1eb39fd7272d162e6268f'),
}
P2_RULES = {'reviewed_media_host.json':'619041c80076a6c7b2c6e17577902433b88ea361',
            'reviewed_live_host.json':'a0c87206a9a73171906524c01aa6a2e5d63a519a',
            'lock.json':'02883814ff3af42a7388d080ef5e20c7bbdbcb79'}
DIFF_SHA = '32b5548504075bd8060172a01df4910781e6a15d65e4e6e820549792c14d29a6'

def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args])

def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def entry(root, ref, path):
    raw=git(root,'ls-tree','-r','-z',ref,'--',path)
    if not raw: return None
    mode,kind,oid=raw.split(b'\t',1)[0].decode().split()
    assert mode=='100644' and kind=='blob' and raw.endswith(path.encode()+b'\0')
    return oid

def hunk_edits(raw):
    """Use exact unified-diff hunks as reviewed, uniquely matching anchors."""
    out={}; path=None; hunk=None
    def flush():
        nonlocal hunk
        if hunk is None: return
        before=''.join(s[1:] for s in hunk if s[0] in ' -')
        after=''.join(s[1:] for s in hunk if s[0] in ' +')
        assert before and after and before!=after
        out[path].append([before,after]); hunk=None
    for line in raw.decode('utf-8').splitlines(keepends=True):
        if line.startswith('diff --git '):
            flush(); a,b=line.rstrip('\n').split()[2:]
            assert a.startswith('a/') and b=='b/'+a[2:]
            path=a[2:]; assert path not in out; out[path]=[]
        elif line.startswith('@@ '):
            flush(); hunk=[]
        elif hunk is not None:
            assert line[0] in ' +-'; hunk.append(line)
    flush(); assert set(out)==set(PINS)
    return out

def apply(text, edits):
    for before,after in edits:
        assert text.count(before)==1,'review anchor drift'
        text=text.replace(before,after)
    return text

def main():
    assert __debug__
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('dev','old-tv','tv','p2','diff','out'):
        ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    for root,ref,tree in ((a.dev,BASE,'46ce297ec3504d175cfe5bdec0a7c2fb8bae8f8f'),
                          (a.old_tv,OLD,'8aa6eebcf6bdf320841ef1158f0434faabc7a61f'),
                          (a.tv,TV,'82953e314d3009f039bb220db05ca537e0eadc92')):
        assert git(root,'rev-parse','HEAD').decode().strip()==ref
        assert git(root,'rev-parse','HEAD^{tree}').decode().strip()==tree
        assert not git(root,'status','--porcelain','--untracked-files=all')
    assert not a.out.exists() and all(not a.out.resolve().is_relative_to(p.resolve()) for p in (a.dev,a.old_tv,a.tv,a.p2))
    assert sha(a.diff.read_bytes())==DIFF_SHA
    assert sha((a.p2/'apply_review_plan.py').read_bytes())=='85104d2cc08e21c9d91887cccfdef666b7c5e890bd31746482b887266834ddbe'
    assert sha((a.p2/'epg-review-edits.json').read_bytes())=='e8c29192039f40d13dae290a590f9df8ffad8565f3f27bc2b81fd38e938ab7ce'
    edits=hunk_edits(a.diff.read_bytes())
    with tempfile.TemporaryDirectory(prefix='epg-rules-') as d:
        tmp=Path(d); p2=tmp/'p2'; patchdir=tmp/'patch'; patchdir.mkdir()
        subprocess.run(['python3','-B',str(a.p2/'apply_review_plan.py'),'--dev',str(a.dev),'--tv',str(a.tv),'--out',str(p2)],check=True)
        data={name:(p2/name).read_bytes() for name in P2_RULES}
        for name,b in data.items(): assert blob(b)==P2_RULES[name],name
        media=json.loads(data['reviewed_media_host.json']);lock=json.loads(data['lock.json'])
        assert len(lock['fork_scope'])==110
        for path,(older,base,resolved) in PINS.items():
            assert entry(a.old_tv,OLD,path)==entry(a.dev,BASE,path)==older
            assert entry(a.tv,TV,path)==base
            assert path not in media and all(r['path']!=path for r in lock['fork_scope'])
            raw=git(a.tv,'show',TV+':'+path)
            assert blob(raw)==base
            f=patchdir/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
        git(patchdir,'init','-q')
        git(patchdir,'apply','--check',str(a.diff.resolve()))
        git(patchdir,'apply',str(a.diff.resolve()))
        for path,(older,base,resolved) in PINS.items():
            raw=git(a.tv,'show',TV+':'+path)
            output=apply(raw.decode('utf-8'),edits[path]).encode('utf-8')
            assert blob(output)==resolved and output==(patchdir/path).read_bytes()
            media[path]={'from':'target','base':base,'resolved':resolved,'edits':edits[path]}
            lock['fork_scope'].append({'path':path,'old':older,'fork':older,'target':base,'strategy':'reviewed-media-host','resolved':resolved})
            print('REPLAY_BROWSE',path,resolved)
        assert len(lock['fork_scope'])==113
        assert sum(r['strategy']=='old-media-compat-review' for r in lock['fork_scope'])==5
        data['reviewed_media_host.json']=(json.dumps(media,indent=2,ensure_ascii=False)+'\n').encode()
        data['lock.json']=(json.dumps(lock,indent=2,ensure_ascii=False)+'\n').encode()
        assert blob(data['lock.json'])=='9e609009050dafb81d46bb1acda953c21374cd1d'
        a.out.mkdir(parents=True)
        for name,b in data.items():
            (a.out/name).write_bytes(b);print('REVIEW_OUTPUT',name,blob(b),sha(b),len(b))
    print('REVIEW_FILES_ONLY; source and Android not yet accepted')

if __name__=='__main__': main()
