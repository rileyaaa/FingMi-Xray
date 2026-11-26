#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Original Peerless source remains at its fixed MIT-licensed revision.
"""Only the isolated Peerless ALPHA_8 copy candidate; no media input."""
import hashlib
import subprocess
import tempfile
from pathlib import Path

PIN = "c6913278e244c87e4abe30ebcf633d681284fa97"
INCLUDES = "#include <stdint.h>\n#include <stddef.h>\n#include <string.h>\n"
HELPER = r'''
/* Copy only valid pixels. libass does not promise trailing row padding. */
static int alpha8_span(size_t w, size_t h, size_t stride, size_t *span) {
    if (!span || !w || !h || stride < w ||
        h - 1 > (SIZE_MAX - w) / stride) return 0;
    *span = (h - 1) * stride + w;
    return 1;
}

static int alpha8_copy(void *dst, size_t dst_size, size_t dst_stride,
                       const void *src, size_t src_size, size_t src_stride,
                       size_t w, size_t h) {
    size_t src_span, dst_span;
    if (!dst || !src || !alpha8_span(w, h, src_stride, &src_span) ||
        !alpha8_span(w, h, dst_stride, &dst_span) ||
        src_span > src_size || dst_span > dst_size) return 0;
    for (size_t y = 0; y < h; ++y)
        memcpy((unsigned char *)dst + y * dst_stride,
               (const unsigned char *)src + y * src_stride, w);
    return 1;
}
'''
START = "jobject createAlphaBitmap(JNIEnv* env, const ASS_Image* image) {"
END = "jint createTexture(JNIEnv* env, const ASS_Image* image) {"
FUNCTION = r'''jobject createAlphaBitmap(JNIEnv* env, const ASS_Image* image) {
    size_t src_span, dst_span;
    if (!image || !image->bitmap || image->w <= 0 || image->h <= 0 ||
        image->stride <= 0 ||
        !alpha8_span((size_t)image->w, (size_t)image->h,
                     (size_t)image->stride, &src_span)) return NULL;

    jclass bitmapConfigClass = (*env)->FindClass(env, "android/graphics/Bitmap$Config");
    jfieldID alpha8FieldId = (*env)->GetStaticFieldID(env, bitmapConfigClass, "ALPHA_8", "Landroid/graphics/Bitmap$Config;");
    jobject alpha8 = (*env)->GetStaticObjectField(env, bitmapConfigClass, alpha8FieldId);
    jclass bitmapClass = (*env)->FindClass(env, "android/graphics/Bitmap");
    jmethodID createBitmapMethodID = (*env)->GetStaticMethodID(env, bitmapClass,
        "createBitmap", "(IILandroid/graphics/Bitmap$Config;)Landroid/graphics/Bitmap;");
    jobject bitmap = (*env)->CallStaticObjectMethod(env, bitmapClass,
        createBitmapMethodID, image->w, image->h, alpha8);
    if (!bitmap || (*env)->ExceptionCheck(env)) return NULL;

    AndroidBitmapInfo info;
    if (AndroidBitmap_getInfo(env, bitmap, &info) != ANDROID_BITMAP_RESULT_SUCCESS ||
        info.format != ANDROID_BITMAP_FORMAT_A_8 ||
        info.width != (uint32_t)image->w || info.height != (uint32_t)image->h ||
        !alpha8_span(info.width, info.height, info.stride, &dst_span)) return NULL;

    void *bitmapPixels = NULL;
    if (AndroidBitmap_lockPixels(env, bitmap, &bitmapPixels) != ANDROID_BITMAP_RESULT_SUCCESS)
        return NULL;
    int copied = alpha8_copy(bitmapPixels, dst_span, info.stride,
        image->bitmap, src_span, (size_t)image->stride, info.width, info.height);
    int unlocked = AndroidBitmap_unlockPixels(env, bitmap);
    return copied && unlocked == ANDROID_BITMAP_RESULT_SUCCESS ? bitmap : NULL;
}

'''


