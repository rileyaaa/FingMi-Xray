package com.fingmi.tvrecovery;

import static org.junit.Assert.*;
import org.junit.Test;
import java.util.ArrayList;
import java.util.List;

public class NetworkRecoveryCoordinatorTest {
    private static final class Fake implements NetworkRecoveryCoordinator.Hooks {
        long generation;
        boolean ready;
        Runnable spiderDone;
        Runnable scheduled;
        int refreshes;
        final List<String> events = new ArrayList<>();
        @Override public long generation() { return generation; }
        @Override public boolean canRecoverHome() { return true; }
        @Override public void cancelRequests() { events.add("cancel"); }
        @Override public void resetApiAndDns() { events.add("api-dns"); }
        @Override public void clearSpiders(Runnable after) { events.add("spider"); spiderDone = after; }
        @Override public boolean networkReady() { return ready; }
        @Override public void schedule(Runnable action, long delay) { scheduled = action; }
        @Override public void unschedule(Runnable action) { if (scheduled == action) scheduled = null; }
        @Override public void showProgress() { events.add("progress"); }
        @Override public void refreshHome() { refreshes++; }
        void completeSpider() { Runnable done = spiderDone; spiderDone = null; done.run(); }
        void tick() { Runnable action = scheduled; scheduled = null; action.run(); }
    }

    @Test public void resumeRebuildsInOrderOnce() {
        Fake fake = new Fake();
        NetworkRecoveryCoordinator recovery = new NetworkRecoveryCoordinator(0, fake);
        recovery.check();
        assertTrue(fake.events.isEmpty());
        fake.generation = 1;
        recovery.check();
        assertEquals(List.of("progress", "cancel", "api-dns", "spider"), fake.events);
        recovery.check();
        assertEquals(4, fake.events.size());
        fake.completeSpider();
        fake.ready = true;
        fake.tick();
        assertEquals(0, fake.refreshes);
        fake.tick();
        assertEquals(1, fake.refreshes);
        recovery.check();
        assertEquals(1, fake.refreshes);
    }

    @Test public void staleCleanupCannotRefreshNewGeneration() {
        Fake fake = new Fake();
        NetworkRecoveryCoordinator recovery = new NetworkRecoveryCoordinator(0, fake);
        fake.generation = 1;
        recovery.check();
        Runnable stale = fake.spiderDone;
        fake.generation = 2;
        recovery.check();
        assertEquals(4, fake.events.size());
        stale.run();
        assertNotNull(fake.scheduled);
        assertEquals(4, fake.events.size());
        fake.tick();
        assertEquals(8, fake.events.size());
        fake.completeSpider();
        fake.ready = true;
        fake.tick();
        fake.tick();
        assertEquals(2, recovery.appliedGeneration());
        assertEquals(1, fake.refreshes);
        recovery.close();
        fake.generation = 3;
        recovery.check();
        assertEquals(1, fake.refreshes);
    }
}
