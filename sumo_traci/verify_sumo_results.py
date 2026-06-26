from __future__ import annotations

import csv
from pathlib import Path

from recompute_latency_throughput_from_accounting import (
    SCHEME_SPECS,
    build_summary,
    latency_ms,
    throughput_mbps,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PACKAGE_ROOT / "results" / "latency_throughput_raw_10runs.csv"
SUMMARY_CSV = PACKAGE_ROOT / "results" / "latency_throughput_mean_std.csv"

EXPECTED_COUNTS = list(range(100, 1001, 100))
EXPECTED_RUNS_PER_COUNT = 10
TOL = 1e-6


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV file: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def as_float(row: dict[str, str], key: str) -> float:
    if key not in row:
        raise KeyError(f"Missing CSV column: {key}")
    return float(row[key])


def assert_close(name: str, observed: float, expected: float, tolerance: float = TOL) -> None:
    if abs(observed - expected) > tolerance:
        raise AssertionError(
            f"{name}: expected {expected:.12f}, observed {observed:.12f}"
        )


def check_raw_rows(rows: list[dict[str, str]]) -> None:
    counts: dict[int, int] = {count: 0 for count in EXPECTED_COUNTS}
    for row in rows:
        count = int(float(row["vehicle_count"]))
        if count in counts:
            counts[count] += 1

    missing = [count for count, num_rows in counts.items() if num_rows != EXPECTED_RUNS_PER_COUNT]
    if missing:
        details = ", ".join(f"{count}:{counts[count]}" for count in missing)
        raise AssertionError(
            "Unexpected number of raw SUMO/TraCI runs per vehicle count "
            f"(expected {EXPECTED_RUNS_PER_COUNT}): {details}"
        )


def check_raw_accounting_mapping(rows: list[dict[str, str]]) -> None:
    for idx, row in enumerate(rows, start=1):
        avg_concurrent_requests = as_float(row, "avg_concurrent_requests")
        for scheme_name, (alpha_us, comm_bytes) in SCHEME_SPECS.items():
            assert_close(
                f"raw row {idx} {scheme_name} latency",
                as_float(row, f"{scheme_name}_avg_latency_ms"),
                latency_ms(alpha_us, avg_concurrent_requests),
            )
            assert_close(
                f"raw row {idx} {scheme_name} throughput",
                as_float(row, f"{scheme_name}_throughput_mbps"),
                throughput_mbps(comm_bytes, alpha_us),
            )


def check_summary_rows(rows: list[dict[str, str]]) -> dict[int, dict[str, str]]:
    by_count = {int(float(row["vehicle_count"])): row for row in rows}
    observed_counts = sorted(by_count)
    if observed_counts != EXPECTED_COUNTS:
        raise AssertionError(
            f"Unexpected summary vehicle counts: {observed_counts}; "
            f"expected {EXPECTED_COUNTS}"
        )

    for count, row in by_count.items():
        num_runs = int(float(row["num_runs"]))
        if num_runs != EXPECTED_RUNS_PER_COUNT:
            raise AssertionError(
                f"vehicle_count={count}: expected {EXPECTED_RUNS_PER_COUNT} runs, "
                f"observed {num_runs}"
            )

    return by_count


def check_summary_matches_raw(
    raw_rows: list[dict[str, str]],
    raw_fieldnames: list[str],
    summary_rows: list[dict[str, str]],
) -> None:
    expected_summary, _expected_fieldnames = build_summary(raw_rows, raw_fieldnames)
    expected_by_count = {
        int(float(row["vehicle_count"])): row
        for row in expected_summary
    }
    observed_by_count = {
        int(float(row["vehicle_count"])): row
        for row in summary_rows
    }

    for count, expected_row in expected_by_count.items():
        observed_row = observed_by_count[count]
        for key, expected_value in expected_row.items():
            if key not in observed_row:
                raise KeyError(f"Summary CSV missing column: {key}")
            if key in {"vehicle_count", "num_runs"}:
                if str(observed_row[key]) != str(expected_value):
                    raise AssertionError(
                        f"vehicle_count={count} {key}: expected {expected_value}, "
                        f"observed {observed_row[key]}"
                    )
            else:
                assert_close(
                    f"vehicle_count={count} summary {key}",
                    float(observed_row[key]),
                    float(expected_value),
                )


def main() -> int:
    raw_rows, raw_fieldnames = read_rows(RAW_CSV)
    summary_rows, _summary_fieldnames = read_rows(SUMMARY_CSV)

    check_raw_rows(raw_rows)
    check_raw_accounting_mapping(raw_rows)
    check_summary_rows(summary_rows)
    check_summary_matches_raw(raw_rows, raw_fieldnames, summary_rows)

    print("All staged SUMO/TraCI result checks passed.")
    print(
        "These checks validate mobility-driven authentication-processing metrics, "
        "not PHY/MAC-layer reliability."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
