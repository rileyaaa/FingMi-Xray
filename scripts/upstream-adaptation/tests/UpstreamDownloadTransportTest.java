package com.github.catvod.net;

import android.os.CancellationSignal;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import okhttp3.Call;
import okhttp3.OkHttpClient;
import okhttp3.Protocol;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.ResponseBody;

import static org.junit.Assert.*;

/** Actual 5.9 Download with real files/Range workers; HTTP responses are synthetic. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 35, manifest = Config.NONE)
public class UpstreamDownloadTransportTest {
    private static final Pattern RANGE = Pattern.compile("bytes=(\\d+)-(\\d+)");
    private static final String URL = "https://media.example/subtitle.bin";

    private static byte[] fixture(int size) {
        byte[] result = new byte[size];
        for (int i = 0; i < result.length; i++) result[i] = (byte)(i * 13 + i / 11);
        return result;
    }

    private static OkHttpClient client(byte[] data, List<Request> seen, boolean fail) {
        return new OkHttpClient.Builder().addInterceptor(chain -> {
            Request request = chain.request();
            seen.add(request);
            if (fail) throw new IOException("synthetic selected transport failure");
            assertEquals(URL, request.url().toString());
            Response.Builder response = new Response.Builder().request(request)
                    .protocol(Protocol.HTTP_1_1).header("ETag", "\"fixture-1\"")
                    .header("Accept-Ranges", "bytes");
            String range = request.header("Range");
            if (range == null) return response.code(200).message("OK")
                    .body(ResponseBody.create(data, null)).build();
            Matcher match = RANGE.matcher(range);
            assertTrue(range, match.matches());
            int start = Integer.parseInt(match.group(1));
            int end = Math.min(data.length-1,Integer.parseInt(match.group(2)));
            assertTrue(start >= 0 && end >= start && end < data.length);
            if (start != 0) assertEquals("\"fixture-1\"",request.header("If-Range"));
            byte[] part = Arrays.copyOfRange(data,start,end+1);
            return response.code(206).message("Partial Content")
                    .header("Content-Range","bytes "+start+"-"+end+"/"+data.length)
                    .body(ResponseBody.create(part,null)).build();
        }).build();
    }

    @Test public void selectedFactoryWritesFile() throws Exception {
        File out = Files.createTempDirectory("subtitle-one-").resolve("file").toFile();
        byte[] data = fixture(3073);
        List<Request> seen = new CopyOnWriteArrayList<>();
        OkHttpClient selected = client(data,seen,false);
        Download task = Download.create(URL,out).client(selected).maxBytes(4096);
        assertEquals(out,task.get(new CancellationSignal(),null));
        assertArrayEquals(data,Files.readAllBytes(out.toPath()));
        assertEquals(1,seen.size());
        assertNull(seen.get(0).header("Range"));
    }

    @Test public void everyRangeUsesSelectedFactory() throws Exception {
        File out = Files.createTempDirectory("subtitle-range-").resolve("file").toFile();
        byte[] data = fixture(2*1024*1024+17);
        List<Request> seen = new CopyOnWriteArrayList<>();
        OkHttpClient selected = client(data,seen,false);
        List<Request> bound = new CopyOnWriteArrayList<>();
        Call.Factory factory = request -> {bound.add(request);return selected.newCall(request);};
        Download task = Download.create(URL,out).client(factory).size(data.length).threads(2).maxBytes(data.length);
        assertEquals(out,task.get(new CancellationSignal(),null));
        assertArrayEquals(data,Files.readAllBytes(out.toPath()));
        assertEquals(2,seen.size());
        assertEquals(2,bound.size());
        assertTrue(seen.stream().anyMatch(r->r.header("If-Range")!=null));
    }

    @Test public void selectedFactoryFailureDoesNotFallback() throws Exception {
        File out = Files.createTempDirectory("subtitle-failure-").resolve("file").toFile();
        List<Request> seen = new CopyOnWriteArrayList<>();
        Download task = Download.create(URL,out).client(client(fixture(16),seen,true));
        try {
            task.get(new CancellationSignal(),null);
            fail("must fail closed");
        } catch (IOException error) {
            assertEquals("synthetic selected transport failure",error.getMessage());
        }
        assertEquals(1,seen.size());
        assertFalse(out.exists());
    }
}
