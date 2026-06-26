/*
 * bench_ecc.c — ECC baseline microbench (OpenSSL P-256 ECDH)
 *
 * Build:
 *   cc -O3 -march=native -std=c11 bench_ecc.c -o bench_ecc \
 *      $(pkg-config --cflags --libs openssl)
 *   # If pkg-config has no openssl entry:
 *   # cc -O3 -march=native -std=c11 bench_ecc.c -o bench_ecc -lssl -lcrypto
 *
 * Run:
 *   ./bench_ecc
 *   ./bench_ecc --iters 20000 --reps 15
 *
 * Notes:
 * - Measures ECDH derive on P-256 (prime256v1).
 * - Repeats (reps) and reports mean/std/min/max.
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <math.h>

#include <openssl/evp.h>
#include <openssl/ec.h>

static inline uint64_t now_ns(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000000ull + (uint64_t)tv.tv_usec * 1000ull;
}

typedef struct { double mean, std, min, max; } stats_t;

static stats_t compute_stats(const double *x, int n) {
    stats_t s; s.min = x[0]; s.max = x[0];
    double sum = 0.0;
    for (int i = 0; i < n; i++) { if (x[i] < s.min) s.min = x[i]; if (x[i] > s.max) s.max = x[i]; sum += x[i]; }
    s.mean = sum / n;
    double var = 0.0;
    for (int i = 0; i < n; i++) { double d = x[i] - s.mean; var += d*d; }
    s.std = (n > 1) ? sqrt(var / (n - 1)) : 0.0;
    return s;
}

static EVP_PKEY* gen_p256_key(void) {
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_EC, NULL);
    if (!pctx) return NULL;
    if (EVP_PKEY_keygen_init(pctx) <= 0) { EVP_PKEY_CTX_free(pctx); return NULL; }
    if (EVP_PKEY_CTX_set_ec_paramgen_curve_nid(pctx, NID_X9_62_prime256v1) <= 0) { EVP_PKEY_CTX_free(pctx); return NULL; }

    EVP_PKEY *pkey = NULL;
    if (EVP_PKEY_keygen(pctx, &pkey) <= 0) pkey = NULL;
    EVP_PKEY_CTX_free(pctx);
    return pkey;
}

static double meas_ecdh(int iters) {
    EVP_PKEY *a = gen_p256_key();
    EVP_PKEY *b = gen_p256_key();
    if (!a || !b) return -1.0;

    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(a, NULL);
    if (!ctx) return -1.0;
    if (EVP_PKEY_derive_init(ctx) <= 0) return -1.0;
    if (EVP_PKEY_derive_set_peer(ctx, b) <= 0) return -1.0;

    size_t secret_len = 0;
    if (EVP_PKEY_derive(ctx, NULL, &secret_len) <= 0) return -1.0;
    unsigned char secret[128];
    if (secret_len > sizeof(secret)) secret_len = sizeof(secret);

    // warmup
    for (int i = 0; i < 200; i++) {
        size_t outlen = secret_len;
        EVP_PKEY_derive(ctx, secret, &outlen);
    }

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) {
        size_t outlen = secret_len;
        EVP_PKEY_derive(ctx, secret, &outlen);
    }
    uint64_t t1 = now_ns();

    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(a);
    EVP_PKEY_free(b);

    return (double)(t1 - t0) / iters;
}

static void usage(const char *argv0) {
    printf("Usage: %s [--iters N] [--reps R]\n", argv0);
}

int main(int argc, char **argv) {
    int iters = 20000;
    int reps  = 11;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--iters") && i + 1 < argc) iters = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--reps") && i + 1 < argc) reps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--help")) { usage(argv[0]); return 0; }
        else { printf("Unknown arg: %s\n", argv[i]); usage(argv[0]); return 1; }
    }
    if (reps < 3) reps = 3;

    double *samples = (double*)malloc(sizeof(double)*reps);
    if (!samples) return 1;

    for (int r = 0; r < reps; r++) {
        samples[r] = meas_ecdh(iters);
        if (samples[r] < 0) { fprintf(stderr, "ECDH meas failed\n"); return 1; }
    }

    stats_t s = compute_stats(samples, reps);
    printf("ECC: P-256 ECDH derive\n");
    printf("Config: iters=%d reps=%d\n", iters, reps);
    printf("mean=%9.2f ns  std=%7.2f  min=%9.2f  max=%9.2f  (%.3f us)\n",
           s.mean, s.std, s.min, s.max, s.mean/1000.0);

    free(samples);
    return 0;
}
