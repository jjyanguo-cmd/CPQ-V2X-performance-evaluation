import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, LogLocator, NullLocator
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
from cpq_model import batch_rsu_expr, mode_key_for_label, mode_tuple  # noqa: E402

# =============================================================================
# 0) Output directory
# =============================================================================
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "computation_overhead"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 1) Paper style
# =============================================================================
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['font.size'] = 8.5
mpl.rcParams['axes.linewidth'] = 0.8
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman', 'Times', 'Nimbus Roman', 'DejaVu Serif']
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42

# =============================================================================
# 2) Core data (us) -- must match the paper tables exactly
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

def get_cost_ms(name, N, part):
    """
    Return overhead in ms for a given scheme, N, and part.
    part in {'vehicle', 'rsu', 'ta', 'total'}
    """
    v, r, t = data_map[name]

    if part == "vehicle":
        res_us = v * N

    elif part == "rsu":
        if name.startswith("Ours"):
            linear, intercept = batch_rsu_expr(mode_key_for_label(name))
            res_us = linear * N + intercept
        else:
            res_us = r * N

    elif part == "ta":
        res_us = t * N

    elif part == "total":
        return (
            get_cost_ms(name, N, "vehicle")
            + get_cost_ms(name, N, "rsu")
            + get_cost_ms(name, N, "ta")
        )

    else:
        raise ValueError(f"Unknown part: {part}")

    return res_us / 1000.0  # us -> ms

# =============================================================================
# 5) Visual style
# =============================================================================
palette = [
    "#000000",  # Cui 2019
    "#E69F00",  # Dabra 2024
    "#56B4E9",  # Cui 2025
    "#009E73",  # Yan 2025
    "#D55E00",  # Ours Intra-AKA
    "#0072B2",  # Ours Inter-AKA
    "#CC79A7",  # Ours Intra-Re-AKA
    "#7F7F7F",  # Ours Inter-Re-AKA
]
markers = ['o', 's', '^', 'v', 'D', 'P', 'X', '*']
linestyles = ['-', '--', '-.', ':', '-', '--', '-.', ':']

colors_dict = {schemes[i]: palette[i] for i in range(len(schemes))}
markers_dict = {schemes[i]: markers[i] for i in range(len(schemes))}
styles_dict = {schemes[i]: linestyles[i] for i in range(len(schemes))}

# =============================================================================
# 6) Plot helper
# =============================================================================
def _set_inset_ticks(axins, yscale="log"):
    """
    Reduce inset tick density to avoid visual overlap.
    """
    if yscale == "log":
        # Keep only major ticks and hide minor ticks.
        axins.yaxis.set_minor_locator(NullLocator())
        axins.xaxis.set_major_locator(MultipleLocator(50))
    else:
        axins.yaxis.set_minor_locator(NullLocator())
        axins.xaxis.set_major_locator(MultipleLocator(50))

    axins.tick_params(axis='both', labelsize=4.8, length=2, pad=1)

def plot_panel(
    part_type,
    filename,
    ylabel,
    legend_loc="lower right",
    bbox_anchor=(1.0, 0.02),
    y_floor=None,
    add_inset=False,
    inset_cfg=None,
):
    fig, ax = plt.subplots(figsize=(3.50, 2.60), dpi=300)

    N_vals = np.arange(1, 1001)
    mark_idx = list(range(0, len(N_vals), 100)) + [len(N_vals) - 1]

    curve_cache = {}

    # -------------------------------------------------------------------------
    # Main curves
    # -------------------------------------------------------------------------
    for name in schemes:
        y = np.array([get_cost_ms(name, int(N), part_type) for N in N_vals])

        if y_floor is not None:
            y = np.maximum(y, y_floor)

        curve_cache[name] = y

        ax.plot(
            N_vals,
            y,
            label=name,
            color=colors_dict[name],
            linestyle=styles_dict[name],
            linewidth=0.95,
            marker=markers_dict[name],
            markersize=3.0,
            markevery=mark_idx,
        )

    # -------------------------------------------------------------------------
    # Main axes style
    # -------------------------------------------------------------------------
    ax.set_yscale('log')
    ax.set_xlabel(r'Number of concurrent requests $N$')
    ax.set_ylabel(ylabel)
    ax.set_xlim(1, 1000)

    ax.xaxis.set_major_locator(MultipleLocator(200))
    ax.yaxis.set_major_locator(LogLocator(base=10, numticks=5))

    ax.grid(True, which='major', linestyle='--', linewidth=0.4, alpha=0.6)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    leg = ax.legend(
        fontsize=6.2,
        ncol=2,
        frameon=True,
        edgecolor='black',
        loc=legend_loc,
        bbox_to_anchor=bbox_anchor,
        handlelength=1.5,
        labelspacing=0.2,
        markerscale=0.7,
        borderpad=0.35,
        handletextpad=0.5,
        columnspacing=0.8,
    )
    leg.get_frame().set_linewidth(0.6)

    # -------------------------------------------------------------------------
    # Inset zoom
    # -------------------------------------------------------------------------
    if add_inset and inset_cfg is not None:
        axins = inset_axes(
            ax,
            width=inset_cfg.get("width", "36%"),
            height=inset_cfg.get("height", "36%"),
            loc=inset_cfg.get("loc", "upper left"),
            borderpad=inset_cfg.get("borderpad", 0.7),
            bbox_to_anchor=inset_cfg.get("bbox_to_anchor", None),
            bbox_transform=ax.transAxes if inset_cfg.get("bbox_to_anchor", None) is not None else None,
        )

        inset_schemes = inset_cfg.get("schemes", schemes)
        x1, x2 = inset_cfg["xlim"]

        # Only selected curves in inset
        for name in inset_schemes:
            axins.plot(
                N_vals,
                curve_cache[name],
                color=colors_dict[name],
                linestyle=styles_dict[name],
                linewidth=inset_cfg.get("inset_lw", 0.95),
            )

        # Auto-compute y-range from selected curves in chosen x-range
        idx = (N_vals >= x1) & (N_vals <= x2)
        y_all = np.concatenate([curve_cache[name][idx] for name in inset_schemes])

        if y_floor is not None:
            y_all = np.maximum(y_all, y_floor)

        ymin = np.min(y_all)
        ymax = np.max(y_all)

        # Padding for log-scale inset
        ypad_ratio = inset_cfg.get("ypad_ratio", 1.15)
        ymin = ymin / ypad_ratio
        ymax = ymax * ypad_ratio

        if "ylim" in inset_cfg:
            ymin, ymax = inset_cfg["ylim"]

        axins.set_xlim(x1, x2)
        axins.set_ylim(ymin, ymax)
        axins.set_yscale("log")

        # Reduce the number of inset ticks.
        _set_inset_ticks(axins, yscale="log")

        axins.grid(True, which='major', linestyle='--', linewidth=0.3, alpha=0.5)

        for spine in axins.spines.values():
            spine.set_linewidth(inset_cfg.get("inset_spine_lw", 0.55))
            spine.set_edgecolor(inset_cfg.get("inset_spine_ec", "0.25"))

        mark_inset(
            ax,
            axins,
            loc1=inset_cfg.get("loc1", 2),
            loc2=inset_cfg.get("loc2", 4),
            fc="none",
            ec=inset_cfg.get("conn_ec", "0.35"),
            lw=inset_cfg.get("conn_lw", 0.60),
        )

    plt.tight_layout(pad=0.5)

    out_pdf = OUTPUT_DIR / filename
    out_png = OUTPUT_DIR / filename.replace(".pdf", ".png")

    plt.savefig(out_pdf, bbox_inches='tight')
    plt.savefig(out_png, bbox_inches='tight', dpi=600)
    if os.environ.get("CPQ_SHOW_FIGURES") == "1":
        plt.show()
    plt.close(fig)

    print(f"Saved: {out_pdf}")
    print(f"Saved: {out_png}")

