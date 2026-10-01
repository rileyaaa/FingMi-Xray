#!/usr/bin/env python3
"""Deterministic synthetic INPUTS only. Expected results come from released JNI."""
import base64
import json
from pathlib import Path
from urllib.parse import quote

UUID = '00000000-0000-4000-8000-000000000001'
PIN = 'ab' * 32
cases = []


def invoke(name, request):
    cases.append({'id': name, 'request': request})


def add(name, link):
    invoke(name, {'apiVersion': 2, 'method': 'convertShareLinksToXrayJson', 'payload': {'text': link}})


def vmess(**changes):
    obj = dict(v='2', ps='synthetic', add='example.com', port='443', id=UUID,
               aid='0', scy='auto', net='tcp', type='none', host='', path='', tls='')
    obj.update(changes)
    return 'vmess://' + base64.b64encode(json.dumps(obj).encode()).decode()


for v in [0, 1, 2, 3, -1]:
    invoke(f'api-version-{v}', {'apiVersion': v, 'method': 'xrayVersion'})
invoke('api-version-missing', {'method': 'xrayVersion'})
invoke('api-version-string', {'apiVersion': '2', 'method': 'xrayVersion'})
invoke('api-unknown-method', {'apiVersion': 2, 'method': 'notARealMethod'})
invoke('api-malformed-json', '{')
invoke('api-convert-missing-payload', {'apiVersion': 2, 'method': 'convertShareLinksToXrayJson'})
invoke('api-test-inline-json-invalid', {'apiVersion': 2, 'method': 'testXray', 'payload': {'xrayJson': '{'}})
invoke('api-test-configpath-only', {'apiVersion': 2, 'method': 'testXray', 'payload': {'configPath': '/not-used/synthetic.json'}})

for header in ['', 'none', 'srtp', 'utp', 'wechat-video', 'dtls', 'wireguard', 'dns', 'wechat', 'unknown', ' SRTP ']:
    for seeded in [False, True]:
        suffix = 'seed' if seeded else 'no-seed'
        q = 'type=kcp&headerType=' + quote(header) + ('&seed=fake-seed' if seeded else '')
        for scheme in ['vless', 'trojan']:
            credential = UUID if scheme == 'vless' else 'fake-password'
            add(f'{scheme}-kcp-{header.strip() or "empty"}-{suffix}',
                f'{scheme}://{credential}@example.com:443?security=tls&' + q)
        add(f'vmess-kcp-{header.strip() or "empty"}-{suffix}', vmess(net='kcp', type=header, path='fake-seed' if seeded else ''))

for transport in ['tcp', 'raw', 'ws', 'websocket', 'grpc', 'gun', 'httpupgrade', 'xhttp', 'splithttp', 'mkcp', 'unknown']:
    for scheme in ['vless', 'trojan', 'vmess']:
        credential = 'fake-password' if scheme == 'trojan' else UUID
        add(f'{scheme}-transport-{transport}', f'{scheme}://{credential}@example.com:443?security=tls&type={transport}&path=%2Ffake&host=cdn.example.com&serviceName=fake-service&authority=rpc.example.com&mode=multi&seed=fake-seed')
for net in ['tcp', 'ws', 'grpc', 'mkcp']:
    add('vmess-qr-' + net, vmess(net=net, path='fake-path', host='cdn.example.com', tls='tls', sni='tls.example.com', alpn='h2,http/1.1', fp='chrome'))

for credential in ['fake-password', 'fake+password', 'fake%2Bpassword', 'fake%25password', 'fake%252Bpassword', 'fake:password', 'fake%3Apassword', '']:
    add('trojan-password-' + (credential or 'empty'), f'trojan://{credential}@example.com:443')
for alpn in ['', 'h2,http/1.1', ' h2 , , http/1.1 ', '["h2"," http/1.1 ",""]', '[broken,h2', '[1,"h2"]', 'h2,h2']:
    add('trojan-alpn-' + str(len(cases)), 'trojan://fake-password@example.com:443?alpn=' + quote(alpn))
for scheme in ['trojan', 'vless']:
    credential = 'fake-password' if scheme == 'trojan' else UUID
    add(scheme + '-reality', f'{scheme}://{credential}@example.com:443?security=reality&sni=example.com&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=0123456789abcdef&spx=%2Ffake')
