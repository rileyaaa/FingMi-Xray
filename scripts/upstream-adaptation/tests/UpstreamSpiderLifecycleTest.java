package com.fongmi.android.tv.api.loader;

import android.content.Context;
import com.github.catvod.crawler.Spider;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import java.util.concurrent.CancellationException;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35,manifest=Config.NONE)
public class UpstreamSpiderLifecycleTest {
    private static class Loader extends SpiderLoader {
        int cleared;
        Spider get(String key,Spider spider){return load(key,RuntimeEnvironment.getApplication(),"",()->spider);}
        protected void clearReferences(){cleared++;}
    }
    private static class Entry extends Spider {
        int closed,destroyed,inits;
        public void init(Context c,String ext){inits++;}
        public void close(){closed++;super.close();}
        public void destroy(){destroyed++;}
    }
    @Test public void retiredGenerationClosesAndOnlyExitDestroys(){
        Loader old=new Loader(),next=new Loader();Entry a=new Entry(),b=new Entry(),fresh=new Entry();
        assertSame(a,old.get("a",a));assertSame(a,old.get("a",new Entry()));assertEquals(1,a.inits);
        old.get("b",b);old.clear();
        assertEquals(1,a.closed);assertEquals(1,b.closed);assertEquals(0,a.destroyed);assertEquals(1,old.cleared);
        try{old.get("new",new Entry());fail("retired loader accepted work");}catch(CancellationException expected){}
        assertSame(fresh,next.get("a",fresh));assertEquals(0,fresh.closed);
        old.destroy();assertEquals(1,a.destroyed);assertEquals(1,b.destroyed);assertEquals(1,a.closed);
        assertEquals(0,fresh.destroyed);assertEquals(0,fresh.closed);
        next.destroy();assertEquals(1,fresh.closed);assertEquals(1,fresh.destroyed);
    }
}
