package com.fongmi.android.tv.api.loader;
import com.fongmi.android.tv.App;
// Boundary fixture only: actual SpiderLoader is tested independently.
public final class BaseLoader {
    private static final BaseLoader INSTANCE=new BaseLoader();
    public int clears;
    public Runnable pending;
    public static BaseLoader get(){return INSTANCE;}
    public void clear(Runnable after){if(pending!=null)throw new AssertionError("overlapping clear");clears++;pending=after;}
    public void complete(){Runnable after=pending;pending=null;App.post(after,0);}
}
