#!/usr/bin/env python3
"""Apply the reproducible FongMi 5.6.8 MPV bridge overlay to pinned FongMi/media."""

from __future__ import annotations

import argparse
from pathlib import Path

OVERLAY_ID = "fongmi-tv-5.6.8-mpv-bridge-v2"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_mpv_lib(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import java.util.concurrent.CopyOnWriteArrayList;\n",
        "import java.nio.ByteBuffer;\n"
        "import java.util.concurrent.ConcurrentHashMap;\n"
        "import java.util.concurrent.CopyOnWriteArrayList;\n",
        "MPVLib stream imports",
    )
    text = replace_once(
        text,
        "  private static final CopyOnWriteArrayList<LogObserver> LOG_OBSERVERS =\n"
        "      new CopyOnWriteArrayList<>();\n",
        "  private static final CopyOnWriteArrayList<LogObserver> LOG_OBSERVERS =\n"
        "      new CopyOnWriteArrayList<>();\n"
        "  private static final ConcurrentHashMap<String, StreamProvider> STREAMS =\n"
        "      new ConcurrentHashMap<>();\n",
        "MPVLib stream registry field",
    )
    text = replace_once(
        text,
        "  public static native int enqueueCommand(long requestId, String[] cmd);\n",
        "  public static native int enqueueCommand(long requestId, String[] cmd);\n\n"
        "  /** Queues a command whose named long result is returned with the command reply. */\n"
        "  public static native int enqueueCommandLongResult(\n"
        "      long requestId, String resultName, String[] cmd);\n",
        "MPVLib long-result native",
    )
    text = replace_once(
        text,
        "  public static void eventCommandReply(long requestId, int error) {\n"
        "    for (EventObserver observer : OBSERVERS) {\n"
        "      observer.eventCommandReply(requestId, error);\n"
        "    }\n"
        "  }\n",
        "  public static void eventCommandReply(long requestId, int error, long result) {\n"
        "    for (EventObserver observer : OBSERVERS) {\n"
        "      observer.eventCommandReply(requestId, error, result);\n"
        "    }\n"
        "  }\n\n"
        "  public static void eventCommandReply(long requestId, int error) {\n"
        "    eventCommandReply(requestId, error, 0L);\n"
        "  }\n",
        "MPVLib three-argument reply",
    )
    text = replace_once(
        text,
        "  public static void removeLogObserver(LogObserver observer) {\n",
        "  public static @Nullable Stream openStream(String name) {\n"
        "    StreamProvider provider = STREAMS.get(name);\n"
        "    return provider == null ? null : provider.open();\n"
        "  }\n\n"
        "  public static void registerStream(String name, StreamProvider provider) {\n"
        "    STREAMS.put(name, provider);\n"
        "  }\n\n"
        "  public static void unregisterStream(String name) {\n"
        "    STREAMS.remove(name);\n"
        "  }\n\n"
        "  public static void removeLogObserver(LogObserver observer) {\n",
        "MPVLib stream registry methods",
    )
    text = replace_once(
        text,
        "    default void eventCommandReply(long requestId, int error) {}\n\n"
        "    void eventEndFile(int reason, int error, @Nullable String errorString);\n",
        "    default void eventCommandReply(long requestId, int error) {}\n\n"
        "    default void eventCommandReply(long requestId, int error, long result) {\n"
        "      eventCommandReply(requestId, error);\n"
        "    }\n\n"
        "    void eventEndFile(int reason, int error, @Nullable String errorString);\n",
        "MPVLib observer long reply",
    )
    text = replace_once(
        text,
        "  public interface LogObserver {\n",
        "  public interface Stream {\n\n"
        "    void cancel();\n\n"
        "    void close();\n\n"
        "    int read(ByteBuffer buffer);\n\n"
        "    long seek(long position);\n\n"
        "    long size();\n"
        "  }\n\n"
        "  public interface StreamProvider {\n\n"
        "    Stream open();\n"
        "  }\n\n"
        "  public interface LogObserver {\n",
        "MPVLib stream interfaces",
    )
    path.write_text(text, encoding="utf-8")


