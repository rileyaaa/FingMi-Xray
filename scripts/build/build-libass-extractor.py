#!/usr/bin/env python3
"""Restore exact historical upstream Libass hooks in the pinned Media3 extractor; test and repack AAR.

Only MatroskaExtractor, SubtitleParser, SubtitleTranscodingTrackOutput and their nested classes change.
This is one prerequisite, not a complete Libass AAR.
"""
import argparse,hashlib,io,json,os,subprocess,tempfile,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[2]
SOURCE='libraries/extractor/src/main/java/androidx/media3/extractor/mkv/MatroskaExtractor.java'
SOURCE_SHA='84e01966733fec404de062fce4aa5c221af432c570afcef9eb1ad0cab07f495f'
RESTORED_SHA='203c3ef5626afa3bc0401befc07a347a3e32e6e2b835b0164b0c05eeba1560db'
COPY_SHA='4acaaa255e7a8b2a33fa1978c655d83cb9cb47d0ce3999b25838e07088b205da'
CONTAINER_SHA='930fca2f018f06f1d08c12599f8c97f31eddbd728edee5de06eb53a882f8fc54'
TIMED_SOURCES={
 'SubtitleParser':('631eaf8c4176a279925d3b956706f97284119c0554a20d9b82c9c184fbe0dc02','174116a743448a5a9c5e9125b2ae0e2b45637b7b00b1902184c6e8d69263388e'),
 'SubtitleTranscodingTrackOutput':('89e6cbc1ce76730ef08d69da12c779616b2618a51d83b81ef9a7ec9136592d87','6ac767d9e13270780e38ad16ae6fd607a69c2a6b0c056f74e82792a71ba7bf3c')}
