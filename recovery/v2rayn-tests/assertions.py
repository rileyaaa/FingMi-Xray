"""Semantic expectations independent of the capture's serialized field order."""
from urllib.parse import parse_qs, urlsplit
import base64,json

def verify(rows,observed):
    assert len(rows)==13
    for row,native,runtime,norm in zip(rows,observed['conversion'],observed['runtime'],observed['normalized']):
        assert row['id']==native['id']==runtime['id']==norm['id']
        config=runtime['runtime'];p=config['outbounds'][0];s=p['settings'];t=p['streamSettings']
        assert p['targetStrategy']=='ForceIP' and 'sendThrough' not in p
        assert s['address'].strip('[]')==row['address'] and s['port']==443
        assert config['dns']['queryStrategy']=='UseIP'
        assert config['routing']['domainStrategy']=='IPOnDemand'
        # Native serializes unused fields as null. Factory must not turn these into objects/strings.
        assert t['sockopt'] is None and t['address'] is None
        if row['kind']=='vmess':
            qr=json.loads(base64.b64decode(row['raw'][8:]))
            assert qr['v']=='2' and qr['aid']=='0' and qr['port']=='443' and 'host' not in qr
            assert s['security']=='auto' and s['id']=='11111111-2222-4333-8444-555555555555'
            assert t['network']=='kcp' and t['kcpSettings']['mtu']==1334
            assert t['finalmask']['udp']==[dict(type='mkcp-legacy',settings=dict(header='',value='synthetic-seed'))]
        elif row['kind'] in ('grpc','xhttp'):
            assert s['encryption']=='none' and s['flow']==''
            r=t['realitySettings'];assert r['serverName']=='sni.synthetic.invalid' and r['fingerprint']=='chrome'
            assert r['publicKey']=='AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8'
            assert r['shortId']=='0123456789abcdef' and r['spiderX']=='/spider?x=1&y=%41'
            assert t['security']=='reality' and t['network']==row['kind']
            if row['kind']=='grpc':
                g=t['grpcSettings'];assert g['authority']=='authority.synthetic.invalid' and g['serviceName']=='/api' and g['multiMode'] is False
            else:
                x=t['xhttpSettings'];assert x['mode']=='packet-up' and x['host']=='host.synthetic.invalid' and x['path']=='/api' and x['extra'] is None
        elif row['kind']=='hy2':
            raw=parse_qs(urlsplit(row['raw']).query);q=parse_qs(urlsplit(norm['finalLink']).query)
            assert raw['mport']==q['ports']==['1000-2000,3000,4000'] and 'mport' not in q
            assert t['finalmask']['quicParams']['udpHop']==dict(interval='0',ports='1000-2000,3000,4000')
            assert t['hysteriaSettings']['auth']=='synthetic+p%41ss' and t['network']=='hysteria'
            tls=t['tlsSettings'];assert tls['serverName']=='sni.synthetic.invalid' and tls['alpn'] is None and tls['allowInsecure'] is False
            assert tls['pinnedPeerCertSha256']==('ab'*32 if row['insecure'] else '')
            if row['insecure']:
                assert norm['probes']==[dict(server=row['address'],port=1000,serverName='sni.synthetic.invalid',timeout=10000)]
                assert 'insecure' not in q
                assert t['finalmask']['udp'][0]['settings']['password']=='synthetic-ob%41fs'
                assert t['finalmask']['udp'][0]['type']=='salamander'
            else: assert norm['probes']==[] and t['finalmask']['udp'] is None
        else:
            assert s['password']=='synthetic+p%41ss' and t['network']=='ws'
            assert t['wsSettings']['host']=='ws.synthetic.invalid'
            assert t['wsSettings']['path']=='/api?x=1&literal=%41&eq=a=b'
            tls=t['tlsSettings'];assert tls['serverName']=='sni.synthetic.invalid' and tls['fingerprint']=='safari'
            assert tls['alpn'] is None and tls['allowInsecure'] is False and norm['probes']==[]
