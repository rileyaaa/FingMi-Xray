#!/usr/bin/env python3
"""Isolated source-only MPV JNI bridge port; not an AAR or a build input.

Base: FongMi/media 3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d.
Contract: FongMi/mpv-android 1bf892e3271e73d8649f2d209027f1fb17515d15.
Run on Linux with Python 3.9+, JDK and cc. No network or Android binaries.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

BASE = "libraries/mpvplayer/src/main/java/is/xyz/mpv/MPVLib.java"
BASE_BLOB = "36da8033843061ffbcbf560ed77566ffdca4dd98"
MIT_BLOB = "81d2ff31ab3e434d6f67fa5ac1e15e345f175db6"


def pinned(path, sha):
    data = path.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if actual != sha:
        raise ValueError("source blob mismatch: " + str(path))
    return data.decode("utf-8")


def port(base, mit):
    def change(old, new):
        nonlocal base
        if base.count(old) != 1:
            raise ValueError("unexpected source anchor: " + old)
        base = base.replace(old, new, 1)

    change("package is.xyz.mpv;", "/* Stream and result callback port from FongMi/mpv-android (MIT).\n"
           + "\n".join(" * " + line for line in mit.rstrip().splitlines())
           + "\n */\npackage is.xyz.mpv;")
    change("import android.content.Context;", "import android.content.Context;\nimport android.graphics.Bitmap;")
    change("import java.util.concurrent.CopyOnWriteArrayList;", "import java.nio.ByteBuffer;\n"
           "import java.util.concurrent.ConcurrentHashMap;\nimport java.util.concurrent.CopyOnWriteArrayList;\n"
           "import java.util.function.Supplier;")
    change("  public static native void create(Context appctx);", """  public interface Stream {
    int read(ByteBuffer buffer);
    long seek(long position);
    long size();
    void cancel();
    void close();
  }

  private static final ConcurrentHashMap<String, Supplier<Stream>> STREAMS =
      new ConcurrentHashMap<>();

  public static void registerStream(String uri, Supplier<Stream> factory) {
    STREAMS.put(uri, factory);
  }

  public static void unregisterStream(String uri) {
    STREAMS.remove(uri);
  }

  @Nullable
  public static Stream openStream(String uri) {
    Supplier<Stream> factory = STREAMS.get(uri);
    return factory == null ? null : factory.get();
  }

  public static native void create(Context appctx);""")
    change("  /** Queues a command whose completion is delivered to {@link EventObserver#eventCommandReply}. */\n"
           "  public static native int enqueueCommand(long requestId, String[] cmd);", """  public static native int command(String[] cmd);

  /** Queues a command whose completion is delivered to {@link EventObserver#eventCommandReply}. */
  public static native int enqueueCommand(long requestId, String[] cmd);

  public static native int enqueueCommandLongResult(long requestId, String resultKey, String[] cmd);

  public static native @Nullable Bitmap grabThumbnail(int dimension);""")
    for name, typ in (("Int", "int"), ("Double", "double"), ("Boolean", "boolean"), ("String", "String")):
        ret = "Integer" if name == "Int" else name
        decl = f"  public static native {ret} getProperty{name}(String property);"
        change(decl, decl + f"\n\n  public static native int setProperty{name}(String property, {typ} value);")
    change("""  public static void eventCommandReply(long requestId, int error) {
    for (EventObserver observer : OBSERVERS) {
      observer.eventCommandReply(requestId, error);
    }
  }""", """  public static void eventCommandReply(long requestId, int error) {
    eventCommandReply(requestId, error, 0);
  }

  public static void eventCommandReply(long requestId, int error, long result) {
    for (EventObserver observer : OBSERVERS) {
      observer.eventCommandReply(requestId, error, result);
    }
  }""")
    change("    default void eventCommandReply(long requestId, int error) {}", """    default void eventCommandReply(long requestId, int error) {}

    default void eventCommandReply(long requestId, int error, long result) {
      eventCommandReply(requestId, error);
    }""")
    return base


# Test-only Android type shells and host JVM fixture, never copied to output.
STUBS = {
    "android/content/Context.java": "package android.content; public class Context {}",
    "android/view/Surface.java": "package android.view; public class Surface {}",
    "android/graphics/Bitmap.java": "package android.graphics; public class Bitmap {}",
    "androidx/annotation/Nullable.java": "package androidx.annotation; public @interface Nullable {}",
    "androidx/annotation/RestrictTo.java": "package androidx.annotation; public @interface RestrictTo { Scope[] value(); enum Scope { LIBRARY_GROUP } }",
}
JAVA = r'''
import is.xyz.mpv.MPVLib;
import java.lang.invoke.MethodType;
import java.lang.reflect.*;
import java.nio.ByteBuffer;
import java.util.*;

public class BridgeContract {
  static void check(boolean ok) { if (!ok) throw new AssertionError(); }
  static native void probe();
  static class Cursor implements MPVLib.Stream {
    int position; boolean cancelled, closed;
    public int read(ByteBuffer b) {
      check(!closed && !cancelled);
      int count = Math.min(b.remaining(), 4 - position);
      for (int i = 0; i < count; i++) b.put((byte) ++position);
      return count;
    }
    public long seek(long p) { check(p >= 0 && p <= 4); position = (int)p; return p; }
    public long size() { return 4; }
    public void cancel() { cancelled = true; }
    public void close() { closed = true; }
  }
  static class Observer implements MPVLib.EventObserver {
    int calls; long request; int error;
    public void eventProperty(String p) {}
    public void eventProperty(String p, long v) {}
    public void eventProperty(String p, boolean v) {}
    public void eventProperty(String p, String v) {}
    public void eventProperty(String p, double v) {}
    public void event(int id) {}
    public void eventEndFile(int r, int e, String s) {}
    public void eventCommandReply(long r, int e) { calls++; request = r; error = e; }
  }
  static class ResultObserver extends Observer {
    long result;
    public void eventCommandReply(long r, int e, long v) { super.eventCommandReply(r, e); result = v; }
  }
  public static void main(String[] args) {
    Set<String> expected = new HashSet<>(Arrays.asList(
      "create(Landroid/content/Context;)V", "init()V", "destroy()I",
      "attachSurface(Landroid/view/Surface;)V", "replaceSurface(Landroid/view/Surface;)V", "detachSurface()V",
      "attachOsdSurface(Landroid/view/Surface;)V", "replaceOsdSurface(Landroid/view/Surface;)V", "detachOsdSurface()V",
      "command([Ljava/lang/String;)I", "enqueueCommand(J[Ljava/lang/String;)I",
      "enqueueCommandLongResult(JLjava/lang/String;[Ljava/lang/String;)I",
      "setOptionString(Ljava/lang/String;Ljava/lang/String;)I", "grabThumbnail(I)Landroid/graphics/Bitmap;",
      "getPropertyInt(Ljava/lang/String;)Ljava/lang/Integer;", "setPropertyInt(Ljava/lang/String;I)I",
      "getPropertyDouble(Ljava/lang/String;)Ljava/lang/Double;", "setPropertyDouble(Ljava/lang/String;D)I",
      "getPropertyBoolean(Ljava/lang/String;)Ljava/lang/Boolean;", "setPropertyBoolean(Ljava/lang/String;Z)I",
      "getPropertyString(Ljava/lang/String;)Ljava/lang/String;", "setPropertyString(Ljava/lang/String;Ljava/lang/String;)I",
      "getPropertyByteArray(Ljava/lang/String;)[B", "observeProperty(Ljava/lang/String;I)I"));
    Set<String> actual = new HashSet<>();
    for (Method m : MPVLib.class.getDeclaredMethods()) if (Modifier.isNative(m.getModifiers())) {
      check(Modifier.isStatic(m.getModifiers()) && Modifier.isPublic(m.getModifiers()));
      actual.add(m.getName() + MethodType.methodType(m.getReturnType(), m.getParameterTypes()).toMethodDescriptorString());
    }
    if (!actual.equals(expected)) throw new AssertionError(actual.toString());
    System.out.println("PASS 24 native descriptors (declarations only)");
    Observer legacy = new Observer(); ResultObserver modern = new ResultObserver();
    MPVLib.addObserver(legacy); MPVLib.addObserver(legacy); MPVLib.addObserver(modern);
    Cursor first = new Cursor();
    MPVLib.registerStream("media3iso://contract", () -> first);
    MPVLib.registerStream("media3iso://independent", Cursor::new);
    check(MPVLib.openStream("media3iso://missing") == null);
    check(MPVLib.openStream("media3iso://independent") != MPVLib.openStream("media3iso://independent"));
    System.load(args[0]); probe();
    check(first.position == 4 && first.cancelled && first.closed);
    check(legacy.calls == 1 && legacy.request == 4294967297L && legacy.error == -7);
    check(modern.calls == 1 && modern.result == 8589934593L);
    MPVLib.eventCommandReply(9L, 0);
    check(legacy.calls == 2 && modern.calls == 2 && modern.result == 0);
    MPVLib.removeObserver(legacy); MPVLib.removeObserver(modern);
    MPVLib.eventCommandReply(1L, 0, 2L); check(legacy.calls == 2 && modern.calls == 2);
    MPVLib.unregisterStream("media3iso://contract"); MPVLib.unregisterStream("media3iso://independent");
    check(MPVLib.openStream("media3iso://contract") == null);
    System.out.println("PASS JNI callback lookup, direct buffer read/seek/size/cancel/close, legacy/result dispatch, registry");
  }
}
'''
C = r'''
#include <jni.h>
#include <assert.h>
#define NOEX() assert(!(*env)->ExceptionCheck(env))
#define STATIC(n,s) (*env)->GetStaticMethodID(env, bridge, n, s)
#define METHOD(n,s) (*env)->GetMethodID(env, stream, n, s)
JNIEXPORT void JNICALL Java_BridgeContract_probe(JNIEnv *env, jclass cls) {
  (void)cls;
  jclass bridge = (*env)->FindClass(env, "is/xyz/mpv/MPVLib"); NOEX(); assert(bridge);
  jclass stream = (*env)->FindClass(env, "is/xyz/mpv/MPVLib$Stream"); NOEX(); assert(stream);
  const char *names[] = {"eventProperty", "eventProperty", "eventProperty", "eventProperty", "eventProperty",
    "event", "eventCommandReply", "eventEndFile", "logMessage"};
  const char *sigs[] = {"(Ljava/lang/String;)V", "(Ljava/lang/String;Z)V", "(Ljava/lang/String;J)V",
    "(Ljava/lang/String;D)V", "(Ljava/lang/String;Ljava/lang/String;)V", "(I)V", "(JIJ)V",
    "(IILjava/lang/String;)V", "(Ljava/lang/String;ILjava/lang/String;)V"};
  for (int i = 0; i < 9; i++) { jmethodID m = STATIC(names[i], sigs[i]); NOEX(); assert(m); }
  jmethodID reply = STATIC("eventCommandReply", "(JIJ)V"); NOEX(); assert(reply);
  jmethodID open = STATIC("openStream", "(Ljava/lang/String;)Lis/xyz/mpv/MPVLib$Stream;"); NOEX(); assert(open);
  jmethodID read = METHOD("read", "(Ljava/nio/ByteBuffer;)I"); NOEX(); assert(read);
  jmethodID seek = METHOD("seek", "(J)J"); NOEX(); assert(seek);
  jmethodID size = METHOD("size", "()J"); NOEX(); assert(size);
  jmethodID cancel = METHOD("cancel", "()V"); NOEX(); assert(cancel);
  jmethodID close = METHOD("close", "()V"); NOEX(); assert(close);
  jstring uri = (*env)->NewStringUTF(env, "media3iso://contract"); NOEX(); assert(uri);
  jobject cursor = (*env)->CallStaticObjectMethod(env, bridge, open, uri); NOEX(); assert(cursor);
  unsigned char data[3] = {0};
  jobject buf = (*env)->NewDirectByteBuffer(env, data, 3); NOEX(); assert(buf);
  jint n = (*env)->CallIntMethod(env, cursor, read, buf); NOEX(); assert(n == 3 && data[0] == 1 && data[2] == 3);
  jlong len = (*env)->CallLongMethod(env, cursor, size); NOEX(); assert(len == 4);
  jlong pos = (*env)->CallLongMethod(env, cursor, seek, (jlong)1); NOEX(); assert(pos == 1);
  buf = (*env)->NewDirectByteBuffer(env, data, 3); NOEX(); assert(buf);
  n = (*env)->CallIntMethod(env, cursor, read, buf); NOEX(); assert(n == 3 && data[0] == 2 && data[2] == 4);
  buf = (*env)->NewDirectByteBuffer(env, data, 3); NOEX(); assert(buf);
  n = (*env)->CallIntMethod(env, cursor, read, buf); NOEX(); assert(n == 0);
  (*env)->CallVoidMethod(env, cursor, cancel); NOEX();
  (*env)->CallVoidMethod(env, cursor, close); NOEX();
  (*env)->CallStaticVoidMethod(env, bridge, reply, (jlong)4294967297LL, (jint)-7, (jlong)8589934593LL); NOEX();
}
'''


def verify(source):
    with tempfile.TemporaryDirectory(prefix="mpv-bridge-") as tmp:
        root = Path(tmp)
        files = dict(STUBS, **{"is/xyz/mpv/MPVLib.java": source, "BridgeContract.java": JAVA})
        for name, data in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(data, encoding="utf-8")
        javac = Path(shutil.which("javac")).resolve()
        jdk = javac.parents[1]
        subprocess.run([str(javac), "--release", "8", "-d", str(root / "classes"),
                        *(str(root / f) for f in files)], check=True)
        c = root / "probe.c"
        c.write_text(C, encoding="utf-8")
        library = root / "libprobe.so"
        subprocess.run(["cc", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                        "-I" + str(jdk / "include"), "-I" + str(jdk / "include/linux"),
                        str(c), "-o", str(library)], check=True)
        subprocess.run([str(jdk / "bin/java"), "-Xcheck:jni", "-cp", str(root / "classes"),
                        "BridgeContract", str(library)], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--media", type=Path, required=True)
    p.add_argument("--mpv", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    out = args.out.resolve()
    if out.exists() or any(out.is_relative_to(x.resolve()) for x in (args.media, args.mpv)):
        p.error("output must be a new file outside both inputs")
    source = port(pinned(args.media / BASE, BASE_BLOB), pinned(args.mpv / "LICENSE", MIT_BLOB))
    verify(source)
    with out.open("x", encoding="utf-8", newline="\n") as f:
        f.write(source)
    print("STAGED", out, "sha256=" + hashlib.sha256(source.encode()).hexdigest())


if __name__ == "__main__":
    main()
