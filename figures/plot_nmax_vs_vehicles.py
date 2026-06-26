import pandas as pd
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from pathlib import Path
import os

# =============================================================================
# 0) Paths
# =============================================================================
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PACKAGE_ROOT / "results" / "latency_throughput_mean_std.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 1) Paper style for small figure
# =============================================================================
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman', 'Times', 'Nimbus Roman', 'DejaVu Serif']
mpl.rcParams['font.size'] = 6.1
mpl.rcParams['axes.linewidth'] = 0.58
mpl.rcParams['axes.labelsize'] = 6.1
mpl.rcParams['xtick.labelsize'] = 5.4
mpl.rcParams['ytick.labelsize'] = 5.4
mpl.rcParams['xtick.major.width'] = 0.50
mpl.rcParams['ytick.major.width'] = 0.50
mpl.rcParams['xtick.minor.width'] = 0.40
mpl.rcParams['ytick.minor.width'] = 0.40
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42

# =============================================================================
# 2) Figure style
# =============================================================================
FIG_W, FIG_H = 2.16, 1.50
MAIN_LW = 0.82
MAIN_MS = 1.8
BAND_ALPHA = 0.10
GRID_LW = 0.22
AXLABEL_FS = 6.1
TICK_FS = 5.4

MAIN_COLOR = "#0072B2"
MAIN_MARKER = "o"
MAIN_LINESTYLE = "-"

# =============================================================================
# 3) Load data
# =============================================================================
df = pd.read_csv(CSV_PATH)
df["vehicle_count"] = pd.to_numeric(df["vehicle_count"], errors="coerce")
df["nmax_mean"] = pd.to_numeric(df["nmax_mean"], errors="coerce")
df["nmax_std"] = pd.to_numeric(df["nmax_std"], errors="coerce")
df = df.sort_values("vehicle_count").reset_index(drop=True)

x = df["vehicle_count"].to_numpy()
y = df["nmax_mean"].to_numpy()
ystd = df["nmax_std"].to_numpy()

y_lower = y - ystd
y_upper = y + ystd

# show markers only on selected points for a cleaner small figure
mark_idx = [0, 2, 4, 6, 8, 9]

# =============================================================================
# 4) Plot
# =============================================================================
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=300)

# shaded uncertainty band
ax.fill_between(
    x, y_lower, y_upper,
    color=MAIN_COLOR,
    alpha=BAND_ALPHA,
    linewidth=0,
    zorder=1
)

# main mean curve
ax.plot(
    x, y,
    color=MAIN_COLOR,
    linestyle=MAIN_LINESTYLE,
    linewidth=MAIN_LW,
    marker=MAIN_MARKER,
    markersize=MAIN_MS,
    markerfacecolor=MAIN_COLOR,
    markeredgewidth=0.0,
    markevery=mark_idx,
    zorder=3
)

# =============================================================================
# 5) Axes / ticks / grid
# =============================================================================
ax.set_xlabel("Number of vehicles", fontsize=AXLABEL_FS, labelpad=0.8)
ax.set_ylabel("Peak concurrent requests", fontsize=AXLABEL_FS, labelpad=0.8)

ax.set_xlim(80, 1020)
ax.set_xticks([200, 400, 600, 800, 1000])
ax.xaxis.set_major_locator(MultipleLocator(200))

ax.set_ylim(0, 140)
ax.set_yticks([0, 40, 80, 120])

ax.tick_params(axis='both', labelsize=TICK_FS, length=1.9, pad=0.7)

ax.grid(True, which='major', linestyle='--', linewidth=GRID_LW, alpha=0.42)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# =============================================================================
# 6) Save
# =============================================================================
plt.tight_layout(pad=0.16)

out_pdf = OUTPUT_DIR / "Fig_Nmax_vs_Vehicles.pdf"
out_png = OUTPUT_DIR / "Fig_Nmax_vs_Vehicles.png"

plt.savefig(out_pdf, bbox_inches="tight")
plt.savefig(out_png, bbox_inches="tight", dpi=600)
if os.environ.get("CPQ_SHOW_FIGURES") == "1":
    plt.show()
plt.close(fig)

print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")
