package android.opengl;

import java.nio.*;
import java.util.*;

/** Test-only recording API. Production compilation separately uses the real Android API jar. */
public final class GLES20 {
    public static final int GL_VERTEX_SHADER=35633, GL_FRAGMENT_SHADER=35632,
        GL_LINK_STATUS=35714, GL_COMPILE_STATUS=35713, GL_NO_ERROR=0,
        GL_TEXTURE_2D=3553, GL_TEXTURE_MIN_FILTER=10241, GL_TEXTURE_MAG_FILTER=10240,
        GL_TEXTURE_WRAP_S=10242, GL_TEXTURE_WRAP_T=10243, GL_LINEAR=9729,
        GL_CLAMP_TO_EDGE=33071, GL_UNPACK_ALIGNMENT=3317, GL_ALPHA=6406,
        GL_UNSIGNED_BYTE=5121, GL_COLOR_BUFFER_BIT=16384, GL_BLEND=3042,
        GL_SRC_ALPHA=770, GL_ONE_MINUS_SRC_ALPHA=771, GL_ONE=1, GL_TEXTURE0=33984,
        GL_FLOAT=5126, GL_TRIANGLE_STRIP=5;
    public static final Set<Integer> shaders=new HashSet<>(),programs=new HashSet<>(),textures=new HashSet<>();
    public static final List<float[]> positions=new ArrayList<>(),colors=new ArrayList<>();
    public static final List<Integer> draws=new ArrayList<>();
    public static final Map<Integer,Integer> parameters=new HashMap<>();
    public static final Map<Integer,String> sources=new HashMap<>();
    public static int next,shaderCount,failShader,failLink,uploadError,error,bound,current,alignment,clears,deletedTextures;
    public static byte[] uploaded;public static int[] blend,viewport;public static float[] clearColor;
    public static void reset(){shaders.clear();programs.clear();textures.clear();positions.clear();colors.clear();draws.clear();parameters.clear();sources.clear();next=shaderCount=failShader=failLink=uploadError=error=bound=current=alignment=clears=deletedTextures=0;uploaded=null;}
    static void check(boolean ok){if(!ok)throw new AssertionError("Invalid GL ownership/order");}
    public static int glCreateShader(int kind){int id=++next;shaders.add(id);shaderCount++;return id;}
    public static void glShaderSource(int shader,String source){check(shaders.contains(shader));sources.put(shader,source);}
    public static void glCompileShader(int shader){check(shaders.contains(shader));}
    public static void glGetShaderiv(int shader,int name,int[] values,int offset){check(shaders.contains(shader)&&name==GL_COMPILE_STATUS);values[offset]=shaderCount==failShader?0:1;}
    public static String glGetShaderInfoLog(int shader){return "synthetic compiler failure";}
    public static void glDeleteShader(int shader){check(shaders.remove(shader));}
    public static int glCreateProgram(){int id=++next;programs.add(id);return id;}
    public static void glAttachShader(int p,int s){check(programs.contains(p)&&shaders.contains(s));}
    public static void glLinkProgram(int p){check(programs.contains(p));}
    public static void glGetProgramiv(int p,int name,int[] values,int offset){check(programs.contains(p)&&name==GL_LINK_STATUS);values[offset]=failLink==0?1:0;}
    public static String glGetProgramInfoLog(int p){return "synthetic linker failure";}
    public static void glDeleteProgram(int p){check(programs.remove(p));}
    public static int glGetAttribLocation(int p,String name){check(programs.contains(p));return name.equals("aPosition")?0:1;}
    public static int glGetUniformLocation(int p,String name){check(programs.contains(p));return 2;}
    public static int glGetError(){int e=error;error=0;return e;}
    public static void glGenTextures(int count,int[] ids,int offset){for(int i=0;i<count;i++){ids[offset+i]=++next;textures.add(next);}}
    public static void glBindTexture(int target,int id){check(target==GL_TEXTURE_2D&&(id==0||textures.contains(id)));bound=id;}
    public static void glTexParameteri(int target,int name,int value){check(bound!=0&&target==GL_TEXTURE_2D);parameters.put(name,value);}
    public static void glPixelStorei(int name,int value){check(name==GL_UNPACK_ALIGNMENT);alignment=value;}
    public static void glTexImage2D(int target,int level,int internal,int width,int height,int border,int format,int type,Buffer pixels){
        check(bound!=0&&target==GL_TEXTURE_2D&&level==0&&border==0&&internal==GL_ALPHA&&format==GL_ALPHA&&type==GL_UNSIGNED_BYTE&&pixels.isDirect());
        uploaded=new byte[width*height];((ByteBuffer)pixels).get(uploaded);error=uploadError;
    }
    public static void glDeleteTextures(int count,int[] ids,int offset){for(int i=0;i<count;i++){check(textures.remove(ids[offset+i]));deletedTextures++;}}
    public static void glViewport(int x,int y,int w,int h){viewport=new int[]{x,y,w,h};}
    public static void glClearColor(float r,float g,float b,float a){clearColor=new float[]{r,g,b,a};}
    public static void glClear(int mask){check(mask==GL_COLOR_BUFFER_BIT);clears++;}
    public static void glEnable(int capability){check(capability==GL_BLEND);}
    public static void glBlendFuncSeparate(int a,int b,int c,int d){blend=new int[]{a,b,c,d};}
    public static void glActiveTexture(int texture){check(texture==GL_TEXTURE0);}
    public static void glUseProgram(int p){check(programs.contains(p));current=p;}
    public static void glEnableVertexAttribArray(int location){}
    public static void glDisableVertexAttribArray(int location){}
    public static void glVertexAttribPointer(int location,int size,int type,boolean normalized,int stride,Buffer data){
        check(size==2&&type==GL_FLOAT&&!normalized&&stride==0&&data.isDirect());
        if(location==0){float[] f=new float[8];((FloatBuffer)data).duplicate().get(f);positions.add(f);}
    }
    public static void glUniform4f(int location,float r,float g,float b,float a){check(location==2);colors.add(new float[]{r,g,b,a});}
    public static void glDrawArrays(int mode,int first,int count){check(programs.contains(current)&&textures.contains(bound)&&mode==GL_TRIANGLE_STRIP&&first==0&&count==4);draws.add(bound);}
}
