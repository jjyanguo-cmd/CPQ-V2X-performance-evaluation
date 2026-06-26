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
# 1) Paper style
# =============================================================================
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.size'] = 7.2
mpl.rcParams['axes.linewidth'] = 0.65
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman', 'Times', 'Nimbus Roman', 'DejaVu Serif']
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['xtick.major.width'] = 0.55
mpl.rcParams['ytick.major.width'] = 0.55
mpl.rcParams['xtick.minor.width'] = 0.45
mpl.rcParams['ytick.minor.width'] = 0.45

# =============================================================================
# 2) Figure style
# =============================================================================
FIG_W, FIG_H = 3.35, 2.45
AXLABEL_FS = 7.2
TICK_FS = 6.2
LEGEND_FS = 5.6
LINE_W = 1.2
MARKER_SZ = 3.2
CAPSIZE = 2.0
ERR_LW = 0.6
GRID_LW = 0.30

# =============================================================================
# 3) Load data
# =============================================================================
df = pd.read_csv(CSV_PATH)
df["vehicle_count"] = pd.to_numeric(df["vehicle_count"], errors="coerce")
df = df.dropna(subset=["vehicle_count"]).sort_values("vehicle_count").reset_index(drop=True)

# Keep only vehicle-count settings from 100 to 1000.
df = df[(df["vehicle_count"] >= 100) & (df["vehicle_count"] <= 1000)].copy()

# =============================================================================
# 4) Scheme definitions
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

# Colors, markers, and line styles.
style_map = {
    "Cui et al. [25]":         dict(color="#7F7F7F", marker="o", linestyle="-"),
    "Dabra et al. [17]":       dict(color="#9A9A9A", marker="s", linestyle="--"),
    "Cui et al. [33]":         dict(color="#B0B0B0", marker="^", linestyle="-."),
    "Yan et al. [35]":         dict(color="#8C8C8C", marker="D", linestyle=":"),
    "Ours (Intra-AKA)":        dict(color="#4C78A8", marker="o", linestyle="-"),
    "Ours (Inter-AKA)":        dict(color="#F58518", marker="s", linestyle="--"),
    "Ours (Intra-Re-AKA)":     dict(color="#54A24B", marker="^", linestyle="-"),
    "Ours (Inter-Re-AKA)":     dict(color="#E45756", marker="D", linestyle="--"),
}

# =============================================================================
# 5) Plot
# =============================================================================
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=300)

x = df["vehicle_count"].values

for scheme, (mean_col, std_col) in scheme_map.items():
    if mean_col not in df.columns or std_col not in df.columns:
        print(f"[Warning] Missing columns for {scheme}: {mean_col} / {std_col}")
        continue

    y = pd.to_numeric(df[mean_col], errors="coerce").values
    yerr = pd.to_numeric(df[std_col], errors="coerce").fillna(0).values

    style = style_map[scheme]

    ax.errorbar(
        x, y, yerr=yerr,
        label=scheme,
        color=style["color"],
        linestyle=style["linestyle"],
        marker=style["marker"],
        linewidth=LINE_W,
        markersize=MARKER_SZ,
        capsize=CAPSIZE,
        elinewidth=ERR_LW,
        capthick=ERR_LW,
        zorder=3
    )

# =============================================================================
# 6) Axes / grid / legend
# =============================================================================
ax.set_xlabel("Number of vehicles", fontsize=AXLABEL_FS, labelpad=1.5)
ax.set_ylabel("Average latency (ms)", fontsize=AXLABEL_FS, labelpad=1.5)

ax.set_xticks(x)
ax.tick_params(axis='x', labelsize=TICK_FS, length=2.4, pad=1.0)
ax.tick_params(axis='y', labelsize=TICK_FS, length=2.4, pad=1.0)

ax.grid(True, linestyle="--", linewidth=GRID_LW, alpha=0.50)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

legend = ax.legend(
    loc="upper left",
    fontsize=LEGEND_FS,
    frameon=True,
    ncol=2,
    handlelength=2.0,
    columnspacing=0.8,
    borderpad=0.3
)
legend.get_frame().set_linewidth(0.5)
legend.get_frame().set_alpha(0.95)

plt.tight_layout(pad=0.35)

# =============================================================================
# 7) Save
# =============================================================================
out_pdf = OUTPUT_DIR / "Fig_Latency_vs_Vehicles.pdf"
out_png = OUTPUT_DIR / "Fig_Latency_vs_Vehicles.png"

plt.savefig(out_pdf, bbox_inches="tight")
plt.savefig(out_png, bbox_inches="tight", dpi=600)
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
