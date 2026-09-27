#!/usr/bin/env python3
"""Build a reconstructed Libass compatibility AAR; never claims exact5.6.3 binary provenance.
Uses fixed Media3 input, current recovered Java and pinned5.6.5 SOs. No Android SDK required.
"""
import argparse,hashlib,io,json,os,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[2]
CANDIDATE='0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee'
EXTRACTOR='feb8be30e3d431391ce4b3b165a6cbfb18313969d7ba7da2d6ccfeb96d25ee68'
CONTAINER='930fca2f018f06f1d08c12599f8c97f31eddbd728edee5de06eb53a882f8fc54'
ANDROID='6c0670454f6fcee9f1b17aa393e81d71bf26e7e6ae7c5777ed3924b062191d5b'
DEPS={'com/google/guava/guava/33.3.1-android/guava-33.3.1-android.jar':'2c3e41d1b380f2044d257947a3aa82dabf3ae4b978622745254aa18b6cf89ab0','androidx/annotation/annotation-jvm/1.9.1/annotation-jvm-1.9.1.jar':'1e343917ebf27ba96fe4dc52b1cad7fd32b738fbc6355bb6cd5b3b305d7212d0'}
APK={'armeabi-v7a':'43efc084598782820079347f00e0d26bb2b594ce7087579b8859856c0c6b2132','arm64-v8a':'5ea69f5dab085f25948f4dfac5ef4cf4ed42bc49e54a86e6075fba83b6b46123'}
SO={'armeabi-v7a':'052c81b548649a0a3d697f034640f8c4b00530b6572662b16cc6ca3f6efb1f26','arm64-v8a':'c625360ef9224a516a1092ea757130f4c6f11c63544c50a1b279b654cf4710f7'}
PREFIX=('androidx/media3/exoplayer/libass/','androidx/media3/ui/libass/')
def sha(data):return hashlib.sha256(data).hexdigest()
def checked(path,expected):
 data=path.read_bytes();assert sha(data)==expected,'Unpinned input: '+str(path);return data
def zipped(entries):
 out=io.BytesIO()
 with ZipFile(out,'w',compression=ZIP_DEFLATED) as z:
  for name,data in sorted(entries.items()):
   info=ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data)
 return out.getvalue()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['candidate','extractor','container','v7-apk','v8-apk','android-jar','output']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--local-repository',type=Path,default=Path.home()/'.m2/repository');a=p.parse_args()
 bundle=checked(a.candidate,CANDIDATE);extractor=checked(a.extractor,EXTRACTOR);container=checked(a.container,CONTAINER);checked(a.android_jar,ANDROID)
 deps=[a.local_repository/path for path in DEPS]
 for path,digest in DEPS.items():checked(a.local_repository/path,digest)
 native={}
 for abi,path in [('armeabi-v7a',a.v7_apk),('arm64-v8a',a.v8_apk)]:
  with ZipFile(io.BytesIO(checked(path,APK[abi]))) as apk:native['jni/'+abi+'/libmedia3ass.so']=apk.read('lib/'+abi+'/libmedia3ass.so')
  assert sha(native['jni/'+abi+'/libmedia3ass.so'])==SO[abi]
 with tempfile.TemporaryDirectory(prefix='libass-candidate-') as td:
  work=Path(td);jars=[];owned={};aar_inputs={}
  with ZipFile(io.BytesIO(bundle)) as z:
   aar_inputs={name:z.read(name) for name in z.namelist() if name.endswith('.aar')}
  aar_inputs['lib-extractor-release.aar']=extractor
  aar_inputs['media3-container-1.11.0.aar']=container
  for name,data in sorted(aar_inputs.items()):
   with ZipFile(io.BytesIO(data)) as z:classes=z.read('classes.jar')
   path=work/(Path(name).stem+'.jar');path.write_bytes(classes);jars.append(path)
   with ZipFile(io.BytesIO(classes)) as jar:
    for entry in jar.namelist():
     if not entry.endswith('.class') or entry.endswith('/module-info.class') or entry=='module-info.class':continue
     assert entry not in owned,'Duplicate dependency class '+entry+' in '+name+' and '+owned.get(entry,'')
     owned[entry]=name
  sources=sorted((ROOT/'compat/media3-libass/src/main/java').rglob('*.java'))
  app_sources=[ROOT/'app/src/main/java/androidx/media3/exoplayer'/path for path in ['trackselection/SecondaryTextTrackSelector.java','text/SecondaryTextOutput.java']]
  classes=work/'classes';classes.mkdir()
  command=['java','com.sun.tools.javac.Main','--release','17','-g:none','-Xlint:-classfile','-cp',os.pathsep.join(map(str,[*jars,a.android_jar,*deps])),'-d',str(classes),*map(str,sources+app_sources)]
  subprocess.run(command,check=True)
  produced={str(path.relative_to(classes)):path.read_bytes() for path in classes.rglob('*.class') if str(path.relative_to(classes)).startswith(PREFIX)}
  assert produced and all(name not in owned for name in produced),'Libass collides with dependency classes'
  # Selector/output remain app-owned; tests/fake Android/JNI/GLES are never compiler inputs.
  assert all('/test/' not in name and 'Test' not in name for name in produced)
  aar={**native,'classes.jar':zipped(produced),'AndroidManifest.xml':b'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="androidx.media3.exoplayer.libass"/>\n','R.txt':b'','proguard.txt':b'-keep class androidx.media3.exoplayer.libass.LibassNative { *; }\n-keep class androidx.media3.exoplayer.libass.LibassFrame { *; }\n-keep class androidx.media3.exoplayer.libass.LibassImage { *; }\n'}
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(zipped(aar))
  report={'kind':'reconstructed compatibility candidate, not exact5.6.3 original','candidate_zip_sha256':CANDIDATE,'extractor_aar_sha256':EXTRACTOR,'container_aar_sha256':CONTAINER,'native_source':'neighboring official5.6.5 APKs','apk_sha256':APK,'so_sha256':SO,'aar_sha256':sha(a.output.read_bytes()),'production_class_count':len(produced),'production_class_sha256':{name:sha(data) for name,data in sorted(produced.items())},'source_sha256':{str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in sources+app_sources},'compile_inputs':{'android_all_sha256':ANDROID,'maven':DEPS},'java_runtime':subprocess.check_output(['java','-version'],stderr=subprocess.STDOUT,text=True).strip(),'target_class_major':61,'class_ownership':'Libass only in candidate; selector/output only in app; extractor compatibility replaces original extractor AAR; no duplicate dependency classes','limits':['no full Android Gradle build','no assemble','no EGL/display or device validation']}
  a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
  subprocess.run(['python',str(ROOT/'scripts/build/check-libass-contract.py'),'--aar',str(a.output)],check=True)
  print(json.dumps({key:report[key] for key in ['kind','aar_sha256','production_class_count','native_source','class_ownership']},indent=2))
if __name__=='__main__':main()
