#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>

#include "api.h"  // PQCLEAN_MLKEM512_CLEAN_* definitions

// ---- Adapt PQClean names to generic names (optional but clean) ----
#define CRYPTO_PUBLICKEYBYTES  PQCLEAN_MLKEM512_CLEAN_CRYPTO_PUBLICKEYBYTES
#define CRYPTO_SECRETKEYBYTES  PQCLEAN_MLKEM512_CLEAN_CRYPTO_SECRETKEYBYTES
#define CRYPTO_CIPHERTEXTBYTES PQCLEAN_MLKEM512_CLEAN_CRYPTO_CIPHERTEXTBYTES
#define CRYPTO_BYTES           PQCLEAN_MLKEM512_CLEAN_CRYPTO_BYTES
#define CRYPTO_ALGNAME         PQCLEAN_MLKEM512_CLEAN_CRYPTO_ALGNAME

static inline int crypto_kem_keypair(uint8_t *pk, uint8_t *sk) {
    return PQCLEAN_MLKEM512_CLEAN_crypto_kem_keypair(pk, sk);
}
static inline int crypto_kem_enc(uint8_t *ct, uint8_t *ss, const uint8_t *pk) {
    return PQCLEAN_MLKEM512_CLEAN_crypto_kem_enc(ct, ss, pk);
}
static inline int crypto_kem_dec(uint8_t *ss, const uint8_t *ct, const uint8_t *sk) {
    return PQCLEAN_MLKEM512_CLEAN_crypto_kem_dec(ss, ct, sk);
}

// ---- Timing ----
static inline uint64_t now_ns(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000000ull + (uint64_t)tv.tv_usec * 1000ull;
}

static double bench_keypair(int iters) {
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];

    for (int i = 0; i < 50; i++) crypto_kem_keypair(pk, sk); // warmup

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) crypto_kem_keypair(pk, sk);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_encaps(int iters) {
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];
    uint8_t ct[CRYPTO_CIPHERTEXTBYTES];
    uint8_t ss[CRYPTO_BYTES];

    crypto_kem_keypair(pk, sk);
    for (int i = 0; i < 50; i++) crypto_kem_enc(ct, ss, pk); // warmup

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) crypto_kem_enc(ct, ss, pk);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

static double bench_decaps(int iters) {
    uint8_t pk[CRYPTO_PUBLICKEYBYTES];
    uint8_t sk[CRYPTO_SECRETKEYBYTES];
    uint8_t ct[CRYPTO_CIPHERTEXTBYTES];
    uint8_t ss1[CRYPTO_BYTES], ss2[CRYPTO_BYTES];

    crypto_kem_keypair(pk, sk);
    crypto_kem_enc(ct, ss1, pk);
    for (int i = 0; i < 50; i++) crypto_kem_dec(ss2, ct, sk); // warmup

    uint64_t t0 = now_ns();
    for (int i = 0; i < iters; i++) crypto_kem_dec(ss2, ct, sk);
    uint64_t t1 = now_ns();
    return (double)(t1 - t0) / iters;
}

int main(void) {
    const int iters = 10000;

    double t_keypair = bench_keypair(iters);
    double t_enc = bench_encaps(iters);
    double t_dec = bench_decaps(iters);

    printf("ALG: %s\n", CRYPTO_ALGNAME);
    printf("KeyGen : %.1f ns (%.3f us)\n", t_keypair, t_keypair / 1000.0);
    printf("Encaps : %.1f ns (%.3f us)\n", t_enc,     t_enc     / 1000.0);
    printf("Decaps : %.1f ns (%.3f us)\n", t_dec,     t_dec     / 1000.0);
    return 0;
}
