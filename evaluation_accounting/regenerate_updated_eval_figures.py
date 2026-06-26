import os
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASELINE_ACCOUNTING = ROOT / "baseline_accounting"
if str(BASELINE_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(BASELINE_ACCOUNTING))
CPQ_ACCOUNTING = ROOT / "cpq_accounting"
if str(CPQ_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(CPQ_ACCOUNTING))

from baseline_model import side_tuple, total_value  # noqa: E402
from cpq_model import batch_rsu_expr, batch_total_alpha, mode_tuple  # noqa: E402
from energy_overhead_analysis import EnergyConfig, concurrent_energy, single_session_energy  # noqa: E402

FIG_DIR = ROOT / "CPQ-V2X-elsarticle" / "Fig"
FIG_DIR.mkdir(parents=True, exist_ok=True)
MPL_CACHE = ROOT / ".matplotlib-cache"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt


mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.family"] = "serif"
mpl.rcParams["font.serif"] = ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"]
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42


SCHEMES_SINGLE = np.array(
    [
        "Cui et al. [25]",
        "Dabra et al. [17]",
        "Cui et al. [33]",
        "Yan et al. [35]",
        "Ours (Intra-AKA)",
        "Ours (Inter-AKA)",
        "Ours (Intra-Re-AKA)",
        "Ours (Inter-Re-AKA)",
    ],
    dtype=object,
)

_baseline_single = [
    side_tuple("Cui2019_ECPP"),
    side_tuple("Dabra2024_SL3PAKE"),
    side_tuple("Cui2025_VDT"),
    side_tuple("Yan2025_BCL3AKA"),
]
_cpq_single = [
    mode_tuple("cpq_intra_aka"),
    mode_tuple("cpq_inter_aka"),
    mode_tuple("cpq_intra_re_aka"),
    mode_tuple("cpq_inter_re_aka"),
]
VEH = np.array([item[0] for item in _baseline_single] + [item[0] for item in _cpq_single])
RSU = np.array([item[1] for item in _baseline_single] + [item[1] for item in _cpq_single])
TA = np.array([item[2] for item in _baseline_single] + [item[2] for item in _cpq_single])
TOTAL = VEH + RSU + TA

_energy_cfg = EnergyConfig()
_single_energy_keys = [
    "Cui2019",
    "Dabra2024",
    "Cui2025",
    "Yan2025",
    "Ours-Intra-AKA",
    "Ours-Inter-AKA",
    "Ours-Intra-Re-AKA",
    "Ours-Inter-Re-AKA",
]
_single_energy_rows = [single_session_energy(key, _energy_cfg) for key in _single_energy_keys]
ENERGY_COMP = np.array([row["E_comp_total_mJ"] for row in _single_energy_rows])
ENERGY_COMM = np.array([row["E_comm_total_mJ"] for row in _single_energy_rows])
ENERGY_TOTAL = ENERGY_COMP + ENERGY_COMM

SCHEMES_N = [
    "Cui et al. [25]",
    "Dabra et al. [17]",
    "Cui et al. [33]",
    "Yan et al. [35]",
    "Ours (Intra-AKA)",
    "Ours (Inter-AKA)",
    "Ours (Intra-Re-AKA)",
    "Ours (Inter-Re-AKA)",
]

DATA_MAP = {
    "Cui et al. [25]": side_tuple("Cui2019_ECPP"),
    "Dabra et al. [17]": side_tuple("Dabra2024_SL3PAKE"),
    "Cui et al. [33]": side_tuple("Cui2025_VDT"),
    "Yan et al. [35]": side_tuple("Yan2025_BCL3AKA"),
    "Ours (Intra-AKA)": mode_tuple("cpq_intra_aka"),
    "Ours (Inter-AKA)": mode_tuple("cpq_inter_aka"),
    "Ours (Intra-Re-AKA)": mode_tuple("cpq_intra_re_aka"),
    "Ours (Inter-Re-AKA)": mode_tuple("cpq_inter_re_aka"),
}

CONCURRENT_TOTAL = {
    "Cui et al. [25]": total_value("Cui2019_ECPP"),
    "Dabra et al. [17]": total_value("Dabra2024_SL3PAKE"),
    "Cui et al. [33]": total_value("Cui2025_VDT"),
    "Yan et al. [35]": total_value("Yan2025_BCL3AKA"),
    "Ours (Intra-AKA)": batch_total_alpha("cpq_intra_aka"),
    "Ours (Inter-AKA)": batch_total_alpha("cpq_inter_aka"),
    "Ours (Intra-Re-AKA)": batch_total_alpha("cpq_intra_re_aka"),
    "Ours (Inter-Re-AKA)": batch_total_alpha("cpq_inter_re_aka"),
}

