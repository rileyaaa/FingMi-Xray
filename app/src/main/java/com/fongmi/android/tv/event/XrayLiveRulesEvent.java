package com.fongmi.android.tv.event;

import org.greenrobot.eventbus.EventBus;

public record XrayLiveRulesEvent(String groups, String channels) {
    public static void post(String groups, String channels) {
        EventBus.getDefault().post(new XrayLiveRulesEvent(groups, channels));
    }
}
