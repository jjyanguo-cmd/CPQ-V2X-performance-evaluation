from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PRIMITIVE_COSTS = ROOT / "primitive_costs.csv"
OPERATION_COUNTS = ROOT / "baseline_operation_counts.csv"
REPORTED_TOTALS = ROOT / "baseline_reported_totals_us.csv"

SIDES = ("vehicle", "rsu", "ta_chain")


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
            key = (row["scheme_key"], row["side"])
            totals[key] += float(row["count"]) * costs[op]
    return dict(totals)


def read_reported_totals() -> list[dict[str, str]]:
    with REPORTED_TOTALS.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def status_for(residual: float) -> str:
    if abs(residual) <= 0.001:
        return "fully_decomposed_from_operation_counts"
    return "nonzero_residual_check_required"


def computed_side_totals() -> dict[str, dict[str, float]]:
    raw = read_operation_counts()
    schemes = {scheme for scheme, _side in raw}
    return {
        scheme: {side: clean_us(raw.get((scheme, side), 0.0)) for side in SIDES}
        for scheme in schemes
    }


def side_tuple(scheme_key: str) -> tuple[float, float, float]:
    totals = computed_side_totals()[scheme_key]
    return tuple(totals[side] for side in SIDES)


def total_value(scheme_key: str) -> float:
    return clean_us(sum(side_tuple(scheme_key)))


def build_verification_rows() -> list[dict[str, object]]:
    computed = read_operation_counts()
    reported = read_reported_totals()

    rows: list[dict[str, object]] = []
    for item in reported:
        scheme_key = item["scheme_key"]
        scheme_label = item["scheme_label"]
        for side in SIDES:
            reported_us = float(item[f"{side}_us"])
            computed_us = computed.get((scheme_key, side), 0.0)
            residual_us = reported_us - computed_us
            rows.append(
                {
                    "scheme_key": scheme_key,
                    "scheme_label": scheme_label,
                    "side": side,
                    "computed_from_listed_counts_us": f"{clean_us(computed_us):.3f}",
                    "reported_in_manuscript_us": f"{clean_us(reported_us):.3f}",
                    "residual_us": f"{clean_us(residual_us):.3f}",
                    "status": status_for(residual_us),
                }
            )

        reported_total = float(item["total_us"])
        computed_total = sum(computed.get((scheme_key, side), 0.0) for side in SIDES)
        residual_total = reported_total - computed_total
        rows.append(
            {
                "scheme_key": scheme_key,
                "scheme_label": scheme_label,
                "side": "total",
                "computed_from_listed_counts_us": f"{clean_us(computed_total):.3f}",
                "reported_in_manuscript_us": f"{clean_us(reported_total):.3f}",
                "residual_us": f"{clean_us(residual_total):.3f}",
                "status": status_for(residual_total),
            }
        )

    return rows