def patch_mpv_client(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  private static final NativeCommandQueue DEFAULT_COMMAND_QUEUE = MPVLib::enqueueCommand;\n\n"
        "  private final LastResult lastResult = new LastResult();\n"
        "  private final Map<Long, PendingRequest> pendingRequests = new HashMap<>();\n"
        "  private final NativeCommandQueue commandQueue;\n"
        "  private long nextRequestId = 1;\n\n"
        "  public MpvClient() {\n"
        "    this(DEFAULT_COMMAND_QUEUE);\n"
        "  }\n\n"
        "  MpvClient(NativeCommandQueue commandQueue) {\n"
        "    this.commandQueue = commandQueue;\n"
        "  }\n",
        "  private static final NativeCommandQueue DEFAULT_COMMAND_QUEUE = MPVLib::enqueueCommand;\n"
        "  private static final NativeLongResultCommandQueue DEFAULT_LONG_RESULT_COMMAND_QUEUE =\n"
        "      MPVLib::enqueueCommandLongResult;\n\n"
        "  private final LastResult lastResult = new LastResult();\n"
        "  private final Map<Long, PendingRequest> pendingRequests = new HashMap<>();\n"
        "  private final NativeCommandQueue commandQueue;\n"
        "  private final NativeLongResultCommandQueue longResultCommandQueue;\n"
        "  private long nextRequestId = 1;\n\n"
        "  public MpvClient() {\n"
        "    this(DEFAULT_COMMAND_QUEUE, DEFAULT_LONG_RESULT_COMMAND_QUEUE);\n"
        "  }\n\n"
        "  MpvClient(NativeCommandQueue commandQueue) {\n"
        "    this(commandQueue, DEFAULT_LONG_RESULT_COMMAND_QUEUE);\n"
        "  }\n\n"
        "  MpvClient(\n"
        "      NativeCommandQueue commandQueue, NativeLongResultCommandQueue longResultCommandQueue) {\n"
        "    this.commandQueue = commandQueue;\n"
        "    this.longResultCommandQueue = longResultCommandQueue;\n"
        "  }\n",
        "MpvClient command queues",
    )
    text = replace_once(
        text,
        "  public boolean command(String[] command) {\n"
        "    String action = command.length == 0 ? \"command\" : \"command:\" + command[0];\n"
        "    return submitCommand(action, command, /* callback= */ null);\n"
        "  }\n",
        "  public boolean command(String[] command) {\n"
        "    String action = command.length == 0 ? \"command\" : \"command:\" + command[0];\n"
        "    return submitCommand(action, command, /* callback= */ null);\n"
        "  }\n\n"
        "  public boolean commandLongResult(\n"
        "      String[] command, String resultName, LongResultCallback callback) {\n"
        "    String action = command.length == 0 ? \"command\" : \"command:\" + command[0];\n"
        "    long requestId = allocateRequestId();\n"
        "    pendingRequests.put(\n"
        "        requestId, new PendingRequest(action, /* callback= */ null, callback));\n"
        "    try {\n"
        "      int result = longResultCommandQueue.enqueue(requestId, resultName, command);\n"
        "      if (result >= MPV_ERROR_SUCCESS) {\n"
        "        return true;\n"
        "      }\n"
        "      pendingRequests.remove(requestId);\n"
        "      fail(action, result);\n"
        "    } catch (RuntimeException e) {\n"
        "      pendingRequests.remove(requestId);\n"
        "      fail(action, e);\n"
        "    }\n"
        "    return false;\n"
        "  }\n",
        "MpvClient long-result command",
    )
    text = replace_once(
        text,
        "  public void onCommandReply(long requestId, int error) {\n"
        "    PendingRequest request = pendingRequests.remove(requestId);\n"
        "    if (request == null) {\n"
        "      return;\n"
        "    }\n"
        "    boolean success = error >= MPV_ERROR_SUCCESS;\n"
        "    if (!success) {\n"
        "      fail(request.action, error);\n"
        "    } else {\n"
        "      lastResult.recordResult(error);\n"
        "    }\n"
        "    if (request.callback != null) {\n"
        "      request.callback.onResult(success);\n"
        "    }\n"
        "  }\n",
        "  public void onCommandReply(long requestId, int error) {\n"
        "    onCommandReply(requestId, error, 0L);\n"
        "  }\n\n"
        "  public void onCommandReply(long requestId, int error, long result) {\n"
        "    PendingRequest request = pendingRequests.remove(requestId);\n"
        "    if (request == null) {\n"
        "      return;\n"
        "    }\n"
        "    boolean success = error >= MPV_ERROR_SUCCESS;\n"
        "    if (!success) {\n"
        "      result = 0L;\n"
        "      fail(request.action, error);\n"
        "    } else {\n"
        "      lastResult.recordResult(error);\n"
        "    }\n"
        "    if (request.callback != null) {\n"
        "      request.callback.onResult(success);\n"
        "    }\n"
        "    if (request.longResultCallback != null) {\n"
        "      request.longResultCallback.onResult(result, success);\n"
        "    }\n"
        "  }\n",
        "MpvClient command reply result",
    )
    text = replace_once(
        text,
        "    pendingRequests.put(requestId, new PendingRequest(action, callback));\n",
        "    pendingRequests.put(\n"
        "        requestId, new PendingRequest(action, callback, /* longResultCallback= */ null));\n",
        "MpvClient pending ordinary request",
    )
    text = replace_once(
        text,
        "  interface NativeCommandQueue {\n\n"
        "    int enqueue(long requestId, String[] command);\n"
        "  }\n\n"
        "  public interface ResultCallback {\n\n"
        "    void onResult(boolean success);\n"
        "  }\n",
        "  interface NativeCommandQueue {\n\n"
        "    int enqueue(long requestId, String[] command);\n"
        "  }\n\n"
        "  interface NativeLongResultCommandQueue {\n\n"
        "    int enqueue(long requestId, String resultName, String[] command);\n"
        "  }\n\n"
        "  public interface ResultCallback {\n\n"
        "    void onResult(boolean success);\n"
        "  }\n\n"
        "  public interface LongResultCallback {\n\n"
        "    void onResult(long result, boolean success);\n"
        "  }\n",
        "MpvClient callback interfaces",
    )
    text = replace_once(
        text,
        "  private static final class PendingRequest {\n\n"
        "    private final String action;\n"
        "    private final @Nullable ResultCallback callback;\n\n"
        "    private PendingRequest(String action, @Nullable ResultCallback callback) {\n"
        "      this.action = action;\n"
        "      this.callback = callback;\n"
        "    }\n"
        "  }\n",
        "  private static final class PendingRequest {\n\n"
        "    private final String action;\n"
        "    private final @Nullable ResultCallback callback;\n"
        "    private final @Nullable LongResultCallback longResultCallback;\n\n"
        "    private PendingRequest(\n"
        "        String action,\n"
        "        @Nullable ResultCallback callback,\n"
        "        @Nullable LongResultCallback longResultCallback) {\n"
        "      this.action = action;\n"
        "      this.callback = callback;\n"
        "      this.longResultCallback = longResultCallback;\n"
        "    }\n"
        "  }\n",
        "MpvClient pending request callbacks",
    )
    path.write_text(text, encoding="utf-8")


