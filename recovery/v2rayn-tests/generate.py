#!/usr/bin/env python3
"""Source-derived v2rayN exporter fixtures; no user credentials, no C# execution claim."""
import base64, json
from pathlib import Path
from urllib.parse import quote
SHA='d433aa3b0484c43d10e6de1c441e30d5e4a2525b'
UUID='11111111-2222-4333-8444-555555555555'
PASSWORD='synthetic+p%41ss'
PUB=base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip('=')
PORTS='1000-2000,3000,4000'
HOSTS={'domain':'node.synthetic.invalid','ipv4':'192.0.2.44','ipv6':'2001:db8::44'}
rows=[]
def uri(proto,host,credential,query):
    authority='['+host+']' if ':' in host else host
    return proto+'://'+quote(credential,safe='')+'@'+authority+':443?'+ '&'.join(k+'='+quote(v,safe='') for k,v in query.items())+'#synthetic'
def row(id,raw,host,**extra):
    rows.append(dict(id=id,raw=raw,address=host,**extra))
for kind,host in HOSTS.items():
    # VmessQRCode annotations write int fields as strings; null host omitted.
    qr=dict(v='2',ps='synthetic',add=host,port='443',id=UUID,aid='0',scy='auto',net='kcp',type='none',path='synthetic-seed',tls='',sni='',alpn='',fp='',insecure='0',vcn='',pcs='')
    row('vmess-kcp-'+kind,'vmess://'+base64.b64encode(json.dumps(qr,indent=2,ensure_ascii=False).encode()).decode(),host,kind='vmess')
for network in ['grpc','xhttp']:
    for kind in ['domain','ipv6']:
        host=HOSTS[kind]
        q=dict(encryption='none',security='reality',sni='sni.synthetic.invalid',fp='chrome',pbk=PUB,sid='0123456789abcdef',spx='/spider?x=1&y=%41',type=network)
        if network=='grpc': q.update(authority='authority.synthetic.invalid',serviceName='/api',mode='gun')
        else: q.update(host='host.synthetic.invalid',path='/api',mode='packet-up')
        row('vless-'+network+'-reality-'+kind,uri('vless',host,UUID,q),host,kind=network)
for kind in ['domain','ipv6']:
    for insecure in [False,True]:
        host=HOSTS[kind]
        q=dict(sni='sni.synthetic.invalid')
        if insecure:q['insecure']='1'
        if insecure:q.update(obfs='salamander',**{'obfs-password':'synthetic-ob%41fs'})
        q['mport']=PORTS
        row('hy2-hopping-'+kind+('-tofu' if insecure else '-verified'),uri('hysteria2',host,PASSWORD,q),host,kind='hy2',insecure=insecure)
for kind in ['domain','ipv6']:
    host=HOSTS[kind]
    q=dict(security='tls',sni='sni.synthetic.invalid',fp='safari',type='ws',host='ws.synthetic.invalid',path='/api?x=1&literal=%41&eq=a=b')
    row('trojan-ws-safari-'+kind,uri('trojan',host,PASSWORD,q),host,kind='trojan')
if __name__=='__main__':
    Path(__file__).with_name('inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
