"""Test-only renderer for the pinned 114 metadata/VOD harness."""
from pathlib import Path
import hashlib
import subprocess
import tempfile


def blob(s):
    b = s.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()


def method(text, signature):
    start = text.index(signature)
    brace = text.index('{', start)
    level = 1
    for pos in range(brace + 1, len(text)):
        if text[pos] == '{': level += 1
        elif text[pos] == '}':
            level -= 1
            if not level: return text[start:pos+1]
    raise AssertionError(signature)


def methods(s, signatures):
    return '\n'.join(method(s, sig) for sig in signatures)


def once(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)


def section(s, start, end, replacement):
    a = s.index(start)
    b = s.index(end, a)
    return s[:a] + replacement + '\n' + s[b:]


CHANNEL_SIGS = ('public void setData(Epg data)', 'public Epg getData(ZoneId zoneId)',
    'Epg getData(ZoneId zoneId, LocalDate day)', 'public List<Epg> getDataList()',
    'public void setDataList(List<Epg> list)', 'public boolean hasEpgOverride()',
    'public String getLogo()', 'public void setLogo(String logo)')


def render(fixture, live, xml, vm, danmaku, epg, epgdata, channel_methods):
    assert blob(fixture) == '544783845b4fd8925ea8923937f48301e7948c7e'
    assert blob(epg) == 'd63ccb03bacb11aba7ef0817f6297d8f0f1494ca'
    assert blob(epgdata) == '57716b5bbf38da67cdeb0ee29155da5fade1b948'
    assert blob(channel_methods.rstrip('\n')+'\n') == 'ce973f99abe0c6247ed9a2bfc897b4dc0d4bf6a6'
    assert blob(danmaku.rstrip('\n')+'\n') == '6eda82f9c7881745d167a7022dcff05e4cd14cd6'
    triple = (blob(live), blob(xml), blob(vm))
    assert triple in (
        ('df0138ae3c510e853bbc113128f61375e422ca2c','8819406efc21deeb900dd5d86a68260edba43980','367f6c10fc6c583887cf08d4a2d8ab7d50f76d0a'),
        ('b22eb5e770fc36107d94c7b18400deea757c8792','10da8a80d0baaa57cdaae3da70d8a32cf8f49726','6fc6cc0cc614165de8f8eeda2fce10b07bbd1c67'))
    s = once(fixture, 'import java.util.concurrent.Callable;', '''import java.util.concurrent.*;
import java.time.format.*;
import java.util.regex.*;
import java.util.stream.Collectors;''')
    s = section(s, 'class Formatters {', 'class Response implements', r'''
class Formatters {
    static final DateTimeFormatter DATE=DateTimeFormatter.ISO_LOCAL_DATE;
    static final DateTimeFormatter TIME=DateTimeFormatter.ofPattern("HH:mm",Locale.ROOT);
    static final DateTimeFormatter EPG_RANGE=DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC);
}
@interface Nullable {}
@interface SerializedName { String value(); }
class TextUtils { static boolean isEmpty(String s) { return s==null || s.isEmpty(); } }
class Trans { static boolean pass() { return true; } static String s2t(String s) { throw new AssertionError("translation boundary"); } }
class Epg {
    private String key,date;
    private List<EpgData> list;
    static Epg objectFrom(String body,String id,String date,ZoneId zone) {
        if (body.equals("epg")) return Epg.create(id,date); // original HTTP fixture token
        return EpgParser.getEpg(body,id,date,zone);
    }
    __EPG_METHODS__
}
__EPG_DATA__
class Channel {
    final List<Epg> days=new ArrayList<>();
    private List<Epg> dataList=days;
    String id="tv", logo="";
    boolean epgFromLive=true;
    String getEpg() { return "https://example.invalid/{date}"; }
    String getTvgId() { return id; }
    String getName() { return id; }
    String getTvgName() { return id; }
    __CHANNEL_METHODS__
}
record Group(List<Channel> getChannel) {}
class Live {
    final List<String> urls=new ArrayList<>();
    final List<Group> groups=new ArrayList<>();
    int bound;
    Live(String... values) {
        urls.addAll(Arrays.asList(values));
        groups.add(new Group(List.of(new Channel() {
            @Override public void setData(Epg data) { super.setData(data); bound++; }
        })));
    }
    List<String> getEpgXml() { return urls; }
    List<Group> getGroups() { return groups; }
    ZoneId getZoneId() { return ZoneId.of("UTC"); }
}''')
    s = once(s, '__EPG_METHODS__', methods(epg, ('public static Epg create(', 'public String getKey()',
        'public void setKey(', 'public String getDate()', 'public void setDate(', 'public List<EpgData> getList()',
        'public void setList(', 'public boolean equal(', 'public EpgData getEpgData()', 'public Epg selected()')))
    s = once(s, '__EPG_DATA__', epgdata[epgdata.index('public class EpgData'):].replace('public class EpgData','class EpgData',1))
    s = once(s, '__CHANNEL_METHODS__', channel_methods)
    s = once(s, 'static File dir;', 'static File dir;\n    static boolean exists(File f) { return f.isFile(); }')
    s = once(s, '''    final File file;
    Download(File file) { this.file = file; }
    static Download create(String url, File file) { return new Download(file); }''', '''    static final Map<String,String> bodies=new HashMap<>();
    final File file;
    final String url;
    Download(String url, File file) { this.url=url; this.file=file; }
    static Download create(String url, File file) { return new Download(url,file); }''')
    s = once(s, 'Files.writeString(file.toPath(), "epg");', 'Files.writeString(file.toPath(), bodies.getOrDefault(url, MetadataHarness.sample("normal", "tv")));')
    # Real full parser. Only Simple XML deserialization is adapted to JDK DOM.
    s = section(s, 'class EpgParser {', 'class LiveApi {', XML_ADAPTER + '\n' + xml[xml.index('public class EpgParser'):].replace('public class EpgParser','class EpgParser',1))
    signatures = ['public static boolean parseXml(@NonNull Live item)', 'public static boolean parseXml(@NonNull Live item, OkHttpClient client)',
        'public static Epg getEpg(@NonNull Channel item, @NonNull ZoneId zoneId)',
        'public static Epg getEpg(@NonNull Channel item, @NonNull ZoneId zoneId, OkHttpClient client)',
        'private static boolean startXml(', 'private static void fetchEpgDay(']
    for sig in ('private static Epg readEpgDay(', 'public static Callable<BooleanSupplier> prepareXml(', 'public static Callable<Supplier<Epg>> prepareEpg('):
        if sig in live: signatures.append(sig)
    s = once(s, '__LIVE__', methods(live, signatures))
    s = once(s, '__VIEWMODEL__', vm[vm.index('public class LiveViewModel'):].replace('public class LiveViewModel','class LiveViewModel',1))
    s = once(s, '__DANMAKU__', danmaku)
    s = once(s, 'new ArrayDeque<>()', 'new ConcurrentLinkedQueue<>()')
    s = section(s, 'class ViewModelTaskRunner<', 'class LiveViewModel extends', RUNNER)
    s = once(s, '    public static void main(String[] args) throws Exception {', RACE+'\n    public static void main(String[] args) throws Exception {')
    s = once(s, '            OkHttpClient proxy = new OkHttpClient();', '            if (args.length==1 && args[0].equals("race")) { race(); return; }\n            OkHttpClient proxy = new OkHttpClient();')
    # Preserve all 19 existing assertions exactly, including order.
    original_checks = [l.strip() for l in fixture.splitlines() if l.strip().startswith('check(')]
    for check in original_checks: assert s.count(check)==1, check
    assert len(original_checks)==19
    return s


