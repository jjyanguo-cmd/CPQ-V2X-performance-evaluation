from __future__ import annotations

import csv
from pathlib import Path

from baseline_model import build_verification_rows

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "computed_baseline_overhead.csv"


def main() -> None:
    rows = build_verification_rows()

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scheme_key",
                "scheme_label",
                "side",
                "computed_from_listed_counts_us",
                "reported_in_manuscript_us",
                "residual_us",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
