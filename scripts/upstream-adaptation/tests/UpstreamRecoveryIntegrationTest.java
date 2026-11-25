package com.github.catvod.net;

import android.app.Activity;
import android.app.Application;
import android.content.Intent;
import android.os.Looper;
import com.fingmi.tvrecovery.NetworkRecoveryCoordinator;
import com.fingmi.tvrecovery.TvNetworkLifecycle;
import com.fingmi.xray.network.XrayHttpClient;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import java.util.concurrent.atomic.AtomicInteger;
import okhttp3.OkHttpClient;
import static org.junit.Assert.*;
import org.robolectric.shadows.ShadowLooper;
import org.robolectric.shadow.api.Shadow;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,manifest=Config.NONE)
@LooperMode(LooperMode.Mode.PAUSED)
public class UpstreamRecoveryIntegrationTest {
    @Test public void standbyGenerationReplacesApiButNotPlayerOrBoundTransport() {
        Application app=RuntimeEnvironment.getApplication();
        AtomicInteger starts=new AtomicInteger(),stops=new AtomicInteger();
        TvNetworkLifecycle lifecycle=TvNetworkLifecycle.get(app,new TvNetworkLifecycle.Renderer(){
            public void start(){starts.incrementAndGet();}
            public void stop(){stops.incrementAndGet();}
        });
        ActivityController<Activity> owner=Robolectric.buildActivity(Activity.class).create().start().resume();
        assertEquals(1,starts.get());
        long first=TvNetworkLifecycle.generation();
        OkHttpClient api=OkHttp.client(),player=OkHttp.player();
        OkProxySelector selector=OkHttp.selector();OkDns dns=OkHttp.dns();
        AtomicInteger cancels=new AtomicInteger(),clears=new AtomicInteger(),refreshes=new AtomicInteger();
        Runnable[] clear={null},poll={null};boolean[] ready={false};
        try(XrayHttpClient xray=new XrayHttpClient(23456,player)) {
            OkHttpClient bound=xray.client();
            NetworkRecoveryCoordinator recovery=new NetworkRecoveryCoordinator(first,new NetworkRecoveryCoordinator.Hooks(){
                public long generation(){return TvNetworkLifecycle.generation();}
                public void cancelRequests(){cancels.incrementAndGet();}
                public void resetApiAndDns(){OkHttp.resetApiNetworkForResume();}
                public void clearSpiders(Runnable after){clears.incrementAndGet();clear[0]=after;}
                public boolean networkReady(){return ready[0];}
                public void schedule(Runnable action,long delay){assertNull(poll[0]);poll[0]=action;assertTrue(delay==0||delay==500);}
                public void unschedule(Runnable action){if(poll[0]==action)poll[0]=null;}
                public void showProgress(){}
                public void refreshHome(){refreshes.incrementAndGet();TvNetworkLifecycle.markRecovered(TvNetworkLifecycle.generation());}
            });
            recovery.check();assertEquals(0,clears.get());
            app.sendBroadcast(new Intent(Intent.ACTION_SCREEN_OFF));mainLooper().idle();
            assertEquals(1,stops.get());
            app.sendBroadcast(new Intent(Intent.ACTION_SCREEN_ON));mainLooper().idle();
            assertEquals(first+1,TvNetworkLifecycle.generation());
            lifecycle.startRendererIfNeeded();assertEquals(2,starts.get());
            recovery.check();recovery.check();assertEquals(1,cancels.get());assertEquals(1,clears.get());
            assertNotSame(api,OkHttp.client());assertSame(player,OkHttp.player());
            assertSame(selector,OkHttp.selector());assertSame(dns,OkHttp.dns());
            assertSame(bound,xray.client());assertFalse(bound.dispatcher().executorService().isShutdown());
            assertNull(poll[0]);assertEquals(0,refreshes.get());
            clear[0].run();runPoll(poll);assertEquals(0,refreshes.get());
            ready[0]=true;runPoll(poll);assertEquals(0,refreshes.get());
            runPoll(poll);assertEquals(1,refreshes.get());
            assertEquals(first+1,TvNetworkLifecycle.recoveredGeneration());
            recovery.check();assertEquals(1,clears.get());
            owner.pause().stop();assertEquals(2,stops.get());
            owner.restart().start().resume();assertEquals(first+2,TvNetworkLifecycle.generation());
            recovery.check();assertEquals(2,clears.get());
            recovery.close();clear[0].run();assertNull(poll[0]);assertEquals(1,refreshes.get());
            assertSame(player,OkHttp.player());assertSame(bound,xray.client());
        }finally{owner.pause().stop().destroy();}
    }
    private static void runPoll(Runnable[] poll){Runnable r=poll[0];assertNotNull(r);poll[0]=null;r.run();}
    private static ShadowLooper mainLooper(){return Shadow.extract(Looper.getMainLooper());}
}
