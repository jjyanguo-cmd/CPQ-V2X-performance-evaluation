/*
 * bench_ec_ops.c — ECC microbench for point add / scalar mul (OpenSSL, P-256)
 *
 * Build:
 *   cc -O3 -march=native -std=c11 bench_ec_ops.c -o bench_ec_ops \
 *      $(pkg-config --cflags --libs openssl) -lm
 *   # fallback:
 *   # cc -O3 -march=native -std=c11 bench_ec_ops.c -o bench_ec_ops -lssl -lcrypto -lm
 *
 * Run:
 *   ./bench_ec_ops --add-iters 200000 --mul-iters 20000 --reps 15
 *
 * Note:
 * - Uses EC_POINT_point2oct (compressed) as a lightweight sink to avoid counting expensive affine extraction.
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/time.h>
#include <stdlib.h>
#include <math.h>

#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>

static inline uint64_t now_ns(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * 1000000000ull + (uint64_t)tv.tv_usec * 1000ull;
}

typedef struct { double mean, std, min, max; } stats_t;
static stats_t stats(const double *x, int n) {
    stats_t s; s.min = x[0]; s.max = x[0];
    double sum = 0.0;
    for (int i=0;i<n;i++){ if(x[i]<s.min) s.min=x[i]; if(x[i]>s.max) s.max=x[i]; sum+=x[i]; }
    s.mean = sum / n;
    double var = 0.0;
    for (int i=0;i<n;i++){ double d=x[i]-s.mean; var += d*d; }
    s.std = (n>1)? sqrt(var/(n-1)) : 0.0;
    return s;
}
static void print(const char *name, const double *samples, int reps) {
    stats_t s = stats(samples, reps);
    printf("%-12s mean=%9.2f ns  std=%7.2f  min=%9.2f  max=%9.2f  (%.3f us)\n",
           name, s.mean, s.std, s.min, s.max, s.mean/1000.0);
}

static volatile uint64_t sink = 0;

static inline void touch_point(const EC_GROUP *grp, const EC_POINT *P, BN_CTX *bnctx) {
    unsigned char buf[65];
    size_t n = EC_POINT_point2oct(grp, P, POINT_CONVERSION_COMPRESSED, buf, sizeof(buf), bnctx);
    // n should be 33 for compressed P-256, but we fold it in anyway
    sink ^= (uint64_t)buf[0] ^ (uint64_t)n;
}

static void usage(const char *a0){
    printf("Usage: %s [--add-iters N] [--mul-iters N] [--reps R]\n", a0);
}

static double meas_point_add(EC_GROUP *grp, BN_CTX *bnctx, int iters) {
    EC_POINT *P = EC_POINT_new(grp);
    EC_POINT *Q = EC_POINT_new(grp);
    EC_POINT *R = EC_POINT_new(grp);
    if (!P||!Q||!R) return -1.0;

    const EC_POINT *G = EC_GROUP_get0_generator(grp);
    EC_POINT_copy(P, G);
    EC_POINT_dbl(grp, Q, G, bnctx); // Q = 2G

    for (int i=0;i<1000;i++){ EC_POINT_add(grp, R, P, Q, bnctx); touch_point(grp, R, bnctx); }

    uint64_t t0 = now_ns();
    for (int i=0;i<iters;i++){
        EC_POINT_add(grp, R, P, Q, bnctx);
        touch_point(grp, R, bnctx);
    }
    uint64_t t1 = now_ns();

    EC_POINT_free(P); EC_POINT_free(Q); EC_POINT_free(R);
    return (double)(t1 - t0) / iters;
}

static double meas_scalar_mul(EC_GROUP *grp, BN_CTX *bnctx, int iters) {
    EC_POINT *R = EC_POINT_new(grp);
    if (!R) return -1.0;

    const EC_POINT *G = EC_GROUP_get0_generator(grp);
    BIGNUM *k = BN_new();
    if (!k) return -1.0;

    BN_hex2bn(&k, "A1B2C3D4E5F60718293A4B5C6D7E8F90123456789ABCDEF0");

    for (int i=0;i<300;i++){ EC_POINT_mul(grp, R, NULL, G, k, bnctx); touch_point(grp, R, bnctx); }

    uint64_t t0 = now_ns();
    for (int i=0;i<iters;i++){
        EC_POINT_mul(grp, R, NULL, G, k, bnctx);
        touch_point(grp, R, bnctx);
    }
    uint64_t t1 = now_ns();

    BN_free(k);
    EC_POINT_free(R);
    return (double)(t1 - t0) / iters;
}

int main(int argc, char **argv) {
    int add_iters = 200000;
    int mul_iters = 20000;
    int reps = 15;

    for (int i=1;i<argc;i++){
        if(!strcmp(argv[i],"--add-iters") && i+1<argc) add_iters = atoi(argv[++i]);
        else if(!strcmp(argv[i],"--mul-iters") && i+1<argc) mul_iters = atoi(argv[++i]);
        else if(!strcmp(argv[i],"--reps") && i+1<argc) reps = atoi(argv[++i]);
        else if(!strcmp(argv[i],"--help")) { usage(argv[0]); return 0; }
        else { printf("Unknown arg: %s\n", argv[i]); usage(argv[0]); return 1; }
    }
    if (reps < 3) reps = 3;

    EC_GROUP *grp = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
    BN_CTX *bnctx = BN_CTX_new();
    if (!grp || !bnctx) { fprintf(stderr, "OpenSSL init failed\n"); return 1; }

    double *A = malloc(sizeof(double)*reps);
    double *M = malloc(sizeof(double)*reps);

    for (int r=0;r<reps;r++){
        A[r] = meas_point_add(grp, bnctx, add_iters);
        M[r] = meas_scalar_mul(grp, bnctx, mul_iters);
    }

    printf("ECC: P-256 ops (OpenSSL, lightweight sink)\n");
    printf("Config: add_iters=%d mul_iters=%d reps=%d\n", add_iters, mul_iters, reps);
    print("PointAdd", A, reps);
    print("ScalarMul", M, reps);
    printf("(sink=%llu)\n", (unsigned long long)sink);

    free(A); free(M);
    BN_CTX_free(bnctx);
    EC_GROUP_free(grp);
    return 0;
}
