package com.fongmi.android.tv.event;

import android.os.Looper;

import com.fongmi.android.tv.App;

import org.greenrobot.eventbus.EventBus;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** Phone input only: success requires the TV settings form to actually apply it. */
public final class XrayLiveRulesEvent {
    private final String groups;
    private final String channels;
    private boolean applied;

    private XrayLiveRulesEvent(String groups, String channels) {
        this.groups = groups;
        this.channels = channels;
    }

    public String groups() { return groups; }
    public String channels() { return channels; }
    public void markApplied() { applied = true; }

    public static boolean post(String groups, String channels) {
        // MAIN subscribers run synchronously when posting from main. A generic
        // Object subscriber is not evidence that the settings page accepted it.
        FutureTask<Boolean> delivery = new FutureTask<>(() -> {
            XrayLiveRulesEvent event = new XrayLiveRulesEvent(groups, channels);
            EventBus.getDefault().post(event);
            return event.applied;
        });
        if (Looper.myLooper() == Looper.getMainLooper()) delivery.run();
        else App.post(delivery);
        try {
            return delivery.get(3, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        } catch (ExecutionException | TimeoutException e) {
            return false;
        } finally {
            // Do not apply a timed-out request later if main has not begun it.
            delivery.cancel(false);
        }
    }
}
