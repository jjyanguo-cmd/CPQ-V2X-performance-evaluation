import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from pathlib import Path

from energy_overhead_analysis import EnergyConfig, concurrent_energy


# =============================================================================
# 0) Output directory
# =============================================================================
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "energy_overhead"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 1) Paper style
# =============================================================================
mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.size"] = 6.5
mpl.rcParams["axes.linewidth"] = 0.6
mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.serif"] = ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"]
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["xtick.major.width"] = 0.55
mpl.rcParams["ytick.major.width"] = 0.55
mpl.rcParams["xtick.minor.width"] = 0.45
mpl.rcParams["ytick.minor.width"] = 0.45

# =============================================================================
# 2) Unified small-figure style
# =============================================================================
FIG_W, FIG_H = 1.78, 1.42

MAIN_LW = 0.75
MAIN_MS = 2.0

TICK_FS = 5.4
AXLABEL_FS = 6.2
GRID_LW = 0.28

# =============================================================================
# 3) Data
# =============================================================================
SCHEME_LABELS = {
    "Cui2019": "Cui et al. [25]",
    "Dabra2024": "Dabra et al. [17]",
    "Cui2025": "Cui et al. [33]",
    "Yan2025": "Yan et al. [35]",
    "Ours-Intra-AKA": "Ours (Intra-AKA)",
    "Ours-Inter-AKA": "Ours (Inter-AKA)",
    "Ours-Intra-Re-AKA": "Ours (Intra-Re-AKA)",
    "Ours-Inter-Re-AKA": "Ours (Inter-Re-AKA)",
}
schemes = list(SCHEME_LABELS.keys())
cfg = EnergyConfig()

palette = ["#000000", "#E69F00", "#56B4E9", "#009E73",
           "#D55E00", "#0072B2", "#CC79A7", "#7F7F7F"]
markers = ["o", "s", "^", "v", "D", "P", "X", "*"]
linestyles = ["-", "--", "-.", ":", "-", "--", "-.", ":"]

colors_dict = {schemes[i]: palette[i] for i in range(len(schemes))}
markers_dict = {schemes[i]: markers[i] for i in range(len(schemes))}
styles_dict = {schemes[i]: linestyles[i] for i in range(len(schemes))}


# =============================================================================
# 4) Energy model
# =============================================================================
def get_cost_mj(name: str, n_requests: int) -> float:
    return concurrent_energy(name, n_requests, cfg)["E_total_mJ"]


# =============================================================================
# 5) Plot
# =============================================================================
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=300)

N_vals = np.arange(1, 1001)
mark_idx = list(range(0, len(N_vals), 100)) + [len(N_vals) - 1]

for name in schemes:
    y = np.array([get_cost_mj(name, int(N)) for N in N_vals])
    ax.plot(
        N_vals,
        y,
        label=SCHEME_LABELS[name],
        color=colors_dict[name],
        linestyle=styles_dict[name],
        linewidth=MAIN_LW,
        marker=markers_dict[name],
        markersize=MAIN_MS,
        markevery=mark_idx,
    )

# =============================================================================
# 6) Axes
# =============================================================================
ax.set_xlabel(r"Number of concurrent requests $N$", fontsize=AXLABEL_FS, labelpad=1.5)
ax.set_ylabel(r"Total energy overhead (mJ)", fontsize=AXLABEL_FS, labelpad=1.5)

ax.set_xlim(1, 1000)
ax.set_ylim(0, 6500)
ax.xaxis.set_major_locator(MultipleLocator(200))
ax.yaxis.set_major_locator(MultipleLocator(1000))

ax.tick_params(axis="both", labelsize=TICK_FS, length=2.2, pad=1.0)
ax.grid(True, which="major", linestyle="--", linewidth=GRID_LW, alpha=0.5)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =============================================================================
# 7) Legend
# =============================================================================
leg = ax.legend(
    fontsize=4.1,
    ncol=2,
    frameon=True,
    edgecolor="black",
    loc="upper left",
    bbox_to_anchor=(0.005, 1.02),
    handlelength=1,
    labelspacing=0.12,
    markerscale=0.52,
    borderpad=0.10,
    handletextpad=0.5,
    columnspacing=0.2,
)
leg.get_frame().set_linewidth(0.5)

plt.tight_layout(pad=0.30)

# =============================================================================
# 8) Save
# =============================================================================
out_pdf = OUTPUT_DIR / "Energy_Total.pdf"
out_png = OUTPUT_DIR / "Energy_Total.png"
plt.savefig(out_pdf, bbox_inches="tight", pad_inches=0.01)
plt.savefig(out_png, bbox_inches="tight", dpi=600, pad_inches=0.01)
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
