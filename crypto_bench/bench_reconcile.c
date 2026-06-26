// bench_reconcile.c
// Ding/NewHope-style reconciliation microbenchmark: Cha() + Mod2()
//
// Build example:
//   PQROOT=~/paper/CPQ-V2X/PQClean
//   PQCOM=$PQROOT/common
//   cc -O3 -march=native -std=c11 -I"$PQCOM" -o bench_reconcile bench_reconcile.c \
//      $(ls "$PQCOM"/*.c | grep -v -E 'bench|test') -lm
//
// Run examples:
//   ./bench_reconcile --iters 200000 --reps 15 --N 256 --q 3329
//   ./bench_reconcile --iters 500000 --reps 30 --N 256 --q 3329

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>

#include "randombytes.h"   // from PQClean/common

// ---------------- timing ----------------
static inline uint64_t now_ns(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000000ull + (uint64_t)tv.tv_usec * 1000ull;
}

// ---------------- helpers ----------------
static inline uint16_t mod_q(int32_t x, uint16_t q) {
    int32_t r = x % (int32_t)q;
    if (r < 0) r += q;
    return (uint16_t)r;
}

// Generate a noisy pair (v, v') in Z_q^N
// v uniform mod q; v' = v + e (mod q), with small noise e in [-2,2]
static void gen_noisy_pair(uint16_t *v, uint16_t *vp, size_t N, uint16_t q) {
    for (size_t i = 0; i < N; i++) {
        uint8_t r[2];
        randombytes(r, 2);
        uint16_t x = (uint16_t)((r[0] | ((uint16_t)r[1] << 8)) % q);

        uint8_t rn;
        randombytes(&rn, 1);
        int32_t e = (int32_t)(rn % 5) - 2;

        v[i]  = x;
        vp[i] = mod_q((int32_t)x + e, q);
    }
}

// ---------------- Ding/NewHope-style reconciliation ----------------
// Cha(): produce 1-bit hint per coefficient (b[i])
static void ding_cha(uint8_t *b, const uint16_t *v, size_t N, uint16_t q) {
    // threshold at q/2; bias by q/4 to reduce boundary flips
    const uint16_t q2 = (uint16_t)(q >> 1);
    const uint16_t q4 = (uint16_t)(q >> 2);

    for (size_t i = 0; i < N; i++) {
        uint16_t y = (uint16_t)(v[i] + q4);
        b[i] = (uint8_t)((y >= q2) ? 1 : 0);
    }
}

// Mod2(): recover 1-bit key per coefficient (k[i]) given noisy v' and hint b
static void ding_mod2(uint8_t *k, const uint16_t *vprime, const uint8_t *b, size_t N, uint16_t q) {
    const uint16_t q2 = (uint16_t)(q >> 1);
    const uint16_t q4 = (uint16_t)(q >> 2);

    for (size_t i = 0; i < N; i++) {
        uint16_t y = (uint16_t)(vprime[i] + (b[i] ? q4 : 0));
        k[i] = (uint8_t)((y >= q2) ? 1 : 0);
    }
}

// ---------------- statistics ----------------
typedef struct {
    double mean;
    double std;
    double min;
    double max;
} stats_t;

static stats_t bench_cha(int iters, int reps, size_t N, uint16_t q) {
    uint16_t *v  = (uint16_t*)malloc(N * sizeof(uint16_t));
    uint16_t *vp = (uint16_t*)malloc(N * sizeof(uint16_t));
    uint8_t  *b  = (uint8_t*)malloc(N);
    if (!v || !vp || !b) { fprintf(stderr, "alloc failed\n"); exit(1); }

    // warmup
    for (int i = 0; i < 10; i++) {
        gen_noisy_pair(v, vp, N, q);
        ding_cha(b, v, N, q);
    }

    double sum = 0.0, sum2 = 0.0;
    double mn = 1e100, mx = 0.0;

    for (int r = 0; r < reps; r++) {
        gen_noisy_pair(v, vp, N, q);

        uint64_t t0 = now_ns();
        for (int i = 0; i < iters; i++) {
            ding_cha(b, v, N, q);
        }
        uint64_t t1 = now_ns();

        double per = (double)(t1 - t0) / iters;
        sum += per; sum2 += per * per;
        if (per < mn) mn = per;
        if (per > mx) mx = per;
    }

    stats_t st;
    st.mean = sum / reps;
    double var = (sum2 / reps) - (st.mean * st.mean);
    st.std = (var > 0) ? sqrt(var) : 0.0;
    st.min = mn;
    st.max = mx;

    volatile uint8_t sink = b[0];
    (void)sink;

    free(v); free(vp); free(b);
    return st;
}