def patch_mpv_client_test(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import java.util.concurrent.atomic.AtomicBoolean;\n",
        "import java.util.concurrent.atomic.AtomicBoolean;\n"
        "import java.util.concurrent.atomic.AtomicLong;\n",
        "MpvClientTest AtomicLong import",
    )
    anchor = "  private static final class FakeNativeCommandQueue implements MpvClient.NativeCommandQueue {\n"
    tests = """  @Test
  public void longResultCommand_successReturnsNativeResult() {
    FakeNativeCommandQueue commandQueue = new FakeNativeCommandQueue();
    FakeNativeLongResultCommandQueue longQueue = new FakeNativeLongResultCommandQueue();
    MpvClient client = new MpvClient(commandQueue, longQueue);
    AtomicBoolean success = new AtomicBoolean();
    AtomicLong result = new AtomicLong();
    String[] command = {"load-script", "/tmp/test.lua"};

    assertThat(
            client.commandLongResult(
                command,
                "client_id",
                (value, ok) -> {
                  result.set(value);
                  success.set(ok);
                }))
        .isTrue();

    client.onCommandReply(longQueue.requestId, MPVLib.MpvError.MPV_ERROR_SUCCESS, 42L);

    assertThat(longQueue.resultName).isEqualTo("client_id");
    assertThat(longQueue.command).isSameInstanceAs(command);
    assertThat(success.get()).isTrue();
    assertThat(result.get()).isEqualTo(42L);
  }

  @Test
  public void longResultCommand_failureReturnsZeroResult() {
    FakeNativeCommandQueue commandQueue = new FakeNativeCommandQueue();
    FakeNativeLongResultCommandQueue longQueue = new FakeNativeLongResultCommandQueue();
    MpvClient client = new MpvClient(commandQueue, longQueue);
    AtomicBoolean success = new AtomicBoolean(true);
    AtomicLong result = new AtomicLong(-1L);

    assertThat(
            client.commandLongResult(
                new String[] {"load-script", "/tmp/test.lua"},
                "client_id",
                (value, ok) -> {
                  result.set(value);
                  success.set(ok);
                }))
        .isTrue();

    client.onCommandReply(longQueue.requestId, MPVLib.MpvError.MPV_ERROR_COMMAND, 99L);

    assertThat(success.get()).isFalse();
    assertThat(result.get()).isEqualTo(0L);
  }

  private static final class FakeNativeLongResultCommandQueue
      implements MpvClient.NativeLongResultCommandQueue {

    private long requestId;
    private String resultName;
    private String[] command;
    private int result;

    @Override
    public int enqueue(long requestId, String resultName, String[] command) {
      this.requestId = requestId;
      this.resultName = resultName;
      this.command = command;
      return result;
    }
  }

"""
    text = replace_once(text, anchor, tests + anchor, "MpvClient long-result tests")
    path.write_text(text, encoding="utf-8")


def patch_mpv_event_adapter(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  @Override\n"
        "  public void eventCommandReply(long requestId, int error) {\n"
        "    playerEventHost.runOnPlayerLooper(\n"
        "        () -> commandReplyListener.onReply(requestId, error));\n"
        "  }\n",
        "  @Override\n"
        "  public void eventCommandReply(long requestId, int error) {\n"
        "    eventCommandReply(requestId, error, 0L);\n"
        "  }\n\n"
        "  @Override\n"
        "  public void eventCommandReply(long requestId, int error, long result) {\n"
        "    playerEventHost.runOnPlayerLooper(\n"
        "        () -> commandReplyListener.onReply(requestId, error, result));\n"
        "  }\n",
        "MpvEventAdapter long reply",
    )
    text = replace_once(
        text,
        "  public interface CommandReplyListener {\n\n"
        "    void onReply(long requestId, int error);\n"
        "  }\n",
        "  public interface CommandReplyListener {\n\n"
        "    void onReply(long requestId, int error, long result);\n"
        "  }\n",
        "MpvEventAdapter reply listener",
    )
    path.write_text(text, encoding="utf-8")


def patch_mpv_event_adapter_test(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    adapter.eventCommandReply(7, -12);\n\n"
        "    verify(listener, never()).onReply(7, -12);\n"
        "    assertThat(posted.get()).isNotNull();\n\n"
        "    posted.get().run();\n\n"
        "    verify(listener).onReply(7, -12);\n",
        "    adapter.eventCommandReply(7, -12, 42L);\n\n"
        "    verify(listener, never()).onReply(7, -12, 42L);\n"
        "    assertThat(posted.get()).isNotNull();\n\n"
        "    posted.get().run();\n\n"
        "    verify(listener).onReply(7, -12, 42L);\n",
        "MpvEventAdapterTest long reply",
    )
    text = replace_once(
        text,
        "        (requestId, error) -> {},\n",
        "        (requestId, error, result) -> {},\n",
        "MpvEventAdapterTest reply lambda",
    )
    path.write_text(text, encoding="utf-8")


