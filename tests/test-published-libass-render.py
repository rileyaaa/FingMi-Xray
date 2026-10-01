#!/usr/bin/env python3
"""Synthetic ASS/font -> pinned 5.6.8 v7 renderer; compare against the frozen 5.6.5 render oracle."""
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FONT_SHA='ae7b7855e115a5966d8b1b3f80f254ccc117ec86f9965e202ee2940453837280'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workdir',type=Path,required=True);p.add_argument('--jni',type=Path,required=True);p.add_argument('--abi',choices=['armeabi-v7a','arm64-v8a'],default='armeabi-v7a');p.add_argument('--font',type=Path,required=True);p.add_argument('--capture',action='store_true');a=p.parse_args()
 e=json.loads((ROOT/'compat/media3-libass/tests/published-568-native-contract.json').read_text())
 expected=e['abis'][a.abi]
 assert hashlib.sha256(a.jni.read_bytes()).hexdigest()==expected['sha256']
 assert hashlib.sha256(a.font.read_bytes()).hexdigest()==FONT_SHA
 arm64=a.abi=='arm64-v8a'
 work=a.workdir.resolve();cc=work/'cross/usr/bin';android=work/'android/root'
 compiler=cc/('aarch64-linux-gnu-gcc-12' if arm64 else 'arm-linux-gnueabi-gcc-12')
 qemu=work/('qemu/usr/bin/qemu-aarch64-static' if arm64 else 'qemu/usr/bin/qemu-arm-static')
 libdir='lib64' if arm64 else 'lib'
 linker='linker64' if arm64 else 'linker'
 with tempfile.TemporaryDirectory(prefix='libass-render-') as td:
  td=Path(td);jni=td/'libmedia3ass.so';jni.write_bytes(a.jni.read_bytes());bridge=td/'bridge'
  fonts=td/'fonts';fonts.mkdir();(fonts/'DejaVuSans.ttf').write_bytes(a.font.read_bytes());cache=td/'cache';cache.mkdir();fc=td/'fontconfig.xml'
  fc.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>{fonts}</dir><cachedir>{cache}</cachedir></fontconfig>')
  env=os.environ.copy();env['LD_LIBRARY_PATH']=str(work/'cross/usr/lib/x86_64-linux-gnu')
  subprocess.run([str(compiler),'-B',str(cc)+'/', '-nostdlib','-fPIC','-fno-stack-protector','-pie','-Wl,-e,_start','-Wl,--dynamic-linker=/system/bin/'+linker,'-Wl,--hash-style=sysv','-Wl,--allow-shlib-undefined','-DFONT_CONFIG="'+str(fc)+'"','-o',str(bridge),str(ROOT/'compat/media3-libass/tests/jni_render_bridge.c'),str(jni),str(android/'system'/libdir/'libc.so')],env=env,check=True)
  r=subprocess.run([str(qemu),'-L',str(android),'-E','LD_LIBRARY_PATH='+str(td)+':'+str(android/'system'/libdir),str(bridge)],capture_output=True,text=True,timeout=60)
  assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
  frames=[json.loads(l.split('\t',1)[1]) for l in r.stdout.splitlines() if l.startswith('FRAME\t')]
  assert len(frames)==8 and frames[0]['images'] and any(i['bytes']>0 for i in frames[0]['images'])
  result=dict(jni_sha256=expected['sha256'],font_sha256=FONT_SHA,runtime=f'QEMU {a.abi}/API24 Bionic, fake JNI objects, no EGL context; GPU-request case only verifies CPU fallback',frames=frames)
  oracle=ROOT/'compat/media3-libass/tests/published-565-render.json'
  if a.capture:
   with oracle.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
  else:
   frozen=json.loads(oracle.read_text())
   assert frames==frozen['frames'],'Published rendering regression'
  print(f'PASS: 5.6.8 {a.abi} synthetic ASS rendering matches frozen 5.6.5 glyph masks/positions; no EGL/ART claim')
if __name__=='__main__':main()
