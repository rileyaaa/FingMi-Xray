#!/usr/bin/env python3
"""Reproduce the frozen EPG rules and compare real full-source stages. No Android build."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

BASE = 'a02429c0e06f07a667fcee5e698bd22adb241a48'
BASE_TREE = '46ce297ec3504d175cfe5bdec0a7c2fb8bae8f8f'
RULE_DIR = 'scripts/upstream-adaptation/'
RULES = ('reviewed_media_host.json', 'reviewed_live_host.json', 'lock.json')
LOCKS = ('d33ade8301812e7964edf16b07fe9437ff83e791', '9e609009050dafb81d46bb1acda953c21374cd1d')
PINS = {
    'old_tv': ('c616c0aa3613e87529791587a9f71b78c278c991', '8aa6eebcf6bdf320841ef1158f0434faabc7a61f'),
    'tv': ('d3a0b84b24cf6628d72a4dbc2be453875b005536', '82953e314d3009f039bb220db05ca537e0eadc92'),
    'media': ('3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d', 'b7a4d78a2168bd5065034d37a242b7e51785ea4e'),
    'media_default': ('2bc207851df311340767e913931ca7b28cab1794', '246fb170134edf5a7b5f8a2ca6f4f8bc81903383'),
}
PREFIX = 'app/src/main/java/com/fongmi/android/tv/'
SOURCES = {
    PREFIX+'api/LiveApi.java': ('df0138ae3c510e853bbc113128f61375e422ca2c','b22eb5e770fc36107d94c7b18400deea757c8792'),
    PREFIX+'api/parser/EpgParser.java': ('8819406efc21deeb900dd5d86a68260edba43980','10da8a80d0baaa57cdaae3da70d8a32cf8f49726'),
    PREFIX+'model/LiveViewModel.java': ('367f6c10fc6c583887cf08d4a2d8ab7d50f76d0a','6fc6cc0cc614165de8f8eeda2fce10b07bbd1c67'),
    'app/src/leanback/java/com/fongmi/android/tv/ui/activity/LiveActivity.java': ('f636c8e185c1976e736af3d5249960ae70fd1cf4','6ac3d00e5e5bc34a5304757e19dc6b75baec6d5c'),
    PREFIX+'browse/BrowseTree.java': ('b907ff3702d0afe6854e8ad040769d84aa0654c8','634d79b333f288334bebbe2f712bdce7ebaec58a'),
    PREFIX+'browse/LiveBrowse.java': ('3d6c8646c2565f1e5f6deef7f269750c8498cdff','82a6ad25e4ef3e33c04ad31e225fb94fa7407992'),
    PREFIX+'service/LiveMetadata.java': ('43b908e5ca364d132dc10e87aa6f7064be54fe7d','f106d211ef63070db9b1eb39fd7272d162e6268f'),
}
CONFLICTS = ['app/src/main/AndroidManifest.xml', PREFIX+'player/mpv/MpvPlayerEngine.java']
MANUAL = ['app/src/main/java/'+p for p in (
    'androidx/media3/exoplayer/libass/LibassFontFile.java',
    'androidx/media3/exoplayer/text/SecondaryTextOutput.java',
    'androidx/media3/exoplayer/trackselection/SecondaryTextTrackSelector.java',
    'androidx/media3/ui/danmaku/DanmakuPlayerViewController.java',
    'com/fongmi/android/tv/player/mpv/MpvUtil.java')]
AARS = {'hook-release.aar':'179856a41a3e03ce569f00a66b8a82ca1071830c',
        'tvbus-release.aar':'2fda22082087a1702436717c72efe05b65efe5ca'}
BLOCKED = 'CANDIDATE NOT BUILDABLE YET: unresolved host/media contracts; no APK produced'
TESTS = {
    'test-upstream-live-host.py':'bb5803aea6e5e45efeb32baca4046fcc7a89f16e',
    'test-upstream-live-activity.py':'fad66d8057c6c3ed24f463af255d452a4be74979',
    'test-upstream-live-metadata-vod.py':'7fbbfe9a62dd71a341eeccb8d5e940ff7b9570de',
    'test-upstream-host-recovery.py':'074a4594e100eb4929c39f6e28ce63a50e624c88',
    'test-upstream-player-host.py':'6bbee1651764805f628f2972155c22aa380387be',
    'test-upstream-transport-host.py':'3dfcdf398ce76492570e11696d01c4dc17bab6c7',
    'test-upstream-side-requests.py':'bdfe70bb53fbaec80ec52b04986832a0fbc7c6e7',
    'test-upstream-recovery-loader.py':'aa8eb2e9da6f751ba894a65edc020f12ca52cd59',
    'test-xray-normalizer-parity.py':'6bc818b0fa49219671a25fa076c4b1b6e4ca8f97',
    'test-xray-session-races.py':'4825fb9e83cf80a00a6d6673cb3554928592aafb',
    'test-xray-playback-session-reentry.py':'f5e6609334f9b0a86e550e3279fbc9b72c82a6ff',
    'test-xray-live-auto.py':'5704156c7b35b0a8fb4d3f2adabb7d2cb8a1fa4a',
    'test-xray-playback-binding-handoff.py':'61921b4621f09f72fd6d66f262d61c68dd8a5f89',
}
OVERLAY_TESTS = {'test-upstream-live-activity.py','test-upstream-live-metadata-vod.py'}
OLD_HOST_TESTS = {'test-xray-live-auto.py','test-xray-playback-binding-handoff.py'}
MODULE_TESTS = {n for n in TESTS if n.startswith('test-xray-')} - OLD_HOST_TESTS
HERE = Path(__file__).resolve().parent

def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*map(str,args)])

def rev(root, *args): return git(root,*args).decode().strip()
def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def check_input(label, root, head, tree):
    assert rev(root,'rev-parse','HEAD') == head, label
    assert rev(root,'rev-parse','HEAD^{tree}') == tree, label
    assert rev(root,'rev-parse','--is-shallow-repository') == 'true', label
    assert not git(root,'status','--porcelain','--ignored','--untracked-files=all'), label
    inventory = git(root,'ls-tree','-r','-z','--full-tree',head)
    objects = git(root,'rev-list','--objects','--missing=print',head)
    assert not any(line.startswith(b'?') for line in objects.splitlines()), label
    print('COMPLETE_INPUT',label,head,tree,'entries',inventory.count(b'\0'),
          'tree_listing_sha256',sha(inventory),flush=True)

def manifest(root):
    rows = {}
    for f in root.rglob('*'):
        assert not f.is_symlink(), f
        if f.is_dir(): continue
        assert f.is_file(), f
        name = f.relative_to(root).as_posix()
        assert '.git' not in Path(name).parts, name
        data = f.read_bytes()
        rows[name] = [stat.S_IMODE(f.stat().st_mode),len(data),sha(data)]
    return rows

def canonical(rows):
    return sha(json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii'))

def guard_worker(dev, output, inputs):
    # Only observe the actual completed overlay before main deletes its tempdir.
    sys.path.insert(0,str(dev/RULE_DIR))
    import prepare_candidate as p
    assert p.ROOT == dev
    original = p.overlay
    def observe(old, tv, dest):
        result = original(old,tv,dest)
        shutil.copytree(dest,output/'candidate')
        rows = manifest(dest)
        assert manifest(output/'candidate') == rows
        (output/'observed.json').write_text(json.dumps({'result':result,'files':rows,'scope':len(p.LOCK['fork_scope'])}))
        print('OBSERVED_FULL_MANIFEST',len(rows),canonical(rows),flush=True)
        return result
    p.overlay = observe
    sys.argv = [str(dev/RULE_DIR/'prepare_candidate.py')]+inputs
    try:
        p.main()
    except SystemExit as e:
        print('ORIGINAL_TERMINAL',e.code,flush=True)
        raise
    finally:
        p.overlay = original
    raise RuntimeError('Missing original terminal guard')

def run_guard(label, dev, output, inputs):
    output.mkdir()
    print('BEGIN_SOURCE_GUARD',label,rev(dev,'rev-parse','HEAD'),flush=True)
    result = subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--guard-worker',str(dev),str(output),*inputs],
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    print(result.stdout,end='',flush=True)
    print('SOURCE_GUARD_EXIT',label,result.returncode,flush=True)
    assert result.returncode == 1 and result.stdout.splitlines().count('ORIGINAL_TERMINAL '+BLOCKED)==1, label
    data = json.loads((output/'observed.json').read_text())
    lines = result.stdout.splitlines()
    prefixes = ('SOURCE ','SHARED_MEDIA_SOURCE ','UPSTREAM_BINARY_INPUT ','PUBLIC_NATIVE_SOURCE_CANDIDATE ',
                'MEDIA_SOURCE_CONTRACT ','MISSING_MEDIA_SOURCE ','METHOD_REVIEW_REQUIRED ','MISSING_REQUIRED_AAR ','BLOCKED:')
    gates = Counter(s for s in lines if s.startswith(prefixes))
    summaries = [s for s in lines if s.startswith('OVERLAY_SUMMARY ')]
    assert len(summaries)==1, label
    summary = re.fullmatch(r'OVERLAY_SUMMARY transferred_or_clean_merge (\d+) unresolved (\d+) old_media_review (\d+) untouched_upstream_verified',summaries[0])
    assert summary, summaries
    data['summary'] = tuple(map(int,summary.groups()))
    data['gates'] = gates
    return data

def compare(original, reviewed, before, after):
    a,b = original['files'],reviewed['files']
    assert len(a)==len(b)==1410 and a.keys()==b.keys()
    changed = {p for p in a if a[p]!=b[p]}
    assert changed == set(SOURCES), sorted(changed)
    for path,(old,new) in SOURCES.items():
        assert a[path][0]==b[path][0]==0o644
        for label,root,oid in (('base',before,old),('reviewed',after,new)):
            data=(root/path).read_bytes()
            assert blob(data)==oid, path
            print('EXACT_JAVA',label,path,oid,len(data),sha(data),flush=True)
    for root in (before,after):
        assert {p.name for p in (root/'app/libs').glob('*.aar')}==set(AARS)
        for name,oid in AARS.items(): assert blob((root/'app/libs'/name).read_bytes())==oid
        assert not (root/'libxray/libs/libXray.aar').exists()
    assert original['scope']==110 and reviewed['scope']==113
    assert original['result']==reviewed['result']==[CONFLICTS,MANUAL]
    x,y=original['summary'],reviewed['summary']
    assert x[1:]==y[1:]==(2,5) and y[0]==x[0]+3
    assert original['gates']==reviewed['gates'], 'Dependency guard changed'
    for name in ('lib-mpvplayer-release.aar','lib-decoder-ffmpeg-release.aar'):
        assert reviewed['gates']['MISSING_REQUIRED_AAR '+name]==2, name
    for f in (after/'app/src').rglob('*'):
        if f.suffix in ('.java','.kt'):
            assert not re.search(r'\bloadLiveMetadata\s*\(',f.read_text(encoding='utf-8')), f
    print('PASS_FULL_SOURCE_REPLAY',len(a),len(b),'changed',len(changed),
          'scope',original['scope'],reviewed['scope'],'conflicts',2,'manual',5,
          'base_manifest',canonical(a),'reviewed_manifest',canonical(b),flush=True)
    print('PASS_ORIGINAL_DEPENDENCY_GUARD_UNCHANGED',flush=True)

def run_existing_tests(dev, review, candidate, old_tv, tv, work):
    # Existing tests have their original deterministic boundary doubles.
    # No new EPG/F3 fixture. Test-support files are kept outside the audited candidate.
    testroot=work/'module-test-root'
    testroot.mkdir()
    shutil.copytree(candidate/'xray',testroot/'xray')
    legacy='recovery/legacy-src/com/fongmi/android/tv/xray/legacy/'
    prefixes=['tests/xray-session',legacy+'LegacyXrayShareLinkNormalizer.java',legacy+'LegacyXrayDisplay.java',
              *('tests/'+n for n in sorted(MODULE_TESTS))]
    for record in git(dev,'ls-tree','-r','-z','--full-tree',BASE,'--',*prefixes).split(b'\0'):
        if not record: continue
        hdr,path=record.split(b'\t',1);mode,kind,oid=hdr.decode().split();name=os.fsdecode(path)
        assert kind=='blob' and mode in ('100644','100755')
        f=testroot/name;f.parent.mkdir(parents=True,exist_ok=True)
        data=git(dev,'cat-file','blob',oid);assert blob(data)==oid
        f.write_bytes(data);f.chmod(int(mode,8)&0o777)
    results={}
    for name,oid in TESTS.items():
        script=dev/'tests'/name
        assert blob(script.read_bytes())==oid
        if name in OVERLAY_TESTS:
            args=['--old-tv',str(old_tv),'--tv',str(tv)]
            cases=[('baseline-overlay',script,args),('reviewed-overlay',review/'tests'/name,args)]
        elif name in OLD_HOST_TESTS:
            # These tests target the frozen 5.6.3 host, not 5.9 generated APIs.
            cases=[('frozen-original-host',script,[])]
        elif name in MODULE_TESTS:
            cases=[('reviewed-module',testroot/'tests'/name,[])]
        elif name=='test-upstream-recovery-loader.py':
            cases=[('reviewed-recovery',script,['--base-loader',str(tv/PREFIX/'api/loader/BaseLoader.java'),
                   '--coordinator',str(candidate/'tv-recovery/src/main/java/com/fingmi/tvrecovery/NetworkRecoveryCoordinator.java')])]
        else: cases=[('reviewed-candidate',script,['--candidate',str(candidate)])]
        for label,entry,args in cases:
            assert blob(entry.read_bytes())==oid,entry
            key=label+':'+name
            print('BEGIN_EXISTING_TEST',key,oid,flush=True)
            try:
                r=subprocess.run([sys.executable,'-B',str(entry),*args],cwd=work,
                                 stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
                print(r.stdout,end='',flush=True);rc=r.returncode
            except subprocess.TimeoutExpired as e:
                print(e.stdout or b'',flush=True);rc=124
            results[key]=rc
            print('END_EXISTING_TEST',key,'exit',rc,flush=True)
    print('EXISTING_TEST_RESULTS',json.dumps(results,sort_keys=True),flush=True)
    return all(rc==0 for rc in results.values())

def main():
    assert __debug__
    if sys.argv[1:2]==['--guard-worker']:
        guard_worker(Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve(),sys.argv[4:]);return
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('dev','review','old-tv','tv','media','media-default'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();dev=a.dev.resolve();review=a.review.resolve()
    assert dev!=review
    check_input('dev-base',dev,BASE,BASE_TREE)
    check_input('review-before',review,BASE,BASE_TREE)
    for label,(head,tree) in PINS.items():check_input(label,getattr(a,label).resolve(),head,tree)
    for root in (dev,review):
        assert not (root/'signing').exists()
        assert blob((root/RULE_DIR/'prepare_candidate.py').read_bytes())=='3d5b90296ef1fe40aa2e93f7418a4553cc8610a0'
    assert blob((dev/RULE_DIR/'lock.json').read_bytes())==LOCKS[0]
    inputs=[v for label in PINS for v in ('--'+label.replace('_','-'),str(getattr(a,label).resolve()))]
    with tempfile.TemporaryDirectory(prefix='epg-full-source-') as tmp:
        work=Path(tmp);rules=work/'rules'
        subprocess.run([sys.executable,'-I','-B',str(HERE/'prepare_browse_review.py'),
                        '--dev',str(dev),'--old-tv',str(a.old_tv.resolve()),'--tv',str(a.tv.resolve()),
                        '--p2',str(HERE),'--diff',str(HERE/'browse-reviewed-source.diff'),'--out',str(rules)],check=True)
        assert {f.name for f in rules.iterdir()}==set(RULES)
        for name in RULES:
            data=(rules/name).read_bytes();(review/RULE_DIR/name).write_bytes(data)
            print('COMBINED_RULE',name,len(data),blob(data),sha(data),flush=True)
        assert blob((review/RULE_DIR/'lock.json').read_bytes())==LOCKS[1]
        git(review,'diff','--check')
        git(review,'add','--',*(RULE_DIR+n for n in RULES))
        git(review,'-c','user.name=Local review','-c','user.email=local-review@invalid','-c','core.hooksPath=/dev/null',
            '-c','commit.gpgsign=false','commit','--no-gpg-sign','-m','local: replay exact EPG rules')
        assert rev(review,'rev-parse','HEAD^')==BASE
        delta=git(review,'diff-tree','--no-commit-id','--name-status','--no-renames','-r',BASE,'HEAD').decode().splitlines()
        assert sorted(delta)==sorted('M\t'+RULE_DIR+n for n in RULES), delta
        head,tree=rev(review,'rev-parse','HEAD'),rev(review,'rev-parse','HEAD^{tree}')
        check_input('review-local-only',review,head,tree)
        original=run_guard('base',dev,work/'base',inputs)
        reviewed=run_guard('reviewed',review,work/'reviewed',inputs)
        before=work/'base/candidate';after=work/'reviewed/candidate'
        compare(original,reviewed,before,after)
        tests_ok=run_existing_tests(dev,review,after,a.old_tv.resolve(),a.tv.resolve(),work)
        assert manifest(after)==reviewed['files'] and manifest(before)==original['files']
        check_input('dev-after',dev,BASE,BASE_TREE)
        check_input('review-after',review,head,tree)
        for label,(pin,t) in PINS.items():check_input(label+'-after',getattr(a,label).resolve(),pin,t)
        print('ANDROID_BLOCKED_NOT_STARTED; no native AAR or Android runtime claim',flush=True)
        assert tests_ok,'One or more unchanged existing tests failed; see END_EXISTING_TEST'
        print('PASS_114_FULL_SOURCE_REPLAY_AND_EXISTING_TESTS_ONLY',flush=True)

if __name__=='__main__':main()
