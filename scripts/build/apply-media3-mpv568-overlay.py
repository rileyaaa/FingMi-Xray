#!/usr/bin/env python3
"""Apply the reproducible FongMi 5.6.8 MPV bridge overlay to pinned FongMi/media."""

from __future__ import annotations

import argparse
from pathlib import Path

OVERLAY_ID = "fongmi-tv-5.6.8-mpv-bridge-v1"


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
        patch_mpv_lib(root / "libraries/mpvplayer/src/main/java/is/xyz/mpv/MPVLib.java")
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
