import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys
import pandas as pd

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BASELINE_ACCOUNTING = PACKAGE_ROOT / "baseline_accounting"
if str(BASELINE_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(BASELINE_ACCOUNTING))
CPQ_ACCOUNTING = PACKAGE_ROOT / "cpq_accounting"
if str(CPQ_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(CPQ_ACCOUNTING))
COMMUNICATION_ACCOUNTING = PACKAGE_ROOT / "communication_accounting"
if str(COMMUNICATION_ACCOUNTING) not in sys.path:
    sys.path.insert(0, str(COMMUNICATION_ACCOUNTING))

from baseline_model import side_tuple, total_value  # noqa: E402
from cpq_model import batch_rsu_expr, batch_total_expr, mode_total, mode_tuple  # noqa: E402
from communication_model import side_tuple as comm_side_tuple, total_value as comm_total_value  # noqa: E402

_CUI2019 = side_tuple("Cui2019_ECPP")
_DABRA2024 = side_tuple("Dabra2024_SL3PAKE")
_CUI2025 = side_tuple("Cui2025_VDT")
_YAN2025 = side_tuple("Yan2025_BCL3AKA")
_CPQ_INTRA = mode_tuple("cpq_intra_aka")
_CPQ_INTER = mode_tuple("cpq_inter_aka")
_CPQ_RE_INTRA = mode_tuple("cpq_intra_re_aka")
_CPQ_RE_INTER = mode_tuple("cpq_inter_re_aka")
_COMM_CUI2019 = comm_side_tuple("Cui2019_ECPP")
_COMM_DABRA2024 = comm_side_tuple("Dabra2024_SL3PAKE")
_COMM_CUI2025 = comm_side_tuple("Cui2025_VDT")
_COMM_YAN2025 = comm_side_tuple("Yan2025_BCL3AKA")
_COMM_CPQ_INTRA = comm_side_tuple("cpq_intra_aka")
_COMM_CPQ_INTER = comm_side_tuple("cpq_inter_aka")
_COMM_CPQ_RE_INTRA = comm_side_tuple("cpq_intra_re_aka")
_COMM_CPQ_RE_INTER = comm_side_tuple("cpq_inter_re_aka")

# =========================================================
# 1) Raw data from your paper tables
# =========================================================

# --- Single-session computation overhead (us)
COMP_SINGLE_US: Dict[str, Dict[str, float]] = {
    "Cui2019":      {"Vehicle": _CUI2019[0], "RSU": _CUI2019[1], "TA": _CUI2019[2], "Total": total_value("Cui2019_ECPP")},
    "Dabra2024":    {"Vehicle": _DABRA2024[0], "RSU": _DABRA2024[1], "TA": _DABRA2024[2], "Total": total_value("Dabra2024_SL3PAKE")},
    "Cui2025":      {"Vehicle": _CUI2025[0], "RSU": _CUI2025[1], "TA": _CUI2025[2], "Total": total_value("Cui2025_VDT")},
    "Yan2025":      {"Vehicle": _YAN2025[0], "RSU": _YAN2025[1], "TA": _YAN2025[2], "Total": total_value("Yan2025_BCL3AKA")},

    "Ours-Intra-AKA":    {"Vehicle": _CPQ_INTRA[0], "RSU": _CPQ_INTRA[1], "TA": _CPQ_INTRA[2], "Total": mode_total("cpq_intra_aka")},
    "Ours-Inter-AKA":    {"Vehicle": _CPQ_INTER[0], "RSU": _CPQ_INTER[1], "TA": _CPQ_INTER[2], "Total": mode_total("cpq_inter_aka")},
    "Ours-Intra-Re-AKA": {"Vehicle": _CPQ_RE_INTRA[0], "RSU": _CPQ_RE_INTRA[1], "TA": _CPQ_RE_INTRA[2], "Total": mode_total("cpq_intra_re_aka")},
    "Ours-Inter-Re-AKA": {"Vehicle": _CPQ_RE_INTER[0], "RSU": _CPQ_RE_INTER[1], "TA": _CPQ_RE_INTER[2], "Total": mode_total("cpq_inter_re_aka")},
}

