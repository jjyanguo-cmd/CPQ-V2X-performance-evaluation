import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

# =============================================================================
# 0) Paths
# =============================================================================
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PACKAGE_ROOT / "results" / "latency_throughput_mean_std.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 1) Paper style for very compact side-by-side subfigures
# =============================================================================
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.size'] = 6.8
mpl.rcParams['axes.linewidth'] = 0.6
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman', 'Times', 'Nimbus Roman', 'DejaVu Serif']
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['xtick.major.width'] = 0.55
mpl.rcParams['ytick.major.width'] = 0.55
mpl.rcParams['xtick.minor.width'] = 0.45
mpl.rcParams['ytick.minor.width'] = 0.45

# =============================================================================
# 2) Unified compact figure style
# =============================================================================
FIG_W, FIG_H = 2.55, 2.05
TICK_FS = 5.8
YTICK_FS = 5.7
AXLABEL_FS = 6.6
GRID_LW = 0.28

BAR_H = 0.56
EDGE_LW = 0.28
ANNOT_FS = 5.1

BASELINE_COLOR = "#AFAFAF"
OURS_COLOR = "#4C78A8"

# =============================================================================
# 3) Load data
# =============================================================================
df = pd.read_csv(CSV_PATH)
df["vehicle_count"] = pd.to_numeric(df["vehicle_count"], errors="coerce")
df = df.sort_values("vehicle_count").reset_index(drop=True)

# throughput is effectively scenario-invariant in the current model,
# so use the mean columns from any row
row = df.iloc[0]

# =============================================================================
# 4) Extract throughput data
# =============================================================================
scheme_map = {
    "Cui et al. [25]": "Cui2019_throughput_mbps_mean",
    "Dabra et al. [17]": "Dabra2024_throughput_mbps_mean",
    "Cui et al. [33]": "Cui2025_throughput_mbps_mean",
    "Yan et al. [35]": "Yan2025_throughput_mbps_mean",
    "Ours (Intra-AKA)": "Ours_Intra_AKA_batch_throughput_mbps_mean",
    "Ours (Inter-AKA)": "Ours_Inter_AKA_batch_throughput_mbps_mean",
    "Ours (Intra-Re-AKA)": "Ours_Intra_ReAKA_batch_throughput_mbps_mean",
    "Ours (Inter-Re-AKA)": "Ours_Inter_ReAKA_batch_throughput_mbps_mean",
}

schemes = list(scheme_map.keys())
values = np.array([float(row[col]) for col in scheme_map.values()])

# reverse so first item appears at top
schemes = schemes[::-1]
values = values[::-1]

# =============================================================================
# 5) Plot
# =============================================================================
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=300)

y = np.arange(len(schemes))
bar_colors = [OURS_COLOR if str(name).startswith("Ours") else BASELINE_COLOR for name in schemes]

ax.barh(
    y,
    values,
    height=BAR_H,
    color=bar_colors,
    edgecolor="black",
    linewidth=EDGE_LW,
    zorder=3
)

# annotate values
pad = max(values) * 0.010
for yi, val in zip(y, values):
    ax.text(
        val + pad,
        yi,
        f"{val:.1f}",
        va="center",
        ha="left",
        fontsize=ANNOT_FS
    )

# =============================================================================
# 6) Axes / ticks / grid
# =============================================================================
ax.set_xlabel("Effective throughput (Mbps)", fontsize=AXLABEL_FS, labelpad=1.2)
ax.set_yticks(y)
ax.set_yticklabels(schemes, fontsize=YTICK_FS)

ax.tick_params(axis='x', labelsize=TICK_FS, length=2.0, pad=1.0)
ax.tick_params(axis='y', length=0, pad=1.1)

ax.grid(True, axis="x", linestyle="--", linewidth=GRID_LW, alpha=0.50)
ax.set_axisbelow(True)

xmax = max(values) * 1.18
ax.set_xlim(0, xmax)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =============================================================================
# 7) Save
# =============================================================================
plt.tight_layout(pad=0.22)

out_pdf = OUTPUT_DIR / "Fig_Throughput_Comparison.pdf"
out_png = OUTPUT_DIR / "Fig_Throughput_Comparison.png"

plt.savefig(out_pdf, bbox_inches="tight")
plt.savefig(out_png, bbox_inches="tight", dpi=600)
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
