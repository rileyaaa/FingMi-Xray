/* Calls the shipped gomobile C bridge, not a reconstructed converter.
 * Input: uint32 little-endian byte length + UTF-8 JSON, repeated until EOF.
 * FD 3 output: uint32 little-endian byte length + UTF-16LE response.
 * Android gomobile init redirects stdout/stderr to logcat; never use FD 1.
 * decodeString owns/frees the malloc-backed input; caller frees the result.
 * This freestanding ARMv7 entry is for QEMU + Android Bionic conversion tests.
 * It is NOT an Android app lifecycle or network/certificate-probe harness.
 */
typedef __SIZE_TYPE__ size_t;
typedef struct { void *ptr; int len; } nstring;
extern void *malloc(size_t);
extern void free(void *);
extern int read(int, void *, size_t);
extern int write(int, const void *, size_t);
extern int *__errno(void);
extern void _exit(int);
extern nstring proxylibXray__Invoke(nstring);

static int transfer(int fd, void *buf, unsigned int size, int output) {
    unsigned int done = 0;
    while (done < size) {
        int n = output ? write(fd, (char *)buf + done, size - done)
                       : read(fd, (char *)buf + done, size - done);
        if (n < 0 && *__errno() == 4) continue; /* EINTR */
        if (n <= 0) return done == 0 && n == 0 ? 0 : -1;
        done += (unsigned int)n;
    }
    return 1;
}

void _start(void) {
    for (;;) {
        unsigned int length;
        int status = transfer(0, &length, 4, 0);
        if (status == 0) _exit(0);
        if (status < 0 || length > 16 * 1024 * 1024) _exit(20);
        void *input = malloc(length ? length : 1);
        if (!input) _exit(21);
        if (length && transfer(0, input, length, 0) != 1) _exit(22);
        nstring result = proxylibXray__Invoke((nstring){input, (int)length});
        if (result.len < 0 || (result.len & 1)) _exit(23);
        length = (unsigned int)result.len;
        if (transfer(3, &length, 4, 1) != 1) _exit(24);
        if (length && transfer(3, result.ptr, length, 1) != 1) _exit(25);
        free(result.ptr);
    }
}
