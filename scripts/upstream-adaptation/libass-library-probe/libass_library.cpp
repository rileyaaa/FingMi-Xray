/* SPDX-License-Identifier: Apache-2.0 */
// Independent library and embedded-font track subset. Not full Media3 libass.
#include <ass/ass.h>
#include <jni.h>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <memory>
#include <limits>
#include <cmath>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace {
std::atomic<int> live_libraries{0};
struct Library {
    ASS_Library *ass;
    std::string config;
    std::mutex mutex;
    explicit Library(std::string path) : ass(ass_library_init()), config(std::move(path)) {
        if (ass) { ass_set_extract_fonts(ass, 1); ++live_libraries; }
    }
    ~Library() { if (ass) { ass_library_done(ass); --live_libraries; } }
};
std::mutex handles_mutex;
std::unordered_map<jlong,std::shared_ptr<Library>> libraries;
jlong next_handle = 1;
void fail(JNIEnv *env, const char *type, const char *msg) {
    if (!env->ExceptionCheck()) {
        jclass cls=env->FindClass(type);
        if (cls) { env->ThrowNew(cls,msg); env->DeleteLocalRef(cls); }
    }
}
std::string str(JNIEnv *env,jstring s) {
    if (!s) return {};
    const char *p=env->GetStringUTFChars(s,nullptr);
    if (!p) return {};
    try { std::string result(p);env->ReleaseStringUTFChars(s,p);return result; }
    catch (...) { env->ReleaseStringUTFChars(s,p);throw; }
}
std::shared_ptr<Library> library(JNIEnv *env,jlong id) {
    std::lock_guard<std::mutex> lock(handles_mutex);
    auto it=libraries.find(id);
    if (it==libraries.end()) {
        fail(env,"java/lang/IllegalStateException","retired libass library handle");
        return {};
    }
    return it->second;
}
template<class F> void jni_void(JNIEnv *env,F fn) {
    try { fn(); }
    catch (const std::bad_alloc&) { fail(env,"java/lang/OutOfMemoryError","libass probe allocation"); }
    catch (...) { fail(env,"java/lang/IllegalStateException","libass probe operation"); }
}
template<class F> jlong jni_long(JNIEnv *env,F fn) {
    jlong result=0;
    jni_void(env,[&]{result=fn();});
    return result;
}

// Shared track lifetime for the legacy fixture and the new isolated track subset.
// The shared_ptr retains the library until renderer and track are destroyed.
struct FixtureTrack {
    std::shared_ptr<Library> lib;
    ASS_Renderer *renderer=nullptr;
    ASS_Track *track=nullptr;
    bool reference_frame_ready=false;
    bool reference_frame_dirty=true;
    int reference_storage_w=0, reference_storage_h=0;
    int reference_frame_w=0, reference_frame_h=0;
    explicit FixtureTrack(std::shared_ptr<Library> l):lib(std::move(l)){}
    ~FixtureTrack() {
        std::lock_guard<std::mutex> lock(lib->mutex);
        if(track)ass_free_track(track);
        if(renderer)ass_renderer_done(renderer);
    }
};
std::unordered_map<jlong,std::shared_ptr<FixtureTrack>> tracks;
std::shared_ptr<FixtureTrack> fixture(JNIEnv *env,jlong id) {
    std::lock_guard<std::mutex> lock(handles_mutex);
    auto it=tracks.find(id);
    if(it==tracks.end()){fail(env,"java/lang/IllegalStateException","retired fixture track");return {};}
    return it->second;
}
const char header[]=
    "[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    "Style: Default,DejaVu Sans,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1\n"
    "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n";
}

