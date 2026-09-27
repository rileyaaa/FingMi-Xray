package androidx.media3.exoplayer.libass;
import java.util.*;

public final class MediaOwnershipTest {
 static final class Media implements LibassMediaOwnership.Resource {
  final String name;int releases;boolean fail;
  Media(String name){this.name=name;}
  public void close(){check(++releases==1);if(fail)throw new IllegalStateException(name);}
 }
 static final class Fixture {
  final Map<String,List<Media>> created=new HashMap<>();
  final LibassMediaOwnership<String,Media> owner=new LibassMediaOwnership<>(s->{Media m=new Media(s);created.computeIfAbsent(s,k->new ArrayList<>()).add(m);return m;});
  final Object player=new Object();
  Fixture(){owner.bindPlayer(player);}
  Media get(String key){return created.get(key).get(0);}
  int count(String key){return created.getOrDefault(key,List.of()).size();}
  void current(String key){owner.updateCurrent(player,key);}
  void timeline(String...keys){owner.updateTimeline(player,List.of(keys));}
 }
 static int passes;
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void test(String name,Runnable r){r.run();passes++;System.out.println("PASS "+name);}
 public static void main(String[]args) {
  test("preload promotion retains the same resource",()->{
   Fixture f=new Fixture();f.owner.setPreload("B");Media b=f.get("B");check(f.owner.createComponents("B")==b);
   f.current("B");f.owner.setPreload(null);check(f.owner.active()==b&&b.releases==0&&f.count("B")==1);f.owner.close();check(b.releases==1);
  });
  test("current previous and preload are independent retainers",()->{
   Fixture f=new Fixture();f.current("A");f.current("B");f.owner.setPreload("P");check(f.get("A").releases==0);
   f.current("C");check(f.get("A").releases==1&&f.get("B").releases==0&&f.get("P").releases==0);
   f.current(null);check(f.get("B").releases==1&&f.get("C").releases==1&&f.get("P").releases==0);f.owner.close();
  });
  test("new components survive empty timeline until acknowledged",()->{
   Fixture f=new Fixture();Media x=f.owner.createComponents("X"),y=f.owner.createComponents("Y");
   f.timeline();check(x.releases==0&&y.releases==0);f.timeline("X");check(x.releases==0&&y.releases==1);
   f.current("X");f.timeline();check(x.releases==0);f.current(null);check(x.releases==1);f.owner.close();
  });
  test("previous-media component preparation has its own retainer",()->{
   Fixture f=new Fixture();f.current("A");f.current("B");Media a=f.owner.createComponents("A");
   f.current("C");check(a.releases==0);f.timeline("C");check(a.releases==1);f.owner.close();
  });
  test("old player callbacks cannot mutate replacement",()->{
   Fixture f=new Fixture();f.current("A");f.owner.setPreload("P");Object next=new Object();f.owner.bindPlayer(next);
   check(f.get("A").releases==1&&f.get("P").releases==0);
   f.current("OLD");f.timeline("OLD");check(f.count("OLD")==0&&f.owner.active()==null);
   f.owner.updateCurrent(next,"P");check(f.owner.active()==f.get("P"));f.owner.bindPlayer(next);check(f.owner.active()==f.get("P"));f.owner.close();
  });
  test("detach releases staged resources but retains explicit preload",()->{
   Fixture f=new Fixture();Media x=f.owner.createComponents("X");f.owner.setPreload("P");f.owner.bindPlayer(null);
   check(x.releases==1&&f.get("P").releases==0);f.owner.setPreload(null);check(f.get("P").releases==1);f.owner.close();
  });
  test("release and late callbacks are idempotent",()->{
   Fixture f=new Fixture();Media x=f.owner.createComponents("X");f.owner.close();f.owner.close();f.current("LATE");f.owner.setPreload("LATE");f.timeline("LATE");
   check(x.releases==1&&f.count("LATE")==0);try{f.owner.createComponents("LATE");throw new AssertionError();}catch(IllegalStateException expected){}
  });
  test("one failing release does not leak other media",()->{
   Fixture f=new Fixture();Media a=f.owner.createComponents("A"),b=f.owner.createComponents("B");a.fail=true;
   try{f.owner.close();throw new AssertionError();}catch(IllegalStateException expected){}
   check(a.releases==1&&b.releases==1);f.owner.close();
  });
  System.out.println("PASS "+passes+" media ownership cases");
 }
}
