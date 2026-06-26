/*
 * bench_sv_small.c -- Microbenchmark for small-coefficient scalar multiplication (T_SV_small).
 * The setup is aligned with the PQClean-based benchmark environment used in this package.
 */

#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

// ML-KEM-512-style dimension and modulus used in the benchmark.
#define N 256
#define Q 3329

// ---------------- timing ----------------
static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static volatile uint64_t sink = 0;

// ------------- core kernel: small-coefficient optimization (T_SV_small) -------------
// Models the linear-combination step used in RSU-side batch verification: res = c * v.
void sv_small_optimized(uint16_t *res, int8_t c, const uint16_t *v) {
    if (c == 1) {
        for (int i = 0; i < N; i++) res[i] = v[i];
    } else if (c == -1) {
        for (int i = 0; i < N; i++) {
            // Modular negation: (Q - v[i]) mod Q.
            res[i] = (v[i] == 0) ? 0 : (Q - v[i]);
        }
    } else { // c == 0
        for (int i = 0; i < N; i++) res[i] = 0;
    }
}

// ---------------- statistics ----------------
static void print_stats(const char *name, const double *samples, int reps) {
    double sum = 0, sum_sq = 0;
    double min = samples[0], max = samples[0];
    for (int i = 0; i < reps; i++) {
        sum += samples[i];
        sum_sq += samples[i] * samples[i];
        if (samples[i] < min) min = samples[i];
        if (samples[i] > max) max = samples[i];
    }
    double mean = sum / reps;
    double std = sqrt(fabs((sum_sq / reps) - (mean * mean)));
    printf("%-28s mean=%9.2f ns  std=%7.2f  min=%9.2f  max=%9.2f\n",
           name, mean, std, min, max);
}

int main(int argc, char **argv) {
    int iters = 200000;
    int reps = 15;

    uint16_t v[N], res[N];
    for(int i = 0; i < N; i++) v[i] = i % Q;

    double *samples = (double*)malloc(sizeof(double) * reps);

    printf("Benchmarking T_SV_small (Optimized for c in {-1, 0, 1})\n");
    printf("Config: iters=%d, reps=%d, N=%d\n\n", iters, reps, N);

    for (int r = 0; r < reps; r++) {
        // Warm-up.
        for (int i = 0; i < 500; i++) {
            sv_small_optimized(res, 1, v);
            sink ^= res[0];
        }

        uint64_t t0 = now_ns();
        for (int i = 0; i < iters; i++) {
            // Alternate small coefficients to model c in {-1, 1}.
            int8_t c = (i & 1) ? 1 : -1;
            sv_small_optimized(res, c, v);
            sink ^= res[0];
        }
        uint64_t t1 = now_ns();
        samples[r] = (double)(t1 - t0) / iters;
    }

    print_stats("T_SV_small (c in {-1,1})", samples, reps);
    printf("\n(sink=%llu)\n", (unsigned long long)sink);

    free(samples);
    return 0;
}
