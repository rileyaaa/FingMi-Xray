#!/usr/bin/env python3
"""Execute pinned 5.6.8 v7 JNI_OnLoad and native library/track lifecycle with fake JNI table.
Reuses prepared Android API24/QEMU/cross compiler; no ART/rendering claim.
"""
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workdir',type=Path,required=True);p.add_argument('--jni',type=Path,required=True);a=p.parse_args()
 e=json.loads((ROOT/'compat/media3-libass/tests/published-568-native-contract.json').read_text())
 assert hashlib.sha256(a.jni.read_bytes()).hexdigest()==e['abis']['armeabi-v7a']['sha256']
 work=a.workdir.resolve();cc=work/'cross/usr/bin';android=work/'android/root'
 with tempfile.TemporaryDirectory(prefix='libass-jni-') as td:
  td=Path(td);jni=td/'libmedia3ass.so';jni.write_bytes(a.jni.read_bytes());bridge=td/'bridge'
  env=os.environ.copy();env['LD_LIBRARY_PATH']=str(work/'cross/usr/lib/x86_64-linux-gnu')
  subprocess.run([str(cc/'arm-linux-gnueabi-gcc-12'),'-B',str(cc)+'/', '-nostdlib','-fPIC','-fno-stack-protector','-pie','-Wl,-e,_start','-Wl,--dynamic-linker=/system/bin/linker','-Wl,--hash-style=sysv','-Wl,--allow-shlib-undefined','-o',str(bridge),str(ROOT/'compat/media3-libass/tests/jni_load_bridge.c'),str(jni),str(android/'system/lib/libc.so')],env=env,check=True)
  r=subprocess.run([str(work/'qemu/usr/bin/qemu-arm-static'),'-L',str(android),'-E','LD_LIBRARY_PATH='+str(td)+':'+str(android/'system/lib'),str(bridge)],capture_output=True,text=True,timeout=60)
  assert r.returncode==0,r.stderr
  rows=[l.split('\t') for l in r.stdout.splitlines()]
  methods={x[1]:x[2] for x in rows if x[0]=='METHOD'}
  assert methods=={x['name']:x['descriptor'] for x in e['abis']['armeabi-v7a']['methods']}
  constructors={x[1].split('/')[-1]:x[3] for x in rows if x[0]=='CONSTRUCTOR'}
  assert constructors==e['constructors']
  assert any(x[0]=='PASS' for x in rows) and not any(x[0]=='THROW' for x in rows)
  assert sum(x[0]=='EXPECTED_THROW' for x in rows)==1
  assert sum(x[0]=='EXPECTED_FAILURE' for x in rows)==1
  print('PASS: 5.6.8 v7 JNI_OnLoad17 methods/2 constructors + library/track lifecycle + null-handle/UTF-acquisition failure recovery')
if __name__=='__main__':main()
