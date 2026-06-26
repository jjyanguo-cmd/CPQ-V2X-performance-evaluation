import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. Primitive-operation cost definitions (unit: microseconds).
# Data source: manuscript primitive-cost table under the 128-bit baseline.
# ==========================================
T_H = 0.382      # Hash (SHA3-256)
T_Enc = 0.515    # AEAD Encryption (AES-GCM)
T_Dec = 0.506    # AEAD Decryption (AES-GCM)
T_SampR = 0.792  # Ring Noise Sampling (eta1)
T_SampZ = 3.045  # Vector Sampling in Z_q^512
T_RM = 4.486     # Ring Multiplication (NTT)
T_RA = 0.007     # Ring Addition
T_AM = 1.781     # Matrix-Vector Multiplication Core
T_SV = 0.640     # Scalar-Vector Scaling
T_VA = 0.015     # Vector Addition
T_Rec = 0.010    # Reconciliation (Cha + Mod2)

# ==========================================
# 2. Compute phase costs according to the manuscript formulas.
# ==========================================

# --- Intra-Domain AKA ---
# Vehicle: Eq.(21)
t_intra_v = (T_Enc + 2*T_SampR + (T_RM + T_RA) + T_H + 
             T_SampZ + 2*(T_RM + T_RA) + T_Rec + T_H + 
             2*T_H + (T_AM + 2*T_SV + 2*T_VA) + 
             (T_SampZ + T_AM) + (T_SV + T_VA))

# RSU: Eq.(22)
t_intra_rsu = (T_H + 4*T_SampR + (T_RM + T_RA) + (2*T_RM + 2*T_RA) + 
               T_Rec + T_H + T_Enc + (T_SampZ + T_AM) + T_H + 
               (T_SV + T_VA) + T_H + (T_AM + 2*T_SV + 2*T_VA))

# --- Inter-Domain AKA ---
# Inter-domain verification adds one SV and one VA operation relative to intra-domain verification.
t_inter_v = (T_Enc + 2*T_SampR + (T_RM + T_RA) + T_H + 
             T_SampZ + 2*(T_RM + T_RA) + T_Rec + T_H + 
             2*T_H + (T_AM + 3*T_SV + 3*T_VA) + 
             (T_SampZ + T_AM) + (T_SV + T_VA))

t_inter_rsu = (T_H + 4*T_SampR + (T_RM + T_RA) + (2*T_RM + 2*T_RA) + 
               T_Rec + T_H + T_Enc + (T_SampZ + T_AM) + T_H + 
               (T_SV + T_VA) + T_H + (T_AM + 3*T_SV + 3*T_VA))

# --- Re-authentication (Lightweight Mode) ---
# Intra Re-Auth
t_re_intra_v = ((2*T_SampR + T_SampZ) + 2*(T_RM + T_RA) + T_Rec + T_H + T_H + 
                (T_SV + T_VA) + T_H + (T_AM + 2*T_SV + 2*T_VA))

t_re_intra_rsu = (T_SampZ + 2*(T_RM + T_RA) + T_Rec + T_H + T_H + 
                  (T_AM + 2*T_SV + 2*T_VA) + T_H + (T_SV + T_VA))

# Inter Re-Auth
t_re_inter_v = ((2*T_SampR + T_SampZ) + 2*(T_RM + T_RA) + T_Rec + T_H + T_H + 
                (T_SV + T_VA) + T_H + (T_AM + 3*T_SV + 3*T_VA))

t_re_inter_rsu = (T_SampZ + 2*(T_RM + T_RA) + T_Rec + T_H + T_H + 
                  (T_AM + 3*T_SV + 3*T_VA) + T_H + (T_SV + T_VA))

# ==========================================
# 3. Print result table.
# ==========================================
scenarios = ["Intra-AKA", "Inter-AKA", "Re-Auth(Intra)", "Re-Auth(Inter)"]
v_costs = [t_intra_v, t_inter_v, t_re_intra_v, t_re_inter_v]
rsu_costs = [t_intra_rsu, t_inter_rsu, t_re_intra_rsu, t_re_inter_rsu]

print(f"{'Scenario':<20} | {'Vehicle (us)':<12} | {'RSU (us)':<12} | {'Total (us)':<12}")
print("-" * 65)
for i in range(len(scenarios)):
    total = v_costs[i] + rsu_costs[i]
    print(f"{scenarios[i]:<20} | {v_costs[i]:<12.3f} | {rsu_costs[i]:<12.3f} | {total:<12.3f}")

# ==========================================
# 4. Plot figure for manuscript evaluation.
# ==========================================
x = np.arange(len(scenarios))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5))
rects1 = ax.bar(x - width/2, v_costs, width, label='Vehicle', color='#3498db', edgecolor='black')
rects2 = ax.bar(x + width/2, rsu_costs, width, label='RSU', color='#e74c3c', edgecolor='black')

ax.set_ylabel('Computation Overhead (us)')
ax.set_title('Computational Cost Comparison of CPQ-V2X')
ax.set_xticks(x)
ax.set_xticklabels(scenarios)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

fig.tight_layout()
if __import__("os").environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)
