package p000;

import com.fongmi.android.p002tv.xray.XrayService;
import java.util.concurrent.ThreadFactory;
import org.jupnp.UpnpServiceImpl;

public final class ch0 implements ThreadFactory {

    public final int f2768a;

    public ch0(int i) {
        this.f2768a = i;
    }

    @Override
    public final Thread newThread(Runnable runnable) {
        switch (this.f2768a) {
            case 0:
                return new Thread(runnable, "Media3:DiskPreloadDownloader");
            case 1:
                Thread thread = new Thread(runnable, "TvNetworkCleanup");
                thread.setDaemon(true);
                return thread;
            case 2:
                return UpnpServiceImpl.lambda$createExecutor$0(runnable);
            case 3:
                Thread thread2 = new Thread(runnable, "XrayProxyCleanup");
                thread2.setDaemon(true);
                return thread2;
            default:
                int i = XrayService.f3215n;
                Thread thread3 = new Thread(runnable, "fongmi-xray-core");
                thread3.setDaemon(true);
                return thread3;
        }
    }
}
