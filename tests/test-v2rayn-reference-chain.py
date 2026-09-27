#!/usr/bin/env python3
"""Separate raw JNI oracle, frozen DEX-recovered Java reference, and current :xray.
Private inputs never become fixtures; no original link or native payload is logged.
The frozen Java is reconstructed/Dex-verified, not ART execution. Probe I/O is synthetic.
"""
import argparse,json,re,subprocess,tempfile
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for x in ['workdir','jni','bridge','qemu','android-root']:p.add_argument('--'+x,type=Path,required=True)
 p.add_argument('--private-input',type=Path);p.add_argument('--capture',action='store_true');a=p.parse_args()
 if a.private_input and a.capture:p.error('Private input capture is prohibited')
 a.workdir.mkdir(parents=True,exist_ok=True)
 native=module(ROOT/'scripts/recovery/run-published-libxray-converter.py','native')
 if a.private_input:
  links=re.findall(r'(?:vmess|vless|trojan|hy2|hysteria2)://[^\s`<>]+',a.private_input.read_text())
  assert len(links)==5,'Expected exactly five links'
  rows=[dict(id='private-'+str(i),raw=u) for i,u in enumerate(links)]
 else:rows=json.loads((ROOT/'recovery/v2rayn-tests/real-shape-inputs.json').read_text())
 jar=(a.workdir/'json.jar').resolve();assert jar.exists(),'Run test-v2rayn-share-chain.py first for pinned JSON jar'
 import hashlib
 assert hashlib.sha256(jar.read_bytes()).hexdigest()=='3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed'
 def run(cmd):
  r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if r.returncode:raise RuntimeError('Java chain failed; details suppressed to protect private node inputs')
 def capture(cases):return native.capture(cases,a.jni,a.bridge,a.qemu,a.android_root)
 with tempfile.TemporaryDirectory(prefix='private-share-',dir=a.workdir) as td:
  td=Path(td).resolve();inp=td/'inputs.json';inp.write_text(json.dumps(rows));commands={}
  for variant in ['reference','current']:
   classes=td/variant;classes.mkdir()
   if variant=='reference':
    src=ROOT/'recovery/legacy-src/com/fongmi/android/tv/xray/legacy'
    files=list((ROOT/'recovery/native-tests/java').rglob('*.java'))+[src/(x+'.java') for x in ['LegacyLibXrayApi','LegacyXrayProbeApi','LegacyXrayShareLinkNormalizer','LegacyXrayTransportSecurity','LegacyXrayRuntimeConfigFactory']];entry='NativeChain'
   else:
    src=ROOT/'xray/src/main/java/com/fingmi/xray'
    files=list((ROOT/'recovery/v2rayn-tests/java').rglob('*.java'))+[src/x for x in ['config/XrayConfigFactory.java','config/XrayShareLinkNormalizer.java','core/LibXrayBridge.java','security/XrayShareLinkSecurity.java']];entry='V2rayNChain'
   run(['java','com.sun.tools.javac.Main','--release','17','-cp',str(jar),'-d',str(classes),*map(str,files)])
   commands[variant]=['java','-cp',str(jar)+':'+str(classes),entry]
  raw=capture([dict(id=r['id'],request=dict(apiVersion=2,method='convertShareLinksToXrayJson',payload=dict(text=r['raw']))) for r in rows])
  normalized={}
  for variant,cmd in commands.items():
   dest=td/(variant+'-normalize.json');run(cmd+['normalize',str(inp),str(dest)]);normalized[variant]=json.loads(dest.read_text())
  for ref,cur in zip(normalized['reference'],normalized['current']):
   assert all(ref[k]==cur[k] for k in ['raw','normalized','secured','finalLink','request']),'Reference/current normalization mismatch'
  converted=capture(normalized['reference']);assert all(c['response']['success'] for c in converted['cases']),'Reference native conversion rejected'
  conv=td/'native.json';conv.write_text(json.dumps(converted));runtimes={}
  for variant,cmd in commands.items():
   dest=td/(variant+'-runtime.json');run(cmd+['runtime',str(inp),str(conv),str(dest)]);runtimes[variant]=json.loads(dest.read_text())
  assert [c['runtime'] for c in runtimes['reference']]==[c['runtime'] for c in runtimes['current']],'Reference/current runtime mismatch'
  tested=capture(runtimes['current']);assert all(c['response']['success'] for c in tested['cases']),'Native testXray rejected'
  result=dict(schema=1,jni_sha256=native.PIN,java_reference='frozen recovery/legacy-src; DEX-verified reconstructed behavior, not ART',
   raw=[dict(id=c['id'],response=c['response']) for c in raw['cases']],normalized=normalized['reference'],
   conversion=[dict(id=c['id'],response=c['response']) for c in converted['cases']],
   runtime=[dict(id=c['id'],runtime=c['runtime']) for c in runtimes['reference']],validation=[dict(id=c['id'],response=c['response']) for c in tested['cases']])
  if not a.private_input:
   oracle=ROOT/'recovery/v2rayn-tests/published-v7-reference.json'
   if a.capture:
    with oracle.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
   else:assert result==json.loads(oracle.read_text()),'Published/reference oracle mismatch'
  print('PASS: five '+('private (not persisted)' if a.private_input else 'synthetic')+' inputs; raw published JNI + frozen Java reference/native + current Java equivalence + published testXray')
if __name__=='__main__':main()
