#!/usr/bin/env python3
"""Fail closed on old Libass Java/JNI ABI. Does not certify complete player API or rendering.
--aar checks a built artifact; --source checks reconstructed JNI declarations against both published SOs.
"""
import argparse,importlib.util,json,re,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('elf_contract',ROOT/'recovery/libass-tests/contract.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=json.loads((ROOT/'recovery/libass-tests/published-565-contract.json').read_text())
def java_methods(cp,name):
 out=subprocess.check_output(['java','com.sun.tools.javap.Main','-p','-s','-classpath',str(cp),'androidx.media3.exoplayer.libass.'+name],text=True)
 return {name:desc for name,desc in re.findall(r'(\w+)\([^;]*?\);\s*descriptor:\s*(\S+)',out)}
def verify_elf(data,abi):
 elf=m.ELF(data);assert elf.machine==E['abis'][abi]['elf_machine'],'Wrong ELF machine'
 got={r['name']:r['descriptor'] for r in elf.methods()}
 expected={r['name']:r['descriptor'] for r in E['abis'][abi]['methods']}
 assert got==expected,'JNI method table differs: '+str(sorted(set(got.items())^set(expected.items())))
def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--aar',type=Path);g.add_argument('--source',action='store_true');p.add_argument('--v7-so',type=Path);p.add_argument('--v8-so',type=Path);a=p.parse_args()
 with tempfile.TemporaryDirectory(prefix='libass-contract-') as td:
  td=Path(td)
  if a.aar:
   with ZipFile(a.aar) as z:
    cp=td/'classes.jar';cp.write_bytes(z.read('classes.jar'))
    for abi in E['abis']:verify_elf(z.read('jni/'+abi+'/libmedia3ass.so'),abi)
  else:
   assert a.v7_so and a.v8_so,'--source requires both published SO paths'
   for abi,path in [('armeabi-v7a',a.v7_so),('arm64-v8a',a.v8_so)]:
    import hashlib
    assert hashlib.sha256(path.read_bytes()).hexdigest()==E['abis'][abi]['sha256'],'Not pinned published SO'
    verify_elf(path.read_bytes(),abi)
   cp=td/'classes';cp.mkdir()
   src=ROOT/'recovery/media3-libass/src/main/java/androidx/media3/exoplayer/libass'
   subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-d',str(cp),*map(str,src.glob("*.java"))],check=True)
  expected={r['name']:r['descriptor'] for r in E['abis']['armeabi-v7a']['methods']}
  got=java_methods(cp,'LibassNative');got.pop('LibassNative',None)
  assert got==expected,'Java native declarations differ from published RegisterNatives'
  for name,descriptor in E['constructors'].items():assert java_methods(cp,name).get(name)==descriptor,'JNI constructor mismatch: '+name
 print('PASS:17 native signatures +2 Java constructors match both ABI contracts (not complete Libass/player certification)')
if __name__=='__main__':main()
