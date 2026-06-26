import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, LogLocator, NullLocator, FixedLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
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
# 0) Output directory
# =============================================================================
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "computation_overhead"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 1) Paper style for 2x2 subfigures in one journal column
# =============================================================================
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.size'] = 6.5
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
# 2) Unified small-figure style
# =============================================================================
FIG_W, FIG_H = 1.78, 1.42

MAIN_LW = 0.75
MAIN_MS = 2.0

INSET_LW = 0.78
INSET_MS = 1.4

TICK_FS = 5.4
INSET_TICK_FS = 4.5
AXLABEL_FS = 6.2

GRID_LW = 0.28
INSET_EDGE_LW = 0.55

# =============================================================================
# 3) Data
# =============================================================================
data_map = {
    "Cui et al. [25]":   side_tuple("Cui2019_ECPP"),
    "Dabra et al. [17]": side_tuple("Dabra2024_SL3PAKE"),
    "Cui et al. [33]":   side_tuple("Cui2025_VDT"),
    "Yan et al. [35]":   side_tuple("Yan2025_BCL3AKA"),
    "Ours (Intra-AKA)":    mode_tuple("cpq_intra_aka"),
    "Ours (Inter-AKA)":    mode_tuple("cpq_inter_aka"),
    "Ours (Intra-Re-AKA)": mode_tuple("cpq_intra_re_aka"),
    "Ours (Inter-Re-AKA)": mode_tuple("cpq_inter_re_aka"),
}
schemes = list(data_map.keys())

palette = ['#000000', '#E69F00', '#56B4E9', '#009E73',
           '#D55E00', '#0072B2', '#CC79A7', '#7F7F7F']
markers = ['o', 's', '^', 'v', 'D', 'P', 'X', '*']
linestyles = ['-', '--', '-.', ':', '-', '--', '-.', ':']

colors_dict = {schemes[i]: palette[i] for i in range(len(schemes))}
markers_dict = {schemes[i]: markers[i] for i in range(len(schemes))}
styles_dict = {schemes[i]: linestyles[i] for i in range(len(schemes))}

# =============================================================================
# 4) Cost model
# =============================================================================
def get_cost_ms(name, N):
    v = data_map[name][0]
    return v * N / 1000.0

# =============================================================================
# 5) Plot
# =============================================================================
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=300)

N_vals = np.arange(1, 1001)
mark_idx = list(range(0, len(N_vals), 100)) + [len(N_vals) - 1]
curve_cache = {}

for name in schemes:
    y = np.array([get_cost_ms(name, int(N)) for N in N_vals])
    curve_cache[name] = y
    ax.plot(
        N_vals, y,
        color=colors_dict[name],
        linestyle=styles_dict[name],
        linewidth=MAIN_LW,
        marker=markers_dict[name],
        markersize=MAIN_MS,
        markevery=mark_idx,
    )

ax.set_yscale('log')
ax.set_xlabel(r'Number of concurrent requests $N$', fontsize=AXLABEL_FS, labelpad=1.5)
ax.set_ylabel(r'Vehicle overhead (ms)', fontsize=AXLABEL_FS, labelpad=1.5)
ax.set_xlim(1, 1000)
ax.xaxis.set_major_locator(MultipleLocator(200))
ax.yaxis.set_major_locator(LogLocator(base=10, numticks=5))
ax.tick_params(axis='both', labelsize=TICK_FS, length=2.2, pad=1)
ax.grid(True, which='major', linestyle='--', linewidth=GRID_LW, alpha=0.5)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =============================================================================
# 6) inset: zoom tail region (800-1000)
# =============================================================================
axins = inset_axes(
    ax,
    width="86%",
    height="86%",
    loc="center",
    borderpad=0.04,
    bbox_to_anchor=(0.35, 0.15, 0.4, 0.4),
    bbox_transform=ax.transAxes,
)

inset_edge_color = "0.30"
inset_edge_lw = INSET_EDGE_LW

inset_schemes = [
        "Yan et al. [35]",

    "Cui et al. [33]",
    "Ours (Intra-AKA)",
    "Ours (Inter-AKA)",
    "Ours (Intra-Re-AKA)",
    "Ours (Inter-Re-AKA)",
]

for name in inset_schemes:
    axins.plot(
        N_vals, curve_cache[name],
        color=colors_dict[name],
        linestyle=styles_dict[name],
        linewidth=INSET_LW,
        marker=markers_dict[name],
        markersize=INSET_MS,
        markevery=mark_idx,
    )

x1, x2 = 800, 1000
idx = (N_vals >= x1) & (N_vals <= x2)
y_all = np.concatenate([curve_cache[name][idx] for name in inset_schemes])

ymin, ymax = np.min(y_all), np.max(y_all)
ymin /= 1.05
ymax *= 1.05

axins.set_xlim(x1, x2)
axins.set_ylim(ymin, ymax)
axins.set_yscale("log")

axins.xaxis.set_major_locator(FixedLocator([800, 900, 1000]))
axins.yaxis.set_major_locator(LogLocator(base=10, numticks=4))
axins.yaxis.set_minor_locator(NullLocator())
axins.yaxis.set_ticks_position('left')
axins.tick_params(axis='y', which='major', labelleft=True, labelright=False)
axins.tick_params(axis='both', labelsize=INSET_TICK_FS, length=1.6, pad=0.8)
axins.grid(True, which='major', linestyle='--', linewidth=0.22, alpha=0.45)

for spine in axins.spines.values():
    spine.set_linewidth(inset_edge_lw)
    spine.set_edgecolor(inset_edge_color)

axins.spines['left'].set_visible(True)
axins.spines['right'].set_visible(True)
axins.spines['top'].set_visible(True)
axins.spines['bottom'].set_visible(True)

mark_inset(
    ax, axins,
    loc1=2, loc2=4,
    fc="none",
    ec=inset_edge_color,
    lw=inset_edge_lw
)

plt.tight_layout(pad=0.30)

out_pdf = OUTPUT_DIR / "Comp_Vehicle.pdf"
out_png = OUTPUT_DIR / "Comp_Vehicle.png"
plt.savefig(out_pdf, bbox_inches='tight')
plt.savefig(out_png, bbox_inches='tight', dpi=600)
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
