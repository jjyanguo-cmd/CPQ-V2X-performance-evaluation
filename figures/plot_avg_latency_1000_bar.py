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
FIG_W, FIG_H = 2.60, 2.08
TICK_FS = 5.8
YTICK_FS = 5.7
AXLABEL_FS = 6.6
GRID_LW = 0.28

BAR_H = 0.56
EDGE_LW = 0.28
ANNOT_FS = 4.95
ERR_LW = 0.55
CAPSIZE = 1.8

BASELINE_COLOR = "#AFAFAF"
OURS_COLOR = "#4C78A8"

# =============================================================================
# 3) Load data
# =============================================================================
df = pd.read_csv(CSV_PATH)
df["vehicle_count"] = pd.to_numeric(df["vehicle_count"], errors="coerce")
df = df.sort_values("vehicle_count").reset_index(drop=True)

row_1000 = df.loc[df["vehicle_count"] == 1000]
if row_1000.empty:
    raise ValueError("No row found for vehicle_count == 1000 in the summary CSV.")
row_1000 = row_1000.iloc[0]

# =============================================================================
# 4) Extract mean/std latency data at 1000 vehicles
# =============================================================================
scheme_map = {
    "Cui et al. [25]": ("Cui2019_avg_latency_ms_mean", "Cui2019_avg_latency_ms_std"),
    "Dabra et al. [17]": ("Dabra2024_avg_latency_ms_mean", "Dabra2024_avg_latency_ms_std"),
    "Cui et al. [33]": ("Cui2025_avg_latency_ms_mean", "Cui2025_avg_latency_ms_std"),
    "Yan et al. [35]": ("Yan2025_avg_latency_ms_mean", "Yan2025_avg_latency_ms_std"),
    "Ours (Intra-AKA)": ("Ours_Intra_AKA_batch_avg_latency_ms_mean", "Ours_Intra_AKA_batch_avg_latency_ms_std"),
    "Ours (Inter-AKA)": ("Ours_Inter_AKA_batch_avg_latency_ms_mean", "Ours_Inter_AKA_batch_avg_latency_ms_std"),
    "Ours (Intra-Re-AKA)": ("Ours_Intra_ReAKA_batch_avg_latency_ms_mean", "Ours_Intra_ReAKA_batch_avg_latency_ms_std"),
    "Ours (Inter-Re-AKA)": ("Ours_Inter_ReAKA_batch_avg_latency_ms_mean", "Ours_Inter_ReAKA_batch_avg_latency_ms_std"),
}

schemes = list(scheme_map.keys())
lat_mean = np.array([float(row_1000[mcol]) for mcol, scol in scheme_map.values()])
lat_std  = np.array([float(row_1000[scol]) for mcol, scol in scheme_map.values()])

# reverse so first item appears at top
schemes = schemes[::-1]
lat_mean = lat_mean[::-1]
lat_std  = lat_std[::-1]

# =============================================================================
# 5) Plot
# =============================================================================
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=300)

y = np.arange(len(schemes))
bar_colors = [OURS_COLOR if str(name).startswith("Ours") else BASELINE_COLOR for name in schemes]

ax.barh(
    y,
    lat_mean,
    xerr=lat_std,
    height=BAR_H,
    color=bar_colors,
    edgecolor="black",
    linewidth=EDGE_LW,
    error_kw=dict(
        ecolor="black",
        elinewidth=ERR_LW,
        capsize=CAPSIZE,
        capthick=ERR_LW
    ),
    zorder=3
)

# =============================================================================
# 6) Value annotations
#    Compact spacing: avoid overlap, but keep labels closer to error bars
# =============================================================================
max_extent = np.max(lat_mean + lat_std)

# Compact spacing between value labels and error bars.
min_gap = max_extent * 0.010
max_gap = max_extent * 0.018

for yi, val, err in zip(y, lat_mean, lat_std):
    dynamic_gap = err * 0.22 + max_extent * 0.0035
    gap = np.clip(dynamic_gap, min_gap, max_gap)

    x_text = val + err + gap

    ax.text(
        x_text,
        yi,
        f"{val:.2f}",
        va="center",
        ha="left",
        fontsize=ANNOT_FS,
        zorder=5,
        bbox=dict(
            boxstyle="round,pad=0.10",
            facecolor="white",
            edgecolor="none",
            alpha=0.88
        )
    )

# =============================================================================
# 7) Axes / ticks / grid
# =============================================================================
ax.set_xlabel("Average latency (ms)", fontsize=AXLABEL_FS, labelpad=1.2)
ax.set_yticks(y)
ax.set_yticklabels(schemes, fontsize=YTICK_FS)

ax.tick_params(axis='x', labelsize=TICK_FS, length=2.0, pad=1.0)
ax.tick_params(axis='y', length=0, pad=1.1)

ax.grid(True, axis="x", linestyle="--", linewidth=GRID_LW, alpha=0.50)
ax.set_axisbelow(True)

# Keep the right-side margin compact as well.
label_right = np.max(lat_mean + lat_std + max_gap) + max_extent * 0.035
ax.set_xlim(0, label_right)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =============================================================================
# 8) Save
# =============================================================================
plt.tight_layout(pad=0.22)

out_pdf = OUTPUT_DIR / "Fig_AvgLatency_1000_Bar_optimized.pdf"
out_png = OUTPUT_DIR / "Fig_AvgLatency_1000_Bar_optimized.png"

plt.savefig(out_pdf, bbox_inches="tight")
plt.savefig(out_png, bbox_inches="tight", dpi=600)
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
