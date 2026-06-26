#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>

#include "api.h"
#include "poly.h"

// ---- timing ----
static inline uint64_t now_ns(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000000ull + (uint64_t)tv.tv_usec * 1000ull;
}
#define WARMUP 50

// ---- Map names to PQClean namespaced functions ----
#define poly_ntt                 PQCLEAN_MLKEM512_CLEAN_poly_ntt
#define poly_invntt_tomont       PQCLEAN_MLKEM512_CLEAN_poly_invntt_tomont
#define poly_basemul_montgomery  PQCLEAN_MLKEM512_CLEAN_poly_basemul_montgomery
#define poly_add                 PQCLEAN_MLKEM512_CLEAN_poly_add
#define poly_getnoise_eta1       PQCLEAN_MLKEM512_CLEAN_poly_getnoise_eta1
#define poly_getnoise_eta2       PQCLEAN_MLKEM512_CLEAN_poly_getnoise_eta2

static double bench_poly_ntt(int iters) {
    poly a;
    memset(&a, 1, sizeof(a));
    for (int i = 0; i < WARMUP; i++) poly_ntt(&a);

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) poly_ntt(&a);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_poly_invntt(int iters) {
    poly a;
    memset(&a, 2, sizeof(a));
    poly_ntt(&a);
    for (int i = 0; i < WARMUP; i++) poly_invntt_tomont(&a);

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) poly_invntt_tomont(&a);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_poly_basemul(int iters) {
    poly a, b, c;
    memset(&a, 3, sizeof(a));
    memset(&b, 4, sizeof(b));
    poly_ntt(&a);
    poly_ntt(&b);

    for (int i = 0; i < WARMUP; i++) poly_basemul_montgomery(&c, &a, &b);

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) poly_basemul_montgomery(&c, &a, &b);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_poly_add(int iters) {
    poly a, b, c;
    memset(&a, 5, sizeof(a));
    memset(&b, 6, sizeof(b));

    for (int i = 0; i < WARMUP; i++) poly_add(&c, &a, &b);

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) poly_add(&c, &a, &b);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_noise_eta1(int iters) {
    poly a;
    uint8_t seed[32] = {0};
    uint8_t nonce = 0;

    for (int i = 0; i < WARMUP; i++) poly_getnoise_eta1(&a, seed, nonce++);

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) poly_getnoise_eta1(&a, seed, nonce++);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_noise_eta2(int iters) {
    poly a;
    uint8_t seed[32] = {0};
    uint8_t nonce = 0;

    for (int i = 0; i < WARMUP; i++) poly_getnoise_eta2(&a, seed, nonce++);

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) poly_getnoise_eta2(&a, seed, nonce++);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

int main(void) {
    const int iters = 200000;

    double t_ntt   = bench_poly_ntt(iters);
    double t_intt  = bench_poly_invntt(iters);
    double t_bmul  = bench_poly_basemul(iters);
    double t_add   = bench_poly_add(iters);
    double t_eta1  = bench_noise_eta1(iters);
    double t_eta2  = bench_noise_eta2(iters);

    printf("ALG: %s\n", PQCLEAN_MLKEM512_CLEAN_CRYPTO_ALGNAME);
    printf("Unit timings (avg):\n");
    printf("poly_ntt                    : %.2f ns\n", t_ntt);
    printf("poly_invntt_tomont          : %.2f ns\n", t_intt);
    printf("poly_basemul_montgomery     : %.2f ns\n", t_bmul);
    printf("poly_add                    : %.2f ns\n", t_add);
    printf("poly_getnoise_eta1          : %.2f ns\n", t_eta1);
    printf("poly_getnoise_eta2          : %.2f ns\n", t_eta2);

    printf("\nSuggested mapping (for your Table of op-units):\n");
    printf("T_RM   ~= NTT + basemul + invNTT = %.2f ns\n", t_ntt + t_bmul + t_intt);
    printf("T_RA   ~= poly_add               = %.2f ns\n", t_add);
    printf("T_SampR (eta1) ~= noise_eta1     = %.2f ns\n", t_eta1);
    printf("T_SampR (eta2) ~= noise_eta2     = %.2f ns\n", t_eta2);

    return 0;
}
