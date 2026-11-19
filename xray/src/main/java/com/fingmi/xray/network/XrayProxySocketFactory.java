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

    /**
     * RTSP redirects are supplied by a remote server after Xray was enabled
     * for the original public playback URL. Re-check EVERY new SOCKS target:
     * the initial playback address guard cannot authorize a redirected host.
     * Keep public hostnames unresolved for remote SOCKS DNS resolution.
     */
    private static String requirePublicDestination(String host) throws IOException {
        String target = host;
        if (target != null && target.startsWith("[") && target.endsWith("]")) {
            target = target.substring(1, target.length() - 1);
        }
        if (PublicPlaybackDestinationInterceptor.isPrivateOrReserved(target)) {
            throw new IOException("Private or reserved RTSP playback destination blocked");
        }
        return target;
    }

    @Override
    public Socket createSocket() {
        return new Socket(proxy);
    }

    @Override
    public Socket createSocket(String host, int port) throws IOException {
        String target = requirePublicDestination(host);
        Socket socket = createSocket();
        try {
            socket.connect(InetSocketAddress.createUnresolved(target, port));
            return socket;
        } catch (IOException | RuntimeException error) {
            closeQuietly(socket);
            throw error;
        }
    }

    @Override
    public Socket createSocket(
            String host,
            int port,
            InetAddress localAddress,
            int localPort) throws IOException {
        String target = requirePublicDestination(host);
        Socket socket = createSocket();
        try {
            socket.bind(new InetSocketAddress(localAddress, localPort));
            socket.connect(InetSocketAddress.createUnresolved(target, port));
            return socket;
        } catch (IOException | RuntimeException error) {
            closeQuietly(socket);
            throw error;
        }
    }

    @Override
    public Socket createSocket(
            InetAddress address,
            int port) throws IOException {
        requirePublicDestination(address == null ? null : address.getHostAddress());
        Socket socket = createSocket();
        try {
            socket.connect(new InetSocketAddress(address, port));
            return socket;
        } catch (IOException | RuntimeException error) {
            closeQuietly(socket);
            throw error;
        }
    }

    @Override
    public Socket createSocket(
            InetAddress address,
            int port,
            InetAddress localAddress,
            int localPort) throws IOException {
        requirePublicDestination(address == null ? null : address.getHostAddress());
        Socket socket = createSocket();
        try {
            socket.bind(new InetSocketAddress(localAddress, localPort));
            socket.connect(new InetSocketAddress(address, port));
            return socket;
        } catch (IOException | RuntimeException error) {
            closeQuietly(socket);
            throw error;
        }
    }
    private static void closeQuietly(Socket socket) {
        try {
            socket.close();
        } catch (IOException | RuntimeException ignored) {
        }
    }

}
