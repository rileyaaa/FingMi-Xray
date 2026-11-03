#!/usr/bin/env python3
"""Compile and execute the actual fork artwork transport guard with JVM doubles.

This is version-independent and uses no Android SDK, Gradle, Maven or network.
It checks proxy isolation and asynchronous cancellation before expensive APK work.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PRODUCTION = ROOT / "app/src/main/java/com/fingmi/integration/xray/XrayArtworkBitmapLoader.java"

STUBS = {
    "android/graphics/Bitmap.java": "package android.graphics; public final class Bitmap {}",
    "android/net/Uri.java": r'''package android.net;
public final class Uri {
    private final String value;
    private Uri(String value) { this.value = value; }
    public static Uri parse(String value) { return new Uri(value); }
    public String getScheme() {
        int colon = value.indexOf(':');
        if (colon < 1) return null;
        String prefix = value.substring(0, colon);
        return prefix.matches("[a-zA-Z][a-zA-Z0-9+.-]*") ? prefix : null;
    }
}''',
    "androidx/annotation/NonNull.java": "package androidx.annotation; public @interface NonNull {}",
    "androidx/media3/common/util/BitmapLoader.java": r'''package androidx.media3.common.util;
import android.graphics.Bitmap;
import android.net.Uri;
import com.google.common.util.concurrent.ListenableFuture;
public interface BitmapLoader {
    boolean supportsMimeType(String type);
    ListenableFuture<Bitmap> decodeBitmap(byte[] data);
    ListenableFuture<Bitmap> loadBitmap(Uri uri);
}''',
    "com/fongmi/android/tv/player/PlayerManager.java": r'''package com.fongmi.android.tv.player;
public final class PlayerManager {
    public boolean active;
    public boolean hasXraySession() { return active; }
}''',
    "com/google/common/util/concurrent/ListenableFuture.java": r'''package com.google.common.util.concurrent;
import java.util.concurrent.Executor;
import java.util.concurrent.Future;
public interface ListenableFuture<T> extends Future<T> {
    void addListener(Runnable listener, Executor executor);
}''',
    "com/google/common/util/concurrent/SettableFuture.java": r'''package com.google.common.util.concurrent;
import java.util.concurrent.*;
public final class SettableFuture<T> implements ListenableFuture<T> {
    private final CompletableFuture<T> future = new CompletableFuture<>();
    public boolean set(T value) { return future.complete(value); }
    public boolean setException(Throwable problem) { return future.completeExceptionally(problem); }
    @Override public boolean cancel(boolean interrupt) { return future.cancel(interrupt); }
    @Override public boolean isCancelled() { return future.isCancelled(); }
    @Override public boolean isDone() { return future.isDone(); }
    @Override public T get() throws InterruptedException, ExecutionException { return future.get(); }
    @Override public T get(long timeout, TimeUnit unit)
        throws InterruptedException, ExecutionException, TimeoutException {
        return future.get(timeout, unit);
    }
    @Override public void addListener(Runnable listener, Executor executor) {
        future.whenComplete((value, failure) -> executor.execute(listener));
    }
}''',
    "com/google/common/util/concurrent/Futures.java": r'''package com.google.common.util.concurrent;
public final class Futures {
    public static <T> ListenableFuture<T> immediateFailedFuture(Throwable problem) {
        SettableFuture<T> result = new SettableFuture<>();
        result.setException(problem);
        return result;
    }
}''',
    "com/google/common/util/concurrent/MoreExecutors.java": r'''package com.google.common.util.concurrent;
import java.util.concurrent.Executor;
public final class MoreExecutors {
    public static Executor directExecutor() { return Runnable::run; }
}''',
}

HARNESS = r'''package com.fingmi.integration.xray;
import android.graphics.Bitmap;
import android.net.Uri;
import androidx.media3.common.util.BitmapLoader;
import com.fongmi.android.tv.player.PlayerManager;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.SettableFuture;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;

public final class ArtworkLoaderTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static final class Delegate implements BitmapLoader {
        final List<SettableFuture<Bitmap>> pending = new ArrayList<>();
        int loads;
        @Override public boolean supportsMimeType(String value) { return "image/png".equals(value); }
        @Override public ListenableFuture<Bitmap> decodeBitmap(byte[] value) {
            return new SettableFuture<>();
        }
        @Override public ListenableFuture<Bitmap> loadBitmap(Uri uri) {
            loads++;
            SettableFuture<Bitmap> result = new SettableFuture<>();
            pending.add(result);
            return result;
        }
    }

    public static void main(String[] args) throws Exception {
        PlayerManager manager = new PlayerManager();
        Delegate delegate = new Delegate();
        XrayArtworkBitmapLoader loader = new XrayArtworkBitmapLoader(manager, delegate);
        check(loader.supportsMimeType("image/png"), "MIME capability must delegate");
        check(!loader.supportsMimeType("image/gif"), "unsupported MIME must remain unsupported");
        check(loader.decodeBitmap(new byte[]{1}) != null, "bitmap decode should delegate");

        // A direct-mode request is allowed but must be canceled if the
        // active playback identity changes while the asynchronous load runs.
        ListenableFuture<Bitmap> old = loader.loadBitmap(Uri.parse("https://cdn.example/old.png"));
        check(delegate.loads == 1, "direct HTTP request should reach delegate");
        manager.active = true;
        loader.cancelRemoteLoads();
        check(old.isCancelled(), "pending direct artwork must cancel when switching to Xray");
        loader.cancelRemoteLoads();

        // Active Xray must reject remote artwork without starting direct IO.
        for (String url : new String[]{"https://cdn.example/image.png", "HTTP://cdn.example/2.png", "ftp://cdn.example/3.png"}) {
            int before = delegate.loads;
            ListenableFuture<Bitmap> blocked = loader.loadBitmap(Uri.parse(url));
            check(delegate.loads == before, "active Xray must not dispatch remote artwork: " + url);
            try {
                blocked.get();
                throw new AssertionError("expected active Xray artwork rejection: " + url);
            } catch (ExecutionException error) {
                check(error.getCause() instanceof IOException, "remote artwork rejection must be IO failure");
            }
        }

        // Locally resolved assets remain allowed during Xray; stopping
        // remote requests must not cancel local resource reads.
        List<ListenableFuture<Bitmap>> local = new ArrayList<>();
        for (String url : new String[]{"file:///tmp/image.png", "content://media/1", "asset:///art.png",
                "data:image/png;base64,AA==", "rawresource:///4", "android.resource://app/4",
                "relative/image.png"}) {
            local.add(loader.loadBitmap(Uri.parse(url)));
        }
        int afterLocal = delegate.loads;
        check(afterLocal == 8, "all seven local/resource requests should delegate");
        loader.cancelRemoteLoads();
        for (ListenableFuture<Bitmap> future : local)
            check(!future.isCancelled(), "Xray cleanup must not cancel local artwork");

        // Completed direct requests are retired from tracking, and an
        // interrupted future cannot revive a canceled network generation.
        manager.active = false;
        ListenableFuture<Bitmap> completed = loader.loadBitmap(Uri.parse("https://cdn.example/done.png"));
        check(delegate.pending.get(delegate.pending.size() - 1).set(new Bitmap()), "complete direct request");
        loader.cancelRemoteLoads();
        check(!completed.isCancelled() && completed.isDone(), "completed remote artwork must remain complete");
        ListenableFuture<Bitmap> pending = loader.loadBitmap(Uri.parse("https://cdn.example/pending.png"));
        loader.cancelRemoteLoads();
        check(pending.isCancelled(), "later pending artwork is canceled");
        System.out.println("PASS Xray artwork: direct, proxy deny, local exception, generation cancel, completion");
    }
}'''


def main():
    if not PRODUCTION.is_file():
        raise SystemExit("XrayArtworkBitmapLoader.java is missing")
    with tempfile.TemporaryDirectory(prefix="fingmi-artwork-jvm-") as temp:
        root = Path(temp)
        files = []
        for name, code in {**STUBS,
                           "com/fingmi/integration/xray/ArtworkLoaderTest.java": HARNESS}.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code + "\n", encoding="utf-8")
            files.append(str(target))
        classes = root / "classes"
        subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-d", str(classes),
                        str(PRODUCTION), *files], check=True)
        subprocess.run(["java", "-cp", str(classes),
                        "com.fingmi.integration.xray.ArtworkLoaderTest"], check=True)


if __name__ == "__main__":
    main()
