#!/usr/bin/env python3
"""Exercise the fork's artwork cleanup against real Glide and Android lifecycle.

Extracts unchanged method bodies from both Leanback hosts; Robolectric supplies
Android while media/session/metadata boundaries count interactions. The Glide
implementation and its AndroidX dependencies come from Gradle's resolved app
runtime, not stubs. This is API 28/35 lifecycle coverage, not TV device playback.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ROOT / 'app/src/leanback/java/com/fongmi/android/tv/ui/activity'
HELPERS = runpy.run_path(str(ROOT / 'tests/test-player-startup.py'))
child, dependency = HELPERS['child'], HELPERS['dependency']


def method(path, signature):
    text = path.read_text()
    start = text.index(signature)
    opening = text.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


JAVA = r'''
package com.fingmi.build;
import static org.junit.Assert.*;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.FragmentActivity;
import com.bumptech.glide.Glide;
import com.bumptech.glide.request.Request;
import com.bumptech.glide.request.transition.Transition;
import com.fongmi.android.tv.impl.CustomTarget;
import java.util.List;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import org.robolectric.util.ReflectionHelpers;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE, sdk={28, 35})
@LooperMode(LooperMode.Mode.PAUSED)
public class ArtworkLifecycleTest {
    static class App {
        static android.app.Application get() { return RuntimeEnvironment.getApplication(); }
        static void removeCallbacks(Object... args) {}
    }
    static class ImgUtil {
        static int loads;
        static void load(android.content.Context context, String url, CustomTarget<Drawable> target) {
            loads++;
            Glide.with(context).load(new ColorDrawable(Color.BLUE)).into(target);
        }
    }
    static class Source {
        static Source get() { return new Source(); }
        void exit() {}
    }
    static class XrayHttpClient {}
    static class XraySessionListener { static final int IDLE=0,STARTING=1,RUNNING=2,ERROR=3; }
    static class Session {
        int closes;
        Runnable duringClose;
        boolean isActive() { return false; }
        void close() { closes++; if (duringClose != null) duringClose.run(); }
    }
    static class Clock { int releases; void release() { releases++; } }
    static class Channel { String getLogo() { return "synthetic"; } }
    static class History { String getVodPic() { return "synthetic"; } }
    static class Adapter { int updates; void setXrayLogoSuppressed(boolean value) { updates++; } }
    static class Player {
        int detaches;
        boolean hasXraySession() { return false; }
        void setPlaybackProxy(XrayHttpClient resources, boolean preserve) { if (resources == null) detaches++; }
        void clearPlaybackProxyPreservingState() { detaches++; }
    }
    static class PlayerView {
        int updates;
        void setDefaultArtwork(Drawable value) { updates++; }
        void setDanmakuSource(Object value) {}
    }
    static class Widget {
        int updates, text;
        boolean selected;
        void setSelected(boolean value) { updates++; selected = value; }
        void setText(int value) { updates++; text = value; }
    }
    static class Action { Widget xray = new Widget(); }
    static class Control { Action action = new Action(); }
    static class Binding { PlayerView player = new PlayerView(); Control control = new Control(); }
    static class Live { int resumes; void resumeChannelAfterXrayStart() { resumes++; } }
    static class R { static class string { static final int xray_on=1,xray_starting=2,xray_error=3,xray_off=4; } }
    static class Notify { static void show(String message) {} }
    static class DanmakuApi { static void cancel(int id) {} }
    static class RefreshEvent { static void keep() {} }
    public abstract static class Host extends FragmentActivity {
        CustomTarget<Drawable> mArtworkTarget;
        final Binding mBinding = new Binding();
        final Session mXray = new Session();
        final Clock mClock = new Clock();
        final Channel mChannel = new Channel();
        final History mHistory = new History();
        final Adapter mChannelAdapter = new Adapter();
        final Player manager = new Player();
        final Live mLive = new Live();
        boolean mXrayRefreshMetadataOnDetach, mXrayStartedFromExistingPlayback, mXrayPendingChannelResume;
        boolean owner = true, mXrayProxyFailed;
        int canceled, logos, metadata, danmaku, saved;
        int mDanmakuRequestId;
        Object mR0,mR1,mR2,mR3,mR4;
        Object service() { return this; }
        boolean isOwner() { return owner; }
        Player player() { return manager; }
        PlayerView getPlayerView() { return mBinding.player; }
        void updatePlaybackDanmakuClient() { danmaku++; }
        void cancelXrayMetadataRequests() { canceled++; }
        void setWidgetLogoSuppressed(boolean value) { logos++; }
        void refreshXrayAwareMetadata() { metadata++; }
        void showError(String value) {}
        void saveHistory(boolean exit) { saved++; }
        public abstract void onStateChanged(int state, String message);
        abstract void createArtwork();
        abstract void clearArtwork();
    }
    public static class LiveHost extends Host {
        __LIVE_METHODS__
        void createArtwork() { setArtwork(); }
        void clearArtwork() { clearArtworkTarget(); }
    }
    public static class VideoHost extends Host {
        __VIDEO_METHODS__
        void createArtwork() { setArtwork(); }
        void clearArtwork() { clearArtworkTarget(); }
    }
    static List<Class<? extends Host>> types() { return List.of(LiveHost.class, VideoHost.class); }
    static ActivityController<? extends Host> create(Class<? extends Host> type) {
        return Robolectric.buildActivity(type).create().start().resume();
    }
    static void verifyLivingStateUpdates(Host activity) {
        Widget button = activity.mBinding.control.action.xray;
        int updates = button.updates;
        int[] states = {XraySessionListener.STARTING, XraySessionListener.RUNNING,
                        XraySessionListener.ERROR, XraySessionListener.IDLE};
        int[] text = {R.string.xray_starting, R.string.xray_on,
                      R.string.xray_error, R.string.xray_off};
        for (int i = 0; i < states.length; i++) {
            activity.onStateChanged(states[i], "");
            assertEquals(updates + 2 * (i + 1), button.updates);
            assertEquals(text[i], button.text);
            assertEquals(states[i] == XraySessionListener.RUNNING, button.selected);
        }
    }
    static void verifyClosedStateDoesNotUpdateUi(Host activity) {
        Widget button = activity.mBinding.control.action.xray;
        int updates = button.updates, text = button.text;
        boolean selected = button.selected;
        for (int state : new int[] {XraySessionListener.STARTING, XraySessionListener.RUNNING,
                                   XraySessionListener.ERROR, XraySessionListener.IDLE}) {
            activity.onStateChanged(state, "");
            assertEquals(updates, button.updates);
            assertEquals(text, button.text);
            assertEquals(selected, button.selected);
        }
    }
    @Test public void originalActivityLookupFailsWithExactReportedMessage() {
        try (ActivityController<FragmentActivity> controller = Robolectric.buildActivity(FragmentActivity.class).create().start().resume()) {
            FragmentActivity activity = controller.get();
            ReflectionHelpers.setField(activity, "mDestroyed", true);
            try {
                Glide.with(activity).clear(new CustomTarget<Drawable>());
                fail("old host lookup must reproduce the reported crash");
            } catch (IllegalArgumentException expected) {
                assertEquals("You cannot start a load for a destroyed activity", expected.getMessage());
            } finally { ReflectionHelpers.setField(activity, "mDestroyed", false); }
        }
    }
    @Test public void applicationClearCancelsActivityOwnedTargetsAndIsIdempotent() {
        for (Class<? extends Host> type : types()) {
            try (ActivityController<? extends Host> controller = create(type)) {
                Host activity = controller.get();
                activity.createArtwork();
                CustomTarget<Drawable> target = activity.mArtworkTarget;
                Request request = target.getRequest();
                assertNotNull(request);
                activity.clearArtwork();
                assertNull(activity.mArtworkTarget);
                assertNull(target.getRequest());
                assertTrue(request.isCleared());
                activity.clearArtwork();
            }
        }
    }
    @Test public void destroyRunsBothHostCleanupMethodsWithoutRetainingTargets() {
        for (Class<? extends Host> type : types()) {
            ActivityController<? extends Host> controller = create(type);
            Host activity = controller.get();
            verifyLivingStateUpdates(activity);
            activity.createArtwork();
            CustomTarget<Drawable> target = activity.mArtworkTarget;
            Request request = target.getRequest();
            controller.pause().stop().destroy();
            assertTrue(activity.isDestroyed());
            verifyClosedStateDoesNotUpdateUi(activity);
            assertNull(activity.mArtworkTarget);
            assertNull(target.getRequest());
            assertTrue(request.isCleared());
            assertEquals(1, activity.mXray.closes);
            assertEquals(1, activity.mClock.releases);
            int loads = ImgUtil.loads;
            activity.createArtwork();
            assertEquals(loads, ImgUtil.loads);
            activity.clearArtwork();
        }
    }
    @Test public void finishingHostsDoNotStartReplacementArtwork() {
        for (Class<? extends Host> type : types()) {
            try (ActivityController<? extends Host> controller = create(type)) {
                Host activity = controller.get();
                activity.createArtwork();
                Request request = activity.mArtworkTarget.getRequest();
                verifyLivingStateUpdates(activity);
                activity.finish();
                verifyClosedStateDoesNotUpdateUi(activity);
                int loads = ImgUtil.loads;
                activity.createArtwork();
                assertEquals(loads, ImgUtil.loads);
                assertNull(activity.mArtworkTarget);
                assertTrue(request.isCleared());
            }
        }
    }
    @Test public void liveCloseStillDetachesProxyWithoutReopeningUiRequests() {
        for (boolean destroyed : new boolean[] {false,true}) {
            ActivityController<LiveHost> controller = Robolectric.buildActivity(LiveHost.class).create().start().resume();
            LiveHost activity = controller.get();
            activity.createArtwork();
            if (destroyed) ReflectionHelpers.setField(activity, "mDestroyed", true);
            else activity.finish();
            int loads = ImgUtil.loads;
            activity.mXrayRefreshMetadataOnDetach = true;
            activity.mXrayPendingChannelResume = true;
            activity.onProxyChanged(null, false);
            activity.onProxyError();
            activity.onStateChanged(XraySessionListener.RUNNING, "");
            assertEquals(2, activity.manager.detaches);
            assertEquals(2, activity.canceled);
            assertEquals(0, activity.mChannelAdapter.updates);
            assertEquals(0, activity.logos);
            assertEquals(0, activity.metadata);
            assertEquals(0, activity.mLive.resumes);
            assertEquals(loads, ImgUtil.loads);
            if (destroyed) ReflectionHelpers.setField(activity, "mDestroyed", false);
            activity.mXray.duringClose = () -> activity.onProxyChanged(null, false);
            controller.pause().stop().destroy();
            assertEquals(3, activity.manager.detaches);
            assertEquals(loads, ImgUtil.loads);
            assertNull(activity.mArtworkTarget);
        }
    }
    @Test public void livingLiveHostStillRestoresArtworkAndMetadata() {
        try (ActivityController<LiveHost> controller = Robolectric.buildActivity(LiveHost.class).create().start().resume()) {
            LiveHost activity = controller.get();
            activity.mXrayRefreshMetadataOnDetach = true;
            int loads = ImgUtil.loads;
            activity.onProxyChanged(null, true);
            assertEquals(1, activity.manager.detaches);
            assertEquals(1, activity.logos);
            assertEquals(1, activity.metadata);
            assertEquals(loads+1, ImgUtil.loads);
            assertNotNull(activity.mArtworkTarget);
        }
    }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', type=Path, required=True)
    parser.add_argument('--maven', type=Path, required=True)
    parser.add_argument('--local-repository', type=Path, required=True)
    parser.add_argument('--runtime-classpath', type=Path)
    parser.add_argument('--host-source', type=Path, default=HOSTS, help='Host directory for before/after source comparison')
    args = parser.parse_args()
    work = args.workdir.resolve()
    if work.exists() and any(work.iterdir()):
        parser.error('--workdir must be empty')
    jars = work / 'jars'
    jars.mkdir(parents=True)
    classpath = args.runtime_classpath
    if classpath is None:
        classpath = work / 'runtime-classpath.txt'
        init = work / 'export.gradle'
        init.write_text('''allprojects { p -> if (p.path == ':app') {
            tasks.register('exportXrayArtworkRuntimeClasspath') { doLast {
                def resolved = configurations.leanbackReleaseRuntimeClasspath.incoming.artifactView {
                    componentFilter { id -> id instanceof org.gradle.api.artifacts.component.ModuleComponentIdentifier }
                }.files.files
                new File(project.findProperty('artworkClasspathFile')).text = resolved.collect { it.absolutePath }.sort().join('\\n') + '\\n'
            }}
        }}''')
        subprocess.run(['bash', str(ROOT/'gradlew'), '-I', str(init), ':app:exportXrayArtworkRuntimeClasspath',
                        '-PartworkClasspathFile='+str(classpath), '--console=plain'], cwd=ROOT, check=True)
    inputs = {}
    for index, line in enumerate(classpath.read_text().splitlines()):
        source = Path(line)
        inputs[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
        if source.suffix == '.jar':
            shutil.copyfile(source, jars / f'{index}-{source.name}')
        elif source.suffix == '.aar':
            with ZipFile(source) as archive:
                for name in archive.namelist():
                    if name == 'classes.jar' or name.startswith('libs/') and name.endswith('.jar'):
                        (jars / f'{index}-{source.stem}-{name.replace("/", "-")}').write_bytes(archive.read(name))
    assert any('glide' in name for name in inputs), 'resolved Glide missing'
    (work/'input-sha256.json').write_text(json.dumps(inputs, indent=2)+'\n')
    java = JAVA
    for name, placeholder in [('LiveActivity', '__LIVE_METHODS__'), ('VideoActivity', '__VIDEO_METHODS__')]:
        signatures = ['private void clearArtworkTarget()', 'private void setArtwork()', 'protected void onDestroy()',
                      'public void onStateChanged(']
        if name == 'LiveActivity':
            signatures += ['public void onProxyChanged(', 'public void onProxyError()']
        java = java.replace(placeholder, '\n'.join(method(args.host_source/(name+'.java'), s) for s in signatures))
    source = work/'tests/com/fingmi/build/ArtworkLifecycleTest.java'
    source.parent.mkdir(parents=True)
    source.write_text(java)
    target = work/'tests/com/fongmi/android/tv/impl/CustomTarget.java'
    target.parent.mkdir(parents=True)
    shutil.copyfile(ROOT/'app/src/main/java/com/fongmi/android/tv/impl/CustomTarget.java', target)
    project = ET.Element('project', xmlns='http://maven.apache.org/POM/4.0.0')
    for key, value in [('modelVersion','4.0.0'), ('groupId','com.fingmi.build'), ('artifactId','xray-artwork-lifecycle'), ('version','1')]:
        child(project,key,value)
    props = child(project,'properties')
    child(props,'maven.compiler.release','17')
    child(props,'project.build.sourceEncoding','UTF-8')
    child(props,'imported.libs',jars)
    repositories = child(project,'repositories')
    for name,url in [('central','https://repo.maven.apache.org/maven2'), ('google','https://dl.google.com/dl/android/maven2/')]:
        node=child(repositories,'repository'); child(node,'id',name); child(node,'url',url)
    dependencies=child(project,'dependencies')
    for index,jar in enumerate(sorted(jars.glob('*.jar'))):
        dependency(dependencies,'local.runtime',f'imported-{index}','1','system','${imported.libs}/'+jar.name)
    dependency(dependencies,'org.robolectric','android-all','15-robolectric-12650502','provided')
    dependency(dependencies,'junit','junit','4.13.2','test')
    dependency(dependencies,'org.robolectric','robolectric','4.14.1','test')
    build=child(project,'build'); child(build,'directory',work/'target'); child(build,'testSourceDirectory',work/'tests')
    plugins=child(build,'plugins')
    for name,version in [('maven-compiler-plugin','3.14.0'),('maven-surefire-plugin','3.5.3')]:
        plugin=child(plugins,'plugin'); child(plugin,'groupId','org.apache.maven.plugins'); child(plugin,'artifactId',name); child(plugin,'version',version)
        if name!='maven-surefire-plugin': continue
        config=child(plugin,'configuration'); properties=child(config,'systemPropertyVariables')
        child(properties,'robolectric.dependency.repo.url','https://repo.maven.apache.org/maven2')
        additional=child(config,'additionalClasspathElements')
        for name in ('monitor','espresso'): child(additional,'additionalClasspathElement',work/'target'/name/'classes.jar')
    pom=work/'pom.xml'; ET.ElementTree(project).write(pom,encoding='unicode')
    command=[str(args.maven.resolve()),'-B','-f',str(pom),'-Dmaven.repo.local='+str(args.local_repository.resolve())]
    settings=ET.Element('settings'); proxies=child(settings,'proxies')
    for protocol in ('http','https'):
        address=os.environ.get(protocol.upper()+'_PROXY')
        if not address: continue
        url=urllib.parse.urlsplit(address); proxy=child(proxies,'proxy')
        for key,value in [('id',protocol),('active','true'),('protocol',protocol),('host',url.hostname),('port',url.port or 80)]: child(proxy,key,value)
        if url.username: child(proxy,'username',urllib.parse.unquote(url.username))
        if url.password: child(proxy,'password',urllib.parse.unquote(url.password))
        command += [f'-D{protocol}.proxyHost={url.hostname}',f'-D{protocol}.proxyPort={url.port or 80}']
    with tempfile.TemporaryDirectory(prefix='artwork-lifecycle-settings-') as directory:
        settings_path=Path(directory)/'settings.xml'; ET.ElementTree(settings).write(settings_path)
        command += ['-s',str(settings_path)]
        subprocess.run(command+['test-compile'],check=True)
        for artifact,name in [('androidx/test/monitor/1.7.2/monitor-1.7.2.aar','monitor'),('androidx/test/espresso/espresso-idling-resource/3.6.1/espresso-idling-resource-3.6.1.aar','espresso')]:
            destination=work/'target'/name; destination.mkdir(parents=True)
            with ZipFile(args.local_repository/artifact) as archive: (destination/'classes.jar').write_bytes(archive.read('classes.jar'))
        subprocess.run(command+['test'],check=True)
    report=ET.parse(work/'target/surefire-reports/TEST-com.fingmi.build.ArtworkLifecycleTest.xml').getroot()
    assert report.get('tests')=='12', ET.tostring(report)
    assert all(report.get(key)=='0' for key in ('errors','failures','skipped')), ET.tostring(report)
    print('PASS: 12 API28/35 real-Glide lifecycle cases, both host cleanup methods, original crash reproduction, cross-manager cancellation and late proxy/UI callbacks')


if __name__ == '__main__':
    main()
