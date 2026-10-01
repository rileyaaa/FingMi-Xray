package android.content;
/** Test-only context: preferences and Binder are separate test doubles. */
public class Context {
    public Context getApplicationContext() { return this; }
}