CONCURRENT_RSU = {
    "Cui et al. [25]": side_tuple("Cui2019_ECPP")[1],
    "Dabra et al. [17]": side_tuple("Dabra2024_SL3PAKE")[1],
    "Cui et al. [33]": side_tuple("Cui2025_VDT")[1],
    "Yan et al. [35]": side_tuple("Yan2025_BCL3AKA")[1],
    "Ours (Intra-AKA)": batch_rsu_expr("cpq_intra_aka")[0],
    "Ours (Inter-AKA)": batch_rsu_expr("cpq_inter_aka")[0],
    "Ours (Intra-Re-AKA)": batch_rsu_expr("cpq_intra_re_aka")[0],
    "Ours (Inter-Re-AKA)": batch_rsu_expr("cpq_inter_re_aka")[0],
}

ENERGY_SCHEME_KEYS = {
    "Cui et al. [25]": "Cui2019",
    "Dabra et al. [17]": "Dabra2024",
    "Cui et al. [33]": "Cui2025",
    "Yan et al. [35]": "Yan2025",
    "Ours (Intra-AKA)": "Ours-Intra-AKA",
    "Ours (Inter-AKA)": "Ours-Inter-AKA",
    "Ours (Intra-Re-AKA)": "Ours-Intra-Re-AKA",
    "Ours (Inter-Re-AKA)": "Ours-Inter-Re-AKA",
}

PALETTE = [
    "#000000",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#D55E00",
    "#0072B2",
    "#CC79A7",
    "#7F7F7F",
]
MARKERS = ["o", "s", "^", "v", "D", "P", "X", "*"]
LINESTYLES = ["-", "--", "-.", ":", "-", "--", "-.", ":"]


def save_current(fig, stem: str) -> None:
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)


def plot_single_comp() -> None:
    mpl.rcParams.update(
        {
            "font.size": 5.8,
            "axes.labelsize": 5.8,
            "xtick.labelsize": 5.2,
            "ytick.labelsize": 5.4,
            "legend.fontsize": 5.2,
            "axes.linewidth": 0.45,
        }
    )

    schemes = SCHEMES_SINGLE[::-1]
    veh = VEH[::-1]
    rsu = RSU[::-1]
    ta = TA[::-1]
    total = TOTAL[::-1]
    y = np.arange(len(schemes))

    fig, ax = plt.subplots(figsize=(2.5, 2.12), dpi=600)
    for yi, name in enumerate(schemes):
        if str(name).startswith("Ours"):
            ax.axhspan(yi - 0.34, yi + 0.34, color="#F5F5F5", zorder=0)

    ax.barh(y, veh, height=0.52, color="#4C78A8", edgecolor="black", linewidth=0.20, label="Vehicle")
    ax.barh(y, rsu, left=veh, height=0.52, color="#F58518", edgecolor="black", linewidth=0.20, label="RSU")
    ax.barh(y, ta, left=veh + rsu, height=0.52, color="#54A24B", edgecolor="black", linewidth=0.20, label="TA/Chain")

    for yi, name in enumerate(schemes):
        if str(name).startswith("Ours"):
            ax.barh(yi, total[yi], height=0.52, color="none", edgecolor="black", linewidth=0.32)

    pad = max(total) * 0.008
    for yi, t in zip(y, total):
        ax.text(t + pad, yi, f"{t:.1f}", va="center", ha="left", fontsize=4.9)

    ax.set_xlabel(r"Computation overhead ($\mu$s)", labelpad=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(schemes)
    ax.grid(True, axis="x", linestyle="--", linewidth=0.24, alpha=0.50)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(total) * 1.10)
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    leg = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 0.96),
        ncol=3,
        frameon=True,
        edgecolor="black",
        handlelength=0.9,
        columnspacing=0.45,
        handletextpad=0.28,
        borderpad=0.18,
        labelspacing=0.18,
    )
    leg.get_frame().set_linewidth(0.35)
    plt.tight_layout(pad=0.20, rect=[0, 0, 1, 0.93])
    save_current(fig, "ComputationOverhead_single_session_comparison_small")


def curve_values(part: str, n_vals: np.ndarray) -> dict[str, np.ndarray]:
    values = {}
    for name in SCHEMES_N:
        v, r, t = DATA_MAP[name]
        if part == "vehicle":
            coeff = v
        elif part == "rsu":
            coeff = CONCURRENT_RSU[name]
        elif part == "ta":
            coeff = t
        elif part == "total":
            coeff = CONCURRENT_TOTAL[name]
        else:
            raise ValueError(part)
        values[name] = coeff * n_vals / 1000.0
    return values


