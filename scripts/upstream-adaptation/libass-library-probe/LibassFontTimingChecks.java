/* SPDX-License-Identifier: Apache-2.0 */
package androidx.media3.exoplayer.libass;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.function.Consumer;

/** Shared new behavior assertions; Android uses the unchanged reference caller.
 * Host uses the actual JNI declarations and frame/image classes directly.
 */
final class LibassFontTimingChecks {
    static final String MISSING="FingMiFixtureUninstalledFamilyX92";
    static final String TEXT="WWii minimum";
    interface Track extends AutoCloseable {
        void codec(byte[] bytes,int off,int len);
        void chunk(byte[] bytes,int off,int len,long startUs,long durationUs);
        LibassFrame render(long ms);
        void fonts(String dir,String family);
        void scale(boolean apply,float value);
        long handle();
        @Override void close();
    }
    interface Factory { Track create(String family); }
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    static void reject(Class<? extends Throwable> type,Runnable r){
        try{r.run();}catch(Throwable e){if(type.isInstance(e))return;throw e;}
        throw new AssertionError("expected "+type.getName());
    }
    static byte[] padded(String s){
        byte[] b=s.getBytes(StandardCharsets.UTF_8),a=new byte[b.length+7];
        Arrays.fill(a,(byte)0x7f);System.arraycopy(b,0,a,3,b.length);return a;
    }
    static void init(Track t,String family){
        String h="[Script Info]\nScriptType: v4.00+\nPlayResX: 640\nPlayResY: 360\n"
            +"[V4+ Styles]\n"
            +"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            +"Style: Default,"+family+",24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,10,10,10,1\n"
            +"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n";
        byte[] b=padded(h);t.codec(b,3,b.length-7);Arrays.fill(b,(byte)0);
    }
    static void chunk(Track t,int order,String caption,long startUs,long durationUs){
        byte[] b=padded(order+",0,Default,,0,0,0,,"+caption);
        t.chunk(b,3,b.length-7,startUs,durationUs);Arrays.fill(b,(byte)0);
    }
    static long hash(LibassFrame f){
        check(f!=null&&!f.isEmpty(),"nonempty real frame");long h=0xcbf29ce484222325L;boolean ink=false;
        for(LibassImage i:f.images){
            check(i.bitmap!=null&&i.textureId==0&&i.bitmap.length==i.width*i.height,"CPU coverage");
            for(int v:new int[]{i.x,i.y,i.width,i.height,i.color})h=(h^v)*1099511628211L;
            for(byte b:i.bitmap){ink|=b!=0;h=(h^(b&255))*1099511628211L;}
        }
        check(ink,"actual glyph pixels");return h;
    }
    static int width(LibassFrame f){
        int l=640,r=0;for(LibassImage i:f.images){l=Math.min(l,i.x);r=Math.max(r,i.x+i.width);}return r-l;
    }
    static int top(LibassFrame f){int y=360;for(LibassImage i:f.images)y=Math.min(y,i.y);return y;}
    static void run(Factory make,String dir,Consumer<String> log){
        try(Track a=make.create("DejaVu Sans");Track b=make.create("DejaVu Serif");Track named=make.create("DejaVu Serif");Track pos=make.create("DejaVu Sans")){
            init(a,MISSING);init(b,MISSING);init(named,"DejaVu Sans");init(pos,"DejaVu Sans");
            for(Track t:new Track[]{a,b,named})chunk(t,1,TEXT,1234000,567000);
            check(a.render(1233).isEmpty(),"before first sample");
            LibassFrame saved=a.render(1234);long sans=hash(saved);long serif=hash(b.render(1234));
            check(sans!=serif,"real external fallback families differ");
            check(sans==hash(named.render(1234)),"explicit family matches actual Sans fallback");
            chunk(a,1,TEXT,1234000,567000);
            check(sans==hash(a.render(1500)),"duplicate read order unchanged");
            check(sans==hash(a.render(1800))&&a.render(1801).isEmpty(),"duration not absolute end");
            chunk(a,2,TEXT,3000000,0);check(a.render(3000).isEmpty(),"zero duration");
            check(sans==hash(a.render(1300)),"backward time to first sample");
            reject(IllegalArgumentException.class,()->chunk(a,3,TEXT,1000,-1));
            byte[] bad=padded("x");reject(RuntimeException.class,()->a.chunk(bad,-1,1,1,1));
            log.accept("PASS_REFERENCE_TIMED_CHUNK start_ms=1234 end_ms=1801 duplicate=1 backward=1 zero_duration=1");
            a.fonts(dir,"DejaVu Serif");
            LibassFrame changed=a.render(1300);check(changed.changed&&hash(changed)==serif,"font switch refresh and real Serif pixels");
            check(hash(b.render(1300))==serif&&hash(named.render(1300))==sans,"other tracks unaffected");
            a.fonts(dir,"DejaVu Sans");check(hash(a.render(1300))==sans,"restore family invalidates caches");
            reject(UnsupportedOperationException.class,()->LibassNative.nativeSetFonts(a.handle(),dir+"/unlisted","DejaVu Serif"));
            check(hash(a.render(1300))==sans,"rejected change preserves pixels");
            log.accept("PASS_REFERENCE_CONFIGURED_FAMILY_CHANGE sans="+Long.toHexString(sans)+" serif="+Long.toHexString(serif)+" restored=1 isolated=1");
            a.scale(false,1);int base=width(a.render(1300));
            a.scale(true,1.5f);LibassFrame large=a.render(1300);int big=width(large);
            a.scale(true,0.5f);LibassFrame small=a.render(1300);int little=width(small);
            check(large.changed&&small.changed&&big>base&&little<base,"actual font scaling");
            a.scale(true,1);check(hash(a.render(1300))==sans,"scale restoration");
            reject(UnsupportedOperationException.class,()->a.scale(false,1.5f));
            reject(IllegalArgumentException.class,()->a.scale(true,Float.NaN));
            check(hash(a.render(1300))==sans,"rejected scale preserves pixels");
            log.accept("PASS_REFERENCE_ORDINARY_FONT_SCALE base="+base+" large="+big+" small="+little+" restored=1");
            chunk(pos,10,"{\\an5\\pos(320,80)}"+TEXT,2000000,500000);
            chunk(pos,11,"{\\an5\\pos(320,220)}"+TEXT,3000000,500000);
            LibassFrame p1=pos.render(2000),p2=pos.render(3000);hash(p1);hash(p2);
            int y1=top(p1),y2=top(p2);
            check(y2-y1==140,"explicit ASS coordinates in timed packets");
            log.accept("PASS_REFERENCE_TIMED_EXPLICIT_GEOMETRY top1="+y1+" top2="+y2+" delta=140");
            long retired=a.handle();a.close();
            reject(IllegalStateException.class,()->LibassNative.nativeSetFonts(retired,dir,"DejaVu Serif"));
            reject(IllegalStateException.class,()->LibassNative.nativeSetFontScale(retired,1,true));
            check(hash(saved)==sans&&hash(b.render(1300))==serif,"saved pixels and other track survive close");
            log.accept("PASS_REFERENCE_FONT_TIMING_LIFETIME retired=1 saved=1 other_track=1");
        }
    }
}
