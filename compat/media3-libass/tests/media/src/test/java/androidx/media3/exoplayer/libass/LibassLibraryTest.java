package androidx.media3.exoplayer.libass;

import static org.junit.Assert.*;
import androidx.media3.common.MediaLibraryInfo;
import org.junit.Test;
import org.junit.Before;
import java.lang.reflect.InvocationTargetException;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=28, manifest=Config.NONE)
public final class LibassLibraryTest {
    private Class<?> library;
    @Before public void isolateStaticLoader() throws Exception {
        ClassLoader loader = new ClassLoader(getClass().getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                if (!name.startsWith(LibassLibrary.class.getName())) return super.loadClass(name, resolve);
                Class<?> found = findLoadedClass(name);
                if (found == null) {
                    try (java.io.InputStream in=getParent().getResourceAsStream(name.replace('.', '/')+".class")) {
                        byte[] bytes=in.readAllBytes();found=defineClass(name,bytes,0,bytes.length);
                    } catch (java.io.IOException e) { throw new ClassNotFoundException(name,e); }
                }
                if (resolve) resolveClass(found);
                return found;
            }
        };
        library = loader.loadClass(LibassLibrary.class.getName());
    }
    private Object call(String name, Class<?>[] types, Object... args) {
        try { java.lang.reflect.Method m=library.getDeclaredMethod(name, types);m.setAccessible(true);return m.invoke(null,args); }
        catch (InvocationTargetException e) { if(e.getCause() instanceof RuntimeException)throw (RuntimeException)e.getCause();if(e.getCause() instanceof Error)throw (Error)e.getCause();throw new AssertionError(e.getCause()); }
        catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private boolean query(String name) { return (Boolean)call(name,new Class<?>[0]); }
    private void enabled(boolean value) { call("setEnabled",new Class<?>[]{boolean.class},value); }
    private void libraries(String... values) { call("setLibraries",new Class<?>[]{String[].class},(Object)values); }
    @Test public void disabledDoesNotAttemptLoad() {
        enabled(false);
        assertFalse(query("isAvailable"));
        // LibraryLoader rejects setLibraries after its first load attempt.
        libraries("missing-libass-disabled-probe");
        assertFalse(query("isEnabled"));
    }
    @Test public void missingLibraryFailsClosedAndCachesFailure() {
        libraries("missing-libass-enabled-probe");
        assertFalse(query("isAvailable"));
        assertFalse(query("isAvailable"));
        assertThrows(IllegalStateException.class, () -> libraries("late"));
    }
    @Test public void nativeAvailabilityIsIndependentOfGlobalEnablement() {
        // Empty library list exercises the real loader's success branch; no fake SO.
        libraries();
        assertTrue(query("isAvailable"));
        enabled(false);
        assertFalse(query("isAvailable"));
        assertTrue(query("isNativeAvailable"));
        enabled(true);
        assertTrue(query("isAvailable"));
    }
    @Test public void moduleRegistrationMatchesPublishedName() {
        query("isEnabled");
        assertTrue(MediaLibraryInfo.registeredModules().contains("media3.exoplayer.libass"));
    }
}
