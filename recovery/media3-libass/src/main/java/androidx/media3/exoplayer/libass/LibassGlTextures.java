package androidx.media3.exoplayer.libass;

import android.opengl.GLES20;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/** Actual GLES2 backend, reconstructed from published libass.e/f and zk1.a/d.
 * Requires a current EGL context owned by this thread; it never creates or destroys that context.
 */
final class LibassGlTextures implements LibassFrameRenderer.Textures, AutoCloseable {
    private static final String VERTEX = "attribute vec2 aPosition;\nattribute vec2 aTexCoord;\n"
            + "varying vec2 vTexCoord;\nvoid main() {\n"
            + "gl_Position = vec4(aPosition, 0.0, 1.0);\nvTexCoord = aTexCoord;\n}\n";
    private static final String FRAGMENT = "precision mediump float;\nuniform sampler2D uTexture;\n"
            + "uniform vec4 uColor;\nvarying vec2 vTexCoord;\nvoid main() {\n"
            + "float coverage = texture2D(uTexture, vTexCoord).a;\n"
            + "gl_FragColor = vec4(uColor.rgb, uColor.a * coverage);\n}\n";

    private final Thread thread = Thread.currentThread();
    private final FloatBuffer positions = buffer(8);
    private final FloatBuffer coordinates = buffer(8);
    private int program;
    private int positionLocation, coordinateLocation, colorLocation;
    private boolean drawing;

    private static FloatBuffer buffer(int count) {
        return ByteBuffer.allocateDirect(count * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
    }

    LibassGlTextures() {
        coordinates.put(new float[]{0, 0, 1, 0, 0, 1, 1, 1}).position(0);
        int vertex = 0, fragment = 0, linked = 0;
        try {
            vertex = shader(GLES20.GL_VERTEX_SHADER, VERTEX);
            fragment = shader(GLES20.GL_FRAGMENT_SHADER, FRAGMENT);
            linked = GLES20.glCreateProgram();
            if (linked == 0) throw new IllegalStateException("Could not create libass shader program");
            GLES20.glAttachShader(linked, vertex);
            GLES20.glAttachShader(linked, fragment);
            GLES20.glLinkProgram(linked);
            int[] status = new int[1];
            GLES20.glGetProgramiv(linked, GLES20.GL_LINK_STATUS, status, 0);
            if (status[0] == 0) throw new IllegalStateException("Libass shader link: " + GLES20.glGetProgramInfoLog(linked));
            positionLocation = GLES20.glGetAttribLocation(linked, "aPosition");
            coordinateLocation = GLES20.glGetAttribLocation(linked, "aTexCoord");
            colorLocation = GLES20.glGetUniformLocation(linked, "uColor");
            if (positionLocation < 0 || coordinateLocation < 0 || colorLocation < 0)
                throw new IllegalStateException("Libass shader locations unavailable");
            checkError("initialize shaders");
            program = linked;
        } finally {
            if (vertex != 0) GLES20.glDeleteShader(vertex);
            if (fragment != 0) GLES20.glDeleteShader(fragment);
            if (program == 0 && linked != 0) GLES20.glDeleteProgram(linked);
        }
    }

    private static int shader(int kind, String source) {
        int shader = GLES20.glCreateShader(kind);
        if (shader == 0) throw new IllegalStateException("Could not create libass shader");
        try {
            GLES20.glShaderSource(shader, source);
            GLES20.glCompileShader(shader);
            int[] status = new int[1];
            GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, status, 0);
            if (status[0] == 0) throw new IllegalStateException("Libass shader compile: " + GLES20.glGetShaderInfoLog(shader));
            return shader;
        } catch (RuntimeException | Error failure) {
            GLES20.glDeleteShader(shader);
            throw failure;
        }
    }

    private void checkThread() {
        if (Thread.currentThread() != thread) throw new IllegalStateException("Wrong libass EGL thread");
    }

    private void checkOpen() {
        checkThread();
        if (program == 0) throw new IllegalStateException("Libass GL backend is closed");
    }