# --- Single-session communication overhead (bytes)
COMM_SINGLE_B: Dict[str, Dict[str, float]] = {
    "Cui2019":      {"Vehicle": _COMM_CUI2019[0], "RSU": _COMM_CUI2019[1], "TA": _COMM_CUI2019[2], "Total": comm_total_value("Cui2019_ECPP")},
    "Dabra2024":    {"Vehicle": _COMM_DABRA2024[0], "RSU": _COMM_DABRA2024[1], "TA": _COMM_DABRA2024[2], "Total": comm_total_value("Dabra2024_SL3PAKE")},
    "Cui2025":      {"Vehicle": _COMM_CUI2025[0], "RSU": _COMM_CUI2025[1], "TA": _COMM_CUI2025[2], "Total": comm_total_value("Cui2025_VDT")},
    "Yan2025":      {"Vehicle": _COMM_YAN2025[0], "RSU": _COMM_YAN2025[1], "TA": _COMM_YAN2025[2], "Total": comm_total_value("Yan2025_BCL3AKA")},

    "Ours-Intra-AKA":    {"Vehicle": _COMM_CPQ_INTRA[0], "RSU": _COMM_CPQ_INTRA[1], "TA": _COMM_CPQ_INTRA[2], "Total": comm_total_value("cpq_intra_aka")},
    "Ours-Inter-AKA":    {"Vehicle": _COMM_CPQ_INTER[0], "RSU": _COMM_CPQ_INTER[1], "TA": _COMM_CPQ_INTER[2], "Total": comm_total_value("cpq_inter_aka")},
    "Ours-Intra-Re-AKA": {"Vehicle": _COMM_CPQ_RE_INTRA[0], "RSU": _COMM_CPQ_RE_INTRA[1], "TA": _COMM_CPQ_RE_INTRA[2], "Total": comm_total_value("cpq_intra_re_aka")},
    "Ours-Inter-Re-AKA": {"Vehicle": _COMM_CPQ_RE_INTER[0], "RSU": _COMM_CPQ_RE_INTER[1], "TA": _COMM_CPQ_RE_INTER[2], "Total": comm_total_value("cpq_inter_re_aka")},
}

# --- Concurrent-N computation expressions from your table
# form: a*N + b
COMP_CONCURRENT_EXPR: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Cui2019": {
        "Vehicle": (_CUI2019[0], 0.0),
        "RSU":   (_CUI2019[1], 0.0),
        "TA":    (_CUI2019[2], 0.0),
        "Total": (total_value("Cui2019_ECPP"), 0.0),
    },
    "Dabra2024": {
        "Vehicle": (_DABRA2024[0], 0.0),
        "RSU":   (_DABRA2024[1], 0.0),
        "TA":    (_DABRA2024[2], 0.0),
        "Total": (total_value("Dabra2024_SL3PAKE"), 0.0),
    },
    "Cui2025": {
        "Vehicle": (_CUI2025[0], 0.0),
        "RSU":   (_CUI2025[1], 0.0),
        "TA":    (_CUI2025[2], 0.0),
        "Total": (total_value("Cui2025_VDT"), 0.0),
    },
    "Yan2025": {
        "Vehicle": (_YAN2025[0], 0.0),
        "RSU":   (_YAN2025[1], 0.0),
        "TA":    (_YAN2025[2], 0.0),
        "Total": (total_value("Yan2025_BCL3AKA"), 0.0),
    },
    "Ours-Intra-AKA": {
        "Vehicle": (_CPQ_INTRA[0], 0.0),
        "RSU":   batch_rsu_expr("cpq_intra_aka"),
        "TA":    (0.0,    0.0),
        "Total": batch_total_expr("cpq_intra_aka"),
    },
    "Ours-Inter-AKA": {
        "Vehicle": (_CPQ_INTER[0], 0.0),
        "RSU":   batch_rsu_expr("cpq_inter_aka"),
        "TA":    (0.0,    0.0),
        "Total": batch_total_expr("cpq_inter_aka"),
    },
    "Ours-Intra-Re-AKA": {
        "Vehicle": (_CPQ_RE_INTRA[0], 0.0),
        "RSU":   batch_rsu_expr("cpq_intra_re_aka"),
        "TA":    (0.0,    0.0),
        "Total": batch_total_expr("cpq_intra_re_aka"),
    },
    "Ours-Inter-Re-AKA": {
        "Vehicle": (_CPQ_RE_INTER[0], 0.0),
        "RSU":   batch_rsu_expr("cpq_inter_re_aka"),
        "TA":    (0.0,    0.0),
        "Total": batch_total_expr("cpq_inter_re_aka"),
    },
}


# =========================================================
# 2) Energy assumptions
# =========================================================

