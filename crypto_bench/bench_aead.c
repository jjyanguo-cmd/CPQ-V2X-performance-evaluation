/*
 * bench_aead.c — AEAD microbench (OpenSSL): AES-128-GCM or ChaCha20-Poly1305
 *
 * Build:
 *   cc -O3 -march=native -std=c11 bench_aead.c -o bench_aead \
 *      $(pkg-config --cflags --libs openssl) -lm
 *   # fallback:
 *   # cc -O3 -march=native -std=c11 bench_aead.c -o bench_aead -lssl -lcrypto -lm
 *
 * Run examples:
 *   ./bench_aead --alg aesgcm --mlen 128 --aad 16 --iters 200000 --reps 15
 *   ./bench_aead --alg chacha --mlen 128 --aad 16 --iters 200000 --reps 15
 *
 * Reports mean/std/min/max for Enc and Dec (ns).
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <math.h>

#include <openssl/evp.h>
#include <openssl/rand.h>

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

static void print_stats(const char *name, const double *samples, int reps) {
    stats_t s = compute_stats(samples, reps);
    printf("%-10s mean=%9.2f ns  std=%7.2f  min=%9.2f  max=%9.2f  (%.3f us)\n",
           name, s.mean, s.std, s.min, s.max, s.mean/1000.0);
}

static volatile uint64_t sink = 0;

static const EVP_CIPHER* pick_cipher(const char *alg) {
    if (!strcmp(alg, "aesgcm")) return EVP_aes_128_gcm();
    if (!strcmp(alg, "chacha")) return EVP_chacha20_poly1305();
    return NULL;
}

static int aead_encrypt_once(const EVP_CIPHER *cipher,
                            const uint8_t *key, size_t klen,
                            const uint8_t *nonce, size_t nlen,
                            const uint8_t *aad, size_t aadlen,
                            const uint8_t *pt, size_t ptlen,
                            uint8_t *ct, uint8_t *tag, size_t taglen)
{
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return 0;

    int len = 0, outlen = 0;

    if (EVP_EncryptInit_ex(ctx, cipher, NULL, NULL, NULL) != 1) return 0;

    // set nonce length for GCM/ChaCha20-Poly1305
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, (int)nlen, NULL) != 1) return 0;

    if (EVP_EncryptInit_ex(ctx, NULL, NULL, key, nonce) != 1) return 0;

    if (aadlen > 0) {
        if (EVP_EncryptUpdate(ctx, NULL, &len, aad, (int)aadlen) != 1) return 0;
    }

    if (EVP_EncryptUpdate(ctx, ct, &len, pt, (int)ptlen) != 1) return 0;
    outlen = len;

    if (EVP_EncryptFinal_ex(ctx, ct + outlen, &len) != 1) return 0;
    outlen += len;

    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_GET_TAG, (int)taglen, tag) != 1) return 0;

    EVP_CIPHER_CTX_free(ctx);
    sink ^= ct[0] ^ tag[0];
    return outlen;
}

static int aead_decrypt_once(const EVP_CIPHER *cipher,
                            const uint8_t *key, size_t klen,
                            const uint8_t *nonce, size_t nlen,
                            const uint8_t *aad, size_t aadlen,
                            const uint8_t *ct, size_t ctlen,
                            const uint8_t *tag, size_t taglen,
                            uint8_t *pt)
{
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return 0;

    int len = 0, outlen = 0;

    if (EVP_DecryptInit_ex(ctx, cipher, NULL, NULL, NULL) != 1) return 0;
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, (int)nlen, NULL) != 1) return 0;
    if (EVP_DecryptInit_ex(ctx, NULL, NULL, key, nonce) != 1) return 0;

    if (aadlen > 0) {
        if (EVP_DecryptUpdate(ctx, NULL, &len, aad, (int)aadlen) != 1) return 0;
    }

    if (EVP_DecryptUpdate(ctx, pt, &len, ct, (int)ctlen) != 1) return 0;
    outlen = len;

    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_TAG, (int)taglen, (void*)tag) != 1) return 0;

    int ok = EVP_DecryptFinal_ex(ctx, pt + outlen, &len);
    EVP_CIPHER_CTX_free(ctx);

    if (ok != 1) return 0;
    outlen += len;
    sink ^= pt[0];
    return outlen;
}

static void usage(const char *argv0) {
    printf("Usage: %s --alg aesgcm|chacha [--mlen N] [--aad N] [--iters N] [--reps R]\n", argv0);
}

int main(int argc, char **argv) {
    const char *alg = "aesgcm";
    size_t mlen = 128, aadlen = 16;
    int iters = 200000, reps = 15;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--alg") && i+1 < argc) alg = argv[++i];
        else if (!strcmp(argv[i], "--mlen") && i+1 < argc) mlen = (size_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--aad") && i+1 < argc) aadlen = (size_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--iters") && i+1 < argc) iters = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--reps") && i+1 < argc) reps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--help")) { usage(argv[0]); return 0; }
        else { printf("Unknown arg: %s\n", argv[i]); usage(argv[0]); return 1; }
    }
    if (reps < 3) reps = 3;

    const EVP_CIPHER *cipher = pick_cipher(alg);
    if (!cipher) { fprintf(stderr, "Unknown alg %s\n", alg); return 1; }

    // fixed sizes
    const size_t klen = (!strcmp(alg,"aesgcm")) ? 16 : 32;
    const size_t nlen = 12;
    const size_t taglen = 16;

    uint8_t *pt  = (uint8_t*)malloc(mlen);
    uint8_t *ct  = (uint8_t*)malloc(mlen + 16);
    uint8_t *aad = (uint8_t*)malloc(aadlen);
    uint8_t *dec = (uint8_t*)malloc(mlen + 16);
    uint8_t key[32], nonce[12], tag[16];

    if (!pt || !ct || !aad || !dec) { fprintf(stderr, "malloc failed\n"); return 1; }
    memset(pt, 0x11, mlen);
    memset(aad, 0x22, aadlen);

    RAND_bytes(key, (int)klen);
    RAND_bytes(nonce, (int)nlen);

    // warmup
    for (int i = 0; i < 500; i++) {
        int ctlen = aead_encrypt_once(cipher, key, klen, nonce, nlen, aad, aadlen, pt, mlen, ct, tag, taglen);
        aead_decrypt_once(cipher, key, klen, nonce, nlen, aad, aadlen, ct, (size_t)ctlen, tag, taglen, dec);
    }

    double *enc_s = (double*)malloc(sizeof(double)*reps);
    double *dec_s = (double*)malloc(sizeof(double)*reps);

    for (int r = 0; r < reps; r++) {
        // Encrypt timing
        uint64_t t0 = now_ns();
        int last_ctlen = 0;
        for (int i = 0; i < iters; i++) {
            last_ctlen = aead_encrypt_once(cipher, key, klen, nonce, nlen, aad, aadlen, pt, mlen, ct, tag, taglen);
        }
        uint64_t t1 = now_ns();
        enc_s[r] = (double)(t1 - t0) / iters;

        // Decrypt timing (use last ciphertext/tag)
        uint64_t t2 = now_ns();
        for (int i = 0; i < iters; i++) {
            aead_decrypt_once(cipher, key, klen, nonce, nlen, aad, aadlen, ct, (size_t)last_ctlen, tag, taglen, dec);
        }
        uint64_t t3 = now_ns();
        dec_s[r] = (double)(t3 - t2) / iters;
    }

    printf("AEAD: %s  mlen=%zuB aad=%zuB iters=%d reps=%d\n", alg, mlen, aadlen, iters, reps);
    print_stats("Enc", enc_s, reps);
    print_stats("Dec", dec_s, reps);
    printf("(sink=%llu)\n", (unsigned long long)sink);

    free(pt); free(ct); free(aad); free(dec);
    free(enc_s); free(dec_s);
    return 0;
}
