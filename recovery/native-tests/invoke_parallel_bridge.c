/* Published gomobile Invoke concurrency harness. ARMv7 + API24 Bionic.
 * Each input group: uint32 count, then count (uint32 length, UTF-8 request).
 * All threads enter Invoke after one pthread barrier; output is in input order:
 * uint32 count, then count (uint32 byte length, UTF-16LE response), on FD 3.
 * No sleep, runtime hooks, binary patching, or assumed completion ordering.
 */
typedef __SIZE_TYPE__ size_t;
typedef struct { void *ptr; int len; } nstring;
typedef unsigned long pthread_t;
extern void *malloc(size_t);
extern void free(void *);
extern int read(int, void *, size_t);
extern int write(int, const void *, size_t);
extern int *__errno(void);
extern void _exit(int);
extern int pthread_create(pthread_t *, const void *, void *(*)(void *), void *);
extern int pthread_join(pthread_t, void **);
extern int pthread_barrier_init(void *, const void *, unsigned);
extern int pthread_barrier_wait(void *);
extern int pthread_barrier_destroy(void *);
extern nstring proxylibXray__Invoke(nstring);

static union { unsigned long long align; char storage[128]; } barrier;
typedef struct { nstring input, output; pthread_t thread; } invocation;

static int transfer(int fd, void *buf, unsigned size, int output) {
    unsigned done = 0;
    while (done < size) {
        int n = output ? write(fd, (char *)buf + done, size - done)
                       : read(fd, (char *)buf + done, size - done);
        if (n < 0 && *__errno() == 4) continue;
        if (n <= 0) return done == 0 && n == 0 ? 0 : -1;
        done += (unsigned)n;
    }
    return 1;
}

static void *invoke(void *arg) {
    invocation *call = arg;
    pthread_barrier_wait(&barrier);
    call->output = proxylibXray__Invoke(call->input);
    return 0;
}

void _start(void) {
    for (;;) {
        unsigned count;
        int status = transfer(0, &count, 4, 0);
        if (status == 0) _exit(0);
        if (status != 1 || !count || count > 8) _exit(20);
        invocation calls[8];
        if (pthread_barrier_init(&barrier, 0, count + 1)) _exit(21);
        for (unsigned i = 0; i < count; ++i) {
            unsigned length;
            if (transfer(0, &length, 4, 0) != 1 || length > 16 * 1024 * 1024) _exit(22);
            calls[i].input.ptr = malloc(length ? length : 1);
            calls[i].input.len = (int)length;
            if (!calls[i].input.ptr || transfer(0, calls[i].input.ptr, length, 0) != 1) _exit(23);
            if (pthread_create(&calls[i].thread, 0, invoke, &calls[i])) _exit(24);
        }
        pthread_barrier_wait(&barrier);
        for (unsigned i = 0; i < count; ++i)
            if (pthread_join(calls[i].thread, 0)) _exit(25);
        pthread_barrier_destroy(&barrier);
        if (transfer(3, &count, 4, 1) != 1) _exit(26);
        for (unsigned i = 0; i < count; ++i) {
            unsigned length = (unsigned)calls[i].output.len;
            if (calls[i].output.len < 0 || (length & 1)) _exit(27);
            if (transfer(3, &length, 4, 1) != 1 || transfer(3, calls[i].output.ptr, length, 1) != 1) _exit(28);
            free(calls[i].output.ptr);
        }
    }
}
