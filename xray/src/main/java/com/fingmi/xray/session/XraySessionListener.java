package com.fingmi.xray.session;

public interface XraySessionListener {

    int IDLE = 1;
    int STARTING = 2;
    int RUNNING = 3;
    int ERROR = 4;

    void onXrayStateChanged(int state, int socksPort, String message);
}
