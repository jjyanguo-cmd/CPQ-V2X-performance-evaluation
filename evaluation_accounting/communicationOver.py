import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
COMMUNICATION_ACCOUNTING = PACKAGE_ROOT / "communication_accounting"
if str(COMMUNICATION_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(COMMUNICATION_ACCOUNTING))

from communication_model import side_tuple  # noqa: E402

# =========================================================
# 0) Output directory: same folder as this .py file
# =========================================================
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "communication_overhead"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# 1) Paper style for small figure (~0.6 column width)
# =========================================================
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman', 'Times', 'Nimbus Roman', 'DejaVu Serif']
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42

# compact typography for a very small figure
mpl.rcParams['font.size'] = 5.8
mpl.rcParams['axes.labelsize'] = 5.8
mpl.rcParams['xtick.labelsize'] = 5.2
mpl.rcParams['ytick.labelsize'] = 5.4
mpl.rcParams['legend.fontsize'] = 5.2

mpl.rcParams['axes.linewidth'] = 0.45
mpl.rcParams['xtick.major.width'] = 0.40
mpl.rcParams['ytick.major.width'] = 0.40
mpl.rcParams['xtick.minor.width'] = 0.35
mpl.rcParams['ytick.minor.width'] = 0.35
mpl.rcParams['xtick.major.size'] = 2.0
mpl.rcParams['ytick.major.size'] = 0.0

# =========================================================
# 2) Data (must match the table exactly)
#    Unit: bytes
# =========================================================
schemes = np.array([
    "Cui et al. [25]",
    "Dabra et al. [17]",
    "Cui et al. [33]",
    "Yan et al. [35]",
    "Ours (Intra-AKA)",
    "Ours (Inter-AKA)",
    "Ours (Intra-Re-AKA)",
    "Ours (Inter-Re-AKA)"
], dtype=object)

_scheme_keys = [
    "Cui2019_ECPP",
    "Dabra2024_SL3PAKE",
    "Cui2025_VDT",
    "Yan2025_BCL3AKA",
    "cpq_intra_aka",
    "cpq_inter_aka",
    "cpq_intra_re_aka",
    "cpq_inter_re_aka",
]
_comm = [side_tuple(key) for key in _scheme_keys]
veh = np.array([item[0] for item in _comm], dtype=float)
rsu = np.array([item[1] for item in _comm], dtype=float)
ta = np.array([item[2] for item in _comm], dtype=float)

total = veh + rsu + ta

# =========================================================
# 3) Reverse order so that "Ours" appears near the top
# =========================================================
schemes = schemes[::-1]
veh = veh[::-1]
rsu = rsu[::-1]
ta = ta[::-1]
total = total[::-1]

# =========================================================
# 4) Colors
# =========================================================
C_VEH = "#4C78A8"
C_RSU = "#F58518"
C_TA  = "#54A24B"
BG_OURS = "#F5F5F5"

# =========================================================
# 5) Figure size
#    Suitable for ~0.6 of a double-column single column width
# =========================================================
FIG_W_IN = 2.5
FIG_H_IN = 2.12
bar_h = 0.52
pad = max(total) * 0.008
xmax_est = max(total) * 1.10
DPI = 600

fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), dpi=DPI)

y = np.arange(len(schemes))
bar_h = 0.48
edge_c = "black"
lw_bar = 0.20
lw_outline = 0.32

# =========================================================
# 6) Highlight our rows
# =========================================================
xmax_est = max(total) * 1.11
for yi, name in enumerate(schemes):
    if str(name).startswith("Ours"):
        ax.axhspan(yi - 0.34, yi + 0.34, color=BG_OURS, zorder=0)

# =========================================================
# 7) Plot stacked horizontal bars
# =========================================================
ax.barh(
    y, veh, height=bar_h, color=C_VEH, edgecolor=edge_c,
    linewidth=lw_bar, label="Vehicle", zorder=3
)
ax.barh(
    y, rsu, height=bar_h, left=veh, color=C_RSU, edgecolor=edge_c,
    linewidth=lw_bar, label="RSU", zorder=3
)
ax.barh(
    y, ta, height=bar_h, left=veh + rsu, color=C_TA, edgecolor=edge_c,
    linewidth=lw_bar, label="TA/Chain", zorder=3
)

# add a thin outline for our schemes
for yi, name in enumerate(schemes):
    if str(name).startswith("Ours"):
        ax.barh(
            yi, total[yi], height=bar_h,
            color="none", edgecolor="black",
            linewidth=lw_outline, zorder=4
        )

# =========================================================
# 8) Annotate totals
# =========================================================
pad = max(total) * 0.008
for yi, t in zip(y, total):
    ax.text(
        t + pad, yi, f"{int(t)}",
        va="center", ha="left",
        fontsize=4.9
    )

# =========================================================
# 9) Axes and grid
# =========================================================
ax.set_xlabel("Communication overhead (bytes)", labelpad=1.2)

ax.set_yticks(y)
ax.set_yticklabels(schemes)

ax.tick_params(axis='x', length=2.0, pad=0.8)
ax.tick_params(axis='y', length=0, pad=1.0)

ax.grid(True, axis="x", linestyle="--", linewidth=0.24, alpha=0.50)
ax.set_axisbelow(True)
ax.set_xlim(0, xmax_est)

# make x ticks a bit cleaner for small figure
ax.xaxis.set_major_locator(plt.MaxNLocator(4))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =========================================================
# 10) Legend
# =========================================================
leg = ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 1.03),
    ncol=3,
    frameon=True,
    edgecolor="black",
    handlelength=1.0,
    columnspacing=0.55,
    handletextpad=0.35,
    borderpad=0.20,
    labelspacing=0.20
)
leg.get_frame().set_linewidth(0.35)

# =========================================================
# 11) Layout
# =========================================================
plt.tight_layout(pad=0.20)

# =========================================================
# 12) Save
# =========================================================
out_pdf = OUTPUT_DIR / "CommunicationOverhead_single_session_comparison_small.pdf"
out_png = OUTPUT_DIR / "CommunicationOverhead_single_session_comparison_small.png"

plt.savefig(out_pdf, bbox_inches="tight", pad_inches=0.01)
plt.savefig(out_png, bbox_inches="tight", pad_inches=0.01, dpi=600)
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