XML_ADAPTER = r'''
record InputNode(org.w3c.dom.Element root) { String getName() { return root.getTagName(); } }
class NodeBuilder {
    static InputNode read(InputStream in) throws Exception { return read(new org.xml.sax.InputSource(in)); }
    static InputNode read(Reader in) throws Exception { return read(new org.xml.sax.InputSource(in)); }
    static InputNode read(org.xml.sax.InputSource in) throws Exception {
        var f=javax.xml.parsers.DocumentBuilderFactory.newInstance();
        f.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true);
        f.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, "");
        f.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        return new InputNode(f.newDocumentBuilder().parse(in).getDocumentElement());
    }
}
class Persister {
    <T> T read(Class<T> kind,InputNode node,boolean strict) {
        if (kind!=Tv.class) throw new AssertionError(kind);
        var channels=new ArrayList<Tv.Channel>(); var programmes=new ArrayList<Tv.Programme>();
        for (var n=node.root().getFirstChild(); n!=null; n=n.getNextSibling()) {
            if (!(n instanceof org.w3c.dom.Element e)) continue;
            if (e.getTagName().equals("channel")) {
                var icon=e.getElementsByTagName("icon").item(0);
                channels.add(new Tv.Channel(e.getAttribute("id"),icon==null?"":((org.w3c.dom.Element)icon).getAttribute("src")));
            } else if (e.getTagName().equals("programme")) {
                programmes.add(new Tv.Programme(e.getAttribute("channel"),e.getAttribute("start"),e.getAttribute("stop"),e.getElementsByTagName("title").item(0).getTextContent()));
            } else throw new AssertionError(e.getTagName());
        }
        return kind.cast(new Tv(channels,programmes));
    }
}
record Tv(List<Tv.Channel> getChannel,List<Tv.Programme> getProgramme) {
    record DisplayName(String getText) {}
    record Channel(String getId,String getSrc) {
        boolean hasSrc() { return !getSrc.isEmpty(); }
        List<DisplayName> getDisplayName() { return List.of(); } // fixture has no aliases
    }
    record Programme(String getChannel,String getStart,String getStop,String getTitle) {}
}
'''