add('vless-flow', f'vless://{UUID}@example.com:443?security=tls&flow=xtls-rprx-vision&encryption=none')
add('vless-public-no-tls', f'vless://{UUID}@example.com:443?encryption=none')
add('vless-private-no-tls', f'vless://{UUID}@192.0.2.1:443?encryption=none')
add('kcp-explicit-tuning', 'trojan://fake-password@example.com:443?type=kcp&mtu=1200&tti=30&uplinkCapacity=7&downlinkCapacity=9&congestion=true&readBufferSize=3&writeBufferSize=4')
add('kcp-finalmask-override', 'trojan://fake-password@example.com:443?type=kcp&headerType=srtp&seed=fake&fm=' + quote('{"udp":[{"type":"salamander","settings":{"password":"synthetic"}}]}'))

for authority in ['example.com', 'example.com:443', 'example.com:443,8443', 'example.com:20000-30000', '[2001:db8::1]', '[2001:db8::1]:443,8443']:
    add('hy2-authority-' + authority, 'hy2://fake-password@' + authority)
for query in ['mport=443,8443', 'ports=443,8443', 'mport=20000-30000', 'ports=20000-30000&hop-interval=10', 'ports=443,8443&hop-interval=10s', 'ports=443,8443&hop-interval=-1', 'hop-interval=10', 'obfs=salamander&obfs-password=fake-obfs', 'obfs=salamander', 'obfs=unknown&obfs-password=fake', 'sni=tls.example.com&alpn=h3&insecure=1', 'up=10&down=20', 'pinSHA256='+PIN, 'pinSHA256='+quote(':'.join(['AB']*32)), 'pinSHA256=bad', 'pcs='+PIN, 'pcs=bad', 'pcs='+PIN+'&pinSHA256=bad', 'mport=443,8443&ports=9443,10443', 'ports=443,8443&ports=9443', 'ports=30000-20000', 'ports=0', 'ports=65536', 'ports=443,,8443']:
    add('hy2-query-' + str(len(cases)), 'hy2://fake-password@example.com:443?' + query)
for q in ['', '?ports=9443,10443', '?mport=9443,10443', '?ports=', '?mport=']:
    add('hy2-authority-conflict-' + str(len(cases)), 'hysteria2://fake+password@example.com:443,8443' + q)

for scheme, credential in [('trojan','fake-password'), ('vless',UUID), ('vmess',UUID), ('hy2','fake-password')]:
    add(scheme + '-ipv6', f'{scheme}://{credential}@[2001:db8::1]:443?security=tls')
    for port in ['0', '65536', '-1', 'abc', '', '443.0']:
        add(scheme + '-bad-port-' + (port or 'empty'), f'{scheme}://{credential}@example.com:{port}?security=tls')
    add(scheme + '-missing-host', f'{scheme}://{credential}@:443?security=tls')
    add(scheme + '-malformed-ipv6', f'{scheme}://{credential}@[2001:db8::1:443?security=tls')

ss_user = base64.b64encode(b'aes-128-gcm:fake+password').decode().rstrip('=')
for link in ['ss://' + ss_user + '@example.com:443', 'ss://' + base64.b64encode(b'aes-128-gcm:fake+password@example.com:443').decode(), 'ss://aes-128-gcm:fake%2Bpassword@example.com:443', 'ss://' + ss_user + '@[2001:db8::1]:443', 'ss://' + ss_user + '@example.com:443?plugin=' + quote('v2ray-plugin;mode=websocket;tls;host=cdn.example.com;path=/fake'), 'ss://bad@example.com:443']:
    add('ss-' + str(len(cases)), link)
for link in ['vmess://not-base64', vmess(port=65536), vmess(id=''), 'unknown://fake@example.com:443', 'trojan://fake-password@example.com:443?type=ws&type=grpc', 'trojan://fake-password@example.com:443?security=none', 'trojan://fake-password@example.com:443?security=tls&security=reality']:
    add('edge-' + str(len(cases)), link)

if __name__ == '__main__':
    path = Path(__file__).with_name('cases.json')
    assert len({c['id'] for c in cases}) == len(cases)
    path.write_text(json.dumps(cases, indent=2) + '\n')
    print(f'{len(cases)} synthetic input cases -> {path}')
