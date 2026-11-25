package com.fingmi.integration.recovery;

import android.app.Activity;
import android.app.Application;
import android.content.Intent;
import android.os.Looper;
import com.fingmi.tvrecovery.TvNetworkLifecycle;
import com.fongmi.android.tv.api.loader.BaseLoader;
import com.fongmi.android.tv.service.DLNARendererService;
import com.fongmi.android.tv.utils.ImgUtil;
import com.github.catvod.net.OkHttp;
import com.fingmi.xray.network.XrayHttpClient;
import okhttp3.OkHttpClient;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;
import org.robolectric.shadows.ShadowLooper;
import org.robolectric.shadow.api.Shadow;

/** Full actual FongMi adapter and leanback renderer bridge; app-only services
 * are boundary fixtures, not Android/player source replacements. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class UpstreamRecoveryAdapterTest {
    @Test public void actualAdapterWakesAndRetiresStaleOwner() {
        Application app=RuntimeEnvironment.getApplication();
        AtomicInteger cancel=new AtomicInteger(),progress=new AtomicInteger(),refresh=new AtomicInteger();
        boolean[] alive={true};
        FongMiNetworkRecovery recovery=new FongMiNetworkRecovery(app,cancel::incrementAndGet,progress::incrementAndGet,()->alive[0],refresh::incrementAndGet);
        ActivityController<Activity> owner=Robolectric.buildActivity(Activity.class).create().start().resume();
        assertEquals(1,DLNARendererService.starts);
        long first=TvNetworkLifecycle.generation();
        OkHttpClient api=OkHttp.client(),player=OkHttp.player();
        try(XrayHttpClient xray=new XrayHttpClient(23457,player)){
            OkHttpClient bound=xray.client();
            recovery.check();assertEquals(0,BaseLoader.get().clears);
            screen(app,Intent.ACTION_SCREEN_OFF);assertEquals(1,DLNARendererService.stops);
            screen(app,Intent.ACTION_SCREEN_ON);assertEquals(first+1,TvNetworkLifecycle.generation());
            recovery.check();recovery.check();
            assertEquals(2,DLNARendererService.starts);
            assertEquals(1,cancel.get());assertEquals(1,progress.get());assertEquals(1,ImgUtil.resets);assertEquals(1,BaseLoader.get().clears);
            assertNotSame(api,OkHttp.client());assertSame(player,OkHttp.player());assertSame(bound,xray.client());
            mainLooper().idleFor(7,TimeUnit.SECONDS);
            assertEquals(0,refresh.get());
            BaseLoader.get().complete();
            mainLooper().idleFor(7,TimeUnit.SECONDS);
            assertEquals(1,refresh.get());assertEquals(first+1,TvNetworkLifecycle.recoveredGeneration());
            recovery.check();assertEquals(1,BaseLoader.get().clears);
            screen(app,Intent.ACTION_SCREEN_OFF);screen(app,Intent.ACTION_SCREEN_ON);
            recovery.check();assertEquals(2,BaseLoader.get().clears);
            alive[0]=false;recovery.close();BaseLoader.get().complete();
            mainLooper().idleFor(7,TimeUnit.SECONDS);
            assertEquals(1,refresh.get());assertEquals(first+1,TvNetworkLifecycle.recoveredGeneration());
            assertSame(player,OkHttp.player());assertSame(bound,xray.client());assertFalse(bound.dispatcher().executorService().isShutdown());
        }finally{recovery.close();owner.pause().stop().destroy();}
    }
    private static void screen(Application app,String action){app.sendBroadcast(new Intent(action));mainLooper().idle();}
    private static ShadowLooper mainLooper(){return Shadow.extract(Looper.getMainLooper());}
}
