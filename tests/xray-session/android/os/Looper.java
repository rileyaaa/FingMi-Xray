package android.os;
/** Test-only application-thread identity. */
public final class Looper {
    private static final Looper MAIN = new Looper();
    public static Looper myLooper() { return MAIN; }
    public static Looper getMainLooper() { return MAIN; }
}