extern "C" JNIEXPORT jlong JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeCreateLibrary(JNIEnv *env,jclass,jstring config) {
    return jni_long(env,[&]()->jlong{
        auto path=str(env,config);
        if(env->ExceptionCheck())return 0;
        auto l=std::make_shared<Library>(std::move(path));
        if(!l->ass){fail(env,"java/lang/OutOfMemoryError","ass_library_init");return 0;}
        std::lock_guard<std::mutex> lock(handles_mutex);
        jlong id=next_handle++;
        libraries.emplace(id,std::move(l));
        return id;
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeReleaseLibrary(JNIEnv *env,jclass,jlong id) {
    jni_void(env,[&]{
        std::shared_ptr<Library> retired;
        {std::lock_guard<std::mutex> lock(handles_mutex);
         auto it=libraries.find(id);if(it!=libraries.end()){retired=std::move(it->second);libraries.erase(it);}}
        // Destruction outside the registry lock; active fixture tracks retain it.
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeAddFont(JNIEnv *env,jclass,jlong id,jstring name,jbyteArray data) {
    jni_void(env,[&]{
        auto l=library(env,id);if(!l)return;
        if(!name||!data){fail(env,"java/lang/IllegalArgumentException","font name/data required");return;}
        auto n=str(env,name);if(env->ExceptionCheck())return;
        jsize len=env->GetArrayLength(data);
        if(n.empty()||len<=0){fail(env,"java/lang/IllegalArgumentException","empty font");return;}
        std::vector<char> bytes(static_cast<size_t>(len));
        env->GetByteArrayRegion(data,0,len,reinterpret_cast<jbyte*>(bytes.data()));
        if(env->ExceptionCheck())return;
        std::lock_guard<std::mutex> lock(l->mutex);
        ass_add_font(l->ass,n.c_str(),bytes.data(),len);
    });
}

// Deliberately separate test-only JNI names, not stand-ins for missing Media3 methods.
extern "C" JNIEXPORT jlong JNICALL
Java_androidx_media3_exoplayer_libass_LibassLibraryProbe_openFixture(JNIEnv *env,jclass,jlong id,jstring text,jlong start,jlong duration) {
    return jni_long(env,[&]()->jlong{
        auto l=library(env,id);if(!l)return 0;
        auto caption=str(env,text);if(env->ExceptionCheck())return 0;
        if(caption.empty()||start<0||duration<=0){fail(env,"java/lang/IllegalArgumentException","bad fixture");return 0;}
        auto t=std::make_shared<FixtureTrack>(l);
        {
            std::lock_guard<std::mutex> lock(l->mutex);
            t->renderer=ass_renderer_init(l->ass);
            t->track=ass_new_track(l->ass);
            if(!t->renderer||!t->track){fail(env,"java/lang/OutOfMemoryError","ass renderer/track");return 0;}
            ass_set_storage_size(t->renderer,320,180);
            ass_set_frame_size(t->renderer,320,180);
            // In the embedded-font test no system font provider is enabled.
            // Optional config path is passed per renderer, never via setenv.
            int provider=l->config.empty()?ASS_FONTPROVIDER_NONE:ASS_FONTPROVIDER_FONTCONFIG;
            ass_set_fonts(t->renderer,nullptr,"DejaVu Sans",provider,l->config.empty()?nullptr:l->config.c_str(),1);
            ass_process_codec_private(t->track,header,sizeof(header)-1);
            std::string packet="0,0,Default,,0,0,0,,"+caption;
            ass_process_chunk(t->track,packet.data(),static_cast<int>(packet.size()),start,duration);
        }
        std::lock_guard<std::mutex> lock(handles_mutex);
        jlong handle=next_handle++;
        tracks.emplace(handle,std::move(t));return handle;
    });
}
extern "C" JNIEXPORT jlong JNICALL
Java_androidx_media3_exoplayer_libass_LibassLibraryProbe_renderFixture(JNIEnv *env,jclass,jlong id,jlong time) {
    return jni_long(env,[&]()->jlong{
        auto t=fixture(env,id);if(!t)return 0;
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        int changed=0;
        uint64_t hash=1469598103934665603ULL,pixels=0;
        for(ASS_Image *im=ass_render_frame(t->renderer,t->track,time,&changed);im;im=im->next){
            if(im->w<=0||im->h<=0)continue;
            for(int y=0;y<im->h;++y)for(int x=0;x<im->w;++x){
                unsigned char v=im->bitmap[static_cast<size_t>(y)*im->stride+x];
                if(v)++pixels;
                hash=(hash^v)*1099511628211ULL;
            }
            hash=(hash^static_cast<uint32_t>(im->dst_x))*1099511628211ULL;
            hash=(hash^static_cast<uint32_t>(im->dst_y))*1099511628211ULL;
        }
        return pixels?static_cast<jlong>((hash&0x7fffffffffffffffULL)|1ULL):0;
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassLibraryProbe_closeFixture(JNIEnv *env,jclass,jlong id) {
    jni_void(env,[&]{
        std::shared_ptr<FixtureTrack> retired;
        {std::lock_guard<std::mutex> lock(handles_mutex);
         auto it=tracks.find(id);if(it!=tracks.end()){retired=std::move(it->second);tracks.erase(it);}}
    });
}
extern "C" JNIEXPORT jint JNICALL
Java_androidx_media3_exoplayer_libass_LibassLibraryProbe_liveLibraries(JNIEnv *,jclass) {
    return live_libraries.load();
}

/* Isolated embedded-font track consumer. No Android font directory/global
 * configuration, viewport/style override, renderLast/partial or texture contract.
 * Reference: LibassTrackSession at dlgt7/media@3382803f (bfbbdf79...);
 * nativeProcessChunk's last parameter is a duration, despite its parameter name.
 * The historical official media3ass implementation is MIT; this code is new.
 */
namespace {
bool copy_slice(JNIEnv *env,jbyteArray data,jint off,jint len,std::vector<char>& bytes) {
    if(!data){fail(env,"java/lang/NullPointerException","subtitle data");return false;}
    jsize size=env->GetArrayLength(data);
    if(off<0||len<0||off>size||len>size-off){
        fail(env,"java/lang/IndexOutOfBoundsException","subtitle range");return false;
    }
    bytes.resize(static_cast<size_t>(len)+1);
    if(len)env->GetByteArrayRegion(data,off,len,reinterpret_cast<jbyte*>(bytes.data()));
    return !env->ExceptionCheck();
}
}
extern "C" JNIEXPORT jlong JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeCreate(JNIEnv *env,jclass,jlong id,jstring directory,jstring family) {
    return jni_long(env,[&]()->jlong{
        auto l=library(env,id);if(!l)return 0;
        auto dir=str(env,directory);if(env->ExceptionCheck())return 0;
        auto font=str(env,family);if(env->ExceptionCheck())return 0;
        // Do not mutate shared library font paths or pretend to implement
        // production Android font discovery in this embedded-font-only profile.
        if(!dir.empty()||!l->config.empty()){
            fail(env,"java/lang/UnsupportedOperationException","embedded-font track probe only");return 0;
        }
        auto t=std::make_shared<FixtureTrack>(l);
        {
            std::lock_guard<std::mutex> lock(l->mutex);
            t->renderer=ass_renderer_init(l->ass);
            t->track=ass_new_track(l->ass);
            if(!t->renderer||!t->track){fail(env,"java/lang/OutOfMemoryError","ass renderer/track");return 0;}
            ass_set_fonts(t->renderer,nullptr,font.empty()?"sans-serif":font.c_str(),ASS_FONTPROVIDER_NONE,nullptr,1);
        }
        std::lock_guard<std::mutex> lock(handles_mutex);
        // Recheck retirement during creation, before publishing the track.
        if(libraries.find(id)==libraries.end()){fail(env,"java/lang/IllegalStateException","library retired during create");return 0;}
        if(next_handle==std::numeric_limits<jlong>::max()){fail(env,"java/lang/IllegalStateException","handle space exhausted");return 0;}
        jlong handle=next_handle++;
        tracks.emplace(handle,std::move(t));
        return handle;
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeRelease(JNIEnv *env,jclass cls,jlong id) {
    Java_androidx_media3_exoplayer_libass_LibassLibraryProbe_closeFixture(env,cls,id);
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeProcessCodecPrivate(JNIEnv *env,jclass,jlong id,jbyteArray data,jint off,jint len) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        std::vector<char> bytes;if(!copy_slice(env,data,off,len,bytes))return;
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        if(len)ass_process_codec_private(t->track,bytes.data(),len);
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeProcessChunk(JNIEnv *env,jclass,jlong id,jbyteArray data,jint off,jint len,jlong start,jlong duration) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        if(start<0||duration<0||start>std::numeric_limits<jlong>::max()-duration){
            fail(env,"java/lang/IllegalArgumentException","unsupported timing range");return;
        }
        std::vector<char> bytes;if(!copy_slice(env,data,off,len,bytes))return;
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        if(len&&duration)ass_process_chunk(t->track,bytes.data(),len,start,duration);
    });
}
// Test-only viewport and CPU snapshot; deliberately NOT nativeRenderFrame.
// The new Java consumer's frame, GL textures, renderLast and allowPartial
// behavior cannot be inferred from libass alone. Copy row-by-row before the
// next render can invalidate ASS_Image storage, preserving raw RRGGBBAA
// (inverted alpha) as consumed by the reference LibassGlImage.
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassTrackProbe_setFixtureFrame(JNIEnv *env,jclass,jlong id) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        ass_set_storage_size(t->renderer,320,180);
        ass_set_frame_size(t->renderer,320,180);
    });
}
extern "C" JNIEXPORT jobjectArray JNICALL
Java_androidx_media3_exoplayer_libass_LibassTrackProbe_snapshot(JNIEnv *env,jclass,jlong id,jlong time) {
    jobjectArray result=nullptr;
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        int changed=0;
        ASS_Image *first=ass_render_frame(t->renderer,t->track,time,&changed);
        size_t total=0;jsize count=0;
        for(auto *im=first;im;im=im->next){
            if(im->w<=0||im->h<=0)continue;
            if(!im->bitmap||im->stride<im->w||im->w>std::numeric_limits<jint>::max()/im->h||
               count>=4096||static_cast<size_t>(im->w)*im->h>64U*1024*1024-total){
                fail(env,"java/lang/IllegalStateException","invalid or excessive libass image");return;
            }
            total+=static_cast<size_t>(im->w)*im->h;++count;
        }
        jclass cls=env->FindClass("androidx/media3/exoplayer/libass/LibassTrackProbe$Image");
        if(!cls)return;
        jmethodID ctor=env->GetMethodID(cls,"<init>","(IIIII[BI)V");
        if(!ctor){env->DeleteLocalRef(cls);return;}
        jobjectArray arr=env->NewObjectArray(count,cls,nullptr);
        if(!arr){env->DeleteLocalRef(cls);return;}
        jsize index=0;
        for(auto *im=first;im;im=im->next){
            if(im->w<=0||im->h<=0)continue;
            jbyteArray data=env->NewByteArray(im->w*im->h);
            if(!data)break;
            for(int row=0;row<im->h;++row){
                env->SetByteArrayRegion(data,row*im->w,im->w,
                    reinterpret_cast<const jbyte*>(im->bitmap+static_cast<size_t>(row)*im->stride));
                if(env->ExceptionCheck())break;
            }
            if(env->ExceptionCheck()){env->DeleteLocalRef(data);break;}
            jobject image=env->NewObject(cls,ctor,im->dst_x,im->dst_y,im->w,im->h,static_cast<jint>(im->color),data,0);
            env->DeleteLocalRef(data);
            if(!image)break;
            env->SetObjectArrayElement(arr,index++,image);
            env->DeleteLocalRef(image);
            if(env->ExceptionCheck())break;
        }
        env->DeleteLocalRef(cls);
        if(index!=count||env->ExceptionCheck()){
            env->DeleteLocalRef(arr);fail(env,"java/lang/IllegalStateException","incomplete image snapshot");return;
        }
        result=arr;
    });
    return result;
}

/* Three unchanged historical Media3 descriptors, with real pinned libass
 * calls. See FongMi/media@9dae39e, media3ass.c (MIT), and the reference
 * LibassTrackSession. Do not mix ass_process_data with ass_process_chunk
 * on one track: libass explicitly warns about duplicate checking.
 */
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeProcessData(JNIEnv *env,jclass,jlong id,jbyteArray data,jint off,jint len) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        std::vector<char> bytes;if(!copy_slice(env,data,off,len,bytes))return;
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        if(len)ass_process_data(t->track,bytes.data(),len);
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeSetStorageSize(JNIEnv *env,jclass,jlong id,jint w,jint h) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        // Match positive sizes in the Java consumer; reject silent reset due
        // to overflow in the actual pinned ass_set_storage_size.
        if(w<=0||h<=0||w>std::numeric_limits<int>::max()/h){
            fail(env,"java/lang/IllegalArgumentException","invalid storage size");return;
        }
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        ass_set_storage_size(t->renderer,w,h);
        t->reference_storage_w=w;t->reference_storage_h=h;
        t->reference_frame_dirty=true;
    });
}
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeSetCacheLimits(JNIEnv *env,jclass,jlong id,jint glyphs,jint mb) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        if(glyphs<0||mb<0||static_cast<size_t>(mb)>std::numeric_limits<size_t>::max()/(1024U*1024U)){
            fail(env,"java/lang/IllegalArgumentException","invalid cache limits");return;
        }
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        ass_set_cache_limits(t->renderer,glyphs,mb);
    });
}

