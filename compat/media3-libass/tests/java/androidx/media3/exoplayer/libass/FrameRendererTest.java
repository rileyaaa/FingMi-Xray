package androidx.media3.exoplayer.libass;

import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

public final class FrameRendererTest {
    static final class GPU implements LibassFrameRenderer.Textures {
        int next=100, uploads, failAt;
        final Set<Integer> live = new HashSet<>();
        final List<Integer> drawn = new ArrayList<>();
        final List<LibassFrameRenderer.Image> images = new ArrayList<>();
        int nativeTexture(){int t=++next;live.add(t);return t;}
        public int upload(byte[] b,int w,int h){
            check(b.length==w*h);
            if(++uploads==failAt)throw new IllegalStateException("upload failure");
            return nativeTexture();
        }
        public void delete(int t){check(live.remove(t));}
        public void draw(LibassFrameRenderer.Image i,int w,int h){
            check(live.contains(i.textureId)&&w==640&&h==360);
            drawn.add(i.textureId);images.add(i);
        }
        void resetDraw(){drawn.clear();images.clear();}
    }
    static final class Fixture {
        final GPU gpu=new GPU();final LibassFrameRenderer r=new LibassFrameRenderer(gpu);
        final Object media=new Object();
        Fixture(){r.bind(media);}
        boolean update(LibassFrame p,LibassFrame s){return r.update(media,new LibassFrameSet(p,s),640,360);}
        void close(){r.close();check(gpu.live.isEmpty());}
    }
    static LibassImage image(int texture,int color){return new LibassImage(10,20,2,3,color,texture==0?new byte[6]:null,texture);}
    static LibassFrame frame(LibassImage...images){return new LibassFrame(1,images);}
    static LibassFrame cpu(){return frame(image(0,0xffffffff));}
    static LibassFrame unchanged(){return new LibassFrame(0,null);}
    static int passes;
    static void check(boolean b){if(!b)throw new AssertionError();}
    static void test(String name,Runnable r){r.run();passes++;System.out.println("PASS "+name);}
    static void expectFailure(Runnable r){try{r.run();throw new AssertionError();}catch(IllegalStateException|IllegalArgumentException expected){}}
    public static void main(String[]args)throws Exception{
        test("native unchanged preserves cache; changed-empty clears",()->{
            Fixture f=new Fixture();check(f.update(cpu(),null));f.r.draw();List<Integer> first=List.copyOf(f.gpu.drawn);
            check(!f.update(unchanged(),null));f.gpu.resetDraw();f.r.draw();check(f.gpu.drawn.equals(first)&&f.gpu.uploads==1);
            check(f.update(frame(),null));check(f.gpu.live.isEmpty());check(!f.update(unchanged(),null));f.close();
        });
        test("primary and secondary advance independently; primary drawn first",()->{
            Fixture f=new Fixture();int p=f.gpu.nativeTexture(),s=f.gpu.nativeTexture();
            f.update(frame(image(p,0)),frame(image(s,0)));f.r.draw();check(f.gpu.drawn.equals(List.of(p,s)));
            f.update(unchanged(),cpu());f.gpu.resetDraw();f.r.draw();check(f.gpu.drawn.get(0)==p&&!f.gpu.live.contains(s));
            f.update(null,unchanged());check(!f.gpu.live.contains(p)&&f.gpu.live.size()==1);f.close();
        });
        test("native textures transfer once and need no bitmap upload",()->{
            Fixture f=new Fixture();int t=f.gpu.nativeTexture();LibassImage i=image(t,0);
            f.update(frame(i),null);check(i.textureId==0&&f.gpu.uploads==0&&f.gpu.live.contains(t));f.close();f.r.close();
        });
        test("ASS packed color uses inverse transparency",()->{
            Fixture f=new Fixture();f.update(frame(image(0,0x12345678)),null);f.r.draw();LibassFrameRenderer.Image i=f.gpu.images.get(0);
            check(i.red==0x12/255f&&i.green==0x34/255f&&i.blue==0x56/255f&&i.alpha==1f-0x78/255f);
            check(i.x==10&&i.y==20&&i.width==2&&i.height==3);f.close();
        });
        test("stale media result freed without overwriting either current lane",()->{
            Fixture f=new Fixture();f.update(cpu(),cpu());Object next=new Object();check(f.r.bind(next));check(f.gpu.live.isEmpty());
            int stale=f.gpu.nativeTexture();check(!f.r.update(f.media,new LibassFrameSet(frame(image(stale,0)),null),640,360));
            check(f.gpu.live.isEmpty());check(f.r.update(next,new LibassFrameSet(cpu(),cpu()),640,360));f.close();
        });
        test("upload failure rolls back both lanes and deletes unconsumed native images",()->{
            Fixture f=new Fixture();f.update(cpu(),cpu());Set<Integer> before=Set.copyOf(f.gpu.live);
            int nativeId=f.gpu.nativeTexture();LibassImage incoming=image(nativeId,0);
            f.gpu.failAt=f.gpu.uploads+2; // secondary upload succeeds; primary upload fails.
            expectFailure(()->f.update(frame(image(0,0),incoming),cpu()));
            check(f.gpu.live.equals(before)&&incoming.textureId==0);f.r.draw();check(f.gpu.drawn.size()==2);f.close();
        });
        test("partial layer failure frees transferred native texture and uploaded image",()->{
            Fixture f=new Fixture();int t=f.gpu.nativeTexture();LibassImage n=image(t,0);
            LibassImage invalid=new LibassImage(0,0,3,3,0,new byte[1],0);
            expectFailure(()->f.update(frame(n,image(0,0),invalid),null));check(n.textureId==0&&f.gpu.live.isEmpty());f.close();
        });
        test("unexpected native textures on unchanged frames are freed",()->{
            Fixture f=new Fixture();f.update(cpu(),null);int t=f.gpu.nativeTexture();
            f.update(new LibassFrame(0,new LibassImage[]{image(t,0)}),null);
            check(!f.gpu.live.contains(t)&&f.gpu.live.size()==1);f.close();
        });
        test("invalid frame dimensions do not leak incoming native textures",()->{
            Fixture f=new Fixture();int t=f.gpu.nativeTexture();
            expectFailure(()->f.r.update(f.media,new LibassFrameSet(frame(image(t,0)),null),0,360));check(f.gpu.live.isEmpty());f.close();
        });
        test("late result after close is consumed and release remains idempotent",()->{
            Fixture f=new Fixture();f.update(cpu(),cpu());f.close();int t=f.gpu.nativeTexture();
            check(!f.update(frame(image(t,0)),null));check(f.gpu.live.isEmpty());f.r.draw();f.r.close();
        });
        Fixture f=new Fixture();f.update(cpu(),null);AtomicReference<Throwable> result=new AtomicReference<>();
        Thread thread=new Thread(()->{try{f.r.close();}catch(Throwable e){result.set(e);}});thread.start();thread.join();
        check(result.get() instanceof IllegalStateException&&f.gpu.live.size()==1);f.close();passes++;
        System.out.println("PASS "+passes+" frame ownership cases (instrumented GPU, no EGL claim)");
    }
}
