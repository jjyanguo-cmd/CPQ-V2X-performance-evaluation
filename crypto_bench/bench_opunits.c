/*
 * bench_opunits.c — Unified op-unit microbench for CPQ-V2X paper
 *   (PQClean ML-KEM-512 + SHA3-256 + stable SampZ via SHAKE256 stream)
 *
 * Build:
 *   cd ~/paper/CPQ-V2X/bench
 *   PQROOT=~/paper/CPQ-V2X/PQClean
 *   PQALG=$PQROOT/crypto_kem/ml-kem-512/clean
 *   PQCOM=$PQROOT/common
 *   cc -O3 -march=native -std=c11 -I"$PQALG" -I"$PQCOM" \
 *      -o bench_opunits bench_opunits.c \
 *      $(ls "$PQALG"/*.c | grep -v -E 'bench|test|kat|PQCgenKAT') \
 *      $(ls "$PQCOM"/*.c | grep -v -E 'bench|test') -lm
 *
 * Run:
 *   ./bench_opunits
 *   ./bench_opunits --iters 200000 --reps 15 --hashlen 128 --d 512
 *
 * Notes:
 * - Timing uses gettimeofday() for portability.
 * - We repeat measurements (reps) and report mean/std/min/max for stability.
 * - A volatile sink is used to prevent the compiler from optimizing away work.
 * - SampZ uses SHAKE256(seed||counter) as deterministic PRG to avoid OS RNG variance.
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <math.h>

#include "api.h"
#include "poly.h"
#include "polyvec.h"
#include "params.h"
#include "fips202.h"
#include "randombytes.h"

// ---------------- timing ----------------
static inline uint64_t now_ns(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000000ull + (uint64_t)tv.tv_usec * 1000ull;
}

// anti-optimization sink
static volatile uint64_t sink = 0;

// ------------- PQClean namespace mapping -------------
#define poly_ntt                 PQCLEAN_MLKEM512_CLEAN_poly_ntt
#define poly_invntt_tomont       PQCLEAN_MLKEM512_CLEAN_poly_invntt_tomont
#define poly_basemul_montgomery  PQCLEAN_MLKEM512_CLEAN_poly_basemul_montgomery
#define poly_add                 PQCLEAN_MLKEM512_CLEAN_poly_add
#define poly_getnoise_eta1       PQCLEAN_MLKEM512_CLEAN_poly_getnoise_eta1
#define poly_getnoise_eta2       PQCLEAN_MLKEM512_CLEAN_poly_getnoise_eta2

#define polyvec_basemul_acc_montgomery PQCLEAN_MLKEM512_CLEAN_polyvec_basemul_acc_montgomery
#define polyvec_add                    PQCLEAN_MLKEM512_CLEAN_polyvec_add

// ---------------- stats ----------------
typedef struct {
    double mean, std, min, max;
} stats_t;

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
    printf("Usage: %s [--iters N] [--reps R] [--hashlen L] [--d D]\n", argv0);
    printf("  --iters   loop iterations per measurement (default 200000)\n");
    printf("  --reps    number of repeated measurements (default 15)\n");
    printf("  --hashlen SHA3-256 message length in bytes (default 128)\n");
    printf("  --d       dimension for SampZ in Zq^d (default 512)\n");
}

// ---------------- microbench kernels ----------------
// return average ns per op for one measurement

static double meas_sha3_256(int iters, size_t msg_len) {
    uint8_t out[32];
    uint8_t msg[2048];
    if (msg_len > sizeof(msg)) msg_len = sizeof(msg);
    memset(msg, 7, msg_len);

    for (int i = 0; i < 200; i++) {
        sha3_256(out, msg, msg_len);
        sink ^= out[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        sha3_256(out, msg, msg_len);
        sink ^= out[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_sampR_eta1(int iters) {
    poly a;
    uint8_t seed[KYBER_SYMBYTES];
    randombytes(seed, sizeof(seed));
    uint8_t nonce = 0;

    for (int i = 0; i < 200; i++) {
        poly_getnoise_eta1(&a, seed, nonce++);
        sink ^= (uint64_t)a.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        poly_getnoise_eta1(&a, seed, nonce++);
        sink ^= (uint64_t)a.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_sampR_eta2(int iters) {
    poly a;
    uint8_t seed[KYBER_SYMBYTES];
    randombytes(seed, sizeof(seed));
    uint8_t nonce = 0;

    for (int i = 0; i < 200; i++) {
        poly_getnoise_eta2(&a, seed, nonce++);
        sink ^= (uint64_t)a.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        poly_getnoise_eta2(&a, seed, nonce++);
        sink ^= (uint64_t)a.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_poly_ntt(int iters) {
    poly a;
    memset(&a, 1, sizeof(a));

    for (int i = 0; i < 200; i++) {
        poly_ntt(&a);
        sink ^= (uint64_t)a.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        poly_ntt(&a);
        sink ^= (uint64_t)a.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_poly_invntt(int iters) {
    poly a;
    memset(&a, 2, sizeof(a));
    poly_ntt(&a);

    for (int i = 0; i < 200; i++) {
        poly_invntt_tomont(&a);
        sink ^= (uint64_t)a.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        poly_invntt_tomont(&a);
        sink ^= (uint64_t)a.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_poly_basemul(int iters) {
    poly a, b, c;
    memset(&a, 3, sizeof(a));
    memset(&b, 4, sizeof(b));
    poly_ntt(&a);
    poly_ntt(&b);

    for (int i = 0; i < 200; i++) {
        poly_basemul_montgomery(&c, &a, &b);
        sink ^= (uint64_t)c.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        poly_basemul_montgomery(&c, &a, &b);
        sink ^= (uint64_t)c.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_poly_add(int iters) {
    poly a, b, c;
    memset(&a, 5, sizeof(a));
    memset(&b, 6, sizeof(b));

    for (int i = 0; i < 400; i++) {
        poly_add(&c, &a, &b);
        sink ^= (uint64_t)c.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        poly_add(&c, &a, &b);
        sink ^= (uint64_t)c.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_polyvec_basemul_acc(int iters) {
    polyvec a, b;
    poly r;
    randombytes((uint8_t*)&a, sizeof(a));
    randombytes((uint8_t*)&b, sizeof(b));

    for (int i = 0; i < 100; i++) {
        polyvec_basemul_acc_montgomery(&r, &a, &b);
        sink ^= (uint64_t)r.coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        polyvec_basemul_acc_montgomery(&r, &a, &b);
        sink ^= (uint64_t)r.coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double meas_polyvec_add(int iters) {
    polyvec a, b, r;
    randombytes((uint8_t*)&a, sizeof(a));
    randombytes((uint8_t*)&b, sizeof(b));

    for (int i = 0; i < 200; i++) {
        polyvec_add(&r, &a, &b);
        sink ^= (uint64_t)r.vec[0].coeffs[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        polyvec_add(&r, &a, &b);
        sink ^= (uint64_t)r.vec[0].coeffs[0];
    }
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

// SampZ: uniform sampling in Zq^d using SHAKE256 stream (deterministic PRG) + mod q
static double meas_sampZ(int iters, size_t d) {
    uint16_t *v = (uint16_t*)malloc(d * sizeof(uint16_t));
    if (!v) return -1.0;

    uint8_t seed[32];
    randombytes(seed, sizeof(seed));

    size_t need = d * sizeof(uint16_t);
    uint8_t *buf = (uint8_t*)malloc(need);
    if (!buf) { free(v); return -1.0; }

    // warmup
    for (int i = 0; i < 200; i++) {
        uint8_t in[36];
        memcpy(in, seed, 32);
        in[32] = (uint8_t)(i);
        in[33] = (uint8_t)(i >> 8);
        in[34] = (uint8_t)(i >> 16);
        in[35] = (uint8_t)(i >> 24);
        shake256(buf, need, in, sizeof(in));

        memcpy(v, buf, need);
        for (size_t j = 0; j < d; j++) v[j] %= KYBER_Q;
        sink ^= v[0];
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        uint8_t in[36];
        memcpy(in, seed, 32);
        in[32] = (uint8_t)(i);
        in[33] = (uint8_t)(i >> 8);
        in[34] = (uint8_t)(i >> 16);
        in[35] = (uint8_t)(i >> 24);
        shake256(buf, need, in, sizeof(in));

        memcpy(v, buf, need);
        for (size_t j = 0; j < d; j++) v[j] %= KYBER_Q;
        sink ^= v[0];
    }
    uint64_t t1 = now_ns();

    free(buf);
    free(v);
    return (double)(t1 - t0) / iters;
}

int main(int argc, char **argv) {
    int iters = 200000;
    int reps  = 15;
    size_t hashlen = 128;
    size_t d = 512;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--iters") && i + 1 < argc) iters = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--reps") && i + 1 < argc) reps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--hashlen") && i + 1 < argc) hashlen = (size_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--d") && i + 1 < argc) d = (size_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--help")) { usage(argv[0]); return 0; }
        else { printf("Unknown arg: %s\n", argv[i]); usage(argv[0]); return 1; }
    }
    if (reps < 3) reps = 3;

    double *sH    = (double*)malloc(sizeof(double)*reps);
    double *sR1   = (double*)malloc(sizeof(double)*reps);
    double *sR2   = (double*)malloc(sizeof(double)*reps);
    double *sNTT  = (double*)malloc(sizeof(double)*reps);
    double *sBMUL = (double*)malloc(sizeof(double)*reps);
    double *sINTT = (double*)malloc(sizeof(double)*reps);
    double *sRA   = (double*)malloc(sizeof(double)*reps);
    double *sAM   = (double*)malloc(sizeof(double)*reps);
    double *sAV   = (double*)malloc(sizeof(double)*reps);
    double *sSZ   = (double*)malloc(sizeof(double)*reps);
    double *sRM   = (double*)malloc(sizeof(double)*reps);

    if (!sH||!sR1||!sR2||!sNTT||!sBMUL||!sINTT||!sRA||!sAM||!sAV||!sSZ||!sRM) {
        fprintf(stderr, "malloc failed\n");
        return 1;
    }

    for (int r = 0; r < reps; r++) {
        sH[r]    = meas_sha3_256(iters, hashlen);
        sR1[r]   = meas_sampR_eta1(iters);
        sR2[r]   = meas_sampR_eta2(iters);
        sNTT[r]  = meas_poly_ntt(iters);
        sBMUL[r] = meas_poly_basemul(iters);
        sINTT[r] = meas_poly_invntt(iters);
        sRA[r]   = meas_poly_add(iters);
        sAM[r]   = meas_polyvec_basemul_acc(iters);
        sAV[r]   = meas_polyvec_add(iters);
        sSZ[r]   = meas_sampZ(iters, d);
        sRM[r]   = sNTT[r] + sBMUL[r] + sINTT[r];
    }

    printf("ALG: %s\n", PQCLEAN_MLKEM512_CLEAN_CRYPTO_ALGNAME);
    printf("Config: iters=%d reps=%d hashlen=%zuB SampZ_d=%zu\n\n", iters, reps, hashlen, d);

    print_stats("T_H (sha3_256)", sH, reps);

    print_stats("T_SampR (eta1)", sR1, reps);
    print_stats("T_SampR (eta2)", sR2, reps);

    print_stats("poly_ntt", sNTT, reps);
    print_stats("poly_basemul_montgomery", sBMUL, reps);
    print_stats("poly_invntt_tomont", sINTT, reps);
    print_stats("T_RM ~= NTT+basemul+invNTT", sRM, reps);

    print_stats("T_RA ~= poly_add", sRA, reps);
    print_stats("T_AM ~= polyvec_basemul_acc", sAM, reps);
    print_stats("T_AV ~= polyvec_add", sAV, reps);

    print_stats("T_SampZ (SHAKE stream, mod q)", sSZ, reps);

    printf("\n(sink=%llu)\n", (unsigned long long)sink);

    free(sH); free(sR1); free(sR2); free(sNTT); free(sBMUL); free(sINTT);
    free(sRA); free(sAM); free(sAV); free(sSZ); free(sRM);

    return 0;
}

