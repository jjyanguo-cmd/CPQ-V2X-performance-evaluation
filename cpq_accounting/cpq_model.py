from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = ROOT.parent
PRIMITIVE_COSTS = PACKAGE_ROOT / "baseline_accounting" / "primitive_costs.csv"
OPERATION_COUNTS = ROOT / "cpq_operation_counts.csv"
REPORTED_TOTALS = ROOT / "cpq_reported_totals_us.csv"
BATCH_RSU_EXPR = ROOT / "cpq_batch_rsu_expr_us.csv"

SIDES = ("vehicle", "rsu", "ta_chain")

MODE_LABELS = {
    "cpq_intra_aka": "Ours (Intra-AKA)",
    "cpq_inter_aka": "Ours (Inter-AKA)",
    "cpq_intra_re_aka": "Ours (Intra-Re-AKA)",
    "cpq_inter_re_aka": "Ours (Inter-Re-AKA)",
}
LABEL_TO_MODE = {label: mode_key for mode_key, label in MODE_LABELS.items()}


def clean_us(value: float) -> float:
    rounded = round(value, 3)
    return 0.0 if abs(rounded) < 0.0005 else rounded


def read_primitive_costs() -> dict[str, float]:
    costs: dict[str, float] = {}
    with PRIMITIVE_COSTS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            costs[row["operation_symbol"]] = float(row["cost_us"])
    return costs


def read_operation_counts(costs: dict[str, float] | None = None) -> dict[tuple[str, str], float]:
    if costs is None:
        costs = read_primitive_costs()

    totals: dict[tuple[str, str], float] = defaultdict(float)
    with OPERATION_COUNTS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            op = row["operation_symbol"]
            if op not in costs:
                raise KeyError(f"Missing primitive cost for {op}")
            key = (row["mode_key"], row["side"])
            totals[key] += float(row["count"]) * costs[op]
    return dict(totals)


def computed_side_totals() -> dict[str, dict[str, float]]:
    raw = read_operation_counts()
    return {
        mode: {side: clean_us(raw.get((mode, side), 0.0)) for side in SIDES}
        for mode in MODE_LABELS
    }


def mode_tuple(mode_key: str) -> tuple[float, float, float]:
    totals = computed_side_totals()[mode_key]
    return tuple(totals[side] for side in SIDES)


def mode_key_for_label(mode_label: str) -> str:
    return LABEL_TO_MODE[mode_label]


def mode_total(mode_key: str) -> float:
    return clean_us(sum(mode_tuple(mode_key)))


def read_reported_totals() -> list[dict[str, str]]:
    with REPORTED_TOTALS.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_batch_rsu_expr() -> dict[str, tuple[float, float]]:
    expr: dict[str, tuple[float, float]] = {}
    with BATCH_RSU_EXPR.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            expr[row["mode_key"]] = (
                float(row["batch_rsu_linear_us"]),
                float(row["batch_rsu_intercept_us"]),
            )
    return expr


def batch_rsu_expr(mode_key: str) -> tuple[float, float]:
    linear, intercept = read_batch_rsu_expr()[mode_key]
    return clean_us(linear), clean_us(intercept)


def batch_total_expr(mode_key: str) -> tuple[float, float]:
    vehicle_us, _rsu_us, ta_us = mode_tuple(mode_key)
    rsu_linear, rsu_intercept = batch_rsu_expr(mode_key)
    return clean_us(vehicle_us + rsu_linear + ta_us), clean_us(rsu_intercept)


def batch_total_alpha(mode_key: str) -> float:
    linear, _intercept = batch_total_expr(mode_key)
    return linear


def no_batch_total_alpha(mode_key: str) -> float:
    return mode_total(mode_key)


def status_for(residual: float) -> str:
    if abs(residual) <= 0.001:
        return "fully_decomposed_from_operation_counts"
    return "nonzero_residual_check_required"


def build_verification_rows() -> list[dict[str, object]]:
    computed = read_operation_counts()
    reported = read_reported_totals()

    rows: list[dict[str, object]] = []
    for item in reported:
        mode_key = item["mode_key"]
        mode_label = item["mode_label"]
        for side in SIDES:
            reported_us = float(item[f"{side}_us"])
            computed_us = computed.get((mode_key, side), 0.0)
            residual_us = reported_us - computed_us
            rows.append(
                {
                    "mode_key": mode_key,
                    "mode_label": mode_label,
                    "side": side,
                    "computed_from_listed_counts_us": f"{clean_us(computed_us):.3f}",
                    "reported_in_manuscript_us": f"{clean_us(reported_us):.3f}",
                    "residual_us": f"{clean_us(residual_us):.3f}",
                    "status": status_for(residual_us),
                }
            )

        reported_total = float(item["total_us"])
        computed_total = sum(computed.get((mode_key, side), 0.0) for side in SIDES)
        residual_total = reported_total - computed_total
        rows.append(
            {
                "mode_key": mode_key,
                "mode_label": mode_label,
                "side": "total",
                "computed_from_listed_counts_us": f"{clean_us(computed_total):.3f}",
                "reported_in_manuscript_us": f"{clean_us(reported_total):.3f}",
                "residual_us": f"{clean_us(residual_total):.3f}",
                "status": status_for(residual_total),
            }
        )

    return rows