def plot_curve_panel(part: str, stem: str, ylabel: str, y_floor: float | None = None) -> None:
    mpl.rcParams.update(
        {
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 6.2,
            "axes.linewidth": 0.8,
        }
    )
    n_vals = np.arange(1, 1001)
    curves = curve_values(part, n_vals)
    fig, ax = plt.subplots(figsize=(3.50, 2.60), dpi=300)
    mark_idx = list(range(0, len(n_vals), 100)) + [len(n_vals) - 1]

    for idx, name in enumerate(SCHEMES_N):
        y = curves[name]
        if y_floor is not None:
            y = np.maximum(y, y_floor)
        ax.plot(
            n_vals,
            y,
            label=name,
            color=PALETTE[idx],
            linestyle=LINESTYLES[idx],
            linewidth=0.95,
            marker=MARKERS[idx],
            markersize=3.0,
            markevery=mark_idx,
        )

    ax.set_yscale("log")
    ax.set_xlabel(r"Number of concurrent requests $N$")
    ax.set_ylabel(ylabel)
    ax.set_xlim(1, 1000)
    ax.grid(True, which="major", linestyle="--", linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    leg = ax.legend(
        fontsize=6.2,
        ncol=2,
        frameon=True,
        edgecolor="black",
        loc="lower right",
        bbox_to_anchor=(1.0, 0.02),
        handlelength=1.5,
        labelspacing=0.2,
        markerscale=0.7,
        borderpad=0.35,
        handletextpad=0.5,
        columnspacing=0.8,
    )
    leg.get_frame().set_linewidth(0.6)
    plt.tight_layout(pad=0.5)
    save_current(fig, stem)


def plot_energy_single() -> None:
    mpl.rcParams.update(
        {
            "font.size": 6.0,
            "axes.labelsize": 6.0,
            "xtick.labelsize": 5.4,
            "ytick.labelsize": 5.6,
            "legend.fontsize": 5.3,
            "axes.linewidth": 0.5,
        }
    )
    schemes = SCHEMES_SINGLE[::-1]
    comp = ENERGY_COMP[::-1]
    comm = ENERGY_COMM[::-1]
    total = ENERGY_TOTAL[::-1]
    y = np.arange(len(schemes))
    fig, ax = plt.subplots(figsize=(2.55, 2.10), dpi=600)
    for yi, name in enumerate(schemes):
        if str(name).startswith("Ours"):
            ax.axhspan(yi - 0.34, yi + 0.34, color="#F5F5F5", zorder=0)
    ax.barh(y, comp, height=0.52, color="#4C78A8", edgecolor="black", linewidth=0.20, label="Computation")
    ax.barh(y, comm, left=comp, height=0.52, color="#F58518", edgecolor="black", linewidth=0.20, label="Communication")
    pad = max(total) * 0.010
    for yi, t in zip(y, total):
        ax.text(t + pad, yi, f"{t:.2f}", va="center", ha="left", fontsize=4.9)
    ax.set_xlabel("Energy overhead (mJ)", labelpad=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(schemes)
    ax.grid(True, axis="x", linestyle="--", linewidth=0.24, alpha=0.50)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(total) * 1.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    leg = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 0.96),
        ncol=2,
        frameon=True,
        edgecolor="black",
        handlelength=0.9,
        columnspacing=0.45,
        handletextpad=0.28,
        borderpad=0.18,
    )
    leg.get_frame().set_linewidth(0.35)
    plt.tight_layout(pad=0.20, rect=[0, 0, 1, 0.93])
    save_current(fig, "EnergyOverhead_single_session_comparison")


def plot_energy_total() -> None:
    mpl.rcParams.update(
        {
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 6.2,
            "axes.linewidth": 0.8,
        }
    )
    n_vals = np.arange(1, 1001)
    fig, ax = plt.subplots(figsize=(3.50, 2.60), dpi=300)
    mark_idx = list(range(0, len(n_vals), 100)) + [len(n_vals) - 1]
    for idx, name in enumerate(SCHEMES_N):
        ax.plot(
            n_vals,
            [concurrent_energy(ENERGY_SCHEME_KEYS[name], int(n), _energy_cfg)["E_total_mJ"] for n in n_vals],
            label=name,
            color=PALETTE[idx],
            linestyle=LINESTYLES[idx],
            linewidth=0.95,
            marker=MARKERS[idx],
            markersize=3.0,
            markevery=mark_idx,
        )
    ax.set_yscale("log")
    ax.set_xlabel(r"Number of concurrent requests $N$")
    ax.set_ylabel("Total energy (mJ)")
    ax.set_xlim(1, 1000)
    ax.grid(True, which="major", linestyle="--", linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    leg = ax.legend(
        fontsize=6.2,
        ncol=2,
        frameon=True,
        edgecolor="black",
        loc="lower right",
        bbox_to_anchor=(1.0, 0.02),
        handlelength=1.5,
        labelspacing=0.2,
        markerscale=0.7,
        borderpad=0.35,
        handletextpad=0.5,
        columnspacing=0.8,
    )
    leg.get_frame().set_linewidth(0.6)
    plt.tight_layout(pad=0.5)
    save_current(fig, "Energy_Total")


if __name__ == "__main__":
    plot_single_comp()
    plot_curve_panel("vehicle", "Comp_Vehicle", r"Vehicle overhead (ms)")
    plot_curve_panel("rsu", "Comp_RSU", r"RSU overhead (ms)")
    plot_curve_panel("ta", "Comp_TAChain", r"TA/Chain overhead (ms)", y_floor=1e-4)
    plot_curve_panel("total", "Comp_Total", r"Total overhead (ms)")
    plot_energy_single()
    plot_energy_total()
    print(f"Updated figures in {FIG_DIR}")
