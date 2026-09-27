/* Minimal fake JNI table for executing the published Android JNI_OnLoad.
 * No ART claim: records RegisterNatives and constructor requests exactly.
 */
typedef unsigned int usize;
typedef int jint;
typedef long long jlong;
typedef void *ptr;
typedef struct { const char *name; const char *signature; ptr function; } Method;
extern int write(int,const void*,usize);
extern void _exit(int);
extern jint JNI_OnLoad(ptr,ptr);
static ptr env_table[234],vm_table[8];
static ptr *env=env_table,*vm=vm_table;
static Method *methods;static jint count;
static int failed,expected_exception;
static usize length(const char *s){usize n=0;while(s[n])n++;return n;}
static void out(const char *s){write(1,s,length(s));}
static int equal(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
static jint get_env(ptr ignored,ptr *result,jint version){(void)ignored;(void)version;*result=&env;return 0;}
static ptr find_class(ptr ignored,const char *name){(void)ignored;return (ptr)name;}
static ptr global(ptr ignored,ptr object){(void)ignored;return object;}
static void drop(ptr ignored,ptr object){(void)ignored;(void)object;}
static jint register_natives(ptr ignored,ptr klass,Method *m,jint n){
 (void)ignored;(void)klass;methods=m;count=n;
 for(jint i=0;i<n;i++){out("METHOD\t");out(m[i].name);out("\t");out(m[i].signature);out("\n");}
 return 0;
}
static ptr get_method(ptr ignored,ptr klass,const char *name,const char *sig){
 (void)ignored;out("CONSTRUCTOR\t");out((const char*)klass);out("\t");out(name);out("\t");out(sig);out("\n");return (ptr)1;
}
static unsigned char exception_check(ptr ignored){(void)ignored;return failed;}
static jint throw_new(ptr ignored,ptr klass,const char*message){(void)ignored;(void)klass;out(expected_exception ? "EXPECTED_THROW\t" : "THROW\t");out(message);out("\n");failed=1;return 0;}
static ptr fail_string(ptr ignored,ptr value,ptr copy){(void)ignored;(void)value;(void)copy;failed=1;return 0;}
static ptr method(const char *name){for(jint i=0;i<count;i++)if(equal(methods[i].name,name))return methods[i].function;return 0;}
void _start(void){
 env_table[6]=(ptr)find_class;env_table[14]=(ptr)throw_new;env_table[21]=(ptr)global;
 env_table[22]=(ptr)drop;env_table[23]=(ptr)drop;env_table[33]=(ptr)get_method;
 env_table[169]=(ptr)fail_string;env_table[215]=(ptr)register_natives;env_table[228]=(ptr)exception_check;vm_table[6]=(ptr)get_env;
 jint version=JNI_OnLoad(&vm,0);if(version!=0x10006||count!=17||failed)_exit(2);
 expected_exception=1;
 jlong rejected=((jlong(*)(ptr,ptr,jlong,ptr,ptr))method("nativeCreate"))(&env,0,0,0,0);
 if(rejected||!failed)_exit(6);
 expected_exception=0;failed=0;
 ((void(*)(ptr,ptr,jlong))method("nativeRelease"))(&env,0,0);
 ((void(*)(ptr,ptr,jlong))method("nativeReleaseLibrary"))(&env,0,0);
 // Null optional strings avoid invented Java objects; no font file/node access.
 jlong library=((jlong(*)(ptr,ptr,ptr))method("nativeCreateLibrary"))(&env,0,0);
 if(!library||failed)_exit(3);
 // Simulate failed JNI UTF acquisition after renderer/track allocation.
 rejected=((jlong(*)(ptr,ptr,jlong,ptr,ptr))method("nativeCreate"))(&env,0,library,(ptr)1,0);
 if(rejected||!failed)_exit(7);
 failed=0;out("EXPECTED_FAILURE\tfont string acquisition; same library remains usable\n");
 jlong track=((jlong(*)(ptr,ptr,jlong,ptr,ptr))method("nativeCreate"))(&env,0,library,0,0);
 if(!track||failed)_exit(4);
 ((void(*)(ptr,ptr,jlong,jint,jint))method("nativeSetCacheLimits"))(&env,0,track,4096,48);
 ((void(*)(ptr,ptr,jlong))method("nativeRelease"))(&env,0,track);
 ((void(*)(ptr,ptr,jlong))method("nativeReleaseLibrary"))(&env,0,library);
 if(failed)_exit(5);
 out("PASS\tcreate library -> create track -> cache limits -> release track -> release library\n");
 _exit(0);
}
