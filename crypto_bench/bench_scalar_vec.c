/*
 * bench_scalar_vec.c — scalar–vector scaling microbench for CPQ-V2X paper
 *
 * Measures:
 *   T_SV_mul: y = c * x mod q
 *   T_SV_acc: y = y + c * x mod q
 *
 * Build (WSL/Linux):
 *   cc -O3 -march=native -DNDEBUG -std=c11 -D_POSIX_C_SOURCE=200809L \
 *      bench_scalar_vec.c -o bench_scalar_vec -lm
 *
 * Run:
 *   ./bench_scalar_vec --iters 200000 --reps 15 --d 512 --q 3329
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

static inline uint64_t now_ns(void) {
    struct timespec ts;

#if defined(CLOCK_MONOTONIC_RAW)
    const clockid_t cid = CLOCK_MONOTONIC_RAW;
#else
    const clockid_t cid = CLOCK_MONOTONIC;
#endif

    if (clock_gettime(cid, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static volatile uint64_t sink = 0;

typedef struct { double mean, std, min, max; } stats_t;

static stats_t compute_stats(const double *x, int n) {
    stats_t s;
    s.min = x[0]; s.max = x[0];
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        if (x[i] < s.min) s.min = x[i];
        if (x[i] > s.max) s.max = x[i];
        sum += x[i];
    }
    s.mean = sum / n;

    double var = 0.0;
    for (int i = 0; i < n; i++) {
        double d = x[i] - s.mean;
        var += d * d;
    }
    s.std = (n > 1) ? sqrt(var / (n - 1)) : 0.0;
    return s;
}

static void print_stats(const char *name, const double *samples, int reps) {
    stats_t s = compute_stats(samples, reps);
    printf("%-28s mean=%9.2f ns  std=%7.2f  min=%9.2f  max=%9.2f\n",
           name, s.mean, s.std, s.min, s.max);
}

static void usage(const char *argv0) {
    printf("Usage: %s [--iters N] [--reps R] [--d D] [--q Q]\n", argv0);
}

/* y = c*x mod q */
static inline void sv_mul(uint16_t *y, const uint16_t *x, uint16_t c, size_t d, uint16_t q) {
    for (size_t i = 0; i < d; i++) {
        y[i] = (uint16_t)(((uint32_t)c * (uint32_t)x[i]) % q);
    }
}

/* y = y + c*x mod q */
static inline void sv_acc(uint16_t *y, const uint16_t *x, uint16_t c, size_t d, uint16_t q) {
    for (size_t i = 0; i < d; i++) {
        uint32_t t = (uint32_t)y[i] + (uint32_t)c * (uint32_t)x[i];
        y[i] = (uint16_t)(t % q);
    }
}

static double meas_sv_mul(int iters, size_t d, uint16_t q) {
    uint16_t *x = (uint16_t*)malloc(d * sizeof(uint16_t));
    uint16_t *y = (uint16_t*)malloc(d * sizeof(uint16_t));
    if (!x || !y) { free(x); free(y); return -1.0; }

    for (size_t i = 0; i < d; i++) {
        x[i] = (uint16_t)((i * 7 + 11) % q);
        y[i] = (uint16_t)(i % q);
    }
    uint16_t c = (uint16_t)(1234 % q);

    for (int i = 0; i < 400; i++) {
        sv_mul(y, x, c, d, q);
        sink ^= y[(size_t)i % d];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        sv_mul(y, x, c, d, q);
        sink ^= y[(size_t)i % d];
    }
    uint64_t t1 = now_ns();

    free(x); free(y);
    return (t1 > t0) ? (double)(t1 - t0) / iters : -1.0;
}

static double meas_sv_acc(int iters, size_t d, uint16_t q) {
    uint16_t *x = (uint16_t*)malloc(d * sizeof(uint16_t));
    uint16_t *y = (uint16_t*)malloc(d * sizeof(uint16_t));
    if (!x || !y) { free(x); free(y); return -1.0; }

    for (size_t i = 0; i < d; i++) {
        x[i] = (uint16_t)((i * 5 + 19) % q);
        y[i] = (uint16_t)((i * 3 + 7) % q);
    }
    uint16_t c = (uint16_t)(2345 % q);

    for (int i = 0; i < 400; i++) {
        sv_acc(y, x, c, d, q);
        sink ^= y[(size_t)i % d];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        sv_acc(y, x, c, d, q);
        sink ^= y[(size_t)i % d];
    }
    uint64_t t1 = now_ns();

    free(x); free(y);
    return (t1 > t0) ? (double)(t1 - t0) / iters : -1.0;
}

int main(int argc, char **argv) {
    int iters = 200000;
    int reps  = 15;
    size_t d = 512;
    uint16_t q = 3329;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--iters") && i + 1 < argc) iters = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--reps") && i + 1 < argc) reps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--d") && i + 1 < argc) d = (size_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--q") && i + 1 < argc) q = (uint16_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--help")) { usage(argv[0]); return 0; }
        else { printf("Unknown arg: %s\n", argv[i]); usage(argv[0]); return 1; }
    }
    if (reps < 3) reps = 3;

    double *s_mul = (double*)malloc(sizeof(double) * reps);
    double *s_acc = (double*)malloc(sizeof(double) * reps);
    if (!s_mul || !s_acc) { fprintf(stderr, "malloc failed\n"); return 1; }

    for (int r = 0; r < reps; r++) {
        s_mul[r] = meas_sv_mul(iters, d, q);
        s_acc[r] = meas_sv_acc(iters, d, q);
    }

    printf("Config: iters=%d reps=%d d=%zu q=%u\n\n", iters, reps, d, q);
    print_stats("T_SV_mul (y=c*x)", s_mul, reps);
    print_stats("T_SV_acc (y+=c*x)", s_acc, reps);

    printf("\n(sink=%llu)\n", (unsigned long long)sink);

    free(s_mul);
    free(s_acc);
    return 0;
}
