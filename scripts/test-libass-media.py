#!/usr/bin/env python3
"""Compile recovered Libass sources against real Media3/Android; deterministic media-state tests.
The test-only JNI double is generated into the test directory, never production classes or AARs.
"""
import argparse,hashlib,io,os,shutil,subprocess,tempfile,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--extractor',type=Path,required=True);p.add_argument('--container',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--workdir',type=Path,required=True);p.add_argument('--maven',required=True);p.add_argument('--local-repository',type=Path,default=Path.home()/'.m2/repository');a=p.parse_args()
 assert hashlib.sha256(a.candidate.read_bytes()).hexdigest()=='0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee'
 work=a.workdir.resolve();(work/'jars').mkdir(parents=True,exist_ok=True)
 with ZipFile(a.candidate) as bundle:
  for name in ['common','exoplayer','datasource']:
   with ZipFile(io.BytesIO(bundle.read('lib-'+name+'-release.aar'))) as aar:(work/('jars/lib-'+name+'-release.jar')).write_bytes(aar.read('classes.jar'))
 assert hashlib.sha256(a.extractor.read_bytes()).hexdigest()=='22ed5d53e6a6977faf12a97d9bdfb97f1cfea9cb39ccfc6418fa1899d3669e6b'
 assert hashlib.sha256(a.container.read_bytes()).hexdigest()=='930fca2f018f06f1d08c12599f8c97f31eddbd728edee5de06eb53a882f8fc54'
 for path,name in [(a.extractor,'extractor'),(a.container,'container')]:
  with ZipFile(path) as aar:(work/('jars/lib-'+name+'-release.jar')).write_bytes(aar.read('classes.jar'))
 tests=work/'tests/androidx/media3/exoplayer/libass';tests.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(ROOT/'recovery/libass-tests/java/androidx/media3/exoplayer/libass/LibassNative.java',tests/'LibassNative.java')
 for test in (ROOT/'recovery/libass-tests/media/src/test/java/androidx/media3/exoplayer/libass').glob('*Test.java'):
  shutil.copyfile(test,tests/test.name)
 cmd=[str(Path(a.maven).resolve()),'-B','-f',str(ROOT/'recovery/libass-tests/media/pom.xml'),'-Dlibass.work='+str(work),'-Drecovery.root='+str(ROOT),'-Dmaven.repo.local='+str(a.local_repository.resolve())]
 settings=ET.Element('settings');proxies=ET.SubElement(settings,'proxies')
 for protocol in ['http','https']:
  address=os.environ.get(protocol.upper()+'_PROXY')
  if not address:continue
  u=urllib.parse.urlsplit(address);proxy=ET.SubElement(proxies,'proxy')
  for k,v in [('id',protocol),('active','true'),('protocol',protocol),('host',u.hostname),('port',str(u.port or 80))]:ET.SubElement(proxy,k).text=v
  if u.username:ET.SubElement(proxy,'username').text=urllib.parse.unquote(u.username)
  if u.password:ET.SubElement(proxy,'password').text=urllib.parse.unquote(u.password)
  cmd+=['-D'+protocol+'.proxyHost='+u.hostname,'-D'+protocol+'.proxyPort='+str(u.port or 80)]
 with tempfile.TemporaryDirectory(prefix='libass-media-settings-') as td:
  settings_path=Path(td)/'settings.xml';ET.ElementTree(settings).write(settings_path);cmd+=['-s',str(settings_path)]
  subprocess.run(cmd+['test-compile'],check=True)
  for artifact,name in [('androidx/test/monitor/1.7.2/monitor-1.7.2.aar','monitor'),('androidx/test/espresso/espresso-idling-resource/3.6.1/espresso-idling-resource-3.6.1.aar','espresso')]:
   directory=work/'target'/name;directory.mkdir(parents=True,exist_ok=True)
   with ZipFile(a.local_repository/artifact) as aar:(directory/'classes.jar').write_bytes(aar.read('classes.jar'))
  subprocess.run(cmd+['test'],check=True)
 print('PASS recovered Libass source compile and Media3 tests (counts in surefire reports); instrumented JNI, not full app/EGL build')
if __name__=='__main__':main()
