#!/usr/bin/env python3
"""Construct/release real Media3 renderers and players from the AARs imported by the app.

Robolectric supplies Android only. No Maven Media3 dependency or Media3 test double may
fill a missing production AAR. This exercises JVM linkage and construction, not TV
codec/native playback, an obfuscated APK, or a real device's Activity lifecycle.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from zipfile import ZipFile


JAVA = r'''
package com.fingmi.build;

import static org.junit.Assert.*;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import androidx.media3.exoplayer.DefaultRenderersFactory;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.Renderer;
import androidx.media3.exoplayer.audio.AudioRendererEventListener;
import androidx.media3.exoplayer.audio.MediaCodecAudioRenderer;
import androidx.media3.exoplayer.text.TextRenderer;
import androidx.media3.exoplayer.video.MediaCodecVideoRenderer;
import androidx.media3.exoplayer.video.VideoRendererEventListener;
import java.util.Arrays;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE, sdk={28, 35})
@LooperMode(LooperMode.Mode.PAUSED)
public class PlayerStartupTest {
    @Test public void constructsProductionVideoAudioAndTextRenderers() {
        Context context = RuntimeEnvironment.getApplication();
        Renderer[] renderers = new DefaultRenderersFactory(context)
            .setExtensionRendererMode(DefaultRenderersFactory.EXTENSION_RENDERER_MODE_ON).createRenderers(
            new Handler(Looper.getMainLooper()), new VideoRendererEventListener() {},
            new AudioRendererEventListener() {}, cues -> {}, metadata -> {});
        try {
            assertTrue(Arrays.stream(renderers).anyMatch(MediaCodecVideoRenderer.class::isInstance));
            assertTrue(Arrays.stream(renderers).anyMatch(MediaCodecAudioRenderer.class::isInstance));
            assertTrue(Arrays.stream(renderers).anyMatch(TextRenderer.class::isInstance));
            for (String extension : new String[] {
                "androidx.media3.decoder.ffmpeg.FfmpegVideoRenderer",
                "androidx.media3.decoder.ffmpeg.FfmpegAudioRenderer",
                "androidx.media3.decoder.mpegh.MpeghAudioRenderer"
            }) {
                assertTrue(extension, Arrays.stream(renderers)
                    .anyMatch(renderer -> renderer.getClass().getName().equals(extension)));
            }
        } finally {
            for (Renderer renderer : renderers) renderer.release();
        }
    }

    @Test public void constructsAndReleasesProductionPlayerRepeatedly() {
        Context context = RuntimeEnvironment.getApplication();
        for (int i = 0; i < 3; i++) {
            ExoPlayer player = new ExoPlayer.Builder(context)
                .setRenderersFactory(new DefaultRenderersFactory(context)
                    .setEnableDecoderFallback(true)
                    .setExtensionRendererMode(DefaultRenderersFactory.EXTENSION_RENDERER_MODE_ON)).build();
            try {
                assertEquals(ExoPlayer.STATE_IDLE, player.getPlaybackState());
            } finally {
                player.release();
            }
        }
    }
}
'''


def child(parent, name, text=None):
    node = ET.SubElement(parent, name)
    if text is not None:
        node.text = str(text)
    return node


def dependency(parent, group, name, version, scope=None, path=None):
    node = child(parent, 'dependency')
    for key, value in [('groupId', group), ('artifactId', name), ('version', version),
                       ('scope', scope), ('systemPath', path)]:
        if value is not None:
            child(node, key, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--libs', type=Path, required=True)
    parser.add_argument('--workdir', type=Path, required=True)
    parser.add_argument('--maven', type=Path, required=True)
    parser.add_argument('--local-repository', type=Path, required=True)
    args = parser.parse_args()
    work = args.workdir.resolve()
    if work.exists() and any(work.iterdir()):
        parser.error('--workdir must be empty, preventing stale jars from masking missing inputs')
    jars = work / 'jars'
    jars.mkdir(parents=True)
    inputs = {}
    # Use exactly the local AAR bytecode set; do not resolve any Media3 artifact from Maven.
    for aar in sorted(args.libs.resolve().glob('*.aar')):
        with ZipFile(aar) as archive:
            for member in archive.namelist():
                if member != 'classes.jar' and not (member.startswith('libs/') and member.endswith('.jar')):
                    continue
                filename = aar.stem + '-' + member.replace('/', '-')
                (jars / filename).write_bytes(archive.read(member))
        inputs[aar.name] = hashlib.sha256(aar.read_bytes()).hexdigest()
    if not inputs:
        parser.error('no imported app AARs found')
    (work / 'input-sha256.json').write_text(json.dumps(inputs, indent=2) + '\n')
    source = work / 'tests/com/fingmi/build/PlayerStartupTest.java'
    source.parent.mkdir(parents=True)
    source.write_text(JAVA)

    project = ET.Element('project', xmlns='http://maven.apache.org/POM/4.0.0')
    for key, value in [('modelVersion', '4.0.0'), ('groupId', 'com.fingmi.build'),
                       ('artifactId', 'imported-player-startup'), ('version', '1')]:
        child(project, key, value)
    props = child(project, 'properties')
    child(props, 'maven.compiler.release', '17')
    child(props, 'project.build.sourceEncoding', 'UTF-8')
    child(props, 'imported.libs', jars)
    repositories = child(project, 'repositories')
    for name, url in [('central', 'https://repo.maven.apache.org/maven2'),
                      ('google', 'https://dl.google.com/dl/android/maven2/')]:
        repository = child(repositories, 'repository')
        child(repository, 'id', name)
        child(repository, 'url', url)
    dependencies = child(project, 'dependencies')
    for index, jar in enumerate(sorted(jars.glob('*.jar'))):
        dependency(dependencies, 'local.app.aar', f'imported-{index}', '1', 'system', '${imported.libs}/' + jar.name)
    dependency(dependencies, 'org.robolectric', 'android-all', '15-robolectric-12650502', 'provided')
    dependency(dependencies, 'com.google.guava', 'guava', '33.3.1-android')
    dependency(dependencies, 'androidx.annotation', 'annotation', '1.9.1')
    dependency(dependencies, 'junit', 'junit', '4.13.2', 'test')
    dependency(dependencies, 'org.robolectric', 'robolectric', '4.14.1', 'test')
    build = child(project, 'build')
    child(build, 'directory', work / 'target')
    child(build, 'testSourceDirectory', work / 'tests')
    plugins = child(build, 'plugins')
    for name, version in [('maven-compiler-plugin', '3.14.0'), ('maven-surefire-plugin', '3.5.3')]:
        plugin = child(plugins, 'plugin')
        child(plugin, 'groupId', 'org.apache.maven.plugins')
        child(plugin, 'artifactId', name)
        child(plugin, 'version', version)
        if name != 'maven-surefire-plugin':
            continue
        config = child(plugin, 'configuration')
        properties = child(config, 'systemPropertyVariables')
        child(properties, 'robolectric.dependency.repo.url', 'https://repo.maven.apache.org/maven2')
        additional = child(config, 'additionalClasspathElements')
        for name in ('monitor', 'espresso'):
            child(additional, 'additionalClasspathElement', work / 'target' / name / 'classes.jar')
    pom = work / 'pom.xml'
    ET.ElementTree(project).write(pom, encoding='unicode')

    command = [str(args.maven.resolve()), '-B', '-f', str(pom),
               '-Dmaven.repo.local=' + str(args.local_repository.resolve())]
    settings = ET.Element('settings')
    proxies = child(settings, 'proxies')
    for protocol in ('http', 'https'):
        address = os.environ.get(protocol.upper() + '_PROXY')
        if not address:
            continue
        url = urllib.parse.urlsplit(address)
        proxy = child(proxies, 'proxy')
        for key, value in [('id', protocol), ('active', 'true'), ('protocol', protocol),
                           ('host', url.hostname), ('port', url.port or 80)]:
            child(proxy, key, value)
        if url.username:
            child(proxy, 'username', urllib.parse.unquote(url.username))
        if url.password:
            child(proxy, 'password', urllib.parse.unquote(url.password))
        command += [f'-D{protocol}.proxyHost={url.hostname}', f'-D{protocol}.proxyPort={url.port or 80}']
    with tempfile.TemporaryDirectory(prefix='player-startup-settings-') as directory:
        settings_path = Path(directory) / 'settings.xml'
        ET.ElementTree(settings).write(settings_path)
        command += ['-s', str(settings_path)]
        subprocess.run(command + ['test-compile'], check=True)
        for artifact, name in [
            ('androidx/test/monitor/1.7.2/monitor-1.7.2.aar', 'monitor'),
            ('androidx/test/espresso/espresso-idling-resource/3.6.1/espresso-idling-resource-3.6.1.aar', 'espresso'),
        ]:
            directory = work / 'target' / name
            directory.mkdir(parents=True)
            with ZipFile(args.local_repository / artifact) as archive:
                (directory / 'classes.jar').write_bytes(archive.read('classes.jar'))
        subprocess.run(command + ['test'], check=True)
    report = ET.parse(work / 'target/surefire-reports/TEST-com.fingmi.build.PlayerStartupTest.xml').getroot()
    assert report.get('tests') == '4', ET.tostring(report)
    assert all(report.get(key) == '0' for key in ('errors', 'failures', 'skipped')), ET.tostring(report)
    print('PASS: imported AAR renderer/player construction and release; 4 Robolectric cases on API 28/35; no external Media3 dependencies')


if __name__ == '__main__':
    main()
