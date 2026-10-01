package com.fingmi.xray.network;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.Socket;

import javax.net.SocketFactory;

/**
 * SOCKS SocketFactory used by the RTSP media source.
 *
 * Used by the shipped RTSP media-source path. Hostname overloads deliberately
 * connect to unresolved targets so SOCKS/Xray performs the remote resolution.
 */
public final class XrayProxySocketFactory extends SocketFactory {

    private final Proxy proxy;

    public XrayProxySocketFactory(Proxy proxy) {
        this.proxy = proxy;
    }

    @Override
    public Socket createSocket() {
        return new Socket(proxy);
    }

    @Override
    public Socket createSocket(String host, int port) throws IOException {
        Socket socket = createSocket();
        socket.connect(InetSocketAddress.createUnresolved(host, port));
        return socket;
    }

    @Override
    public Socket createSocket(
            String host,
            int port,
            InetAddress localAddress,
            int localPort) throws IOException {
        Socket socket = createSocket();
        socket.bind(new InetSocketAddress(localAddress, localPort));
        socket.connect(InetSocketAddress.createUnresolved(host, port));
        return socket;
    }

    @Override
    public Socket createSocket(
            InetAddress address,
            int port) throws IOException {
        Socket socket = createSocket();
        socket.connect(new InetSocketAddress(address, port));
        return socket;
    }

    @Override
    public Socket createSocket(
            InetAddress address,
            int port,
            InetAddress localAddress,
            int localPort) throws IOException {
        Socket socket = createSocket();
        socket.bind(new InetSocketAddress(localAddress, localPort));
        socket.connect(new InetSocketAddress(address, port));
        return socket;
    }
}