/* Reference consumer subset: dlgt7/media@3382803f actual Java
 * LibassTrackSession, LibassFrame, LibassImage, LibassGlImage.
 * A full synchronous CPU frame is allowed when allowPartial is true.
 * Only renderLast=true (the actual caller's value) is implemented here.
 * No GPU texture creation or unknown fallback/partial semantics.
 * Geometry restricted to same-size storage/display, in-frame viewport.
 */
extern "C" JNIEXPORT void JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeSetFrameSize(
    JNIEnv *env,jclass,jlong id,jint w,jint h,jint left,jint top,jint right,jint bottom,jdouble par) {
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        if(w<=0||h<=0||w>std::numeric_limits<int>::max()/h||
           right<=left||bottom<=top||!std::isfinite(par)||par<0){
            fail(env,"java/lang/IllegalArgumentException","invalid reference frame geometry");return;
        }
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        // The reference playback caller may supply video dimensions but a
        // separately sized render surface; do not guess that transformation.
        if(w!=t->reference_storage_w||h!=t->reference_storage_h||
           left<0||top<0||right>w||bottom>h){
            fail(env,"java/lang/UnsupportedOperationException","same-size in-frame viewport probe only");return;
        }
        ass_set_frame_size(t->renderer,w,h);
        ass_set_margins(t->renderer,top,h-bottom,left,w-right);
        ass_set_use_margins(t->renderer,0);
        ass_set_pixel_aspect(t->renderer,par);
        t->reference_frame_w=w;t->reference_frame_h=h;
        t->reference_frame_ready=true;t->reference_frame_dirty=true;
    });
}