RUNNER = r'''
class ViewModelTaskRunner<T extends Enum<T>> {
    static Pause next;
    static boolean threaded;
    static class Pause implements AutoCloseable {
        final CountDownLatch ready=new CountDownLatch(1), release=new CountDownLatch(1);
        Thread worker; volatile Throwable failed; volatile boolean held;
        void await() {
            try { if(!ready.await(5,TimeUnit.SECONDS)) throw new AssertionError("worker not prepared"); }
            catch(InterruptedException e) { throw new AssertionError(e); }
            if(failed!=null || held) throw new AssertionError("worker failed or holds parser lock",failed);
        }
        public void close() { release.countDown(); join(worker); if(failed!=null) throw new AssertionError(failed); }
    }
    static void join(Thread worker) {
        if(worker==null) return;
        try { worker.join(5000); } catch(InterruptedException e) { throw new AssertionError(e); }
        if(worker.isAlive()) throw new AssertionError("worker did not exit");
    }
    static Pause pauseNext() { if(next!=null) throw new AssertionError("pause already armed"); return next=new Pause(); }
    ViewModelTaskRunner(Class<T> kind) {}
    // Deliberately allow completion after cancel: isolate the real main-thread admission gate.
    void cancel(T type) {}
    void cancelAll() {}
    <V> void execute(T type,long timeout,Callable<V> call,Consumer<V> success,Consumer<Throwable> error) {
        Pause p=next; next=null;
        if(p==null) {
            Runnable work=() -> { try { success.accept(call.call()); } catch(Exception e) { error.accept(e); } };
            if(threaded) {
                FutureTask<Void> task=new FutureTask<>(work,null);
                Thread worker=new Thread(task,"current-metadata-worker");worker.start();join(worker);
                try { task.get(); } catch(Exception e) { throw new AssertionError(e); }
            } else work.run();
            return;
        }
        p.worker=new Thread(() -> {
            try {
                V result=call.call(); p.held=Thread.holdsLock(EpgParser.class); p.ready.countDown();
                if(!p.release.await(10,TimeUnit.SECONDS)) throw new AssertionError("release timeout");
                success.accept(result);
            } catch(Throwable e) { p.failed=e; p.ready.countDown(); }
        },"paused-metadata-worker");
        p.worker.start(); p.await();
    }
}
'''

