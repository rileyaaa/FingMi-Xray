package com.fongmi.android.tv.network;

import android.content.Context;

import com.fongmi.android.tv.service.DLNARendererService;

/** Leanback-only bridge for the TV DLNA renderer lifecycle. */
final class TvDlnaLifecycle {

    private TvDlnaLifecycle() {
    }

    static void start(Context context) {
        DLNARendererService.start(context);
    }

    static void stop(Context context) {
        DLNARendererService.stop(context);
    }
}
