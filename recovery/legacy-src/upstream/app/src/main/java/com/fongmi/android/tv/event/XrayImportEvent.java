package com.fongmi.android.tv.event;

import org.greenrobot.eventbus.EventBus;

public record XrayImportEvent(String link) {

    public static void post(String link) {
        EventBus.getDefault().post(new XrayImportEvent(link));
    }
}
