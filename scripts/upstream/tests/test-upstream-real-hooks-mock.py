import importlib.util
import contextlib
import io
from pathlib import Path
import sys
import types

called=[]
markers = ('versionName "v5.8.7-xray.1"', 'versionCode 587001',
           'new FongMiNetworkRecovery(', 'checkNetworkGeneration();',
           'Intentionally disabled upstream APK updater', 'public void start(',
           'case "xray" -> onXray(params);', 'XrayImportEvent.post(link.trim());',
           'mBinding.xray.setOnClickListener', 'SettingXrayActivity.start(this);',
           'android:id="@+id/xray"', 'android:id="@+id/xrayText"',
           'cancelResultRequest()', 'clear(Runnable onComplete)',
           'resetApiNetworkForResume', 'resetForNetworkChange',
           'resetNetworkFailures', 'new OkHttpUrlLoader.Factory')

def good(label):
    def fn(text, *a):
        called.append(label)
        return 'GENERATED ' + '\n'.join(markers)
    return fn

def bad(label):
    def fn(text, *a):
        called.append(label)
        raise ValueError('pretend upstream drift ' + label)
    return fn

class AnyTree(dict):
    def __contains__(self, key): return True
    def __getitem__(self,key): return ('100644',key)

mods={}
for module in ('sync','prepare_release','recovery_adapters','xray_adapters'):
    obj=types.ModuleType(module)
    sys.modules[module]=mods[module]=obj
mods['sync'].git_tree=lambda repo,target:AnyTree()
mods['sync'].upstream_version=lambda repo,target:('5.8.7',587)
mods['sync'].blob=lambda repo,entry:b'ORIGINAL'
for module, names in [
    ('prepare_release',('gradle','home')),
    ('recovery_adapters',('site_view_model','base_loader','ok_http','ok_dns','img_util','ok_glide')),
    ('xray_adapters',('disable_upstream_apk_update','xray_import_action','setting_activity','setting_layout')),
]:
    for n in names:
        setattr(mods[module],n,bad(n) if n in ('ok_dns','setting_layout') else good(n))

spec=importlib.util.spec_from_file_location('new_preflight', str(Path(__file__).with_name('test-upstream-real-hooks.py')))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with contextlib.redirect_stderr(io.StringIO()) as captured_errors, contextlib.redirect_stdout(io.StringIO()):
    try:
        module.verify('/unused','0'*40)
    except AssertionError as err:
        assert '2/12' in str(err),str(err)
    else: raise AssertionError('Expected failure of both adapters')
assert captured_errors.getvalue().count('FAIL: ') == 2
assert len(called)==12,(len(called),called)
print('PASS mock integration: 12 hooks invoked; 2 independent failures aggregated')
called.clear()
mods['recovery_adapters'].ok_dns=good('ok_dns')
mods['xray_adapters'].setting_layout=good('setting_layout')
# Imported bindings are direct references: overwrite the test module too.
module.ok_dns=good('ok_dns')
module.setting_layout=good('setting_layout')
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    assert module.verify('/unused','0'*40)==12
assert len(called)==12
print('PASS mock integration: 12 hooks all pass')
