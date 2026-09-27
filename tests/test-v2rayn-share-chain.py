#!/usr/bin/env python3
"""13 source-derived v2rayN formats through current :xray Java and published v7 JNI.

--capture creates, never overwrites, a frozen oracle. Normal runs compare it.
Only certificate probe I/O and Android pin persistence are test doubles.
No actual v2rayN process, node connection, ART or playback is asserted.
"""
import argparse, hashlib, importlib.util, json, subprocess, tempfile, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'recovery/v2rayn-tests'
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['workdir','jni','bridge','qemu','android-root']:p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--capture',action='store_true');a=p.parse_args();a.workdir.mkdir(parents=True,exist_ok=True)
    old=module(ROOT/'tests/test-native-share-chain.py','chain_util')
    jar=a.workdir/'json.jar';url,digest=old.JARS['json.jar']
    if not jar.exists():
        with urllib.request.urlopen(url,timeout=90) as r:jar.write_bytes(r.read())
    assert hashlib.sha256(jar.read_bytes()).hexdigest()==digest
    src=ROOT/'xray/src/main/java/com/fingmi/xray'
    files=list((FIX/'java').rglob('*.java'))+[src/x for x in ['config/XrayShareLinkNormalizer.java','config/XrayConfigFactory.java','security/XrayShareLinkSecurity.java','core/LibXrayBridge.java']]
    native=module(ROOT/'scripts/recovery/run-published-libxray-converter.py','native')
    generated=module(FIX/'generate.py','exporter')
    assert json.loads((FIX/'inputs.json').read_text())==generated.rows,'Fixture differs from exporter model'
    with tempfile.TemporaryDirectory(dir=a.workdir) as td:
        td=Path(td).resolve();classes=td/'classes';classes.mkdir()
        subprocess.run(['java','com.sun.tools.javac.Main','--release','17','-cp',str(jar.resolve()),'-d',str(classes),*map(str,files)],check=True)
        cmd=['java','-cp',str(jar.resolve())+':'+str(classes),'V2rayNChain']
        inp=str(FIX/'inputs.json');norm=td/'normalized.json';conv=td/'native.json';runtime=td/'runtime.json'
        subprocess.run(cmd+['normalize',inp,str(norm)],check=True)
        normalized=json.loads(norm.read_text())
        converted=native.capture(normalized,a.jni,a.bridge,a.qemu,a.android_root)
        assert all(c['response']['success'] for c in converted['cases'])
        conv.write_text(json.dumps(converted))
        subprocess.run(cmd+['runtime',inp,str(conv),str(runtime)],check=True)
        configs=json.loads(runtime.read_text())
        validation=native.capture(configs,a.jni,a.bridge,a.qemu,a.android_root)
        assert all(c['response']['success'] for c in validation['cases']),validation
        observed=dict(schema=1,exporter_commit=generated.SHA,jni_sha256=native.PIN,
                      normalized=normalized,conversion=[dict(id=c['id'],response=c['response']) for c in converted['cases']],
                      runtime=[dict(id=c['id'],runtime=c['runtime']) for c in configs],
                      validation=[dict(id=c['id'],response=c['response']) for c in validation['cases']])
        checks=module(FIX/'assertions.py','checks');checks.verify(generated.rows,observed)
        oracle=FIX/'published-v7.json'
        if a.capture:
            with oracle.open('x') as f:json.dump(observed,f,indent=2);f.write('\n')
        else:
            assert json.loads(oracle.read_text())==observed,'Published chain regression'
        print('PASS: 13 exporter-format -> current Java -> published converter -> current runtime -> native testXray chains')
if __name__=='__main__':main()
