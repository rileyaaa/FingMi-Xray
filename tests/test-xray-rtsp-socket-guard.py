#!/usr/bin/env python3
"""JDK test: real Xray SOCKS socket factory rejects RTSP private redirect targets.

The Git-pinned FongMi/media RtspClient calls createSocket(host, port) on both
initial and HTTP-style RTSP redirect connection. The SOCKS server below lives
entirely on loopback; it does not connect to the requested media destinations.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / 'xray/src/main/java/com/fingmi/xray/network/XrayProxySocketFactory.java'
GUARD = ROOT / 'xray/src/main/java/com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java'
PLAYBACK_ADDRESS = ROOT / 'xray/src/main/java/com/fingmi/xray/session/XrayPlaybackAddress.java'
STUBS = {
    'okhttp3/HttpUrl.java': 'package okhttp3; public class HttpUrl { public String scheme(){return "http";} public boolean isHttps(){return false;} public String host(){return "example.com";} }',
    'okhttp3/Request.java': 'package okhttp3; public class Request { public HttpUrl url(){return new HttpUrl();} }',
    'okhttp3/Response.java': 'package okhttp3; public class Response {}',
    'okhttp3/Interceptor.java': 'package okhttp3; import java.io.IOException; public interface Interceptor { Response intercept(Chain c) throws IOException; interface Chain { Request request(); Response proceed(Request r) throws IOException; } }',
}
HARNESS = r'''
package com.fingmi.xray.network;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import com.fingmi.xray.session.XrayPlaybackAddress;

public final class RtspSocketGuardTest {
    private static int assertions;
    private static void check(boolean yes, String message) {
        assertions++;
        if (!yes) throw new AssertionError(message);
    }
    private static Proxy proxy(ServerSocket server) {
        return new Proxy(Proxy.Type.SOCKS, new InetSocketAddress(server.getInetAddress(), server.getLocalPort()));
    }
    private interface Connector { Socket connect() throws IOException; }
    private static void blocked(String label, Connector attempt) throws Exception {
        try (Socket socket=attempt.connect()) {
            throw new AssertionError("reserved RTSP target was accepted by " + label);
        } catch (IOException rejected) {
            check(rejected.getMessage() != null && rejected.getMessage().contains("Private or reserved RTSP"),
                    "reserved RTSP target reached SOCKS or failed for wrong reason: " + label + ": " + rejected);
        }
    }
    private static void privateTargets() throws Exception {
        try(ServerSocket server=new ServerSocket(0,10,InetAddress.getLoopbackAddress())) {
            server.setSoTimeout(100);
            java.util.concurrent.atomic.AtomicInteger requests = new java.util.concurrent.atomic.AtomicInteger();
            java.util.concurrent.atomic.AtomicBoolean live = new java.util.concurrent.atomic.AtomicBoolean(true);
            // Negative test has a local sink: without the guard, the old
            // factory contacts SOCKS and receives EOF, never the guard error.
            Thread sink = new Thread(() -> {
                while(live.get()) {
                    try(Socket accepted=server.accept()) {requests.incrementAndGet();}
                    catch(SocketTimeoutException ignored) {}
                    catch(IOException closed) {return;}
                }
            }, "rtsp-private-target-sink");
            sink.setDaemon(true);sink.start();
            XrayProxySocketFactory f=new XrayProxySocketFactory(proxy(server));
            for (String address : List.of(
                    "127.0.0.1", "10.0.0.1", "192.168.1.15", "localhost", "camera.local",
                    "localhost.", "camera.local.", "media.localhost.",
                    "100.64.0.1", "203.0.113.5", "[::1]", "[fc00::1]", "::ffff:127.0.0.1")) {
                check(!XrayPlaybackAddress.supports("rtsp://"+address+"/stream"),
                        "private RTSP initial URL was accepted: "+address);
                check(!XrayPlaybackAddress.supports("https://"+address+"/stream"),
                        "private HTTPS initial URL was accepted: "+address);
                blocked("name " + address, ()->f.createSocket(address,8554));
                blocked("name-bound " + address,
                        ()->f.createSocket(address,8554,InetAddress.getLoopbackAddress(),0));
            }
            for (InetAddress address : List.of(
                    InetAddress.getByAddress(new byte[]{127,0,0,1}),
                    InetAddress.getByAddress(new byte[]{10,1,2,3}),
                    InetAddress.getByName("::1"),
                    InetAddress.getByName("fc00::1"))) {
                blocked("inet " + address, ()->f.createSocket(address,8554));
                blocked("inet-bound " + address,
                        ()->f.createSocket(address,8554,InetAddress.getLoopbackAddress(),0));
            }
            live.set(false);sink.join(600);
            check(requests.get()==0,
                    "private RTSP target reached the local SOCKS endpoint: " + requests);
        }
    }
    private static String acceptSocks(ServerSocket server) throws Exception {
        try(Socket c=server.accept()) {
            c.setSoTimeout(4000);
            DataInputStream in=new DataInputStream(c.getInputStream());
            DataOutputStream out=new DataOutputStream(c.getOutputStream());
            check(in.readUnsignedByte()==5,"SOCKS5 version");
            int count=in.readUnsignedByte();
            byte[] methods=new byte[count];in.readFully(methods);
            out.write(new byte[]{5,0});out.flush();
            check(in.readUnsignedByte()==5 && in.readUnsignedByte()==1 && in.readUnsignedByte()==0,
                    "SOCKS5 CONNECT request");
            int atyp=in.readUnsignedByte();String host;
            if(atyp==3){int len=in.readUnsignedByte();byte[] name=new byte[len];in.readFully(name);
                host=new String(name,java.nio.charset.StandardCharsets.US_ASCII);
            } else if(atyp==1){byte[] address=new byte[4];in.readFully(address);
                host=InetAddress.getByAddress(address).getHostAddress();
            } else if(atyp==4){byte[] address=new byte[16];in.readFully(address);
                host=InetAddress.getByAddress(address).getHostAddress();
            } else throw new AssertionError("SOCKS invalid address type " + atyp);
            int port=in.readUnsignedShort();
            out.write(new byte[]{5,0,0,1,127,0,0,1,0,0});out.flush();
            return host+":"+port;
        }
    }
    private static void publicTargets() throws Exception {
        try(ServerSocket server=new ServerSocket(0,10,InetAddress.getLoopbackAddress())) {
            server.setSoTimeout(4000);
            ExecutorService pool=Executors.newSingleThreadExecutor();
            Future<List<String>> received=pool.submit(()->{
                List<String> results=new ArrayList<>();
                for(int i=0;i<5;i++)results.add(acceptSocks(server));
                return results;
            });
            try {
                XrayProxySocketFactory f=new XrayProxySocketFactory(proxy(server));
                try(Socket s=f.createSocket("media.example",8554)) { check(s.isConnected(),"public hostname"); }
                try(Socket s=f.createSocket("[2606:4700:4700::1111]",8554)) { check(s.isConnected(),"public bracketed IPv6"); }
                InetAddress publicV4=InetAddress.getByAddress(new byte[]{8,8,8,8});
                try(Socket s=f.createSocket(publicV4,8554)) { check(s.isConnected(),"public InetAddress"); }
                try(Socket s=f.createSocket("media.example",8555,InetAddress.getLoopbackAddress(),0)) {check(s.isConnected(),"public bound hostname");}
                try(Socket s=f.createSocket("media.example.",8556)) {check(s.isConnected(),"public absolute FQDN");}
                check(XrayPlaybackAddress.supports("rtsp://media.example./stream"),
                        "public trailing-dot FQDN was blocked from initial playback");
                List<String> got=received.get(5,TimeUnit.SECONDS);
                check(got.size()==5,"successful SOCKS request count: "+got);
                check(got.get(0).equals("media.example:8554"),"SOCKS remote hostname: "+got);
                check(got.get(1).contains("2606:4700:4700::1111") && got.get(1).endsWith(":8554")
                                && !got.get(1).contains("[") && !got.get(1).contains("]"),
                        "SOCKS public IPv6 brackets should be stripped: "+got);
                check(got.get(2).equals("8.8.8.8:8554"),"SOCKS public IPv4: "+got);
                check(got.get(3).equals("media.example:8555"),"SOCKS bound hostname: "+got);
                check(got.get(4).equals("media.example.:8556"),"public trailing-dot FQDN must be preserved: "+got);
            } finally {pool.shutdownNow();}
        }
    }
    public static void main(String[] args) throws Exception {
        publicTargets();
        privateTargets();
        System.out.println("PASS real RTSP SOCKS destinations: " + assertions +
                " checks, private redirect refusals and public remote DNS/IPv6 preserved");
    }
}
'''

def run(factory=FACTORY, guard=GUARD, require_success=True):
    with tempfile.TemporaryDirectory(prefix='xray-rtsp-guard-') as tmp:
        root=Path(tmp)
        sources=[]
        for path, source in STUBS.items():
            p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(source+'\n',encoding='utf-8');sources.append(p)
        p=root/'RtspSocketGuardTest.java';p.write_text(HARNESS,encoding='utf-8');sources.append(p)
        classes=root/'classes'
        subprocess.run(['javac','--release','17','-d',str(classes),str(factory),str(guard),str(PLAYBACK_ADDRESS),*map(str,sources)],check=True)
        result=subprocess.run(['java','-cp',str(classes),'com.fingmi.xray.network.RtspSocketGuardTest'],capture_output=True,text=True,timeout=12)
        if require_success and result.returncode:
            raise AssertionError(result.stdout+'\n'+result.stderr)
        return result

def mutations():
    original=FACTORY.read_text(encoding='utf-8')
    # Independently remove the check on each of the four SocketFactory
    # overloads. A successful mutation test must fail its *runtime* assertion,
    # never merely fail to compile.
    cases = (
        ('hostname socket', 'String target = requirePublicDestination(host);',
         'String target = host;', 0),
        ('bound hostname socket', 'String target = requirePublicDestination(host);',
         'String target = host;', 1),
        ('InetAddress socket', 'requirePublicDestination(address == null ? null : address.getHostAddress());',
         '/* missing address target policy */', 0),
        ('bound InetAddress socket', 'requirePublicDestination(address == null ? null : address.getHostAddress());',
         '/* missing address target policy */', 1),
    )
    with tempfile.TemporaryDirectory(prefix='xray-rtsp-guard-mutations-') as folder:
        replacement=Path(folder)/'XrayProxySocketFactory.java'
        for title,before,after,which in cases:
            count=original.count(before)
            if count!=2:
                raise AssertionError(f'Mutation anchor changed for {title}: {count}')
            first=original.find(before)
            position=first if which==0 else original.find(before,first+len(before))
            replacement.write_text(original[:position]+after+original[position+len(before):],encoding='utf-8')
            bad=run(replacement,require_success=False)
            if bad.returncode==0 or 'AssertionError' not in bad.stderr or not (
                    'reserved RTSP target' in bad.stderr or 'SOCKS public IPv6 brackets' in bad.stderr):
                raise AssertionError(f'Missing RTSP guard mutation survived: {title}\n'
                                     +bad.stdout+bad.stderr)
        # An absolute FQDN ending in a DNS root dot must not bypass the
        # existing localhost/.local source guard in HTTP or redirected RTSP.
        guard_source = GUARD.read_text(encoding='utf-8')
        root_dot_check = '        while (value.endsWith(".")) {\n            value = value.substring(0, value.length() - 1);\n        }\n'
        if guard_source.count(root_dot_check) != 1:
            raise AssertionError('DNS root-dot guard mutation anchor changed')
        broken_guard = Path(folder) / 'PublicPlaybackDestinationInterceptor.java'
        broken_guard.write_text(guard_source.replace(root_dot_check, '        /* root-dot guard removed */\n'),encoding='utf-8')
        bad = run(guard=broken_guard, require_success=False)
        if bad.returncode == 0 or 'AssertionError' not in bad.stderr or not (
                'private RTSP initial URL' in bad.stderr or 'reserved RTSP target' in bad.stderr):
            raise AssertionError('Missing root-dot guard mutation survived\n'+bad.stdout+bad.stderr)
    return len(cases) + 1


if __name__=='__main__':
    result=run()
    print(result.stdout.strip())
    count=mutations()
    print(f'PASS {count} guard-removal mutation negatives (real production socket factory)')