# =============================================================================
# 7) Generate figures
# =============================================================================
if __name__ == "__main__":
    # 1) Vehicle overhead
    plot_panel(
        part_type='vehicle',
        filename="Comp_Vehicle.pdf",
        ylabel=r"Vehicle overhead (ms)",
        add_inset=True,
        inset_cfg={
            "xlim": (1, 200),
            "loc": "upper left",
            "bbox_to_anchor": (0.08, 0.05, 0.88, 0.88),   # Move the inset slightly inward.
            "width": "36%",
            "height": "36%",
            "borderpad": 0.6,
            "loc1": 2,
            "loc2": 4,
            "ypad_ratio": 1.10,
            "conn_lw": 0.60,
            "conn_ec": "0.35",
            "inset_lw": 1.00,
            "schemes": [
                "Cui et al. [33]",
                "Ours (Intra-AKA)",
                "Ours (Inter-AKA)",
                "Ours (Intra-Re-AKA)",
                "Ours (Inter-Re-AKA)",
            ],
        },
    )

    # 2) RSU overhead
    plot_panel(
        part_type='rsu',
        filename="Comp_RSU.pdf",
        ylabel=r"RSU overhead (ms)",
        add_inset=True,
        inset_cfg={
            "xlim": (600, 800),
            "loc": "center left",
            "bbox_to_anchor": (0.14, 0.08, 0.82, 0.82),   # Move the inset slightly inward.
            "width": "32%",
            "height": "32%",
            "borderpad": 0.6,
            "loc1": 2,
            "loc2": 4,
            "ypad_ratio": 1.08,
            "conn_lw": 0.60,
            "conn_ec": "0.35",
            "inset_lw": 1.00,
            "schemes": [
                "Cui et al. [33]",
                "Ours (Intra-AKA)",
                "Ours (Inter-AKA)",
                "Ours (Intra-Re-AKA)",
                "Ours (Inter-Re-AKA)",
            ],
        },
    )

    # 3) TA/Chain overhead
    plot_panel(
        part_type='ta',
        filename="Comp_TAChain.pdf",
        ylabel=r"TA/Chain overhead (ms)",
        bbox_anchor=(1.0, 0.10),
        y_floor=1e-4,
        add_inset=False,
    )

    # 4) Total overhead -- main zoomed comparison.
    plot_panel(
        part_type='total',
        filename="Comp_Total.pdf",
        ylabel=r"Total overhead (ms)",
        add_inset=True,
        inset_cfg={
            "xlim": (20, 120),                         # Narrow the range to focus on the key interval.
            "loc": "upper right",
            "bbox_to_anchor": (0.05, 0.07, 0.90, 0.86),  # Place the inset clearly inside the main panel.
            "width": "36%",
            "height": "34%",
            "borderpad": 0.5,
            "loc1": 1,
            "loc2": 3,
            "ypad_ratio": 1.06,
            "conn_lw": 0.65,
            "conn_ec": "0.30",
            "inset_lw": 1.00,
            # If the generated figure is still not ideal, adjust the inset y-limits here.
            # "ylim": (1.0, 7.0),
            "schemes": [
                "Cui et al. [33]",
                "Ours (Intra-AKA)",
                "Ours (Inter-AKA)",
                "Ours (Intra-Re-AKA)",
                "Ours (Inter-Re-AKA)",
            ],
        },
    )