RACE = r'''
    static String sample(String title,String... ids) {
        LocalDate day=LocalDate.now(ZoneOffset.UTC);
        var fmt=DateTimeFormatter.BASIC_ISO_DATE;
        String start=day.format(fmt)+"000000 +0000", end=day.plusDays(1).format(fmt)+"000000 +0000";
        StringBuilder b=new StringBuilder("<tv>");
        for(String id:ids) {
            String icon=title.equals("NEW") && id.equals("blank") ? "" : "<icon src='"+title+"-logo'/>";
            b.append("<channel id='"+id+"'>"+icon+"</channel><programme channel='"+id+"' start='"+start+"' stop='"+end+"'><title>"+title+"</title></programme>");
        }
        return b.append("</tv>").toString();
    }
    static EpgData cue(String title,long start,long end,boolean selected) {
        EpgData x=new EpgData(); x.setTitle(title);x.setStartTime(start);x.setEndTime(end);x.setSelected(selected);return x;
    }
    static Channel cached(String label,EpgData[] out) {
        Channel c=new Channel(); LocalDate d=LocalDate.now(ZoneOffset.UTC);
        long midnight=d.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
        long next=d.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli();
        out[0]=cue(label,midnight-1000,next,false);
        out[1]=cue(label+"-future",next+1000,next+2000,true);
        for(int offset=-1;offset<=1;offset++) {
            Epg day=Epg.create("tv",d.plusDays(offset).toString());
            if(offset==-1) day.getList().add(out[0]);
            if(offset==0) day.getList().add(out[1]);
            c.setData(day);
        }
        return c;
    }
    static void race() {
        TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
        ViewModelTaskRunner.threaded=true;
        ZoneId zone=ZoneId.of("UTC"); OkHttpClient proxy=new OkHttpClient();
        LiveViewModel vm=new LiveViewModel(); vm.createPlaybackController(new LivePlaybackHost(true));
        Channel ordinary=new Channel(), custom=new Channel(), blank=new Channel();
        custom.id="custom"; custom.setLogo("user-logo"); blank.id="blank";
        Live old=new Live("old.xml"), newer=new Live("new.xml");
        Group group=new Group(List.of(ordinary,custom,blank));
        for(Live x:List.of(old,newer)) { x.groups.clear();x.groups.add(group); }
        Download.bodies.put("old.xml",sample("OLD","tv","custom","blank"));
        Download.bodies.put("new.xml",sample("NEW","tv","custom","blank"));
        EpgData[] retired=new EpgData[2], current=new EpgData[2];
        Channel cache=cached("OLD-CACHE",retired), fresh=cached("NEW-CACHE",current), alias=new Channel();
        alias.setDataList(cache.getDataList());
        check(alias.getData(zone).getList().stream().anyMatch(x->x==retired[0]) && alias.getDataList().get(0)==cache.getDataList().get(0),"shared cache fixture");
        int httpBefore=OkHttp.routed;
        var px=ViewModelTaskRunner.pauseNext();
        try {
            vm.parseXml(old,proxy);
            var pe=ViewModelTaskRunner.pauseNext();
            try {
                vm.getEpg(cache,proxy);
                check(!px.held&&!pe.held,"paused after parser lock");
                check(ordinary.getDataList().isEmpty() && ordinary.getLogo().isEmpty() && blank.getLogo().isEmpty(),"OLD_WORKER_MUTATED_BEFORE_ADMISSION");
                check(!retired[0].isSelected() && retired[1].isSelected(),"OLD_WORKER_SELECTED_BEFORE_ADMISSION");
                check(vm.xml().deliveries==0 && vm.epg().deliveries==0,"no pre-admission notification");
                vm.cancelPlaybackMetadata();
                vm.parseXml(newer,proxy); vm.getEpg(fresh,proxy); App.drain();
                check(ordinary.getData(zone).getList().get(0).getTitle().equals("NEW"),"NEW_XML_COMMIT");
                check(ordinary.getLogo().equals("NEW-logo") && custom.getLogo().equals("user-logo") && blank.getLogo().isEmpty(),"NEW_LOGO_COMMIT");
                check(current[0].isSelected() && !current[1].isSelected() && vm.epg().value.getEpgData()==current[0],"NEW_SELECTED_COMMIT");
                check(Boolean.TRUE.equals(vm.xml().value)&&vm.xml().deliveries==1&&vm.epg().deliveries==1,"NEW_NOTIFICATION_COMMIT");
                px.close(); pe.close();
                check(App.queue.size()==2,"both stale callbacks really reached owner queue");
                App.drain();
                for(Channel c:List.of(ordinary,custom,blank)) check(c.getData(zone).getList().size()==1 && c.getData(zone).getList().get(0).getTitle().equals("NEW"),"STALE_EPG_DATA");
                check(ordinary.getLogo().equals("NEW-logo") && custom.getLogo().equals("user-logo") && blank.getLogo().isEmpty(),"STALE_LOGO_MUTATION");
                check(!retired[0].isSelected() && retired[1].isSelected() && alias.getDataList().get(0)==cache.getDataList().get(0),"STALE_SELECTED_MUTATION");
                check(current[0].isSelected()&&!current[1].isSelected(),"NEW_SELECTED_STATE_CHANGED");
                check(vm.xml().deliveries==1 && vm.epg().deliveries==1 && vm.epg().value.getEpgData()==current[0],"STALE_NOTIFICATION");
                check(OkHttp.routed==httpBefore,"cached EPG used no network");
                System.out.println("PASS paused-worker XML/EPG/cached shared selection/notification: "+checks+" assertions");
            } finally { pe.close(); }
        } finally { px.close(); }
    }
'''


