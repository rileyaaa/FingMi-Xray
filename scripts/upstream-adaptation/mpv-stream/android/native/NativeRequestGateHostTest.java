/* SPDX-License-Identifier: Apache-2.0 */
import androidx.media3.mpvplayer.media.MpvStreamOwner;
import androidx.media3.mpvplayer.media.MpvNativeRequestGate;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public final class NativeRequestGateHostTest {
    public static void main(String[] args)throws Exception{
        MpvStreamOwner owner=new MpvStreamOwner();
        MpvNativeRequestGate gate=new MpvNativeRequestGate();
        MpvStreamOwner.Factory unused=()->{throw new AssertionError("gate must not open a data source");};
        MpvStreamOwner.Lease old=owner.replace(unused);
        long delayed=gate.reserve(old), oldOther=gate.reserve(old);
        MpvStreamOwner.Lease next=owner.replace(unused);
        long first=gate.reserve(next),second=gate.reserve(next),discard=gate.reserve(next);
        AtomicInteger count=new AtomicInteger();
        MpvNativeRequestGate.Reply sink=(id,e,v)->{if(id<=Integer.MAX_VALUE||v!=(1L<<45))throw new AssertionError("64 bit");count.incrementAndGet();};
        long result=1L<<45;
        if(gate.deliver(delayed,0,result,sink)||gate.deliver(oldOther,0,result,sink))throw new AssertionError("stale owner");
        try{gate.reserve(old);throw new AssertionError("stale reserve");}catch(IllegalStateException ok){}
        if(!gate.deliver(second,0,result,sink)||!gate.deliver(first,0,result,sink))throw new AssertionError("out of order");
        if(gate.deliver(first,0,result,sink))throw new AssertionError("duplicate");
        gate.forget(discard);if(gate.deliver(discard,0,result,sink))throw new AssertionError("discard");
        long raced=gate.reserve(next);
        ExecutorService e=Executors.newFixedThreadPool(2);
        try{
            CountDownLatch start=new CountDownLatch(1);
            Callable<Boolean> c=()->{start.await();return gate.deliver(raced,0,result,sink);};
            Future<Boolean> a=e.submit(c),b=e.submit(c);start.countDown();
            if(a.get()==b.get())throw new AssertionError("duplicate concurrent delivery");
        }finally{e.shutdownNow();}
        owner.retire(next);gate.clear();
        if(count.get()!=3)throw new AssertionError("count");
        System.out.println("PASS_HOST_REQUEST_GATE 64-bit out-of-order duplicate concurrent stale discard; synthetic replies only");
    }
}
