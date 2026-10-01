package android.os;
import java.util.*;
/** Test-only virtual main queue. No wall clock or sleeping. */
public final class Handler {
    private record Task(long time, long sequence, Runnable callback) {}
    private static final PriorityQueue<Task> tasks = new PriorityQueue<>(Comparator.comparingLong(Task::time).thenComparingLong(Task::sequence));
    private static long now, sequence;
    public Handler(Looper looper) {}
    public boolean postDelayed(Runnable callback, long delay) { tasks.add(new Task(now + delay, ++sequence, callback)); return true; }
    public void removeCallbacks(Runnable callback) { tasks.removeIf(task -> task.callback == callback); }
    public static void reset() { tasks.clear(); now = sequence = 0; }
    public static void advance(long amount) {
        long target = now + amount;
        while (!tasks.isEmpty() && tasks.peek().time <= target) {
            Task task = tasks.remove(); now = task.time; task.callback.run();
        }
        now = target;
    }
}