PREFIXES=['androidx/media3/extractor/mkv/MatroskaExtractor']+['androidx/media3/extractor/text/'+n for n in TIMED_SOURCES]
def sha(b):return hashlib.sha256(b).hexdigest()
def write_zip(entries):
 b=io.BytesIO()
 with ZipFile(b,'w',compression=ZIP_DEFLATED) as z:
  for name,data in sorted(entries.items()):
   info=ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data)
 return b.getvalue()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--workdir',type=Path,required=True);p.add_argument('--maven',required=True);p.add_argument('--source',type=Path);p.add_argument('--source-root',type=Path);p.add_argument('--container',type=Path);p.add_argument('--local-repository',type=Path,default=Path.home()/'.m2/repository');a=p.parse_args()
 assert sha(a.candidate.read_bytes())=='0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee'
 work=a.workdir.resolve();(work/'jars').mkdir(parents=True,exist_ok=True)
 # Official same-version container is an explicit upstream extractor dependency, absent from
 # the16-AAR candidate bundle; use the real artifact rather than substitute its classes.
 container=a.container or work/'media3-container-1.11.0.aar'
 if not container.exists():
  with urllib.request.urlopen('https://dl.google.com/dl/android/maven2/androidx/media3/media3-container/1.11.0/media3-container-1.11.0.aar') as r:container.write_bytes(r.read())
 assert sha(container.read_bytes())==CONTAINER_SHA
 with ZipFile(container) as z:(work/'jars/media3-container.jar').write_bytes(z.read('classes.jar'))
 with ZipFile(a.candidate) as bundle:
  aar=bundle.read('lib-extractor-release.aar')
  for name in ['common','extractor']:
   with ZipFile(io.BytesIO(bundle.read('lib-'+name+'-release.aar'))) as z:(work/'jars'/('lib-'+name+'-release.jar')).write_bytes(z.read('classes.jar'))
 if a.source_root:source=(a.source_root/SOURCE).read_bytes()
 elif a.source:source=a.source.read_bytes()
 else:
  with urllib.request.urlopen('https://raw.githubusercontent.com/FongMi/media/3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d/'+SOURCE) as r:source=r.read()
 assert sha(source)==SOURCE_SHA,'Wrong fixed source'
 target=work/'source'/SOURCE;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source)
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/'compat/media3-libass/patches/matroska-libass-hooks.patch')],cwd=work/'source',check=True)
 assert sha(target.read_bytes())==RESTORED_SHA,'Restored source must be byte-identical to real upstream9dae39e9'
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/'compat/media3-libass/patches/matroska-libass-copy.patch')],cwd=work/'source',check=True)
 assert sha(target.read_bytes())==COPY_SHA
 for name,(before,after) in TIMED_SOURCES.items():
  path='libraries/extractor/src/main/java/androidx/media3/extractor/text/'+name+'.java'
  original=a.source_root/path if a.source_root else work/'input'/path
  if not original.exists():
   original.parent.mkdir(parents=True,exist_ok=True)
   with urllib.request.urlopen('https://raw.githubusercontent.com/FongMi/media/3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d/'+path) as r:original.write_bytes(r.read())
  content=original.read_bytes();assert sha(content)==before,'Wrong fixed timed-parser source'
  destination=work/'source'/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/'compat/media3-libass/patches/subtitle-sample-time.patch')],cwd=work/'source',check=True)
 for name,(before,after) in TIMED_SOURCES.items():assert sha((work/'source/libraries/extractor/src/main/java/androidx/media3/extractor/text'/ (name+'.java')).read_bytes())==after
 cmd=[str(Path(a.maven).resolve()),'-B','-f',str(ROOT/'compat/media3-libass/tests/matroska/pom.xml'),'-Dlibass.work='+str(work),'-Dmaven.repo.local='+str(a.local_repository.resolve())]
 settings=ET.Element('settings');proxies=ET.SubElement(settings,'proxies')
 for protocol in ['http','https']:
  value=os.environ.get(protocol.upper()+'_PROXY')
  if not value:continue
  u=urllib.parse.urlsplit(value);proxy=ET.SubElement(proxies,'proxy')
  for k,v in [('id',protocol),('active','true'),('protocol',protocol),('host',u.hostname),('port',str(u.port or 80))]:ET.SubElement(proxy,k).text=v
  if u.username:ET.SubElement(proxy,'username').text=urllib.parse.unquote(u.username)
  if u.password:ET.SubElement(proxy,'password').text=urllib.parse.unquote(u.password)
  cmd += ['-D'+protocol+'.proxyHost='+u.hostname,'-D'+protocol+'.proxyPort='+str(u.port or 80)]
 with tempfile.TemporaryDirectory(prefix='libass-maven-settings-') as td:
  settings_path=Path(td)/'settings.xml';ET.ElementTree(settings).write(settings_path);cmd+=['-s',str(settings_path)]
  subprocess.run(cmd+['test-compile'],check=True)
  for artifact,name in [('androidx/test/monitor/1.7.2/monitor-1.7.2.aar','monitor'),('androidx/test/espresso/espresso-idling-resource/3.6.1/espresso-idling-resource-3.6.1.aar','espresso')]:
   d=work/'target'/name;d.mkdir(parents=True,exist_ok=True)
   with ZipFile(a.local_repository/artifact) as z:(d/'classes.jar').write_bytes(z.read('classes.jar'))
  subprocess.run(cmd+['test'],check=True)
 with ZipFile(io.BytesIO(aar)) as z:entries={n:z.read(n) for n in z.namelist()}
 with ZipFile(io.BytesIO(entries['classes.jar'])) as z:original={n:z.read(n) for n in z.namelist()}
 def selected(n):return any(n==prefix+'.class' or n.startswith(prefix+'$') and n.endswith('.class') for prefix in PREFIXES)
 classes={n:b for n,b in original.items() if not selected(n)}
 produced={str(f.relative_to(work/'target/classes')):f.read_bytes() for f in (work/'target/classes').rglob('*.class')}
 assert produced and all(selected(n) for n in produced),'Unexpected compiled classes'
 classes.update(produced)
 assert all(classes[n]==b for n,b in original.items() if not selected(n))
 entries['classes.jar']=write_zip(classes);out=work/'lib-extractor-libass-release.aar';out.write_bytes(write_zip(entries))
 report={'candidate_zip_sha256':sha(a.candidate.read_bytes()),'original_source_sha256':SOURCE_SHA,'restored_source_sha256':RESTORED_SHA,'integration_source_sha256':COPY_SHA,'source_provenance':'Matroska: real FongMi/media@9dae39e9689ee305c83f94bd11cf3bcecb9d6171 source plus reconstructed configuration-preserving constructor; timed parser: reconstructed published5.6.5 behavior','reconstructed_timed_parser_source_sha256':TIMED_SOURCES,'official_container_aar_sha256':CONTAINER_SHA,'original_extractor_aar_sha256':sha(aar),'output_aar_sha256':sha(out.read_bytes()),'replaced_classes':sorted(produced),'other_class_contents_unchanged':True,'tests':'5 synthetic public extractor read-path tests plus4 timed-parser propagation/compatibility tests and1 flags-copy test','limitation':'restores Matroska callbacks and parser timestamps; not a complete newer Libass API/AAR'}
 (work/'extractor-evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
