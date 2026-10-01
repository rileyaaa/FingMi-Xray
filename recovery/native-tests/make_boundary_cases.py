#!/usr/bin/env python3
"""Additional synthetic boundary inputs; expected values require published JNI."""
import base64
import json
from pathlib import Path
from urllib.parse import quote

cases=[]
def add(name,link):
    cases.append({'id': name,'request':{'apiVersion':2,'method':'convertShareLinksToXrayJson','payload':{'text':link}}})
for q in ['','&seed=','&seed','&headerType=','&headerType','&headerType=none','&headerType=none&seed=','&headerType=srtp&seed=','&headerType=unknown&fm=%7B%7D','&headerType=srtp&headerType=dtls','&seed=&seed=second']:
    add('kcp-presence-'+str(len(cases)),'trojan://synthetic@example.com:443?type=kcp'+q)
for mode in ['','auto','packet-up','stream-up','stream-one']:
    for transport in ['xhttp','splithttp']:
        add(transport+'-mode-'+mode,'trojan://synthetic@example.com:443?type='+transport+'&mode='+mode+'&host=cdn.example.com&path=%2Ffake')
for authority in ['443-443','0443,08443','443,','443,,8443','443-444-445','30000-20000','0,443','443,65536','443,8443-0','443,8443-8442','443, 8443']:
    add('hy2-authority-boundary-'+str(len(cases)),'hy2://fake+pass@example.com:'+authority+'/?sni=tls.example.com#synthetic')
for query in ['%70orts=9443','ports','ports=','mport=9443','Ports=9443','x=1%26ports%3D9443','ports%3D9443','ports=9443;foo=1']:
    add('hy2-conflict-boundary-'+str(len(cases)),'hy2://fake@example.com:443,8443?'+query)
pin='ab'*32
for q in ['pinSHA256=','pinSHA256','pinSHA256='+pin+'&pcs=', 'pinSHA256='+pin+'&pcs='+pin,'pinSHA256='+pin+'&pinSHA256='+pin,'pinSHA256='+pin+'&insecure=1','pinSHA256='+pin+'&insecure=0','pinSHA256='+quote(' -'.join(['AB']*32)),'obfs=','obfs=none','obfs=SALAMANDER&obfs-password=fake','obfs-password=fake']:
    add('hy2-security-boundary-'+str(len(cases)),'hy2://fake@example.com:443?'+q)
for scheme in ['trojan','vmess','vless','hy2']:
    for credential in ['fake%20pass','fake%2Fpass','fake%40pass','fake%ZZ','']:
        add('userinfo-'+str(len(cases)),scheme+'://'+credential+'@example.com:443?security=tls')
for value in ['[]','[" ",""]',' , ','[null,"h2"]','[true]','["h2","h2"]']:
    add('alpn-boundary-'+str(len(cases)),'trojan://fake@example.com:443?alpn='+quote(value))
for port in [0,65536,-1,443.0,443.5,'00443','443.0','',None]:
    obj={'add':'example.com','port':port,'id':'00000000-0000-4000-8000-000000000001','net':'tcp'}
    add('vmess-port-boundary-'+str(len(cases)),'vmess://'+base64.b64encode(json.dumps(obj).encode()).decode())
for decoded in ['aes-128-gcm:fake+pass@example.com:443','aes-128-gcm:fake%2Bpass@example.com:443','aes-128-gcm:fake@pass@example.com:443','aes-128-gcm:fake:pass@[2001:db8::1]:443']:
    add('ss-legacy-boundary-'+str(len(cases)),'ss://'+base64.b64encode(decoded.encode()).decode()+'#synthetic')
if __name__=='__main__':
    Path(__file__).with_name('boundary-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    print(len(cases))
