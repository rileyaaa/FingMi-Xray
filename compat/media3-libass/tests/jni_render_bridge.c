/* Published Android render probe with bounded fake JNI objects, not ART or an EGL test. */
#define _start lifecycle_start
#include "jni_load_bridge.c"
#undef _start
typedef __builtin_va_list va_list;
#define va_start __builtin_va_start
#define va_arg __builtin_va_arg
#define va_end __builtin_va_end
extern void *calloc(usize,usize);
extern void *memcpy(void*,const void*,usize);
extern int snprintf(char*,usize,const char*,...);
typedef struct { int size; unsigned char *data; } Bytes;
typedef struct { int size; ptr *data; } Objects;
typedef struct { int x,y,w,h,color;Bytes *bitmap;int texture; } Image;
typedef struct { int changed;Objects *images; } Frame;
static ptr get_string(ptr e,ptr str,ptr copy){(void)e;(void)copy;return str;}
static void release_string(ptr e,ptr str,ptr chars){(void)e;(void)str;(void)chars;}
static jint array_length(ptr e,Bytes *b){(void)e;return b->size;}
static ptr bytes(ptr e,jint size){(void)e;Bytes*b=calloc(1,sizeof(Bytes));b->size=size;b->data=calloc(size?size:1,1);return b;}
static ptr elements(ptr e,Bytes*b,ptr copy){(void)e;(void)copy;return b->data;}
static void release_elements(ptr e,Bytes*b,ptr data,jint mode){(void)e;(void)b;(void)data;(void)mode;}
static void byte_region(ptr e,Bytes*b,jint start,jint size,const void*data){(void)e;if(start<0||size<0||start>b->size-size)_exit(11);memcpy(b->data+start,data,size);}
static ptr objects(ptr e,jint size,ptr klass,ptr initial){(void)e;(void)klass;(void)initial;Objects*a=calloc(1,sizeof(Objects));a->size=size;a->data=calloc(size?size:1,sizeof(ptr));return a;}
static void object_region(ptr e,Objects*a,jint index,ptr obj){(void)e;if(index<0||index>=a->size)_exit(12);a->data[index]=obj;}
static ptr new_object(ptr e,ptr klass,ptr ctor,...){
 (void)e;(void)ctor;va_list a;va_start(a,ctor);
 if(equal((const char*)klass,"androidx/media3/exoplayer/libass/LibassFrame")){
  Frame*f=calloc(1,sizeof(Frame));f->changed=va_arg(a,int);f->images=va_arg(a,Objects*);va_end(a);return f;
 }
 Image*i=calloc(1,sizeof(Image));i->x=va_arg(a,int);i->y=va_arg(a,int);i->w=va_arg(a,int);i->h=va_arg(a,int);i->color=va_arg(a,int);i->bitmap=va_arg(a,Bytes*);i->texture=va_arg(a,int);va_end(a);return i;
}
static void render(jlong track,const char*id,jlong ms,jint force,jint gpu){
 Frame*f=((ptr(*)(ptr,ptr,jlong,jlong,jint,jint))method("nativeRenderFrame"))(&env,0,track,ms,force,gpu);
 if(failed||!f)_exit(13);char b[512];
 snprintf(b,sizeof(b),"FRAME\t{\"id\":\"%s\",\"changed\":%d,\"images\":[",id,f->changed);out(b);
 if(f->images)for(int k=0;k<f->images->size;k++){
  Image*i=f->images->data[k];unsigned int hash=2166136261u;
  if(i->bitmap)for(int j=0;j<i->bitmap->size;j++){hash^=i->bitmap->data[j];hash*=16777619u;}
  snprintf(b,sizeof(b),"%s{\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,\"color\":%u,\"bytes\":%d,\"fnv1a\":%u,\"textureId\":%d}",k?",":"",i->x,i->y,i->w,i->h,(unsigned int)i->color,i->bitmap?i->bitmap->size:0,hash,i->texture);out(b);
 }
 out("]}\n");
}
static const char sample[]=
 "[Script Info]\nScriptType: v4.00+\nPlayResX: 640\nPlayResY: 360\n"
 "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
 "Style: Default,DejaVu Sans,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,20,1\n"
 "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
 "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Synthetic subtitle\n";
void _start(void){
 setup_jni();env_table[169]=(ptr)get_string;env_table[170]=(ptr)release_string;
 env_table[171]=(ptr)array_length;env_table[172]=(ptr)objects;env_table[174]=(ptr)object_region;
 env_table[176]=(ptr)bytes;env_table[184]=(ptr)elements;env_table[192]=(ptr)release_elements;
 env_table[208]=(ptr)byte_region;env_table[28]=(ptr)new_object;
 if(JNI_OnLoad(&vm,0)!=0x10006||failed)_exit(2);
 jlong lib=((jlong(*)(ptr,ptr,ptr))method("nativeCreateLibrary"))(&env,0,0);
 jlong track=((jlong(*)(ptr,ptr,jlong,ptr,ptr))method("nativeCreate"))(&env,0,lib,(ptr)FONT_CONFIG,(ptr)"DejaVu Sans");
 if(!track||failed)_exit(3);
 ((void(*)(ptr,ptr,jlong,jint,jint,jint,jint,jint,jint))method("nativeSetFrameSize"))(&env,0,track,640,360,0,0,640,360);
 ((void(*)(ptr,ptr,jlong,jint,jint))method("nativeSetStorageSize"))(&env,0,track,640,360);
 Bytes data={(int)sizeof(sample)-1,(unsigned char*)sample};
 ((void(*)(ptr,ptr,jlong,Bytes*,jint,jint))method("nativeProcessData"))(&env,0,track,&data,0,data.size);
 render(track,"first-cpu",1000,0,0);render(track,"unchanged",1000,0,0);
 render(track,"forced-cpu",1000,1,0);render(track,"gpu-request-without-context",1000,1,1);
 ((void(*)(ptr,ptr,jlong,float,jint))method("nativeSetFontScale"))(&env,0,track,1.5f,1);
 render(track,"scaled",1000,0,0);
 ((void(*)(ptr,ptr,jlong,float))method("nativeSetBottomPositionFraction"))(&env,0,track,0.5f);
 render(track,"positioned",1000,0,0);
 render(track,"after-event",6000,0,0);render(track,"after-event-unchanged",6000,0,0);
 ((void(*)(ptr,ptr,jlong))method("nativeRelease"))(&env,0,track);
 ((void(*)(ptr,ptr,jlong))method("nativeReleaseLibrary"))(&env,0,lib);
 _exit(failed?4:0);
}
