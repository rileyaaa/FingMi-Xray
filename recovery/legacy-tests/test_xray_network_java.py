from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
NETWORK = ROOT / "xray/src/main/java/com/fingmi/xray/network"

STUBS = {
    "okhttp3/HttpUrl.java": "package okhttp3; public class HttpUrl { public String scheme(){return \"http\";} public boolean isHttps(){return false;} public String host(){return \"example.com\";} }",
    "okhttp3/Request.java": "package okhttp3; public class Request { public HttpUrl url(){return new HttpUrl();} }",
    "okhttp3/Response.java": "package okhttp3; public class Response {}",
    "okhttp3/Interceptor.java": "package okhttp3; import java.io.IOException; public interface Interceptor { Response intercept(Chain c) throws IOException; interface Chain { Request request(); Response proceed(Request r) throws IOException; } }",
    "okhttp3/ConnectionPool.java": "package okhttp3; import java.util.concurrent.TimeUnit; public class ConnectionPool { public ConnectionPool(int a, long b, TimeUnit c){} public void evictAll(){} }",
    "okhttp3/Dispatcher.java": "package okhttp3; import java.util.concurrent.ExecutorService; import java.util.concurrent.Executors; public class Dispatcher { public ExecutorService executorService(){return Executors.newSingleThreadExecutor();} public void cancelAll(){} }",
    "okhttp3/OkHttpClient.java": "package okhttp3; import java.net.Proxy; public class OkHttpClient { public Builder newBuilder(){return new Builder();} public static class Builder { public Builder cache(Object x){return this;} public Builder dispatcher(Dispatcher x){return this;} public Builder connectionPool(ConnectionPool x){return this;} public Builder proxy(Proxy x){return this;} public Builder addNetworkInterceptor(Interceptor x){return this;} public OkHttpClient build(){return new OkHttpClient();} } }",
}

HARNESS = """package com.fingmi.xray.network;
public class NetworkCheck {
    public static void main(String[] args) {
        String[] blocked = {"localhost", "a.local", "127.0.0.1", "10.0.0.1",
            "192.168.1.1", "169.254.1.1", "100.64.0.1", "0.1.2.3",
            "224.0.0.1", "198.18.0.1", "192.0.2.1", "198.51.100.1",
            "203.0.113.1", "::1", "fe80::1", "fc00::1", "2001:db8::1"};
        String[] allowed = {"example.com", "some.invalid", "1.1.1.1", "2606:4700:4700::1111"};
        for (String host : blocked) {
            if (!PublicPlaybackDestinationInterceptor.isPrivateOrReserved(host))
                throw new AssertionError("allowed reserved: " + host);
        }
        for (String host : allowed) {
            if (PublicPlaybackDestinationInterceptor.isPrivateOrReserved(host))
                throw new AssertionError("blocked public: " + host);
        }
        System.out.println("17 blocked and 4 allowed destinations passed");
    }
}
"""

with TemporaryDirectory() as temp:
    root = Path(temp)
    for name, source in STUBS.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    harness = root / "com/fingmi/xray/network/NetworkCheck.java"
    harness.parent.mkdir(parents=True, exist_ok=True)
    harness.write_text(HARNESS)
    source_files = list(root.rglob("*.java")) + [
        NETWORK / "PublicPlaybackDestinationInterceptor.java",
        NETWORK / "XrayProxySocketFactory.java",
        NETWORK / "XrayHttpClient.java",
    ]
    subprocess.run(["java", "com.sun.tools.javac.Main", "-d", str(root),
                    *map(str, source_files)], check=True)
    print("Three Xray network classes compiled against minimal OkHttp interfaces")
    subprocess.run(["java", "-cp", str(root), "com.fingmi.xray.network.NetworkCheck"], check=True)
