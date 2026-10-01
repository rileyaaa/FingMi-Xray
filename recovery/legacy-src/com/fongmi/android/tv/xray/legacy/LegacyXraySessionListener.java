package com.fongmi.android.tv.xray.legacy;

/**
 * UI-facing state callback recovered from xz3.
 */
public interface LegacyXraySessionListener {

    int OFF = 1;
    int STARTING = 2;
    int RUNNING = 3;
    int ERROR = 4;

    void onXrayState(int state, int socksPort, String message);
}
