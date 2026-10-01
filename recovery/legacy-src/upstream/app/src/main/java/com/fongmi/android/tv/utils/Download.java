package com.fongmi.android.tv.utils;

import com.fongmi.android.tv.App;
import com.github.catvod.net.OkHttp;
import com.github.catvod.utils.Path;
import com.google.common.net.HttpHeaders;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.util.concurrent.Future;

import okhttp3.Call;
import okhttp3.OkHttpClient;
import okhttp3.Response;

/**
 * FongMi 5.6.0 Download reconstructed with the shipped network-ownership
 * changes used by Xray-aware subtitle/XML downloads.
 */
public class Download {

    private final File file;
    private final String url;

    private Callback callback;
    private Future<?> future;
    private volatile Call currentCall;
    private volatile boolean cancelled;
    private OkHttpClient client;
    private long maxBytes;
    private String tag;

    public static Download create(String url, File file) {
        return new Download(url, file);
    }

    public Download(String url, File file) {
        this.maxBytes = Long.MAX_VALUE;
        this.tag = url;
        this.url = url;
        this.file = file;
    }

    public Download tag(String tag) {
        this.tag = tag;
        return this;
    }

    /**
     * Final APK ji0.f9200g: bind this download to an explicit network client.
     */
    public Download client(OkHttpClient client) {
        this.client = client;
        return this;
    }

    public Download maxBytes(long maxBytes) {
        this.maxBytes = maxBytes > 0 ? maxBytes : Long.MAX_VALUE;
        return this;
    }

    public File get() {
        doInBackground();
        return file;
    }

    public void start(Callback callback) {
        this.callback = callback;
        future = Task.submit(this::doInBackground);
    }

    public Download cancel() {
        cancelled = true;

        Future<?> task = future;
        if (task != null) task.cancel(true);

        Call call = currentCall;
        if (call != null) call.cancel();

        if (client == null) {
            OkHttp.cancel(tag);
        } else {
            OkHttp.cancel(client, tag);
        }

        future = null;
        currentCall = null;
        return this;
    }

    private void doInBackground() {
        if (isCancelled()) {
            Path.clear(file);
            return;
        }

        Call call =
                client == null
                        ? OkHttp.newCall(url, tag)
                        : OkHttp.newCall(client, url, tag);
        currentCall = call;

        try {
            if (isCancelled()) {
                call.cancel();
                Path.clear(file);
                return;
            }

            try (Response response = call.execute()) {
                download(
                        response.body().byteStream(),
                        getLength(response));

                if (!cancelled && callback != null) {
                    App.post(() -> callback.success(file));
                }
            }
        } catch (Exception error) {
            Path.clear(file);

            if (!cancelled) {
                if (callback != null) {
                    App.post(
                            () ->
                                    callback.error(
                                            error.getMessage()));
                } else {
                    throw new RuntimeException(
                            error.getMessage(),
                            error);
                }
            }
        } finally {
            if (currentCall == call) {
                currentCall = null;
            }
        }
    }

    private void download(
            InputStream inputStream,
            double length) throws IOException {
        if (length > maxBytes) {
            throw new IOException(
                    "Download size limit exceeded");
        }

        try (BufferedInputStream input =
                        new BufferedInputStream(inputStream);
                FileOutputStream output =
                        new FileOutputStream(Path.create(file))) {
            byte[] buffer = new byte[16384];
            long totalBytes = 0;

            while (true) {
                int readBytes = input.read(buffer);
                if (readBytes == -1) return;

                if (isCancelled()) {
                    throw new InterruptedIOException(
                            "Download cancelled");
                }

                totalBytes += readBytes;
                if (totalBytes > maxBytes) {
                    throw new IOException(
                            "Download size limit exceeded");
                }

                output.write(
                        buffer,
                        0,
                        readBytes);

                if (length <= 0 || callback == null) {
                    continue;
                }

                int progress =
                        (int) (totalBytes / length * 100.0);
                App.post(
                        () ->
                                callback.progress(
                                        progress));
            }
        }
    }

    private boolean isCancelled() {
        return cancelled
                || Thread.currentThread().isInterrupted();
    }

    private double getLength(Response response) {
        try {
            String header =
                    response.header(
                            HttpHeaders.CONTENT_LENGTH);
            return header == null
                    ? -1
                    : Double.parseDouble(header);
        } catch (Exception ignored) {
            return -1;
        }
    }

    public interface Callback {

        void progress(int progress);

        void error(String msg);

        void success(File file);
    }
}
