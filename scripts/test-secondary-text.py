#!/usr/bin/env python3
"""Compile/test reconstructed dual text against the pinned real Media3 AARs.

Requires Java 17+, Maven 3.9+, and network access for pinned test dependencies.
This tests the selector/output, not the still-missing newer Libass control API.
"""
import argparse
import hashlib
from io import BytesIO
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--maven', default='mvn')
    parser.add_argument('--local-repository', type=Path, default=Path.home() / '.m2/repository')
    args = parser.parse_args()
    assert hashlib.sha256(args.candidate.read_bytes()).hexdigest() == '0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee'
    jars = ROOT / 'media-test-libs'
    jars.mkdir(exist_ok=True)
    with ZipFile(args.candidate) as bundle:
        for name in ('common', 'exoplayer', 'extractor', 'datasource'):
            with ZipFile(BytesIO(bundle.read(f'lib-{name}-release.aar'))) as aar:
                (jars / f'lib-{name}-release.jar').write_bytes(aar.read('classes.jar'))
    command = [str(Path(args.maven).resolve()) if '/' in args.maven else args.maven,
               '-B', '-f', str(ROOT / 'recovery/media-tests/pom.xml'),
               '-Dmaven.repo.local=' + str(args.local_repository.resolve())]
    # Work environments may expose an HTTP proxy only through environment vars.
    settings = ET.Element('settings')
    proxies = ET.SubElement(settings, 'proxies')
    for protocol in ('http', 'https'):
        address = os.environ.get(protocol.upper() + '_PROXY')
        if not address:
            continue
        url = urllib.parse.urlsplit(address)
        proxy = ET.SubElement(proxies, 'proxy')
        for key, value in [('id', protocol), ('active', 'true'), ('protocol', protocol),
                           ('host', url.hostname), ('port', str(url.port or 80))]:
            ET.SubElement(proxy, key).text = value
        if url.username:
            ET.SubElement(proxy, 'username').text = urllib.parse.unquote(url.username)
        if url.password:
            ET.SubElement(proxy, 'password').text = urllib.parse.unquote(url.password)
        command += [f'-D{protocol}.proxyHost={url.hostname}', f'-D{protocol}.proxyPort={url.port or 80}']
    with tempfile.TemporaryDirectory(prefix='media-test-settings-') as directory:
        path = Path(directory) / 'settings.xml'
        ET.ElementTree(settings).write(path)
        command += ['-s', str(path)]
        subprocess.run(command + ['test-compile'], check=True)
        # Maven resolves AARs but does not place their nested classes.jar on the JVM classpath.
        for artifact, name in [('androidx/test/monitor/1.7.2/monitor-1.7.2.aar', 'monitor'),
                               ('androidx/test/espresso/espresso-idling-resource/3.6.1/espresso-idling-resource-3.6.1.aar', 'espresso')]:
            target = ROOT / 'recovery/media-tests/target' / name
            target.mkdir(parents=True, exist_ok=True)
            with ZipFile(args.local_repository / artifact) as aar:
                (target / 'classes.jar').write_bytes(aar.read('classes.jar'))
        subprocess.run(command + ['test'], check=True)


if __name__ == '__main__':
    main()