def patch_mpv_command_dispatcher(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  public boolean stop() {\n"
        "    return client.command(new String[] {CMD_STOP});\n"
        "  }\n",
        "  public boolean loadScript(String path, MpvClient.LongResultCallback callback) {\n"
        "    return client.commandLongResult(\n"
        "        new String[] {\"load-script\", path}, \"client_id\", callback);\n"
        "  }\n\n"
        "  public boolean unloadScript(long clientId) {\n"
        "    return client.command(new String[] {\"unload-script\", Long.toString(clientId)});\n"
        "  }\n\n"
        "  public boolean stop() {\n"
        "    return client.command(new String[] {CMD_STOP});\n"
        "  }\n",
        "MpvCommandDispatcher script lifecycle",
    )
    path.write_text(text, encoding="utf-8")


def patch_mpv_command_dispatcher_test(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import static org.mockito.AdditionalMatchers.aryEq;\n"
        "import static org.mockito.Mockito.mock;\n",
        "import static org.mockito.AdditionalMatchers.aryEq;\n"
        "import static org.mockito.Mockito.eq;\n"
        "import static org.mockito.Mockito.mock;\n"
        "import static org.mockito.Mockito.same;\n",
        "MpvCommandDispatcherTest matcher imports",
    )
    anchor = """  @Test
  public void loadFile_queuesCommand() {
"""
    tests = """  @Test
  public void loadScript_queuesLongResultCommand() {
    MpvClient client = mock(MpvClient.class);
    MpvCommandDispatcher dispatcher = new MpvCommandDispatcher(client);
    MpvClient.LongResultCallback callback = mock(MpvClient.LongResultCallback.class);
    String[] command = {"load-script", "/tmp/test.lua"};
    when(client.commandLongResult(aryEq(command), eq("client_id"), same(callback))).thenReturn(true);

    boolean queued = dispatcher.loadScript("/tmp/test.lua", callback);

    assertThat(queued).isTrue();
    verify(client).commandLongResult(aryEq(command), eq("client_id"), same(callback));
    verifyNoMoreInteractions(client);
  }

  @Test
  public void unloadScript_queuesCommand() {
    MpvClient client = mock(MpvClient.class);
    MpvCommandDispatcher dispatcher = new MpvCommandDispatcher(client);
    String[] command = {"unload-script", "42"};
    when(client.command(aryEq(command))).thenReturn(true);

    boolean queued = dispatcher.unloadScript(42L);

    assertThat(queued).isTrue();
    verify(client).command(aryEq(command));
    verifyNoMoreInteractions(client);
  }

"""
    text = replace_once(text, anchor, tests + anchor, "MpvCommandDispatcher script tests")
    path.write_text(text, encoding="utf-8")


def patch_subtitle_defaults(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '  private static final String PROP_SUB_SCALE = "sub-scale";\n',
        '  private static final String PROP_SUB_SCALE = "sub-scale";\n'
        '  private static final String PROP_SECONDARY_SUB_SCALE = "secondary-sub-scale";\n',
        "secondary subtitle scale constant",
    )
    text = replace_once(
        text,
        "    if (options.isScaleSet()) {\n"
        "      addSubtitleDouble(builder, PROP_SUB_SCALE, options.getScale());\n"
        "      addSubtitleString(builder, PROP_SUB_SCALE_SIGNS, VALUE_YES);\n"
        "    }\n",
        "    if (options.isScaleSet()) {\n"
        "      addSubtitleDouble(builder, PROP_SUB_SCALE, options.getScale());\n"
        "      addSubtitleDouble(builder, PROP_SECONDARY_SUB_SCALE, options.getScale());\n"
        "      addSubtitleString(builder, PROP_SUB_SCALE_SIGNS, VALUE_YES);\n"
        "    }\n",
        "secondary subtitle scale application",
    )
    path.write_text(text, encoding="utf-8")


def patch_subtitle_test(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '        .containsExactly("sub-scale-signs=yes", "sub-pos=80.0", "sub-scale=1.25");\n',
        '        .containsExactly(\n'
        '            "sub-scale-signs=yes",\n'
        '            "sub-pos=80.0",\n'
        '            "sub-scale=1.25",\n'
        '            "secondary-sub-scale=1.25");\n',
        "subtitle scale test",
    )
    path.write_text(text, encoding="utf-8")



def patch_build_gradle(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '  implementation(project(":lib-exoplayer"))\n',
        '  implementation(project(":lib-exoplayer"))\n'
        '  implementation(project(":lib-datasource"))\n',
        "MPV datasource dependency",
    )
    path.write_text(text, encoding="utf-8")


def patch_player_config(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import androidx.media3.common.DolbyVisionOutputPolicy;\n",
        "import androidx.media3.common.DolbyVisionOutputPolicy;\n"
        "import androidx.media3.datasource.DataSource;\n",
        "MpvPlayerConfig datasource import",
    )
    text = replace_once(
        text,
        "  private final boolean videoSharpnessSupported;\n",
        "  private final boolean videoSharpnessSupported;\n"
        "  @Nullable private final DataSource.Factory dataSourceFactory;\n",
        "MpvPlayerConfig datasource field",
    )
    text = replace_once(
        text,
        "    this.videoSharpnessSupported = builder.videoSharpnessSupported;\n",
        "    this.videoSharpnessSupported = builder.videoSharpnessSupported;\n"
        "    this.dataSourceFactory = builder.dataSourceFactory;\n",
        "MpvPlayerConfig datasource assignment",
    )
    text = replace_once(
        text,
        "  @Nullable\n"
        "  @RestrictTo(LIBRARY_GROUP)\n"
        "  public String getRequestedPassthroughCodecs() {\n"
        "    return requestedPassthroughCodecs;\n"
        "  }\n",
        "  @Nullable\n"
        "  @RestrictTo(LIBRARY_GROUP)\n"
        "  public String getRequestedPassthroughCodecs() {\n"
        "    return requestedPassthroughCodecs;\n"
        "  }\n\n"
        "  @Nullable\n"
        "  @RestrictTo(LIBRARY_GROUP)\n"
        "  public DataSource.Factory getDataSourceFactory() {\n"
        "    return dataSourceFactory;\n"
        "  }\n",
        "MpvPlayerConfig datasource getter",
    )
    text = replace_once(
        text,
        "    private boolean videoSharpnessSupported = true;\n"
        "    private boolean buildCalled;\n",
        "    private boolean videoSharpnessSupported = true;\n"
        "    @Nullable private DataSource.Factory dataSourceFactory;\n"
        "    private boolean buildCalled;\n",
        "MpvPlayerConfig builder datasource field",
    )
    text = replace_once(
        text,
        "    @CanIgnoreReturnValue\n"
        "    @RestrictTo(LIBRARY_GROUP)\n"
        "    public Builder setVideoSharpnessSupported(boolean videoSharpnessSupported) {\n"
        "      checkState(!buildCalled);\n"
        "      this.videoSharpnessSupported = videoSharpnessSupported;\n"
        "      return this;\n"
        "    }\n",
        "    @CanIgnoreReturnValue\n"
        "    @RestrictTo(LIBRARY_GROUP)\n"
        "    public Builder setVideoSharpnessSupported(boolean videoSharpnessSupported) {\n"
        "      checkState(!buildCalled);\n"
        "      this.videoSharpnessSupported = videoSharpnessSupported;\n"
        "      return this;\n"
        "    }\n\n"
        "    @CanIgnoreReturnValue\n"
        "    @RestrictTo(LIBRARY_GROUP)\n"
        "    public Builder setDataSourceFactory(@Nullable DataSource.Factory dataSourceFactory) {\n"
        "      checkState(!buildCalled);\n"
        "      this.dataSourceFactory = dataSourceFactory;\n"
        "      return this;\n"
        "    }\n",
        "MpvPlayerConfig datasource setter",
    )
    path.write_text(text, encoding="utf-8")


def patch_request_headers(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    String mpvHeaderFields() {\n",
        "    Map<String, String> dataSourceHeaders() {\n"
        "      Map<String, String> headers = new LinkedHashMap<>(headerFields);\n"
        "      if (userAgent != null) {\n"
        "        headers.put(HttpHeaders.USER_AGENT, userAgent);\n"
        "      }\n"
        "      if (referrer != null) {\n"
        "        headers.put(HttpHeaders.REFERER, referrer);\n"
        "      }\n"
        "      return headers;\n"
        "    }\n\n"
        "    String mpvHeaderFields() {\n",
        "MpvRequestHeaders datasource headers",
    )
    path.write_text(text, encoding="utf-8")


def write_iso_stream_files(root: Path) -> None:
    media_dir = (
        root
        / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/media"
    )
    tests_dir = (
        root
        / "libraries/mpvplayer/src/test/java/androidx/media3/mpvplayer/media"
    )
    tests_dir.mkdir(parents=True, exist_ok=True)

    (media_dir / "MpvIsoStream.java").write_text(
        r'''/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.mpvplayer.media;

import android.net.Uri;
import androidx.annotation.Nullable;
import androidx.media3.common.C;
import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DataSpec;
import is.xyz.mpv.MPVLib;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Map;

/** Random-access Media3 DataSource bridge used by the MPV media3iso protocol. */
final class MpvIsoStream implements MPVLib.Stream {

  private static final int READ_BUFFER_SIZE = 64 * 1024;

  private final DataSource.Factory dataSourceFactory;
  private final Uri uri;
  private final Map<String, String> requestHeaders;
  private final byte[] scratch;

  @Nullable private DataSource dataSource;
  private long resolvedLength;
  private volatile boolean canceled;

  MpvIsoStream(
      DataSource.Factory dataSourceFactory, Uri uri, Map<String, String> requestHeaders) {
    this.dataSourceFactory = dataSourceFactory;
    this.uri = uri;
    this.requestHeaders = requestHeaders;
    this.scratch = new byte[READ_BUFFER_SIZE];
    this.resolvedLength = C.LENGTH_UNSET;
    openAt(/* position= */ 0L);
  }

  @Override
  public synchronized int read(ByteBuffer buffer) {
    ensureActive();
    if (!buffer.hasRemaining()) {
      return 0;
    }
    int length = Math.min(scratch.length, buffer.remaining());
    try {
      int read = requireDataSource().read(scratch, 0, length);
      if (read == C.RESULT_END_OF_INPUT) {
        return 0;
      }
      buffer.put(scratch, 0, read);
      return read;
    } catch (IOException e) {
      throw new IllegalStateException("ISO stream read failed", e);
    }
  }

  @Override
  public synchronized long seek(long position) {
    ensureActive();
    if (position < 0) {
      return 0L;
    }
    openAt(position);
    return position;
  }

  @Override
  public synchronized long size() {
    ensureActive();
    return resolvedLength;
  }

  @Override
  public void cancel() {
    canceled = true;
    synchronized (this) {
      closeDataSource();
    }
  }

  @Override
  public void close() {
    cancel();
  }

  private void openAt(long position) {
    ensureActive();
    closeDataSource();
    DataSource next = dataSourceFactory.createDataSource();
    DataSpec spec =
        new DataSpec.Builder()
            .setUri(uri)
            .setHttpRequestHeaders(requestHeaders)
            .setPosition(position)
            .build();
    try {
      long remaining = next.open(spec);
      dataSource = next;
      if (remaining != C.LENGTH_UNSET) {
        long total = position + remaining;
        if (resolvedLength == C.LENGTH_UNSET || total > resolvedLength) {
          resolvedLength = total;
        }
      }
    } catch (IOException e) {
      try {
        next.close();
      } catch (IOException ignored) {
        // Preserve the open failure.
      }
      throw new IllegalStateException("ISO stream open failed", e);
    }
  }

  private void ensureActive() {
    if (canceled) {
      throw new IllegalStateException("ISO stream canceled");
    }
  }

  private DataSource requireDataSource() {
    DataSource current = dataSource;
    if (current == null) {
      throw new IllegalStateException("ISO stream is closed");
    }
    return current;
  }

  private void closeDataSource() {
    DataSource current = dataSource;
    dataSource = null;
    if (current != null) {
      try {
        current.close();
      } catch (IOException ignored) {
        // Closing is best-effort; the stream is no longer reusable after cancellation/reseek.
      }
    }
  }
}
''',
        encoding="utf-8",
    )

    (media_dir / "MpvIsoStreamManager.java").write_text(
        r'''/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.mpvplayer.media;

import static androidx.annotation.RestrictTo.Scope.LIBRARY_GROUP;

import android.net.Uri;
import androidx.annotation.Nullable;
import androidx.annotation.RestrictTo;
import androidx.media3.common.MediaItem;
import androidx.media3.datasource.DataSource;
import is.xyz.mpv.MPVLib;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

/** Owns the temporary MPV media3iso stream registration for the active MediaItem. */
public final class MpvIsoStreamManager {

  private static final String STREAM_SCHEME = "media3iso";

  private final DataSource.Factory dataSourceFactory;
  private final List<MpvIsoStream> activeStreams;

  @Nullable private String streamName;

  @RestrictTo(LIBRARY_GROUP)
  public MpvIsoStreamManager(DataSource.Factory dataSourceFactory) {
    this.dataSourceFactory = dataSourceFactory;
    this.activeStreams = new CopyOnWriteArrayList<>();
  }

  public Uri prepare(MediaItem item, Uri uri) {
    close();
    if (!isIso(item, uri)) {
      return uri;
    }

    Uri sourceUri = uri.getFragment() == null ? uri : uri.buildUpon().fragment(null).build();
    String scheme = sourceUri.getScheme();
    if (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme)) {
      return sourceUri;
    }

    String registered = STREAM_SCHEME + "://" + UUID.randomUUID() + "/disc.iso";
    streamName = registered;
    MPVLib.registerStream(
        registered,
        () -> {
          MpvIsoStream stream =
              new MpvIsoStream(
                  dataSourceFactory,
                  sourceUri,
                  MpvRequestHeaders.from(item).dataSourceHeaders());
          activeStreams.add(stream);
          return stream;
        });
    return Uri.parse(registered);
  }

  public void close() {
    String registered = streamName;
    streamName = null;
    if (registered != null) {
      MPVLib.unregisterStream(registered);
    }
    for (MpvIsoStream stream : activeStreams) {
      stream.cancel();
    }
    activeStreams.clear();
  }

  static boolean isIso(MediaItem item, Uri uri) {
    if (MpvMediaItems.isIsoMimeType(item)) {
      return true;
    }
    String path = uri.getPath();
    return path != null
        && path.length() >= 4
        && path.toLowerCase(Locale.US).endsWith(".iso");
  }
}
''',
        encoding="utf-8",
    )

    (tests_dir / "MpvIsoStreamTest.java").write_text(
        r'''/*
 * Copyright (C) 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */
package androidx.media3.mpvplayer.media;

import static com.google.common.truth.Truth.assertThat;

import android.net.Uri;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MimeTypes;
import androidx.media3.datasource.ByteArrayDataSource;
import androidx.media3.datasource.DataSource;
import is.xyz.mpv.MPVLib;
import java.nio.ByteBuffer;
import java.util.Collections;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;

@RunWith(RobolectricTestRunner.class)
public final class MpvIsoStreamTest {

  private static final byte[] DATA = new byte[] {10, 20, 30, 40, 50, 60};

  @Test
  public void stream_readsSeeksAndReportsSize() {
    DataSource.Factory factory = () -> new ByteArrayDataSource(DATA);
    MpvIsoStream stream =
        new MpvIsoStream(
            factory, Uri.parse("https://example.test/disc.iso"), Collections.emptyMap());

    assertThat(stream.size()).isEqualTo(DATA.length);

    ByteBuffer first = ByteBuffer.allocate(2);
    assertThat(stream.read(first)).isEqualTo(2);
    assertThat(first.array()).isEqualTo(new byte[] {10, 20});

    assertThat(stream.seek(3)).isEqualTo(3);
    ByteBuffer second = ByteBuffer.allocate(3);
    assertThat(stream.read(second)).isEqualTo(3);
    assertThat(second.array()).isEqualTo(new byte[] {40, 50, 60});
    assertThat(stream.read(ByteBuffer.allocate(1))).isEqualTo(0);

    stream.close();
  }

  @Test
  public void stream_cancelRejectsFurtherReads() {
    MpvIsoStream stream =
        new MpvIsoStream(
            () -> new ByteArrayDataSource(DATA),
            Uri.parse("https://example.test/disc.iso"),
            Collections.emptyMap());

    stream.cancel();

    boolean failed = false;
    try {
      stream.read(ByteBuffer.allocate(1));
    } catch (IllegalStateException expected) {
      failed = true;
    }
    assertThat(failed).isTrue();
  }

  @Test
  public void manager_httpIsoRegistersMedia3StreamAndUnregistersOnClose() {
    MpvIsoStreamManager manager =
        new MpvIsoStreamManager(() -> new ByteArrayDataSource(DATA));
    Uri source = Uri.parse("https://example.test/disc.ISO#title");
    MediaItem item =
        new MediaItem.Builder().setUri(source).setMimeType(MimeTypes.VIDEO_ISO).build();

    Uri rewritten = manager.prepare(item, source);

    assertThat(rewritten.getScheme()).isEqualTo("media3iso");
    MPVLib.Stream stream = MPVLib.openStream(rewritten.toString());
    assertThat(stream).isNotNull();
    assertThat(stream.size()).isEqualTo(DATA.length);

    manager.close();

    assertThat(MPVLib.openStream(rewritten.toString())).isNull();
  }

  @Test
  public void manager_localIsoOnlyStripsFragment() {
    MpvIsoStreamManager manager =
        new MpvIsoStreamManager(() -> new ByteArrayDataSource(DATA));
    Uri source = Uri.parse("file:///sdcard/disc.iso#title");
    MediaItem item = new MediaItem.Builder().setUri(source).build();

    Uri rewritten = manager.prepare(item, source);

    assertThat(rewritten.toString()).isEqualTo("file:///sdcard/disc.iso");
    manager.close();
  }

  @Test
  public void manager_nonIsoHttpIsUnchanged() {
    MpvIsoStreamManager manager =
        new MpvIsoStreamManager(() -> new ByteArrayDataSource(DATA));
    Uri source = Uri.parse("https://example.test/video.mkv#chapter");
    MediaItem item = new MediaItem.Builder().setUri(source).build();

    assertThat(manager.prepare(item, source)).isEqualTo(source);

    manager.close();
  }
}
''',
        encoding="utf-8",
    )


def patch_player_components(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import android.os.Handler;\n",
        "import android.os.Handler;\n"
        "import androidx.media3.datasource.DataSource;\n"
        "import androidx.media3.datasource.DefaultDataSource;\n",
        "MpvPlayerComponents datasource imports",
    )
    text = replace_once(
        text,
        "import androidx.media3.mpvplayer.media.MpvMediaLoader;\n",
        "import androidx.media3.mpvplayer.media.MpvIsoStreamManager;\n"
        "import androidx.media3.mpvplayer.media.MpvMediaLoader;\n",
        "MpvPlayerComponents ISO manager import",
    )
    text = replace_once(
        text,
        "    this.mediaLoader =\n"
        "        new MpvMediaLoader(\n",
        "    DataSource.Factory isoDataSourceFactory = config.getDataSourceFactory();\n"
        "    if (isoDataSourceFactory == null) {\n"
        "      isoDataSourceFactory = new DefaultDataSource.Factory(applicationContext);\n"
        "    }\n"
        "    this.mediaLoader =\n"
        "        new MpvMediaLoader(\n",
        "MpvPlayerComponents ISO datasource factory",
    )
    text = replace_once(
        text,
        "            loadGeneration,\n"
        "            perFileOptionsComposer,\n"
        "            MpvPlayerHosts.mediaLoaderHost(player, playerInfo));\n",
        "            loadGeneration,\n"
        "            perFileOptionsComposer,\n"
        "            new MpvIsoStreamManager(isoDataSourceFactory),\n"
        "            MpvPlayerHosts.mediaLoaderHost(player, playerInfo));\n",
        "MpvPlayerComponents ISO manager wiring",
    )
    path.write_text(text, encoding="utf-8")


def patch_media_loader(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  private final MpvLoadOptionsFactory loadOptionsFactory;\n"
        "  private final Host host;\n",
        "  private final MpvLoadOptionsFactory loadOptionsFactory;\n"
        "  private final MpvIsoStreamManager isoStreamManager;\n"
        "  private final Host host;\n",
        "MpvMediaLoader ISO field",
    )
    text = replace_once(
        text,
        "      MpvLoadGeneration loadGeneration,\n"
        "      PerFileOptionsProvider perFileOptionsProvider,\n"
        "      Host host) {\n",
        "      MpvLoadGeneration loadGeneration,\n"
        "      PerFileOptionsProvider perFileOptionsProvider,\n"
        "      MpvIsoStreamManager isoStreamManager,\n"
        "      Host host) {\n",
        "MpvMediaLoader constructor signature",
    )
    text = replace_once(
        text,
        "    this.loadOptionsFactory = new MpvLoadOptionsFactory(perFileOptionsProvider);\n"
        "    this.host = host;\n",
        "    this.loadOptionsFactory = new MpvLoadOptionsFactory(perFileOptionsProvider);\n"
        "    this.isoStreamManager = isoStreamManager;\n"
        "    this.host = host;\n",
        "MpvMediaLoader ISO assignment",
    )
    text = replace_once(
        text,
        "    MpvLoadOptions loadOptions = loadOptionsFactory.create(item, uri, startPositionMs);\n"
        "    playbackState.startLoading(\n",
        "    MpvLoadOptions loadOptions = loadOptionsFactory.create(item, uri, startPositionMs);\n"
        "    Uri loadUri = isoStreamManager.prepare(item, uri);\n"
        "    playbackState.startLoading(\n",
        "MpvMediaLoader ISO prepare",
    )
    text = replace_once(
        text,
        "    if (!commandDispatcher.loadFile(uri, loadOptions.perFileOptions())) {\n"
        "      host.fail(errorFactory.createLoadFailure(uri));\n"
        "      return;\n"
        "    }\n",
        "    if (!commandDispatcher.loadFile(loadUri, loadOptions.perFileOptions())) {\n"
        "      isoStreamManager.close();\n"
        "      host.fail(errorFactory.createLoadFailure(uri));\n"
        "      return;\n"
        "    }\n",
        "MpvMediaLoader rewritten URI",
    )
    text = replace_once(
        text,
        "    host.invalidatePlayerState();\n"
        "  }\n\n"
        "  public interface Host {\n",
        "    host.invalidatePlayerState();\n"
        "  }\n\n"
        "  public void closeIsoStream() {\n"
        "    isoStreamManager.close();\n"
        "  }\n\n"
        "  public interface Host {\n",
        "MpvMediaLoader close ISO",
    )
    path.write_text(text, encoding="utf-8")


def patch_player(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "          releaseAudioFocus();\n"
        "          surfaceController.release();\n"
        "          nativeLifecycle.release();\n",
        "          releaseAudioFocus();\n"
        "          mediaLoader.closeIsoStream();\n"
        "          surfaceController.release();\n"
        "          nativeLifecycle.release();\n",
        "MpvPlayer release ISO cleanup",
    )
    text = replace_once(
        text,
        "    playbackState.stopActiveFile();\n"
        "    seekController.reset();\n",
        "    mediaLoader.closeIsoStream();\n"
        "    playbackState.stopActiveFile();\n"
        "    seekController.reset();\n",
        "MpvPlayer stop ISO cleanup",
    )
    path.write_text(text, encoding="utf-8")


def patch_proguard(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    anchor = """-keep class is.xyz.mpv.MPVLib {
  *;
}
"""
    addition = anchor + """
# libplayer 5.6.8 resolves this nested stream ABI and method names by JNI.
-keep interface is.xyz.mpv.MPVLib$Stream {
  *;
}
-keep interface is.xyz.mpv.MPVLib$StreamProvider {
  *;
}
"""
    text = replace_once(text, anchor, addition, "MPV stream proguard")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    root = args.source.resolve()
    try:
        patch_build_gradle(root / "libraries/mpvplayer/build.gradle.kts")
        patch_mpv_lib(root / "libraries/mpvplayer/src/main/java/is/xyz/mpv/MPVLib.java")
        patch_player_config(
            root / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/MpvPlayerConfig.java"
        )
        patch_request_headers(
            root / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/media/MpvRequestHeaders.java"
        )
        write_iso_stream_files(root)
        patch_player_components(
            root / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/MpvPlayerComponents.java"
        )
        patch_media_loader(
            root / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/media/MpvMediaLoader.java"
        )
        patch_player(
            root / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/MpvPlayer.java"
        )
        patch_mpv_client(
            root
            / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/nativebridge/MpvClient.java"
        )
        patch_mpv_event_adapter(
            root
            / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/nativebridge/MpvEventAdapter.java"
        )
        patch_mpv_event_adapter_test(
            root
            / "libraries/mpvplayer/src/test/java/androidx/media3/mpvplayer/nativebridge/MpvEventAdapterTest.java"
        )
        patch_mpv_client_test(
            root
            / "libraries/mpvplayer/src/test/java/androidx/media3/mpvplayer/nativebridge/MpvClientTest.java"
        )
        patch_mpv_command_dispatcher(
            root
            / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/nativebridge/MpvCommandDispatcher.java"
        )
        patch_mpv_command_dispatcher_test(
            root
            / "libraries/mpvplayer/src/test/java/androidx/media3/mpvplayer/nativebridge/MpvCommandDispatcherTest.java"
        )
        patch_subtitle_defaults(
            root
            / "libraries/mpvplayer/src/main/java/androidx/media3/mpvplayer/options/MpvSubtitleOptionDefaults.java"
        )
        patch_subtitle_test(
            root
            / "libraries/mpvplayer/src/test/java/androidx/media3/mpvplayer/options/MpvSubtitleOptionDefaultsTest.java"
        )
        patch_proguard(root / "libraries/mpvplayer/proguard-rules.txt")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"PASS: applied {OVERLAY_ID}")


if __name__ == "__main__":
    main()
