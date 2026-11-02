#!/usr/bin/env python3
"""Compile and exercise production Xray-only media DataSource via JVM stubs."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app/src/main/java/com/fingmi/integration/xray/XrayGuardedPlaybackDataSource.java"
MEDIA_SOURCE = ROOT / "app/src/main/java/com/fongmi/android/tv/player/exo/ExoMediaSourceFactory.java"

# Only the active Xray branch may instantiate the restricted wrapper.
media = MEDIA_SOURCE.read_text(encoding="utf-8")
if "new XrayGuardedPlaybackDataSource(upstream.createDataSource())" not in media:
    raise SystemExit("Xray media source lost guarded transport")
if "dataSourceFactory = proxy == null" not in media:
    raise SystemExit("Direct and Xray transports are no longer isolated")

STUBS = {
    "android/net/Uri.java": """package android.net;
        public final class Uri {
            private final String scheme;
            public Uri(String scheme) { this.scheme = scheme; }
            public String getScheme() { return scheme; }
        }""",
    "androidx/media3/datasource/TransferListener.java":
        "package androidx.media3.datasource; public interface TransferListener {}",
    "androidx/media3/datasource/DataSpec.java": """package androidx.media3.datasource;
        public class DataSpec {
            public final android.net.Uri uri;
            public DataSpec(String scheme) { uri = new android.net.Uri(scheme); }
        }""",
    "androidx/media3/datasource/DataSource.java": """package androidx.media3.datasource;
        import java.io.IOException;
        import java.util.List;
        import java.util.Map;
        public interface DataSource {
            void addTransferListener(TransferListener listener);
            long open(DataSpec spec) throws IOException;
            int read(byte[] buffer, int offset, int length) throws IOException;
            android.net.Uri getUri();
            Map<String, List<String>> getResponseHeaders();
            void close() throws IOException;
        }""",
    "XrayGuardedPlaybackHarness.java": r"""import com.fingmi.integration.xray.XrayGuardedPlaybackDataSource;
        import androidx.media3.datasource.*;
        import android.net.Uri;
        import java.io.IOException;
        import java.util.*;
        public final class XrayGuardedPlaybackHarness {
            static final class Fake implements DataSource {
                int opens, closes, reads, listeners;
                boolean failOpen;
                String scheme;
                public void addTransferListener(TransferListener listener) { listeners++; }
                public long open(DataSpec spec) throws IOException {
                    opens++; scheme = spec.uri.getScheme();
                    if (failOpen) throw new IOException("transport failed");
                    return 42;
                }
                public int read(byte[] buf,int off,int len) { reads++; return len; }
                public Uri getUri() { return new Uri(scheme); }
                public Map<String,List<String>> getResponseHeaders() {
                    return Map.of("test", List.of("yes"));
                }
                public void close() { closes++; }
            }
            private static void check(boolean pass,String reason) {
                if (!pass) throw new AssertionError(reason);
            }
            public static void main(String[] ignored) throws Exception {
                int valid = 0, blocked = 0;
                String[] allowed = {"http","HTTP","https","Https","file","FILE","asset",
                    "content","data","rawresource","android.resource",null,"","   ","\u2003"};
                for (String scheme: allowed) {
                    Fake fake = new Fake();
                    XrayGuardedPlaybackDataSource ds = new XrayGuardedPlaybackDataSource(fake);
                    ds.addTransferListener(null);
                    check(ds.open(new DataSpec(scheme)) == 42,"open: "+scheme);
                    check(ds.read(new byte[8],0,8) == 8,"read");
                    check("yes".equals(ds.getResponseHeaders().get("test").get(0)),"headers");
                    check(Objects.equals(ds.getUri().getScheme(),scheme),"uri");
                    ds.close(); ds.close();
                    check(fake.opens==1 && fake.closes==1 && fake.reads==1 && fake.listeners==1,
                        "delegate lifetime: "+scheme);
                    valid++;
                }
                for (String scheme: new String[]{"rtsp","rtspt","RTSP","smb","ftp",
                        "file+http","javascript","ws","udp","\u00a0"," https"}) {
                    Fake fake = new Fake();
                    XrayGuardedPlaybackDataSource ds = new XrayGuardedPlaybackDataSource(fake);
                    boolean threw = false;
                    try { ds.open(new DataSpec(scheme)); }
                    catch (IOException ex) { threw=ex.getMessage().contains("Xray"); }
                    ds.close();
                    check(threw && fake.opens==0 && fake.closes==0,"direct leak: "+scheme);
                    blocked++;
                }
                Fake failing = new Fake(); failing.failOpen = true;
                XrayGuardedPlaybackDataSource ds = new XrayGuardedPlaybackDataSource(failing);
                try { ds.open(new DataSpec("https")); throw new AssertionError("must throw"); }
                catch (IOException expected) { check(failing.opens==1,"open tried"); }
                ds.close(); ds.close();
                check(failing.closes==1,"failed open must permit cleanup");
                System.out.println("PASS Xray source boundary: "+valid+" allowed, "+blocked+
                    " blocked, failure cleanup and direct delegation");
            }
        }""",
}

with tempfile.TemporaryDirectory(prefix="xray-guarded-source-") as directory:
    root = Path(directory)
    stubs = []
    for name, content in STUBS.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        stubs.append(str(target))
    subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-d", str(root),
                    str(SOURCE), *stubs], check=True)
    subprocess.run(["java", "-cp", str(root), "XrayGuardedPlaybackHarness"], check=True)
