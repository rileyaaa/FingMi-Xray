package androidx.media3.exoplayer.libass;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;

/**
 * Reconstructed ownership portion of5.6.5 sk1 and the inlined vr0.e component factory.
 * K is MediaItem in the eventual session; kept generic to exercise the state machine on a host JVM.
 * No player listeners, renderers or networking belong here.
 */
final class LibassMediaOwnership<K,V extends LibassMediaOwnership.Resource> implements AutoCloseable {
    interface Resource { void close(); }
    private final Function<K,V> create;
    private final Map<K,V> media = new LinkedHashMap<>();
    private final Set<K> timeline = new HashSet<>();
    private final Set<K> preparing = new HashSet<>();
    private Object player;
    private K current, previous, preload;
    private boolean closed;

    LibassMediaOwnership(Function<K,V> create) { this.create=Objects.requireNonNull(create); }

    synchronized V createComponents(K key) {
        ensureOpen(); Objects.requireNonNull(key);
        V value=getOrCreate(key);
        if(!Objects.equals(key,current)&&!Objects.equals(key,preload)&&!timeline.contains(key)) {
            preparing.add(key);
            collect();
        }
        return value;
    }

    synchronized void bindPlayer(Object next) {
        if(closed||player==next)return;
        player=next;timeline.clear();
        if(next==null)preparing.clear();
        current=null;previous=null;
        collect();
    }

    synchronized void updateCurrent(Object sender,K next) {
        if(closed||player==null||sender!=player)return;
        if(next==null) { current=null;previous=null; }
        else {
            getOrCreate(next);
            if(!Objects.equals(current,next))previous=current;
            current=next;preparing.remove(next);
        }
        collect();
    }

    synchronized void updateTimeline(Object sender,Collection<K> items) {
        if(closed||player==null||sender!=player)return;
        timeline.clear();timeline.addAll(items);
        if(!timeline.isEmpty())preparing.clear();
        collect();
    }

    synchronized void setPreload(K next) {
        if(closed)return;
        if(next!=null)getOrCreate(next);
        preload=next;
        if(next!=null)preparing.remove(next);
        collect();
    }

    synchronized V active() { return closed?null:media.get(current); }

    synchronized void forEach(java.util.function.Consumer<V> action) {
        if(closed)return;
        for(V value:new ArrayList<>(media.values()))action.accept(value);
    }

    private V getOrCreate(K key) {
        V value=media.get(key);
        if(value==null) {
            value=Objects.requireNonNull(create.apply(key));
            if(closed) { value.close();ensureOpen(); }
            media.put(key,value);
        }
        return value;
    }
    private void ensureOpen() {
        if(closed)throw new IllegalStateException("Libass playback session is closed");
    }
    private void collect() {
        ArrayList<V> obsolete=new ArrayList<>();
        Iterator<Map.Entry<K,V>> iterator=media.entrySet().iterator();
        while(iterator.hasNext()) {
            Map.Entry<K,V> entry=iterator.next();K key=entry.getKey();
            if(!Objects.equals(key,current)&&!Objects.equals(key,previous)&&!Objects.equals(key,preload)
                    &&!timeline.contains(key)&&!preparing.contains(key)) {
                obsolete.add(entry.getValue());iterator.remove();
            }
        }
        release(obsolete);
    }
    private void release(Collection<V> values) {
        Throwable failure=null;
        for(V value:values) {
            try { value.close(); } catch(RuntimeException|Error error) {
                if(failure==null)failure=error;else failure.addSuppressed(error);
            }
        }
        if(failure instanceof RuntimeException)throw (RuntimeException)failure;
        if(failure instanceof Error)throw (Error)failure;
    }
    @Override public synchronized void close() {
        if(closed)return;
        closed=true;player=null;current=null;previous=null;preload=null;
        timeline.clear();preparing.clear();
        ArrayList<V> releasing=new ArrayList<>(media.values());media.clear();
        release(releasing);
    }
}
