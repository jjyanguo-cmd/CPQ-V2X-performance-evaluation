from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
for subdir in (
    "baseline_accounting",
    "cpq_accounting",
    "communication_accounting",
    "evaluation_accounting",
):
    path = ROOT / subdir
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import baseline_model  # noqa: E402
import communication_model  # noqa: E402
import cpq_model  # noqa: E402
from energy_overhead_analysis import EnergyConfig, build_single_energy_table  # noqa: E402


def check_residuals(name: str, rows: list[dict[str, object]], residual_field: str, tolerance: float) -> int:
    failures: list[dict[str, object]] = []
    for row in rows:
        residual = abs(float(row[residual_field]))
        status = str(row.get("status", ""))
        if residual > tolerance or status.startswith("nonzero"):
            failures.append(row)

    if failures:
        print(f"[FAIL] {name}: {len(failures)} nonzero residual rows")
        for row in failures:
            print(f"  - {row}")
        return 1

    print(f"[OK] {name}: {len(rows)} residual rows closed")
    return 0


def check_energy_summary() -> int:
    expected = {
        "Ours-Intra-AKA": (0.715, 4.022, 4.737),
        "Ours-Inter-AKA": (0.736, 4.052, 4.788),
        "Ours-Intra-Re-AKA": (0.475, 1.846, 2.321),
        "Ours-Inter-Re-AKA": (0.497, 1.860, 2.357),
    }

    cfg = EnergyConfig()
    df = build_single_energy_table(cfg, only_ours=False)
    rows = {row["Scheme"]: row for row in df.to_dict("records")}

    failures: list[str] = []
    for scheme, values in expected.items():
        row = rows.get(scheme)
        if row is None:
            failures.append(f"{scheme}: missing from energy table")
            continue
        observed = (
            float(row["E_comp_total_mJ"]),
            float(row["E_comm_total_mJ"]),
            float(row["E_total_mJ"]),
        )
        if observed != values:
            failures.append(f"{scheme}: expected {values}, observed {observed}")

    if failures:
        print("[FAIL] CPQ-V2X energy summary mismatch")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("[OK] CPQ-V2X energy summary matches the staged manuscript values")
    return 0


def main() -> int:
    status = 0
    status |= check_residuals(
        "baseline computation accounting",
        baseline_model.build_verification_rows(),
        "residual_us",
        0.001,
    )
    status |= check_residuals(
        "CPQ-V2X computation accounting",
        cpq_model.build_verification_rows(),
        "residual_us",
        0.001,
    )
    status |= check_residuals(
        "communication accounting",
        communication_model.build_verification_rows(),
        "residual_bytes",
        0.0,
    )
    status |= check_energy_summary()

    if status:
        print("\nAccounting verification failed.")
        return 1

    print("\nAll staged accounting checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