    private static void checkError(String operation) {
        int error = GLES20.glGetError();
        if (error != GLES20.GL_NO_ERROR) throw new IllegalStateException("Libass GL " + operation + ": " + error);
    }

    @Override public int upload(byte[] coverage, int width, int height) {
        checkOpen();
        if (width <= 0 || height <= 0 || coverage == null || (long) width * height != coverage.length)
            throw new IllegalArgumentException("Invalid libass coverage bitmap");
        // Allocate before creating the GL object so allocation failure cannot leak a texture.
        ByteBuffer pixels = ByteBuffer.allocateDirect(coverage.length);
        pixels.put(coverage).position(0);
        int[] texture = new int[1];
        boolean success = false;
        try {
            GLES20.glGenTextures(1, texture, 0);
            if (texture[0] == 0) throw new IllegalStateException("Libass texture creation failed");
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texture[0]);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
            GLES20.glPixelStorei(GLES20.GL_UNPACK_ALIGNMENT, 1);
            GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_ALPHA, width, height,
                    0, GLES20.GL_ALPHA, GLES20.GL_UNSIGNED_BYTE, pixels);
            checkError("upload coverage");
            success = true;
            return texture[0];
        } finally {
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, 0);
            if (!success && texture[0] != 0) GLES20.glDeleteTextures(1, texture, 0);
        }
    }

    @Override public void delete(int textureId) {
        checkOpen();
        if (textureId != 0) GLES20.glDeleteTextures(1, new int[]{textureId}, 0);
    }

    /** Clears the entire surface, including when a subtitle has disappeared. */
    void beginFrame(int surfaceWidth, int surfaceHeight) {
        checkOpen();
        if (surfaceWidth <= 0 || surfaceHeight <= 0) throw new IllegalArgumentException("Invalid surface size");
        if (drawing) throw new IllegalStateException("Libass frame already begun");
        GLES20.glViewport(0, 0, surfaceWidth, surfaceHeight);
        GLES20.glClearColor(0, 0, 0, 0);
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
        GLES20.glEnable(GLES20.GL_BLEND);
        GLES20.glBlendFuncSeparate(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA,
                GLES20.GL_ONE, GLES20.GL_ONE_MINUS_SRC_ALPHA);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glUseProgram(program);
        GLES20.glEnableVertexAttribArray(positionLocation);
        GLES20.glEnableVertexAttribArray(coordinateLocation);
        coordinates.position(0);
        GLES20.glVertexAttribPointer(coordinateLocation, 2, GLES20.GL_FLOAT, false, 0, coordinates);
        drawing = true;
    }

    @Override public void draw(LibassFrameRenderer.Image image, int frameWidth, int frameHeight) {
        checkOpen();
        if (!drawing) throw new IllegalStateException("Libass frame not begun");
        if (frameWidth <= 0 || frameHeight <= 0) throw new IllegalArgumentException("Invalid render size");
        float left = image.x * 2f / frameWidth - 1;
        float right = (image.x + (float) image.width) * 2 / frameWidth - 1;
        float top = 1 - image.y * 2f / frameHeight;
        float bottom = 1 - (image.y + (float) image.height) * 2 / frameHeight;
        positions.clear();
        positions.put(left).put(top).put(right).put(top).put(left).put(bottom).put(right).put(bottom);
        positions.position(0);
        GLES20.glVertexAttribPointer(positionLocation, 2, GLES20.GL_FLOAT, false, 0, positions);
        GLES20.glUniform4f(colorLocation, image.red, image.green, image.blue, image.alpha);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, image.textureId);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
    }

    void endFrame() {
        checkOpen();
        if (!drawing) return;
        drawing = false;
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, 0);
        GLES20.glDisableVertexAttribArray(positionLocation);
        GLES20.glDisableVertexAttribArray(coordinateLocation);
        checkError("draw");
    }

    @Override public void close() {
        checkThread();
        if (program == 0) return;
        try { endFrame(); }
        finally {
            int released = program; program = 0;
            GLES20.glDeleteProgram(released);
        }
    }
}
