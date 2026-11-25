package com.github.catvod.net;

import com.fingmi.xray.network.XrayHttpClient;
import com.github.catvod.utils.Auth;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

import java.net.Proxy;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import okhttp3.Call;
import okhttp3.OkHttpClient;
import okhttp3.Protocol;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.ResponseBody;

import static org.junit.Assert.*;

/** Actual OkHttp/catvod interceptors; the terminal HTTP exchange is synthetic. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 35, manifest = Config.NONE)
public class UpstreamPlaybackAuthTest {
    private static final String ORIGIN = "https://media.example/";
    private static final String OTHER = "https://other.example/";

    private static Request request(String url) {
        return new Request.Builder().url(url).build();
    }

    @Test public void boundClientAndRecoveryAreIndependent() {
        OkHttpClient api = OkHttp.client(), player = OkHttp.player();
        try (XrayHttpClient resources = new XrayHttpClient(23456, player)) {
            OkHttpClient bound = resources.client();
            assertNotSame(player, bound);
            assertNotSame(player.dispatcher(), bound.dispatcher());
            assertNotSame(player.connectionPool(), bound.connectionPool());
            assertEquals(Proxy.Type.SOCKS, bound.proxy().type());
            assertSame(bound, OkHttp.player(bound, null));
            Call call = OkHttp.player(bound, Auth.Context.NONE).newCall(request(ORIGIN+"index"));
            assertSame(Auth.Context.NONE, call.request().tag(Auth.Context.class));
            OkHttp.resetApiNetworkForResume();
            assertNotSame(api, OkHttp.client());
            assertSame(player, OkHttp.player());
            assertSame(bound, resources.client());
            assertFalse(bound.dispatcher().executorService().isShutdown());
        }
    }

    private static void redirect(Auth.Context auth, String header, String token) throws Exception {
        assertNotNull(auth);
        List<Request> seen = new ArrayList<>();
        List<Proxy> routes = new ArrayList<>();
        OkHttpClient base = OkHttp.player().newBuilder().addInterceptor(chain -> {
            Request req = chain.request();
            seen.add(req);
            routes.add(chain.getProxy());
            Response.Builder response = new Response.Builder().request(req).protocol(Protocol.HTTP_1_1)
                    .body(ResponseBody.EMPTY);
            String path = req.url().encodedPath();
            if (path.equals("/start")) return response.code(302).message("Found").header("Location", ORIGIN+"segment").build();
            if (path.equals("/segment")) return response.code(302).message("Found").header("Location", OTHER+"final").build();
            return response.code(200).message("OK").build();
        }).build();
        try (XrayHttpClient resources = new XrayHttpClient(23456, base)) {
            Request plain = request(ORIGIN+"start");
            Call.Factory factory = OkHttp.player(resources.client(), auth);
            try (Response response = factory.newCall(plain).execute()) {
                assertEquals(200,response.code());
            }
            assertEquals(3,seen.size());
            for (int i=0;i<3;i++) {
                assertSame(auth, seen.get(i).tag(Auth.Context.class));
                assertEquals(resources.client().proxy(),routes.get(i));
            }
            for (int i=0;i<2;i++) {
                assertEquals(header, seen.get(i).header("Authorization"));
                assertEquals(token, seen.get(i).url().queryParameter("auth"));
            }
            assertNull(seen.get(2).header("Authorization"));
            assertNull(seen.get(2).url().queryParameter("auth"));
            Request regular = OkHttp.player(auth).newCall(plain).request();
            assertEquals(regular.url(),seen.get(0).url());
            assertEquals(regular.header("Authorization"),seen.get(0).header("Authorization"));
        }
    }

    @Test public void tokenFollowsOnlyCapturedOriginThroughRedirects() throws Exception {
        String url = ORIGIN+"start?auth=fixture-token";
        redirect(Auth.capture(url, Map.of(),url,null),null,"fixture-token");
    }

    @Test public void basicAuthFollowsOnlyCapturedOriginThroughRedirects() throws Exception {
        String basic = "Basic Zml4dHVyZTpwYXNz";
        redirect(Auth.capture(ORIGIN+"start",Map.of("Authorization",basic),ORIGIN+"start",basic),basic,null);
    }
}