def patched_source(raw):
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != PIN:
        raise ValueError("Peerless C pin mismatch")
    text = raw.decode("utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("ALPHA_8 function anchors changed")
    first, last = text.index(START), text.index(END)
    if last <= first:
        raise ValueError("ALPHA_8 function order changed")
    prefix = text[:first]
    if prefix.count("#include <string.h>\n") != 1:
        raise ValueError("include anchor changed")
    prefix = prefix.replace("#include <string.h>\n", INCLUDES, 1)
    return (prefix + HELPER + FUNCTION + text[last:]).encode("utf-8")


def stage_alpha8(source, target):
    if source.resolve() == target.resolve():
        raise ValueError("original source must remain untouched")
    data = patched_source(source.read_bytes())
    with target.open("xb") as out:
        out.write(data)
    return hashlib.sha256(data).hexdigest()


TEST = r'''
#include <assert.h>
#include <stdio.h>
static void normal(size_t ss, size_t ds) {
    unsigned char src[32], dst[32];
    memset(src, 0x11, sizeof(src));
    memset(dst, 0xA5, sizeof(dst));
    for (size_t y = 0; y < 3; ++y)
        for (size_t x = 0; x < 4; ++x) src[y * ss + x] = (unsigned char)(1 + y * 4 + x);
    assert(alpha8_copy(dst, sizeof(dst), ds, src, sizeof(src), ss, 4, 3));
    for (size_t y = 0; y < 3; ++y) {
        assert(!memcmp(dst + y * ds, src + y * ss, 4));
        for (size_t x = 4; x < ds; ++x) assert(dst[y * ds + x] == 0xA5);
    }
    for (size_t i = 3 * ds; i < sizeof(dst); ++i) assert(dst[i] == 0xA5);
}
int main(void) {
    normal(4, 4); puts("PASS tight rows");
    normal(8, 8); puts("PASS equal padded strides");
    normal(8, 6); normal(6, 8); puts("PASS different strides both directions");
    unsigned char src[16] = {1, 2, 3, 4}, dst[16], before[16];
    memset(dst, 0xA5, sizeof(dst)); memcpy(before, dst, sizeof(dst));
    assert(alpha8_copy(dst, sizeof(dst), 8, src, sizeof(src), 8, 4, 1));
    assert(!memcmp(dst, src, 4)); assert(!memcmp(dst + 4, before + 4, 12));
    puts("PASS one row");
    memcpy(dst, before, sizeof(dst));
    assert(!alpha8_copy(dst, sizeof(dst), 4, src, sizeof(src), 4, 0, 1));
    assert(!alpha8_copy(dst, sizeof(dst), 4, src, sizeof(src), 4, 4, 0));
    assert(!alpha8_copy(dst, sizeof(dst), 4, NULL, 0, 4, 4, 1));
    assert(!alpha8_copy(NULL, 0, 4, src, sizeof(src), 4, 4, 1));
    assert(!memcmp(dst, before, sizeof(dst))); puts("PASS empty and null rejected");
    assert(!alpha8_copy(dst, sizeof(dst), 3, src, sizeof(src), 4, 4, 1));
    assert(!alpha8_copy(dst, sizeof(dst), 4, src, sizeof(src), 3, 4, 1));
    assert(!alpha8_copy(dst, 3, 4, src, sizeof(src), 4, 4, 1));
    assert(!alpha8_copy(dst, sizeof(dst), 4, src, 3, 4, 4, 1));
    assert(!memcmp(dst, before, sizeof(dst))); puts("PASS invalid stride and short bounds rejected");
    size_t span;
    assert(!alpha8_span(2, SIZE_MAX, 2, &span));
    assert(!alpha8_span(2, 2, SIZE_MAX, &span));
    assert(!alpha8_copy(dst, sizeof(dst), 4, src, sizeof(src), SIZE_MAX, 2, 2));
    assert(!alpha8_copy(dst, sizeof(dst), SIZE_MAX, src, sizeof(src), 4, 2, 2));
    assert(!memcmp(dst, before, sizeof(dst))); puts("PASS overflow rejected before access");
    return 0;
}
'''


def self_test():
    with tempfile.TemporaryDirectory(prefix="peerless-alpha8-") as tmp:
        source = Path(tmp) / "rows.c"
        binary = Path(tmp) / "rows"
        source.write_text(INCLUDES + HELPER + TEST, encoding="utf-8")
        subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-O1", "-g", "-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all", str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS_PEERLESS_ALPHA8_HOST_ONLY")


if __name__ == "__main__":
    self_test()
