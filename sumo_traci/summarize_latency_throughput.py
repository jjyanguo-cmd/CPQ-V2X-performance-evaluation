import re
from pathlib import Path

import pandas as pd


# =============================================================================
# 0) Paths
# =============================================================================
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PACKAGE_ROOT / "results" / "latency_throughput_raw_10runs.csv"
OUT_CSV = PACKAGE_ROOT / "results" / "latency_throughput_mean_std.csv"


# =============================================================================
# 1) Helpers
# =============================================================================
def extract_vehicle_count_and_run(scenario_name: str) -> tuple[int | None, int | None]:
    """
    Extract vehicle count and run index from scenario names like:
        chaoyang_100_run1.sumocfg
        chaoyang_1000_run10.sumocfg

    Returns:
        (vehicle_count, run_id)
    """
    if not isinstance(scenario_name, str):
        return None, None

    m = re.search(r"chaoyang_(\d+)_run(\d+)\.sumocfg", scenario_name)
    if m:
        return int(m.group(1)), int(m.group(2))

    # fallback: try to extract first integer as vehicle_count
    m2 = re.search(r"(\d+)", scenario_name)
    if m2:
        return int(m2.group(1)), None

    return None, None


# =============================================================================
# 2) Load raw results
# =============================================================================
if not RAW_CSV.exists():
    raise FileNotFoundError(f"Raw CSV not found: {RAW_CSV}")

df = pd.read_csv(RAW_CSV)

if "scenario" not in df.columns:
    raise ValueError("The raw CSV must contain a 'scenario' column.")

# =============================================================================
# 3) Parse scenario metadata
# =============================================================================
parsed = df["scenario"].apply(extract_vehicle_count_and_run)
df["vehicle_count_parsed"] = parsed.apply(lambda x: x[0])
df["run_id"] = parsed.apply(lambda x: x[1])

# If the original vehicle_count column exists, prefer it if valid; otherwise use parsed
if "vehicle_count" in df.columns:
    df["vehicle_count"] = pd.to_numeric(df["vehicle_count"], errors="coerce")
    df["vehicle_count"] = df["vehicle_count"].fillna(df["vehicle_count_parsed"])
else:
    df["vehicle_count"] = df["vehicle_count_parsed"]

if df["vehicle_count"].isna().any():
    bad_rows = df[df["vehicle_count"].isna()][["scenario"]]
    raise ValueError(
        "Failed to parse vehicle_count from some scenario names.\n"
        f"Problematic rows:\n{bad_rows.to_string(index=False)}"
    )

df["vehicle_count"] = df["vehicle_count"].astype(int)

# =============================================================================
# 4) Select numeric columns for aggregation
# =============================================================================
# Exclude helper columns and columns that should not be averaged directly
exclude_cols = {
    "vehicle_count_parsed",
    "run_id",
}

numeric_cols: list[str] = []
for col in df.columns:
    if col in exclude_cols:
        continue
    if col == "vehicle_count":
        continue
    if col == "scenario":
        continue

    # convert if possible
    converted = pd.to_numeric(df[col], errors="coerce")
    if converted.notna().any():
        df[col] = converted
        numeric_cols.append(col)

# =============================================================================
# 5) Group and aggregate mean/std
# =============================================================================
grouped = df.groupby("vehicle_count", sort=True)

summary_parts = []

# count runs
run_counts = grouped.size().rename("num_runs").to_frame()
summary_parts.append(run_counts)

# mean
mean_df = grouped[numeric_cols].mean()
mean_df = mean_df.rename(columns={col: f"{col}_mean" for col in mean_df.columns})
summary_parts.append(mean_df)

# std
std_df = grouped[numeric_cols].std(ddof=1)
std_df = std_df.fillna(0.0)
std_df = std_df.rename(columns={col: f"{col}_std" for col in std_df.columns})
summary_parts.append(std_df)

summary = pd.concat(summary_parts, axis=1).reset_index()

# =============================================================================
# 6) Optional: keep some convenient alias columns for plotting
# =============================================================================
# These aliases make plotting easier without always typing *_mean
alias_candidates = [
    "nmax",
    "peak_time_s",
]

for base_col in alias_candidates:
    mean_col = f"{base_col}_mean"
    if mean_col in summary.columns:
        summary[base_col] = summary[mean_col]

# =============================================================================
# 7) Save
# =============================================================================
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print(f"Saved summary CSV: {OUT_CSV}")
print(f"Rows: {len(summary)}")
print("Vehicle counts included:", summary["vehicle_count"].tolist())
print("Number of aggregated numeric metrics:", len(numeric_cols))