static stats_t bench_mod2(int iters, int reps, size_t N, uint16_t q) {
    uint16_t *v  = (uint16_t*)malloc(N * sizeof(uint16_t));
    uint16_t *vp = (uint16_t*)malloc(N * sizeof(uint16_t));
    uint8_t  *b  = (uint8_t*)malloc(N);
    uint8_t  *k  = (uint8_t*)malloc(N);
    if (!v || !vp || !b || !k) { fprintf(stderr, "alloc failed\n"); exit(1); }

    // warmup
    for (int i = 0; i < 10; i++) {
        gen_noisy_pair(v, vp, N, q);
        ding_cha(b, v, N, q);
        ding_mod2(k, vp, b, N, q);
    }

    double sum = 0.0, sum2 = 0.0;
    double mn = 1e100, mx = 0.0;

    for (int r = 0; r < reps; r++) {
        gen_noisy_pair(v, vp, N, q);
        ding_cha(b, v, N, q); // prepare hints

        uint64_t t0 = now_ns();
        for (int i = 0; i < iters; i++) {
            ding_mod2(k, vp, b, N, q);
        }
        uint64_t t1 = now_ns();

        double per = (double)(t1 - t0) / iters;
        sum += per; sum2 += per * per;
        if (per < mn) mn = per;
        if (per > mx) mx = per;
    }

    stats_t st;
    st.mean = sum / reps;
    double var = (sum2 / reps) - (st.mean * st.mean);
    st.std = (var > 0) ? sqrt(var) : 0.0;
    st.min = mn;
    st.max = mx;

    volatile uint8_t sink = k[0];
    (void)sink;

    free(v); free(vp); free(b); free(k);
    return st;
}

// ---------------- CLI ----------------
static void usage(const char *p) {
    fprintf(stderr,
        "Usage: %s [--iters N] [--reps R] [--N dim] [--q modulus]\n"
        "Defaults: iters=200000 reps=15 N=256 q=3329\n", p);
}

static int argi(int *i, int argc, char **argv) {
    if (*i + 1 >= argc) return 0;
    (*i)++;
    return atoi(argv[*i]);
}

int main(int argc, char **argv) {
    int iters = 200000;
    int reps  = 15;
    int N     = 256;
    int q_in  = 3329;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--iters")) iters = argi(&i, argc, argv);
        else if (!strcmp(argv[i], "--reps")) reps = argi(&i, argc, argv);
        else if (!strcmp(argv[i], "--N")) N = argi(&i, argc, argv);
        else if (!strcmp(argv[i], "--q")) q_in = argi(&i, argc, argv);
        else if (!strcmp(argv[i], "-h") || !strcmp(argv[i], "--help")) { usage(argv[0]); return 0; }
        else { fprintf(stderr, "Unknown arg: %s\n", argv[i]); usage(argv[0]); return 1; }
    }

    if (iters <= 0 || reps <= 0 || N <= 0 || q_in <= 0) {
        fprintf(stderr, "Invalid parameters.\n");
        return 1;
    }

    uint16_t q = (uint16_t)q_in;

    printf("Reconciliation: Ding-style (Cha + Mod2)\n");
    printf("Config: iters=%d reps=%d N=%d q=%u\n\n", iters, reps, N, q);

    stats_t s_cha  = bench_cha(iters, reps, (size_t)N, q);
    stats_t s_mod2 = bench_mod2(iters, reps, (size_t)N, q);

    // For reporting: T_Rec = T_Cha + T_Mod2 (mean); min/max just sum mins/maxs for a conservative range.
    stats_t s_rec;
    s_rec.mean = s_cha.mean + s_mod2.mean;
    // std of sum (rough, assuming independence) => sqrt(std1^2 + std2^2)
    s_rec.std  = sqrt(s_cha.std * s_cha.std + s_mod2.std * s_mod2.std);
    s_rec.min  = s_cha.min + s_mod2.min;
    s_rec.max  = s_cha.max + s_mod2.max;

    printf("T_Cha (hint generation)     mean=%10.2f ns  std=%7.2f  min=%10.2f  max=%10.2f\n",
           s_cha.mean, s_cha.std, s_cha.min, s_cha.max);
    printf("T_Mod2 (robust extraction)  mean=%10.2f ns  std=%7.2f  min=%10.2f  max=%10.2f\n",
           s_mod2.mean, s_mod2.std, s_mod2.min, s_mod2.max);
    printf("T_Rec = Cha + Mod2          mean=%10.2f ns  std=%7.2f  min=%10.2f  max=%10.2f\n",
           s_rec.mean, s_rec.std, s_rec.min, s_rec.max);

    return 0;
}

