#!/usr/bin/env python3
"""Port only the existing TV recovery clear-completion contract to TV 5.9.0."""
import hashlib

UPSTREAM_BLOB = "a4129fc79a16c2920907d184c8e264dd49435cb3"


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def adapt_base_loader(data):
    if git_blob(data) != UPSTREAM_BLOB:
        raise RuntimeError("BaseLoader upstream drift; review recovery port again")
    source = data.decode("utf-8")
    edits = (
        ("import com.fongmi.android.tv.api.config.LiveConfig;", "import com.fongmi.android.tv.App;\nimport com.fongmi.android.tv.api.config.LiveConfig;"),
        ("import com.github.catvod.utils.Task;", "import com.github.catvod.utils.Task;\nimport com.google.common.util.concurrent.MoreExecutors;"),
        ("import java.util.Objects;", "import java.util.Objects;\nimport java.util.concurrent.Executor;"),
        ("    private final List<SpiderLoader> retiredLoaders;", "    private final List<SpiderLoader> retiredLoaders;\n    private final Executor clearExecutor = MoreExecutors.newSequentialExecutor(Task.executor());"),
        ("""    public void clear() {
        clear(false);
    }

    public void destroy() {
        clear(true);
    }

    private void clear(boolean exiting) {""", """    public void clear() {
        clear(null);
    }

    /** Notify Home only after its retired loaders have been cleared. */
    public void clear(Runnable onComplete) {
        clear(false, onComplete);
    }

    public void destroy() {
        clear(true, null);
    }

    private void clear(boolean exiting, Runnable onComplete) {"""),
        ("""        }
        Task.execute(() -> clearLoaders(previous, retired));""", """            // Queue under the same lock as the upstream loader swap so another
            // owner cannot enqueue a newer clear ahead of this generation.
            // Keep the dedicated FIFO on Task's normal pool, not the DB lane.
            clearExecutor.execute(() -> {
                try {
                    clearLoaders(previous, retired);
                } finally {
                    if (onComplete != null) App.post(onComplete);
                }
            });
        }"""),
    )
    for before, after in edits:
        if source.count(before) != 1:
            raise RuntimeError("Unexpected BaseLoader port anchor")
        source = source.replace(before, after)
    return source.encode("utf-8")
