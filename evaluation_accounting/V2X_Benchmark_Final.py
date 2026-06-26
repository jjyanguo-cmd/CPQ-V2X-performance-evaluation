import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BASELINE_ACCOUNTING = PACKAGE_ROOT / "baseline_accounting"
if str(BASELINE_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(BASELINE_ACCOUNTING))
CPQ_ACCOUNTING = PACKAGE_ROOT / "cpq_accounting"
if str(CPQ_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(CPQ_ACCOUNTING))

from baseline_model import side_tuple  # noqa: E402
from cpq_model import mode_tuple  # noqa: E402

# =============================================================================
# 1. Hardware benchmark data synchronized with the manuscript tables and measured values.
# =============================================================================
T = {
    "H1": 0.382, "H2": 0.382, "H3": 0.382, # All hash calls use the measured SHA3-256 cost.
    "Enc": 0.515, "Dec": 0.506,
    "SampR": 0.792, "SampZ": 3.045, "Sampq": 3.045, # T_Sampq is mapped to T_SampZ in this accounting model.
    "RM": 4.486, "RA": 0.007,
    "AM": 1.781, "VA": 0.015, "SV": 0.640,
    "Rec": 0.010, # Covers Cha and Mod2.
    "ECMul": 35.125, "Rand": 0.792, "XOR": 0.001, "cat": 0.001,
    
    # Blockchain-related costs used for the Yan et al. baseline.
    "T_SC_ver": 7.391, 
    "T_prep": 35.507   
}

# =============================================================================
# 2. Scheme cost definitions aligned with the manuscript equations.
# =============================================================================

# --- Case 1: Intra-domain initial AKA ---
def eval_ours_intra():
    return mode_tuple("cpq_intra_aka")

# --- Case 2: Inter-domain initial AKA ---
def eval_ours_inter():
    return mode_tuple("cpq_inter_aka")

# --- Case 3: Intra-domain re-authentication ---
def eval_ours_re_intra():
    return mode_tuple("cpq_intra_re_aka")

# --- Case 4: Inter-domain re-authentication ---
def eval_ours_re_inter():
    return mode_tuple("cpq_inter_re_aka")

# --- Baseline schemes ---
# Baseline side totals are computed from baseline_accounting/baseline_operation_counts.csv.
def eval_cui(): return side_tuple("Cui2025_VDT")
def eval_yan(): return side_tuple("Yan2025_BCL3AKA")
def eval_sl3(): return side_tuple("Dabra2024_SL3PAKE")
def eval_ecpp(): return side_tuple("Cui2019_ECPP")

# =============================================================================
# 3. Summarize and print results.
# =============================================================================
schemes = {
    "Cui et al.": eval_cui(),
    "Yan et al.": eval_yan(),
    "SL3PAKE": eval_sl3(),
    "ECPP": eval_ecpp(),
    "Ours (Intra)": eval_ours_intra(),
    "Ours (Inter)": eval_ours_inter(),
    "Ours (Re-In)": eval_ours_re_intra(),
    "Ours (Re-Ex)": eval_ours_re_inter()
}

df = pd.DataFrame(schemes, index=["Vehicle", "Infrastructure", "Authority"]).T
df["Total"] = df.sum(axis=1)

print("\n" + "="*80)
print("   COMPUTATION OVERHEAD FINAL REPORT (4 CPQ-V2X SCENARIOS)")
print("="*80)
print(df.to_string(float_format="%.3f"))
print("="*80 + "\n")

# =============================================================================
# 4. Publication-style plotting.
# =============================================================================
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 10
fig, ax = plt.subplots(figsize=(14, 6), dpi=300)

x = np.arange(len(df))
width = 0.55
colors = ['#4C72B0', '#55A868', '#C44E52']

bottom = np.zeros(len(df))
for i, col in enumerate(["Vehicle", "Infrastructure", "Authority"]):
    ax.bar(x, df[col], width, bottom=bottom, label=col, color=colors[i], edgecolor='black', linewidth=0.6)
    bottom += df[col]

ax.set_ylabel(r'Computation Overhead ($\mu$s)', fontsize=12, fontweight='bold')
ax.set_title('Computation Cost Comparison (Validated against Formula 7-16)', fontsize=13, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(df.index, rotation=25)
ax.legend(frameon=True, shadow=True, loc='upper left')
ax.yaxis.grid(True, linestyle='--', alpha=0.7)

for i, total in enumerate(df["Total"]):
    ax.text(i, total + 2, f'{total:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close()