def run(java, root, reviewed):
    def check_run(source, name, arg=None, fail=None):
        d=root/name;d.mkdir();src=d/'MetadataHarness.java';src.write_text(source,encoding='utf-8')
        subprocess.run(['javac','--release','17',str(src)],check=True,timeout=30)
        r=subprocess.run(['java','-Duser.timezone=UTC','-cp',str(d),'MetadataHarness']+([arg] if arg else []),capture_output=True,text=True,timeout=30)
        if fail:
            assert r.returncode!=0 and 'AssertionError: '+fail in r.stderr, (name,r.returncode,r.stdout,r.stderr)
            print(name,'EXPECTED_REJECTION',fail,flush=True)
        else:
            assert r.returncode==0,(name,r.returncode,r.stdout,r.stderr)
            print(name,r.stdout.strip(),flush=True)
    check_run(java,'existing')
    for name,before,after,failure in (
        ('old-neg-url','if (latestUrlRequest != request) return;','','latest URL only'),
        ('old-neg-xml','if (client != null) request.client(client).tag(tag == null ? url : tag);','','explicit XML client and tag'),
        ('old-neg-danmaku','if (!isCurrent.getAsBoolean()) return -1;\n        DanmakuApi.cancel();','DanmakuApi.cancel();\n        if (!isCurrent.getAsBoolean()) return -1;','retired owner cannot cancel new Danmaku')):
        check_run(once(java,before,after),name,fail=failure)
    if not reviewed:
        check_run(java,'race-baseline','race','OLD_WORKER_MUTATED_BEFORE_ADMISSION')
    else:
        check_run(java,'race-reviewed','race')
        check_run(once(java,'if (xmlGeneration == generation) xml.setValue(result.getAsBoolean());','xml.setValue(result.getAsBoolean());'),'race-neg-xml','race','STALE_EPG_DATA')
        check_run(once(java,'if (epgGeneration != generation) return;',''),'race-neg-epg','race','STALE_SELECTED_MUTATION')
