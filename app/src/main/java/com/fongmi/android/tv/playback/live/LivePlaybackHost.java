package com.fongmi.android.tv.playback.live;

import androidx.annotation.Nullable;
import androidx.media3.common.MediaMetadata;

import com.fongmi.android.tv.bean.Channel;
import com.fongmi.android.tv.bean.EpgData;
import com.fongmi.android.tv.bean.Group;
import com.fongmi.android.tv.bean.Result;

import java.time.ZoneId;

public interface LivePlaybackHost {

    int getGroupCount();

    int getGroupPosition();

    Group getGroup(int position);

    boolean isPlayerLive();

    boolean hasPlaybackSession();

    /** A host can hold an already-resolved result until its playback transport is ready. */
    default boolean isPlaybackStartPending() { return false; }

    boolean isPlaybackServiceReady();

    void restorePlaybackKey(@Nullable String key);

    long getPlayerPosition();

    ZoneId getZoneId();

    void onCatchupRequested();

    void stopPlaybackForRefresh();

    default void resetXrayForPlaybackChange() { }

    default void prepareXrayForPlaybackChange(LivePlayRequest request) {
        resetXrayForPlaybackChange();
    }

    void startPlayback(Result result, long position, MediaMetadata metadata);

    void resetPlaybackForError(String msg);

    void renderGroupSelection(Group group);

    void renderGroupChannels(Group group);

    void renderChannelSelection(Channel channel);

    default void renderChannelSelection(Channel channel, boolean newPlayback) {
        renderChannelSelection(channel);
    }

    void renderLineSelection(Channel channel, boolean show);

    void renderEpgSelection(EpgData data);

    void renderPlaybackMetadata(MediaMetadata metadata);

    void showCatchupReady(EpgData data);

    void showProgress();
}