@dataclass
class EnergyConfig:
    # Device powers (W)
    p_obu: float = 7.0       # peak OBU power
    p_rsu: float = 26.0      # max RSU power
    p_ta: float = 26.0       # assumed TA/Chain compute-side power

    # Active radio power (W)
    p_radio: float = 0.91

    # Effective PC5 rate (bps), conservative 10 MHz
    rate_bps: float = 15.84e6

    # Whether to include TA/Chain side
    include_ta_compute: bool = True
    include_ta_comm: bool = True

    # System-level sender + receiver accounting
    duplex_factor: float = 2.0


# =========================================================
# 3) Helpers
# =========================================================

def us_to_s(x_us: float) -> float:
    return x_us * 1e-6

def bytes_to_bits(x_b: float) -> float:
    return x_b * 8.0

def round_df(df: pd.DataFrame, digits: int = 3) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if c != "Scheme" and pd.api.types.is_numeric_dtype(out[c]):
            out[c] = out[c].round(digits)
    return out

def percent_diff(ours: float, baseline: float) -> float:
    if baseline == 0:
        return math.nan
    return (ours - baseline) / baseline * 100.0

def reduction_or_increase_label(ours: float, baseline: float) -> str:
    if ours < baseline:
        return "Reduced"
    elif ours > baseline:
        return "Increased"
    return "Equal"


# =========================================================
# 4) Single-session energy
# =========================================================

def single_session_energy(scheme: str, cfg: EnergyConfig) -> Dict[str, float]:
    comp = COMP_SINGLE_US[scheme]
    comm = COMM_SINGLE_B[scheme]

    # Computation-side energy
    e_comp_v = cfg.p_obu * us_to_s(comp["Vehicle"])
    e_comp_r = cfg.p_rsu * us_to_s(comp["RSU"])
    e_comp_t = cfg.p_ta * us_to_s(comp["TA"]) if cfg.include_ta_compute else 0.0
    e_comp_total = e_comp_v + e_comp_r + e_comp_t

    # Communication-side energy
    total_comm_b = comm["Vehicle"] + comm["RSU"] + (comm["TA"] if cfg.include_ta_comm else 0.0)
    e_comm_total = cfg.duplex_factor * cfg.p_radio * bytes_to_bits(total_comm_b) / cfg.rate_bps

    e_total = e_comp_total + e_comm_total

    return {
        "Scheme": scheme,
        "E_comp_total_mJ": e_comp_total * 1000.0,
        "E_comm_total_mJ": e_comm_total * 1000.0,
        "E_total_mJ": e_total * 1000.0,
    }

def build_single_energy_table(cfg: EnergyConfig, only_ours: bool = False) -> pd.DataFrame:
    names = list(COMP_SINGLE_US.keys())
    if only_ours:
        names = [n for n in names if n.startswith("Ours-")]
    rows = [single_session_energy(n, cfg) for n in names]
    return round_df(pd.DataFrame(rows))


# =========================================================
# 5) Concurrent-N energy
# =========================================================

def expr_value_us(expr: Tuple[float, float], N: int, include_intercept: bool = True) -> float:
    a, b = expr
    return a * N + (b if include_intercept else 0.0)

def concurrent_comp_total_us(scheme: str, N: int, include_intercept: bool = True) -> float:
    return expr_value_us(COMP_CONCURRENT_EXPR[scheme]["Total"], N, include_intercept)

def concurrent_comm_total_b(scheme: str, N: int) -> float:
    # communication scales linearly with N
    return COMM_SINGLE_B[scheme]["Total"] * N

def concurrent_energy(
    scheme: str,
    N: int,
    cfg: EnergyConfig,
    include_intercept: bool = False,
) -> Dict[str, float]:
    # Side-specific computation energy.  This is important for CPQ-V2X because
    # RSU-side batch verification changes the RSU coefficient but not the
    # vehicle-side coefficient.
    expr = COMP_CONCURRENT_EXPR[scheme]
    vehicle_us = expr_value_us(expr["Vehicle"], N, include_intercept)
    rsu_us = expr_value_us(expr["RSU"], N, include_intercept)
    ta_us = expr_value_us(expr["TA"], N, include_intercept)

    e_comp_v = cfg.p_obu * us_to_s(vehicle_us)
    e_comp_r = cfg.p_rsu * us_to_s(rsu_us)
    e_comp_t = cfg.p_ta * us_to_s(ta_us) if cfg.include_ta_compute else 0.0
    e_comp_total = e_comp_v + e_comp_r + e_comp_t

    # total communication energy
    total_comm_b = concurrent_comm_total_b(scheme, N)
    e_comm_total = cfg.duplex_factor * cfg.p_radio * bytes_to_bits(total_comm_b) / cfg.rate_bps

    e_total = e_comp_total + e_comm_total

    return {
        "Scheme": scheme,
        "N": N,
        "E_comp_total_mJ": e_comp_total * 1000.0,
        "E_comm_total_mJ": e_comm_total * 1000.0,
        "E_total_mJ": e_total * 1000.0,
    }

