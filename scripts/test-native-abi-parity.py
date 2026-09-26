#!/usr/bin/env python3
"""Selected published v7/arm64 semantic parity, including local TLS and QUIC."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import queue
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v7', type=Path, required=True)
    parser.add_argument('--arm64', type=Path, required=True)
    parser.add_argument('--arm64-jni', type=Path, required=True)
    parser.add_argument('--peer', type=Path, required=True)
    parser.add_argument('--capture', type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('native', Path(__file__).with_name('run-published-libxray-converter.py'))
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    def capture(cases, abi):
        work = args.v7 if abi == 'armeabi-v7a' else args.arm64
        jni = work / 'published-v7-libgojni.so' if abi == 'armeabi-v7a' else args.arm64_jni
        return native.capture(cases, jni, work / 'invoke-bridge',
                              work / 'qemu/usr/bin' / ('qemu-arm-static' if abi == 'armeabi-v7a' else 'qemu-aarch64-static'),
                              work / 'android/root', abi)
    cases = []
    def add(name, method, payload=None):
        request = {'apiVersion': 2, 'method': method}
        if payload is not None:
            request['payload'] = payload
        cases.append({'id': name, 'request': request})
    valid = {'xrayJson': '{"outbounds":[{"protocol":"freedom"}]}'}
    add('api_version', 'getXrayState'); cases[-1]['request']['apiVersion'] = 1
    add('unknown', 'notAMethod')
    add('empty_stop', 'stopXray')
    add('test', 'testXray', valid)
    add('test_invalid', 'testXray', {'xrayJson': 'invalid'})
    add('state_after_test', 'getXrayState')
    add('batch_idle', 'pingBatch', {'configs': [{'xrayJson': 'invalid'}], 'timeout': 100, 'url': 'http://127.0.0.1/'})
    add('run', 'runXray', valid)
    add('run_again', 'runXray', valid)
    add('running', 'getXrayState')
    add('batch_running', 'pingBatch', {'configs': [{'xrayJson': 'invalid'}], 'timeout': 100, 'url': 'http://127.0.0.1/'})
    add('stop', 'stopXray')
    add('stopped', 'getXrayState')
    add('stop_again', 'stopXray')
    add('tls_missing', 'probeTLSCertificate', {})
    add('hy2_missing', 'probeHysteria2Certificate', {})
    vmess = base64.b64encode(json.dumps({'v': '2', 'ps': 'abi', 'add': 'example.invalid', 'port': '443',
        'id': '00000000-0000-0000-0000-000000000001', 'aid': '0', 'net': 'tcp', 'type': 'none', 'tls': 'tls'}).encode()).decode()
    for name, link in [('trojan', 'trojan://synthetic@example.invalid:443'),
                       ('vless', 'vless://00000000-0000-0000-0000-000000000001@example.invalid:443?security=tls'),
                       ('vmess', 'vmess://' + vmess),
                       ('kcp', 'vless://00000000-0000-0000-0000-000000000001@example.invalid:443?type=kcp&headerType=srtp&seed=synthetic'),
                       ('hy2', 'hysteria2://synthetic@example.invalid:443?sni=example.invalid&insecure=1')]:
        add('convert_' + name, 'convertShareLinksToXrayJson', {'text': link})
    age = json.loads((ROOT / 'recovery/native-tests/published-v7-age-matrix.json').read_text())
    for row in age['cases']:
        if row['id'] in {'age_x25519_success', 'age_hybrid_success', 'age_wrong_identity', 'age_malformed_armor', 'age_corrupt_ciphertext', 'age_decrypted_invalid', 'key_bad_payload'}:
            cases.append({'id': row['id'], 'request': row['request']})
    first = capture(cases, 'armeabi-v7a')
    second = capture(cases, 'arm64-v8a')
    for v7, arm64 in zip(first['cases'], second['cases']):
        assert v7['response'] == arm64['response'], (v7['id'], v7['response'], arm64['response'])
    evidence = {'v7': first, 'arm64': second, 'probes': []}
    for protocol, method in [('tls', 'probeTLSCertificate'), ('quic', 'probeHysteria2Certificate')]:
        peer = subprocess.Popen([str(args.peer.resolve()), protocol], stdout=subprocess.PIPE, text=True)
        events = queue.Queue()
        def read():
            for line in peer.stdout:
                events.put(json.loads(line))
        thread = threading.Thread(target=read, daemon=True); thread.start()
        observed = []
        try:
            ready = events.get(timeout=10)
            assert ready['event'] == 'ready'
            payload = {'server': '127.0.0.1', 'port': int(ready['address'].split(':')[-1]),
                       'serverName': 'abi.synthetic.invalid', 'timeout': 5000}
            if protocol == 'tls': payload['alpn'] = ['http/1.1']
            request = {'apiVersion': 2, 'method': method, 'payload': payload}
            responses = []
            for abi in ('armeabi-v7a', 'arm64-v8a'):
                result = capture([{'id': protocol + '_success', 'request': request}], abi)
                response = result['cases'][0]['response']
                assert response == {'success': True, 'data': {'sha256': ready['sha256']}, 'error': ''}, response
                responses.append(response)
                for kind in ('hello', 'accepted', 'closed'):
                    event = events.get(timeout=12); assert event['event'] == kind, event
                    if kind == 'hello': assert event['sni'] == 'abi.synthetic.invalid'
                    observed.append(event)
            evidence['probes'].append({'protocol': protocol, 'request': request, 'peer': ready,
                                       'responses_v7_arm64': responses, 'events': observed})
        finally:
            peer.terminate(); peer.wait(timeout=5); thread.join(timeout=5)
    if args.capture:
        with args.capture.open('x') as file:
            json.dump(evidence, file, indent=2); file.write('\n')
    print(f'PASS: {len(cases)} selected published v7/arm64 responses plus TLS/QUIC success and close')


if __name__ == '__main__':
    main()
