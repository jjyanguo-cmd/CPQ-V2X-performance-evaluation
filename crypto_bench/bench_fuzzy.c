// bench_fuzzy.c
// Benchmark fuzzy extractor Gen/Rep using code-offset construction + libcorrect Reed-Solomon.
//
// Build (from ~/paper/CPQ-V2X/bench):
//   LIBCORRECT=~/paper/CPQ-V2X/libcorrect
//   cc -O3 -march=native -std=c11 bench_fuzzy.c -o bench_fuzzy \
//      -I"$LIBCORRECT/include" -L"$LIBCORRECT/build" -lcorrect -lm
//
// Run:
//   ./bench_fuzzy --iters 200000 --reps 15 --wlen 64 --klen 32 --ecc 32
//
// Notes:
// - This uses RS over GF(2^8). We follow libcorrect API patterns shown in upstream examples/issues.
// - We measure mean/std/min/max over reps, each rep averages iters iterations.
// - RNG uses OpenSSL RAND_bytes for convenience; you can swap to PQClean randombytes if you want.

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>
#include <time.h>
#include <math.h>

#include <openssl/rand.h>
#include "correct.h"

// ---------- timing ----------
static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static void stats_print(const char *name, const double *xs, int n) {
    double sum = 0.0, sum2 = 0.0;
    double mn = xs[0], mx = xs[0];
    for (int i = 0; i < n; i++) {
        sum += xs[i];
        sum2 += xs[i] * xs[i];
        if (xs[i] < mn) mn = xs[i];
        if (xs[i] > mx) mx = xs[i];
    }
    double mean = sum / n;
    double var = sum2 / n - mean * mean;
    double sd = (var > 0) ? sqrt(var) : 0.0;
    printf("%-28s mean=%9.2f ns  std=%7.2f  min=%9.2f  max=%9.2f\n",
           name, mean, sd, mn, mx);
}

// ---------- helpers ----------
static void xorb(uint8_t *out, const uint8_t *a, const uint8_t *b, size_t n) {
    for (size_t i = 0; i < n; i++) out[i] = a[i] ^ b[i];
}

// A tiny SHA3-256 wrapper using OpenSSL EVP
#include <openssl/evp.h>
static void sha3_256(uint8_t out[32], const uint8_t *in, size_t inlen) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha3_256(), NULL);
    EVP_DigestUpdate(ctx, in, inlen);
    unsigned int outlen = 0;
    EVP_DigestFinal_ex(ctx, out, &outlen);
    EVP_MD_CTX_free(ctx);
}

// ---------- FE (code-offset) using RS ----------
typedef struct {
    correct_reed_solomon *rs;
    size_t wlen;      // length of "biometric/PUF string" in bytes (we treat as raw bytes)
    size_t klen;      // length of extracted secret r in bytes
    size_t ecclen;    // ECC parity bytes (num_roots)
    size_t codelen;   // klen + ecclen (systematic)
} fe_ctx;

static fe_ctx *fe_init(size_t wlen, size_t klen, size_t ecclen) {
    fe_ctx *f = (fe_ctx*)calloc(1, sizeof(fe_ctx));
    if (!f) return NULL;

    // Primitive polynomial constant is provided by libcorrect.
    // Example usage is shown in upstream issue snippet.
    // num_roots controls parity length.
    const uint16_t primitive_polynomial = correct_rs_primitive_polynomial_8_4_3_2_0;
    const uint8_t first_consecutive_root = 0;
    const uint8_t generator_root_gap = 1;
    const uint8_t num_roots = (uint8_t)ecclen;

    f->rs = correct_reed_solomon_create(primitive_polynomial,
                                       first_consecutive_root,
                                       generator_root_gap,
                                       num_roots);
    if (!f->rs) {
        free(f);
        return NULL;
    }

    f->wlen = wlen;
    f->klen = klen;
    f->ecclen = ecclen;
    f->codelen = klen + ecclen;

    if (f->wlen != f->codelen) {
        // For simplest code-offset, helper and w must be same length as codeword.
        // You can set wlen=codelen (recommended), or extend w externally.
        fprintf(stderr, "[warn] wlen != (klen+ecc). For benchmark, please set --wlen == --klen+--ecc.\n");
    }
    return f;
}

static void fe_free(fe_ctx *f) {
    if (!f) return;
    if (f->rs) correct_reed_solomon_destroy(f->rs);
    free(f);
}

// Gen(w): sample random r (klen), encode -> codeword c (codelen), helper = c xor w, key=SHA3(c)
static void fe_gen(const fe_ctx *f,
                   const uint8_t *w, uint8_t *helper,
                   uint8_t key_out[32],
                   volatile uint64_t *sink) {
    uint8_t *r = (uint8_t*)alloca(f->klen);
    uint8_t *c = (uint8_t*)alloca(f->codelen);

    RAND_bytes(r, (int)f->klen);

    // libcorrect returns 255 historically; we ignore return value and use produced bytes.
    (void)correct_reed_solomon_encode(f->rs, r, (ssize_t)f->klen, c);

    xorb(helper, c, w, f->codelen);
    sha3_256(key_out, c, f->codelen);

    // prevent optimizing away
    uint64_t acc = 0;
    for (size_t i = 0; i < f->codelen; i++) acc += c[i];
    *sink ^= acc;
}

