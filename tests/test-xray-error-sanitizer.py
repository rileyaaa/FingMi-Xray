#!/usr/bin/env python3
"""Compile the real sanitizer and check synthetic quoted/truncated error inputs.

No Android stubs are needed for this production class. All credentials are
synthetic canaries; this test neither reads saved nodes nor accesses a network.
Requires Python 3.9+ and a JDK with javac/java on PATH.
"""
from pathlib import Path
import argparse
import base64
import json
import shutil
import subprocess
import tempfile

KEYS = ('password', 'passwd', 'token', 'secret', 'auth', 'obfs-password',
        'uuid', 'privatekey', 'publickey', 'shortid', 'seed')


def build_cases():
    cases = []
    def add(name, original, expected):
        cases.append((name, original, expected))
    values = ['CANARY_A tail_CANARY', 'CANARY_A,tail_CANARY',
              'CANARY_A;tail_CANARY', 'CANARY_A&tail_CANARY',
              'CANARY_A}tail_CANARY', 'CANARY_A]tail_CANARY',
              'CANARY_A\\tail_CANARY', 'CANARY_A"tail_CANARY',
              "CANARY_A'tail_CANARY", 'CANARY_A\nnext_CANARY']
    prefixes = ['', 'native: ', '\u0130 prefix: ', '\U0001f512\u5bc6\u7801: ']
    for key in KEYS:
        for spelling in (key, key.upper(), key.title()):
            for pi, prefix in enumerate(prefixes):
                for vi, value in enumerate(values):
                    # Python's JSON encoder supplies an independent string grammar.
                    quoted = json.dumps(value, ensure_ascii=False)
                    add(f'json-{key}-{spelling}-{pi}-{vi}',
                        prefix+'{"'+spelling+'":'+quoted+',"status":"bad"}',
                        prefix+'{"'+spelling+'":"<redacted>","status":"bad"}')
                    for quote in ('"', "'"):
                        escaped = value.replace('\\', '\\\\').replace(quote, '\\'+quote)
                        add(f'quoted-{key}-{spelling}-{pi}-{vi}-{quote}',
                            prefix+spelling+' = '+quote+escaped+quote+' status=bad',
                            prefix+spelling+' = <redacted> status=bad')
                for suffix in ('CANARY_TRUNCATED', 'CANARY_TRUNCATED\\',
                               'CANARY_TRUNCATED\\"tail_CANARY'):
                    add(f'truncated-json-{key}-{spelling}-{pi}-{len(suffix)}',
                        prefix+'{"'+spelling+'":"'+suffix,
                        prefix+'{"'+spelling+'":"<redacted>')
                    add(f'truncated-assignment-{key}-{spelling}-{pi}-{len(suffix)}',
                        prefix+spelling+'="'+suffix,
                        prefix+spelling+'=<redacted>')
                add(f'bare-{key}-{spelling}-{pi}', prefix+spelling+'=CANARY_BARE status=bad',
                    prefix+spelling+'=<redacted> status=bad')
    add('multiple-json', '{"password":"CANARY_ONE","auth":"CANARY_TWO"}',
        '{"password":"<redacted>","auth":"<redacted>"}')
    add('multiple-assignments', "auth='CANARY_ONE x'; token=CANARY_TWO status=bad",
        'auth=<redacted>; token=<redacted> status=bad')
    add('json-escaped-backslashes', '{"auth":"CANARY\\\\","status":"bad"}',
        '{"auth":"<redacted>","status":"bad"}')
    add('empty-json', '{"password":""}', '{"password":"<redacted>"}')
    add('empty-assignment', 'password="" status=bad', 'password=<redacted> status=bad')
    for scheme in ('vmess','vless','trojan','ss','hy2','hysteria2'):
        add('share-'+scheme, scheme+'://synthetic_CANARY@node.invalid:443 error',
            '<redacted-share-link> error')
    add('uuid', 'id=12345678-1234-1234-1234-123456789abc', 'id=<redacted-uuid>')
    add('ordinary', 'connection refused at node.invalid:443', 'connection refused at node.invalid:443')
    add('blank', ' \t\n', '')
    add('limit', 'x'*1100, 'x'*1024)
    add('long-secret', '{"password":"'+'CANARY'*500+'"}', '{"password":"<redacted>"}')
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    for tool in ('javac','java'):
        if not shutil.which(tool): raise SystemExit(f'{tool} is required')
    source=args.repo.resolve()/'xray/src/main/java/com/fingmi/xray/util/XrayErrorSanitizer.java'
    cases=build_cases()
    java=r'''
import com.fingmi.xray.util.XrayErrorSanitizer;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.Base64;
public final class ErrorSanitizerAudit {
    static String decode(String s) { return new String(Base64.getDecoder().decode(s),StandardCharsets.UTF_8); }
    public static void main(String[] args) throws Exception {
        int cases=0, failed=0;
        for (String line:Files.readAllLines(Path.of(args[0]),StandardCharsets.UTF_8)) {
            String[] parts=line.split("\t",-1);
            String name=parts[0], input=decode(parts[1]), expected=decode(parts[2]);
            String actual=XrayErrorSanitizer.sanitize(input);
            cases++;
            if (!actual.equals(expected)) {
                if (failed<12) System.out.println("FAIL "+name+" actual="+actual.replace("\n","\\n"));
                failed++;
            }
            String twice=XrayErrorSanitizer.sanitize(actual);
            if (!actual.equals(twice)) { failed++; System.out.println("FAIL idempotence "+name); }
        }
        if (!XrayErrorSanitizer.sanitize((String)null).equals("")) throw new AssertionError("null string");
        if (!XrayErrorSanitizer.sanitize((Throwable)null).equals("")) throw new AssertionError("null throwable");
        if (!XrayErrorSanitizer.fromException(new IllegalArgumentException()).equals("IllegalArgumentException")) throw new AssertionError("exception fallback");
        if (!XrayErrorSanitizer.sanitize(new LinkageError("password=CANARY_NATIVE")).equals("password=<redacted>")) throw new AssertionError("linkage error");
        System.out.println("Sanitizer cases="+cases+" failures="+failed+" plus idempotence and 4 API checks");
        if (failed>0) throw new AssertionError("Sanitizer failed "+failed+" checks");
    }
}
'''
    with tempfile.TemporaryDirectory(prefix='xray-sanitizer-audit-') as directory:
        temp=Path(directory)
        harness=temp/'ErrorSanitizerAudit.java'; harness.write_text(java,encoding='utf-8')
        data=temp/'cases.tsv'
        def enc(s): return base64.b64encode(s.encode('utf-8')).decode('ascii')
        data.write_text(''.join(name+'\t'+enc(value)+'\t'+enc(expected)+'\n'
                                for name,value,expected in cases),encoding='utf-8')
        subprocess.run(['javac','-encoding','UTF-8','-d',str(temp),str(source),str(harness)],check=True)
        subprocess.run(['java','-cp',str(temp),'ErrorSanitizerAudit',str(data)],check=True)

if __name__=='__main__': main()
