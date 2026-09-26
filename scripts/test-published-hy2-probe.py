#!/usr/bin/env python3
"""Compare published JNI and reconstructed Go against one synthetic QUIC peer.

Build recovery/native-tests/synthetic/main.go inside the patched official module
(go build -buildvcs=false), then pass that executable with --peer.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import queue
import subprocess
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', type=Path, required=True)
    parser.add_argument('--peer', type=Path, required=True)
    parser.add_argument('--capture', type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('native', Path(__file__).with_name('run-published-libxray-converter.py'))
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    peer = subprocess.Popen([str(args.peer.resolve())], stdout=subprocess.PIPE, text=True)
    events = queue.Queue()
    def read():
        for line in peer.stdout:
            events.put(json.loads(line))
    threading.Thread(target=read, daemon=True).start()
    observations = []
    def event(kind):
        value = events.get(timeout=15)
        observations.append(value)
        assert value['event'] == kind, value
        return value
    try:
        ready = event('ready')
        assert hashlib.sha256(base64.b64decode(ready['leaf_der_base64'])).hexdigest() == ready['sha256']
        request = {'apiVersion': 2, 'method': 'probeHysteria2Certificate', 'payload': {
            'server': '127.0.0.1', 'port': int(ready['address'].split(':')[-1]),
            'serverName': 'probe.synthetic.invalid', 'timeout': 5000}}
        work = args.harness.resolve()
        fixture = native.capture([{'id': 'hy2_success', 'request': request}],
                                 work / 'published-v7-libgojni.so', work / 'invoke-bridge',
                                 work / 'qemu/usr/bin/qemu-arm-static', work / 'android/root')
        published = fixture['cases'][0]['response']
        assert published == {'success': True, 'data': {'sha256': ready['sha256']}, 'error': ''}, published
        for implementation in ('published', 'reconstructed'):
            if implementation == 'reconstructed':
                output = subprocess.check_output([str(args.peer.resolve()), 'invoke'], input=json.dumps(request)+'\n', text=True)
                reconstructed = json.loads(output)
                assert reconstructed == published, (reconstructed, published)
            hello = event('hello')
            assert hello['sni'] == 'probe.synthetic.invalid' and hello['alpn'] == ['h3'], hello
            assert event('accepted')['alpn'] == 'h3'
            closed = event('closed')
            assert closed['reason'] in ('APPLICATION_ERROR (remote)', 'Application error 0x0 (remote)'), closed
        fixture['evidence']['limits'] = 'Synthetic QUIC/TLS only; no HY2 proxy authentication or user endpoint'
        fixture['synthetic_peer'] = observations
        fixture['reconstructed_response'] = reconstructed
        if args.capture:
            with args.capture.open('x') as file:
                json.dump(fixture, file, ensure_ascii=False, indent=2)
                file.write('\n')
        print('PASS: published/reconstructed HY2 pin, SNI, h3 ALPN and peer-observed close')
    finally:
        peer.terminate()
        peer.wait(timeout=5)


if __name__ == '__main__':
    main()