// Rep(w', helper): c' = helper xor w', decode -> r_hat, re-encode -> c_hat, key=SHA3(c_hat)
static void fe_rep(const fe_ctx *f,
                   const uint8_t *w_prime, const uint8_t *helper,
                   uint8_t key_out[32],
                   volatile uint64_t *sink) {
    uint8_t *cprime = (uint8_t*)alloca(f->codelen);
    uint8_t *rhat   = (uint8_t*)alloca(f->klen);
    uint8_t *chat   = (uint8_t*)alloca(f->codelen);

    xorb(cprime, helper, w_prime, f->codelen);

    // decode returns recovered data length on success (per upstream example)
    (void)correct_reed_solomon_decode(f->rs, cprime, (ssize_t)f->codelen, rhat);

    (void)correct_reed_solomon_encode(f->rs, rhat, (ssize_t)f->klen, chat);
    sha3_256(key_out, chat, f->codelen);

    uint64_t acc = 0;
    for (size_t i = 0; i < f->klen; i++) acc += rhat[i];
    *sink ^= acc;
}

// ---------- CLI ----------
static uint64_t parse_u64(const char *s, uint64_t defv) {
    if (!s) return defv;
    char *end = NULL;
    uint64_t v = strtoull(s, &end, 10);
    return (end && *end == '\0') ? v : defv;
}

int main(int argc, char **argv) {
    uint64_t iters = 200000, reps = 15;
    uint64_t wlen = 64, klen = 32, ecc = 32;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--iters") && i + 1 < argc) iters = parse_u64(argv[++i], iters);
        else if (!strcmp(argv[i], "--reps") && i + 1 < argc) reps = parse_u64(argv[++i], reps);
        else if (!strcmp(argv[i], "--wlen") && i + 1 < argc) wlen = parse_u64(argv[++i], wlen);
        else if (!strcmp(argv[i], "--klen") && i + 1 < argc) klen = parse_u64(argv[++i], klen);
        else if (!strcmp(argv[i], "--ecc")  && i + 1 < argc) ecc  = parse_u64(argv[++i], ecc);
        else if (!strcmp(argv[i], "--help")) {
            printf("Usage: %s [--iters N] [--reps R] [--wlen bytes] [--klen bytes] [--ecc parity_bytes]\n", argv[0]);
            return 0;
        }
    }

    printf("Fuzzy Extractor: code-offset + RS (libcorrect)\n");
    printf("Config: iters=%" PRIu64 " reps=%" PRIu64 " wlen=%" PRIu64 " klen=%" PRIu64 " ecc=%" PRIu64 "\n\n",
           iters, reps, wlen, klen, ecc);

    fe_ctx *f = fe_init((size_t)wlen, (size_t)klen, (size_t)ecc);
    if (!f) {
        fprintf(stderr, "fe_init failed (check libcorrect build/linking)\n");
        return 1;
    }
    if (f->codelen != f->wlen) {
        fprintf(stderr, "For clean benchmark, set --wlen == --klen+--ecc (now codelen=%zu, wlen=%zu)\n",
                f->codelen, f->wlen);
    }

    uint8_t *w = (uint8_t*)malloc(f->codelen);
    uint8_t *w2 = (uint8_t*)malloc(f->codelen);
    uint8_t *helper = (uint8_t*)malloc(f->codelen);
    if (!w || !w2 || !helper) return 1;

    // Generate a base w, and w' with small noise (flip a few bytes)
    RAND_bytes(w, (int)f->codelen);
    memcpy(w2, w, f->codelen);
    // noise: flip 4 random positions
    for (int t = 0; t < 4; t++) {
        uint8_t idx;
        RAND_bytes(&idx, 1);
        size_t pos = idx % f->codelen;
        w2[pos] ^= 0xFF;
    }

    double *gen_ns = (double*)malloc(sizeof(double) * reps);
    double *rep_ns = (double*)malloc(sizeof(double) * reps);
    if (!gen_ns || !rep_ns) return 1;

    volatile uint64_t sink = 0;
    uint8_t key[32];

    // bench Gen
    for (uint64_t r = 0; r < reps; r++) {
        uint64_t t0 = now_ns();
        for (uint64_t i = 0; i < iters; i++) {
            fe_gen(f, w, helper, key, &sink);
        }
        uint64_t t1 = now_ns();
        gen_ns[r] = (double)(t1 - t0) / (double)iters;
    }

    // bench Rep (uses helper from last Gen; fine for timing)
    for (uint64_t r = 0; r < reps; r++) {
        uint64_t t0 = now_ns();
        for (uint64_t i = 0; i < iters; i++) {
            fe_rep(f, w2, helper, key, &sink);
        }
        uint64_t t1 = now_ns();
        rep_ns[r] = (double)(t1 - t0) / (double)iters;
    }

    stats_print("T_Gen (RS + XOR + SHA3)", gen_ns, (int)reps);
    stats_print("T_Rep (XOR + RSdec + SHA3)", rep_ns, (int)reps);

    printf("\n(sink=%" PRIu64 ")\n", sink);

    free(gen_ns); free(rep_ns);
    free(w); free(w2); free(helper);
    fe_free(f);
    return 0;
}

