from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
COMPONENTS = ROOT / "communication_components.csv"
REPORTED_TOTALS = ROOT / "communication_reported_totals_bytes.csv"

SIDES = ("vehicle", "rsu", "ta_chain")


def clean_bytes(value: float) -> int:
    rounded = round(value)
    if abs(value - rounded) > 1e-9:
        raise ValueError(f"Non-integer byte accounting result: {value}")
    return int(rounded)


def read_components() -> dict[tuple[str, str], int]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    with COMPONENTS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["scheme_key"], row["side"])
            totals[key] += float(row["size_bytes"]) * float(row["count"])
    return {key: clean_bytes(value) for key, value in totals.items()}


def read_reported_totals() -> list[dict[str, str]]:
    with REPORTED_TOTALS.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def computed_side_totals() -> dict[str, dict[str, int]]:
    raw = read_components()
    schemes = {scheme for scheme, _side in raw}
    return {
        scheme: {side: raw.get((scheme, side), 0) for side in SIDES}
        for scheme in schemes
    }


def side_tuple(scheme_key: str) -> tuple[int, int, int]:
    totals = computed_side_totals()[scheme_key]
    return tuple(totals[side] for side in SIDES)


def total_value(scheme_key: str) -> int:
    return sum(side_tuple(scheme_key))


def status_for(residual: int) -> str:
    if residual == 0:
        return "fully_decomposed_from_component_lengths"
    return "nonzero_residual_check_required"


def build_verification_rows() -> list[dict[str, object]]:
    computed = read_components()
    reported = read_reported_totals()

    rows: list[dict[str, object]] = []
    for item in reported:
        scheme_key = item["scheme_key"]
        scheme_label = item["scheme_label"]
        for side in SIDES:
            reported_bytes = int(item[f"{side}_bytes"])
            computed_bytes = computed.get((scheme_key, side), 0)
            residual_bytes = reported_bytes - computed_bytes
            rows.append(
                {
                    "scheme_key": scheme_key,
                    "scheme_label": scheme_label,
                    "side": side,
                    "computed_from_components_bytes": computed_bytes,
                    "reported_in_manuscript_bytes": reported_bytes,
                    "residual_bytes": residual_bytes,
                    "status": status_for(residual_bytes),
                }
            )

        reported_total = int(item["total_bytes"])
        computed_total = sum(computed.get((scheme_key, side), 0) for side in SIDES)
        residual_total = reported_total - computed_total
        rows.append(
            {
                "scheme_key": scheme_key,
                "scheme_label": scheme_label,
                "side": "total",
                "computed_from_components_bytes": computed_total,
                "reported_in_manuscript_bytes": reported_total,
                "residual_bytes": residual_total,
                "status": status_for(residual_total),
            }
        )

    return rows
