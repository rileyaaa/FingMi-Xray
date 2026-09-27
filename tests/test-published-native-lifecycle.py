#!/usr/bin/env python3
"""Exercise the pinned v7 JNI state machine, including barrier-started races.

Requires prepare-native-converter-harness.py --parallel. Assertions accept only
legal serialized outcomes; thread completion order is deliberately not golden.
The listening socket distinguishes construction/validation from actual Start.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile

PIN = '6f01f219fe4087790cd8e647394de9dbefc61e0d750d927924b93f120b06fb7e'


def request(method, config=None):
    result = {'apiVersion': 2, 'method': method}
    if config is not None:
        result['payload'] = {'xrayJson': config if isinstance(config, str) else json.dumps(config)}
    return result


def capture(work, groups):
    work = work.resolve()
    jni = work / 'published-v7-libgojni.so'
    bridge = work / 'invoke-parallel-bridge'
    if hashlib.file_digest(jni.open('rb'), 'sha256').hexdigest() != PIN:
        raise ValueError('Wrong published JNI')
    if f'Shared library: [{jni}]' not in subprocess.check_output(['readelf', '-d', str(bridge)], text=True):
        raise ValueError('Bridge JNI link does not match')
    raw = bytearray()
    for group in groups:
        raw += struct.pack('<I', len(group['requests']))
        for req in group['requests']:
            value = json.dumps(req).encode()
            raw += struct.pack('<I', len(value)) + value
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'responses'
        env = dict(os.environ, NATIVE_CAPTURE=str(output))
        root = work / 'android/root'
        command = ['sh', '-c', 'exec "$@" 3>"$NATIVE_CAPTURE"', 'sh',
                   str(work / 'qemu/usr/bin/qemu-arm-static'), '-L', str(root),
                   '-E', 'LD_LIBRARY_PATH=' + str(root / 'system/lib'), str(bridge)]
        subprocess.run(command, input=raw, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       env=env, timeout=90, check=True)
        data = output.read_bytes()
    offset = 0
    for group in groups:
        count, = struct.unpack_from('<I', data, offset)
        offset += 4
        assert count == len(group['requests'])
        responses = []
        for _ in range(count):
            size, = struct.unpack_from('<I', data, offset)
            offset += 4
            value = data[offset:offset + size].decode('utf-16le')
            offset += size
            responses.append({'response': json.loads(value), 'raw_response': value})
        group['observed'] = responses
    assert offset == len(data)
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', type=Path, required=True)
    parser.add_argument('--capture', type=Path)
    args = parser.parse_args()
    valid = {'outbounds': [{'protocol': 'freedom', 'tag': 'direct'}]}
    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1', 0))
        occupied.listen()
        busy = dict(valid, inbounds=[{'listen': '127.0.0.1', 'port': occupied.getsockname()[1],
                                    'protocol': 'socks', 'settings': {'udp': False}}])
        with socket.socket() as available:
            available.bind(('127.0.0.1', 0))
            first = {'listen': '127.0.0.1', 'port': available.getsockname()[1],
                     'protocol': 'socks', 'settings': {'udp': False}}
        partial = dict(valid, inbounds=[first, busy['inbounds'][0]])
        reuse = dict(valid, inbounds=[first])
        groups = []
        def add(name, *reqs):
            groups.append({'id': name, 'requests': list(reqs)})
        stop, state = request('stopXray'), request('getXrayState')
        run, test = request('runXray', valid), request('testXray', valid)
        add('empty_stop', stop)
        add('test_occupied_port', request('testXray', busy))
        add('after_test', state)
        add('run_occupied_port', request('runXray', busy))
        add('after_failed_start', state)
        add('invalid_run', request('runXray', 'invalid'))
        add('after_invalid_run', state)
        add('invalid_test', request('testXray', 'invalid'))
        add('after_invalid_test', state)
        add('partial_start_failure', request('runXray', partial))
        add('after_partial_failure', state)
        add('reuse_partially_opened_port', request('runXray', reuse))
        add('stop_reused_port', stop)
        add('competing_runs', run, run)
        add('after_competing_runs', state)
        add('test_during_run', test)
        add('after_test_during_run', state)
        add('invalid_run_while_running', request('runXray', 'invalid'))
        add('overlapping_stop_run', stop, run)
        add('after_stop_run', state)
        add('cleanup', stop)
        add('competing_empty_stops', stop, stop)
        add('parallel_test_run', test, run)
        add('after_parallel_test_run', state)
        add('final_stop', stop)
        add('final_state', state)
        observed = capture(args.harness, groups)
    by_id = {g['id']: [o['response'] for o in g['observed']] for g in observed}
    success = {'success': True, 'data': {}, 'error': ''}
    already = {'success': False, 'data': None, 'error': 'xray is already running'}
    for name in ['empty_stop', 'test_occupied_port', 'reuse_partially_opened_port',
                 'stop_reused_port', 'test_during_run', 'cleanup', 'final_stop']:
        assert by_id[name] == [success], (name, by_id[name])
    for name in ['after_test', 'after_failed_start', 'after_invalid_run', 'after_invalid_test',
                 'after_partial_failure', 'final_state']:
        assert by_id[name] == [{'success': True, 'data': {'running': False}, 'error': ''}], name
    for name in ['after_competing_runs', 'after_test_during_run', 'after_parallel_test_run']:
        assert by_id[name] == [{'success': True, 'data': {'running': True}, 'error': ''}], name
    assert not by_id['run_occupied_port'][0]['success']
    assert 'address already in use' in by_id['run_occupied_port'][0]['error']
    assert not by_id['partial_start_failure'][0]['success']
    assert 'address already in use' in by_id['partial_start_failure'][0]['error']
    for name in ['invalid_run', 'invalid_test']:
        assert not by_id[name][0]['success'] and by_id[name][0]['data'] is None
    assert by_id['competing_runs'].count(success) == 1
    assert by_id['competing_runs'].count(already) == 1
    assert by_id['invalid_run_while_running'] == [already]
    assert by_id['competing_empty_stops'] == [success, success]
    assert by_id['parallel_test_run'] == [success, success]
    stop_result, run_result = by_id['overlapping_stop_run']
    assert stop_result == success and run_result in (success, already)
    assert by_id['after_stop_run'][0]['data']['running'] == (run_result == success)
    result = {'schema': 1, 'evidence': {'kind': 'published-native-execution', 'abi': 'armeabi-v7a',
              'jni_sha256': PIN, 'runtime': 'QEMU ARM + API24 Bionic',
              'concurrency': 'pthread barrier; invariants do not assume scheduling order',
              'limits': 'No ART, device lifecycle, or proof of every possible schedule'}, 'groups': observed}
    if args.capture:
        with args.capture.open('x') as file:
            json.dump(result, file, indent=2)
            file.write('\n')
    print('PASS: 26 native lifecycle groups, including 4 barrier-synchronized groups')


if __name__ == '__main__':
    main()