extern "C" JNIEXPORT jobject JNICALL
Java_androidx_media3_exoplayer_libass_LibassNative_nativeRenderFrame(
    JNIEnv *env,jclass,jlong id,jlong time,jboolean allow_partial,jboolean render_last) {
    jobject result=nullptr;
    jni_void(env,[&]{
        auto t=fixture(env,id);if(!t)return;
        if(!render_last){
            fail(env,"java/lang/UnsupportedOperationException","reference renderLast=false contract not established");return;
        }
        (void)allow_partial; // Permission, not a requirement: synchronous full render only.
        std::lock_guard<std::mutex> lock(t->lib->mutex);
        if(!t->reference_frame_ready||
           t->reference_frame_w!=t->reference_storage_w||
           t->reference_frame_h!=t->reference_storage_h){
            fail(env,"java/lang/IllegalStateException","reference geometry not ready");return;
        }
        // If copying/constructing fails after ass_render_frame changed its
        // previous-image state, the next successful frame must refresh Java.
        const bool force=t->reference_frame_dirty;
        t->reference_frame_dirty=true;
        int changed=0;
        ASS_Image *first=ass_render_frame(t->renderer,t->track,time,&changed);
        size_t total=0;jsize count=0;
        for(auto *im=first;im;im=im->next){
            if(im->w<=0||im->h<=0)continue;
            if(!im->bitmap||im->stride<im->w||im->w>std::numeric_limits<jint>::max()/im->h||
               count>=4096||static_cast<size_t>(im->w)*im->h>64U*1024*1024-total){
                fail(env,"java/lang/IllegalStateException","invalid or excessive reference image");return;
            }
            total+=static_cast<size_t>(im->w)*im->h;++count;
        }
        // Use the actual reference Java classes, not the former fixture DTO.
        jclass image_cls=env->FindClass("androidx/media3/exoplayer/libass/LibassImage");
        if(!image_cls)return;
        jmethodID image_ctor=env->GetMethodID(image_cls,"<init>","(IIIII[BI)V");
        if(!image_ctor){env->DeleteLocalRef(image_cls);return;}
        jobjectArray images=env->NewObjectArray(count,image_cls,nullptr);
        if(!images){env->DeleteLocalRef(image_cls);return;}
        jsize index=0;
        for(auto *im=first;im;im=im->next){
            if(im->w<=0||im->h<=0)continue;
            jbyteArray data=env->NewByteArray(im->w*im->h);
            if(!data)break;
            for(int row=0;row<im->h;++row){
                env->SetByteArrayRegion(data,row*im->w,im->w,
                    reinterpret_cast<const jbyte*>(im->bitmap+static_cast<size_t>(row)*im->stride));
                if(env->ExceptionCheck())break;
            }
            if(env->ExceptionCheck()){env->DeleteLocalRef(data);break;}
            jobject image=env->NewObject(image_cls,image_ctor,im->dst_x,im->dst_y,im->w,im->h,
                                          static_cast<jint>(im->color),data,0);
            env->DeleteLocalRef(data);
            if(!image)break;
            env->SetObjectArrayElement(images,index++,image);
            env->DeleteLocalRef(image);
            if(env->ExceptionCheck())break;
        }
        env->DeleteLocalRef(image_cls);
        if(index!=count||env->ExceptionCheck()){
            env->DeleteLocalRef(images);fail(env,"java/lang/IllegalStateException","incomplete reference frame");return;
        }
        jclass frame_cls=env->FindClass("androidx/media3/exoplayer/libass/LibassFrame");
        if(!frame_cls){env->DeleteLocalRef(images);return;}
        jmethodID ctor=env->GetMethodID(frame_cls,"<init>","(I[Landroidx/media3/exoplayer/libass/LibassImage;)V");
        if(ctor)result=env->NewObject(frame_cls,ctor,static_cast<jint>(force||changed!=0),images);
        env->DeleteLocalRef(images);env->DeleteLocalRef(frame_cls);
        if(result&&!env->ExceptionCheck())t->reference_frame_dirty=false;
    });
    return result;
}
