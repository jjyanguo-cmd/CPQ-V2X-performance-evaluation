from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
for subdir in ("baseline_accounting", "cpq_accounting", "communication_accounting"):
    path = PACKAGE_ROOT / subdir
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from baseline_model import total_value as baseline_total_us  # noqa: E402
from communication_model import total_value as communication_total_bytes  # noqa: E402
from cpq_model import batch_total_alpha, no_batch_total_alpha  # noqa: E402


RAW_CSV = PACKAGE_ROOT / "results" / "latency_throughput_raw_10runs.csv"
SUMMARY_CSV = PACKAGE_ROOT / "results" / "latency_throughput_mean_std.csv"


SCHEME_SPECS: dict[str, tuple[float, int]] = {
    "Cui2019": (
        baseline_total_us("Cui2019_ECPP"),
        communication_total_bytes("Cui2019_ECPP"),
    ),
    "Dabra2024": (
        baseline_total_us("Dabra2024_SL3PAKE"),
        communication_total_bytes("Dabra2024_SL3PAKE"),
    ),
    "Cui2025": (
        baseline_total_us("Cui2025_VDT"),
        communication_total_bytes("Cui2025_VDT"),
    ),
    "Yan2025": (
        baseline_total_us("Yan2025_BCL3AKA"),
        communication_total_bytes("Yan2025_BCL3AKA"),
    ),
    "Ours_Intra_AKA_batch": (
        batch_total_alpha("cpq_intra_aka"),
        communication_total_bytes("cpq_intra_aka"),
    ),
    "Ours_Inter_AKA_batch": (
        batch_total_alpha("cpq_inter_aka"),
        communication_total_bytes("cpq_inter_aka"),
    ),
    "Ours_Intra_ReAKA_batch": (
        batch_total_alpha("cpq_intra_re_aka"),
        communication_total_bytes("cpq_intra_re_aka"),
    ),
    "Ours_Inter_ReAKA_batch": (
        batch_total_alpha("cpq_inter_re_aka"),
        communication_total_bytes("cpq_inter_re_aka"),
    ),
    "Ours_Intra_AKA_noBatch": (
        no_batch_total_alpha("cpq_intra_aka"),
        communication_total_bytes("cpq_intra_aka"),
    ),
    "Ours_Inter_AKA_noBatch": (
        no_batch_total_alpha("cpq_inter_aka"),
        communication_total_bytes("cpq_inter_aka"),
    ),
    "Ours_Intra_ReAKA_noBatch": (
        no_batch_total_alpha("cpq_intra_re_aka"),
        communication_total_bytes("cpq_intra_re_aka"),
    ),
    "Ours_Inter_ReAKA_noBatch": (
        no_batch_total_alpha("cpq_inter_re_aka"),
        communication_total_bytes("cpq_inter_re_aka"),
    ),
}


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing raw CSV: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def latency_ms(alpha_us_per_request: float, avg_concurrent_requests: float) -> float:
    return alpha_us_per_request * avg_concurrent_requests / 1000.0


def throughput_mbps(comm_bytes: int, alpha_us_per_request: float) -> float:
    return 8.0 * comm_bytes / alpha_us_per_request


def infer_avg_concurrent_requests(row: dict[str, str], anchor_scheme: str) -> float:
    if row.get("avg_concurrent_requests"):
        return float(row["avg_concurrent_requests"])

    if anchor_scheme not in SCHEME_SPECS:
        raise KeyError(f"Unknown anchor scheme: {anchor_scheme}")

    anchor_alpha_us, _anchor_comm_bytes = SCHEME_SPECS[anchor_scheme]
    anchor_latency_key = f"{anchor_scheme}_avg_latency_ms"
    if anchor_latency_key not in row:
        raise KeyError(
            f"Cannot infer mobility load because column {anchor_latency_key!r} "
            "is missing from the raw CSV."
        )

    return float(row[anchor_latency_key]) * 1000.0 / anchor_alpha_us


