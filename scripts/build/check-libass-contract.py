#!/usr/bin/env python3
"""Fail closed on old Libass Java/JNI ABI. Does not certify complete player API or rendering.
--aar checks a built artifact; --source checks reconstructed JNI declarations against both published SOs.
"""
import argparse,hashlib,importlib.util,json,re,subprocess,tempfile
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('elf_contract',ROOT/'recovery/libass-tests/contract.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=json.loads((ROOT/'recovery/libass-tests/published-565-contract.json').read_text())
def java_methods(cp,name):
 out=subprocess.check_output(['java','com.sun.tools.javap.Main','-p','-s','-classpath',str(cp),'androidx.media3.exoplayer.libass.'+name],text=True)
 return {name:desc for name,desc in re.findall(r'(\w+)\([^;]*?\);\s*descriptor:\s*(\S+)',out)}
def verify_elf(data,abi):
 assert hashlib.sha256(data).hexdigest()==E['abis'][abi]['sha256'],'Unpinned Libass native binary'
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
   src=ROOT/'compat/media3-libass/src/main/java/androidx/media3/exoplayer/libass'
   # This gate checks the JNI boundary; Android/player source compilation is separate.
   files=[src/name for name in ['LibassNative.java','LibassFrame.java','LibassImage.java']]
   subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-d',str(cp),*map(str,files)],check=True)
  if a.aar:
   public={
    'androidx.media3.exoplayer.libass.LibassPlaybackSession':{
     ('LibassPlaybackSession','(Landroidx/media3/exoplayer/libass/LibassConfiguration;Z)V'),
     ('isAvailable','()Z'),('createClockRenderer','()Landroidx/media3/exoplayer/Renderer;'),
     ('createMediaComponents','(Landroidx/media3/common/MediaItem;Landroidx/media3/extractor/ExtractorsFactory;)Landroidx/media3/exoplayer/libass/LibassPlaybackSession$MediaComponents;'),
     ('setPreloadMediaItem','(Landroidx/media3/common/MediaItem;)V'),('setFontScale','(FZ)V'),
     ('setBottomPositionFraction','(F)V'),('setSecondaryBottomPositionFraction','(F)V'),('close','()V')},
    'androidx.media3.exoplayer.libass.LibassSubtitleController':{
     ('LibassSubtitleController','(Landroidx/media3/exoplayer/ExoPlayer;Landroidx/media3/exoplayer/libass/LibassPlaybackSession;Landroidx/media3/exoplayer/trackselection/SecondaryTextTrackSelector$Factory;Landroidx/media3/exoplayer/text/SecondaryTextOutput;)V'),
     ('getPrimaryTextTrackSelectionOverride','()Landroidx/media3/common/TrackSelectionOverride;'),('getSecondaryTextTrackSelectionOverride','()Landroidx/media3/common/TrackSelectionOverride;'),
     ('getSecondaryTextTrackSelectionOverrides','()Ljava/util/List;'),('isSecondaryTextTrackSuppressed','()Z'),('setSecondaryTextTrackSelectionOverride','(Landroidx/media3/common/TrackSelectionOverride;)V'),('setSecondaryTextTrackAutoSelectionEnabled','(Z)V'),('close','()V')},
    'androidx.media3.ui.libass.LibassPlayerViewController':{
     ('LibassPlayerViewController','(Landroidx/media3/common/Player;Landroidx/media3/exoplayer/libass/LibassPlaybackSession;Landroidx/media3/exoplayer/libass/LibassSubtitleController;)V'),
     ('bind','(Landroidx/media3/ui/PlayerView;)V'),('setStyleOverride','(Landroidx/media3/ui/CaptionStyleCompat;Ljava/lang/String;)V'),('setSecondarySubtitleViewConfigurator','(Ljava/util/function/Consumer;)V'),('close','()V')}
   }
   for name,required in public.items():
    output=subprocess.check_output(['java','com.sun.tools.javap.Main','-public','-s','-classpath',str(cp),name],text=True)
    found=set(re.findall(r'(\w+)\([^;]*?\);\s*descriptor:\s*(\S+)',output))
    assert required<=found,'Missing production public API: '+name+' '+str(required-found)
   output=subprocess.check_output(['java','com.sun.tools.javap.Main','-public','-s','-classpath',str(cp),'androidx.media3.exoplayer.libass.LibassPlaybackSession$MediaComponents'],text=True)
   for field,kind in [('extractorsFactory','androidx/media3/extractor/ExtractorsFactory'),('subtitleParserFactory','androidx/media3/extractor/text/SubtitleParser$Factory')]:
    assert re.search(re.escape(field)+r';\s*descriptor: '+re.escape('L'+kind+';'),output),'Missing MediaComponents field '+field
  expected={r['name']:r['descriptor'] for r in E['abis']['armeabi-v7a']['methods']}
  got=java_methods(cp,'LibassNative');got.pop('LibassNative',None)
  assert got==expected,'Java native declarations differ from published RegisterNatives'
  for name,descriptor in E['constructors'].items():assert java_methods(cp,name).get(name)==descriptor,'JNI constructor mismatch: '+name
 print('PASS:17 native signatures +2 JNI constructors and pinned hashes match both ABIs; built AAR also checks app-facing production APIs (not app/EGL certification)')
if __name__=='__main__':main()
