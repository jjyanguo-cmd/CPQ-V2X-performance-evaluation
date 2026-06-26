from __future__ import annotations

import csv
from pathlib import Path

from cpq_model import build_verification_rows


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "computed_cpq_overhead.csv"


def main() -> None:
    rows = build_verification_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