def update_raw_rows(rows: list[dict[str, str]], anchor_scheme: str) -> list[dict[str, str]]:
    updated: list[dict[str, str]] = []
    for row in rows:
        avg_concurrent_requests = infer_avg_concurrent_requests(row, anchor_scheme)
        new_row = dict(row)
        new_row["avg_concurrent_requests"] = f"{avg_concurrent_requests:.12f}"

        for scheme_name, (alpha_us, comm_bytes) in SCHEME_SPECS.items():
            new_row[f"{scheme_name}_avg_latency_ms"] = (
                f"{latency_ms(alpha_us, avg_concurrent_requests):.15f}"
            )
            new_row[f"{scheme_name}_throughput_mbps"] = (
                f"{throughput_mbps(comm_bytes, alpha_us):.15f}"
            )
        updated.append(new_row)

    return updated


def parse_float(value: str) -> float | None:
    if value in ("", "True", "False"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def build_summary(rows: list[dict[str, str]], fieldnames: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    groups: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        vehicle_count = int(float(row["vehicle_count"]))
        groups.setdefault(vehicle_count, []).append(row)

    numeric_cols: list[str] = []
    excluded = {"scenario", "vehicle_count", "peak_rsu"}
    for field in fieldnames:
        if field in excluded:
            continue
        values = [parse_float(row.get(field, "")) for row in rows]
        if any(value is not None and math.isfinite(value) for value in values):
            numeric_cols.append(field)

    summary_fieldnames = ["vehicle_count", "num_runs"]
    summary_fieldnames += [f"{col}_mean" for col in numeric_cols]
    summary_fieldnames += [f"{col}_std" for col in numeric_cols]
    for alias in ("nmax", "peak_time_s"):
        if alias in numeric_cols:
            summary_fieldnames.append(alias)

    summary_rows: list[dict[str, str]] = []
    for vehicle_count in sorted(groups):
        group = groups[vehicle_count]
        out: dict[str, str] = {
            "vehicle_count": str(vehicle_count),
            "num_runs": str(len(group)),
        }
        for col in numeric_cols:
            values = [
                parsed
                for row in group
                if (parsed := parse_float(row.get(col, ""))) is not None
            ]
            if not values:
                continue
            out[f"{col}_mean"] = f"{statistics.fmean(values):.15f}"
            out[f"{col}_std"] = (
                f"{statistics.stdev(values):.15f}" if len(values) > 1 else "0.000000000000000"
            )

        for alias in ("nmax", "peak_time_s"):
            mean_key = f"{alias}_mean"
            if mean_key in out:
                out[alias] = out[mean_key]

        summary_rows.append(out)

    return summary_rows, summary_fieldnames


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute scenario latency/throughput CSVs from the staged mobility "
            "load and the current computation/communication accounting model."
        )
    )
    parser.add_argument("--raw", type=Path, default=RAW_CSV, help="Raw per-run CSV to update")
    parser.add_argument("--summary", type=Path, default=SUMMARY_CSV, help="Mean/std summary CSV to write")
    parser.add_argument(
        "--anchor-scheme",
        default="Cui2019",
        choices=sorted(SCHEME_SPECS),
        help=(
            "Scheme used to infer average concurrent requests when the raw CSV "
            "does not already contain avg_concurrent_requests."
        ),
    )
    args = parser.parse_args()

    rows, fieldnames = read_rows(args.raw)
    if "avg_concurrent_requests" not in fieldnames:
        insert_after = "num_steps" if "num_steps" in fieldnames else "ever_covered_any"
        insert_at = fieldnames.index(insert_after) + 1 if insert_after in fieldnames else len(fieldnames)
        fieldnames = fieldnames[:insert_at] + ["avg_concurrent_requests"] + fieldnames[insert_at:]

    updated_rows = update_raw_rows(rows, args.anchor_scheme)
    write_rows(args.raw, updated_rows, fieldnames)

    summary_rows, summary_fieldnames = build_summary(updated_rows, fieldnames)
    write_rows(args.summary, summary_rows, summary_fieldnames)

    print(f"Updated raw CSV: {args.raw}")
    print(f"Updated summary CSV: {args.summary}")
    print(f"Rows: {len(updated_rows)} raw runs, {len(summary_rows)} vehicle-count groups")
    print(f"Anchor scheme for inferred mobility load: {args.anchor_scheme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