def build_concurrent_energy_table(
    N: int,
    cfg: EnergyConfig,
    only_ours: bool = False,
    include_intercept: bool = False,
) -> pd.DataFrame:
    names = list(COMP_CONCURRENT_EXPR.keys())
    if only_ours:
        names = [n for n in names if n.startswith("Ours-")]
    rows = [concurrent_energy(n, N, cfg, include_intercept=include_intercept) for n in names]
    return round_df(pd.DataFrame(rows))


# =========================================================
# 6) Comparison tables
# =========================================================

def compare_to_baselines(
    df: pd.DataFrame,
    ours_scheme: str,
    metric_col: str,
) -> pd.DataFrame:
    baselines = [s for s in df["Scheme"].tolist() if not s.startswith("Ours-")]
    ours_val = float(df.loc[df["Scheme"] == ours_scheme, metric_col].iloc[0])

    rows = []
    for b in baselines:
        base_val = float(df.loc[df["Scheme"] == b, metric_col].iloc[0])
        diff = ours_val - base_val
        pct = percent_diff(ours_val, base_val)
        rows.append({
            "Baseline": b,
            "Ours": ours_scheme,
            "BaselineValue": base_val,
            "OursValue": ours_val,
            "Diff(Ours-Baseline)": diff,
            "Relation": reduction_or_increase_label(ours_val, base_val),
            "PercentChange(%)": pct,
        })
    return round_df(pd.DataFrame(rows))

def compare_single_energy_all_ours(cfg: EnergyConfig) -> Dict[str, pd.DataFrame]:
    df = build_single_energy_table(cfg, only_ours=False)
    ours_modes = [s for s in df["Scheme"].tolist() if s.startswith("Ours-")]
    return {ours: compare_to_baselines(df, ours, "E_total_mJ") for ours in ours_modes}

def compare_concurrent_energy_all_ours(N: int, cfg: EnergyConfig) -> Dict[str, pd.DataFrame]:
    df = build_concurrent_energy_table(N, cfg, only_ours=False)
    ours_modes = [s for s in df["Scheme"].tolist() if s.startswith("Ours-")]
    return {ours: compare_to_baselines(df, ours, "E_total_mJ") for ours in ours_modes}


# =========================================================
# 7) Pretty print
# =========================================================

def print_comparison_dict(title: str, comp_dict: Dict[str, pd.DataFrame]):
    print(f"\n{'='*90}\n{title}\n{'='*90}")
    for ours, df in comp_dict.items():
        print(f"\n--- {ours} ---")
        print(df.to_string(index=False))


# =========================================================
# 8) Demo
# =========================================================

if __name__ == "__main__":
    cfg = EnergyConfig(
        p_obu=7.0,
        p_rsu=26.0,
        p_ta=26.0,
        p_radio=0.91,
        rate_bps=15.84e6,   # 10 MHz conservative case
        include_ta_compute=True,
        include_ta_comm=True,
        duplex_factor=2.0,
    )

    # A. Single-session energy table
    print("\n=== Single-session energy table (all schemes) ===")
    df_single = build_single_energy_table(cfg, only_ours=False)
    print(df_single.to_string(index=False))

    # B. Single-session comparisons
    single_cmp = compare_single_energy_all_ours(cfg)
    print_comparison_dict("Single-session energy comparisons", single_cmp)

    # C. Concurrent-N energy table
    N = 100
    print(f"\n=== Concurrent-N energy table (N={N}) ===")
    df_conc = build_concurrent_energy_table(N, cfg, only_ours=False)
    print(df_conc.to_string(index=False))

    # D. Concurrent-N comparisons
    conc_cmp = compare_concurrent_energy_all_ours(N, cfg)
    print_comparison_dict(f"Concurrent-N energy comparisons (N={N})", conc_cmp)
