import os
import sys
import json
import csv
import math
import argparse
from pathlib import Path

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

from baseline_model import total_value  # noqa: E402
from cpq_model import batch_total_alpha, no_batch_total_alpha  # noqa: E402
from communication_model import total_value as comm_total_value  # noqa: E402

# =========================================================
# 0) SUMO / TraCI import
# =========================================================
if "SUMO_HOME" not in os.environ:
    raise EnvironmentError("Please set the SUMO_HOME environment variable.")

SUMO_HOME = os.environ["SUMO_HOME"]
TOOLS = os.path.join(SUMO_HOME, "tools")
if TOOLS not in sys.path:
    sys.path.append(TOOLS)

import traci  # noqa: E402

# =========================================================
# 1) Scheme data from the manuscript
#    alpha_us: dominant concurrent computation term (us/request)
#    comm_bytes: per-session communication overhead (Bytes)
# =========================================================
SCHEMES = {
    "Cui2019": {
        "alpha_us": total_value("Cui2019_ECPP"),
        "comm_bytes": comm_total_value("Cui2019_ECPP"),
    },
    "Dabra2024": {
        "alpha_us": total_value("Dabra2024_SL3PAKE"),
        "comm_bytes": comm_total_value("Dabra2024_SL3PAKE"),
    },
    "Cui2025": {
        "alpha_us": total_value("Cui2025_VDT"),
        "comm_bytes": comm_total_value("Cui2025_VDT"),
    },
    "Yan2025": {
        "alpha_us": total_value("Yan2025_BCL3AKA"),
        "comm_bytes": comm_total_value("Yan2025_BCL3AKA"),
    },

    "Ours_Intra_AKA_batch": {
        "alpha_us": batch_total_alpha("cpq_intra_aka"),
        "comm_bytes": comm_total_value("cpq_intra_aka"),
    },
    "Ours_Inter_AKA_batch": {
        "alpha_us": batch_total_alpha("cpq_inter_aka"),
        "comm_bytes": comm_total_value("cpq_inter_aka"),
    },
    "Ours_Intra_ReAKA_batch": {
        "alpha_us": batch_total_alpha("cpq_intra_re_aka"),
        "comm_bytes": comm_total_value("cpq_intra_re_aka"),
    },
    "Ours_Inter_ReAKA_batch": {
        "alpha_us": batch_total_alpha("cpq_inter_re_aka"),
        "comm_bytes": comm_total_value("cpq_inter_re_aka"),
    },

    "Ours_Intra_AKA_noBatch": {
        "alpha_us": no_batch_total_alpha("cpq_intra_aka"),
        "comm_bytes": comm_total_value("cpq_intra_aka"),
    },
    "Ours_Inter_AKA_noBatch": {
        "alpha_us": no_batch_total_alpha("cpq_inter_aka"),
        "comm_bytes": comm_total_value("cpq_inter_aka"),
    },
    "Ours_Intra_ReAKA_noBatch": {
        "alpha_us": no_batch_total_alpha("cpq_intra_re_aka"),
        "comm_bytes": comm_total_value("cpq_intra_re_aka"),
    },
    "Ours_Inter_ReAKA_noBatch": {
        "alpha_us": no_batch_total_alpha("cpq_inter_re_aka"),
        "comm_bytes": comm_total_value("cpq_inter_re_aka"),
    },
}

# =========================================================
# 2) Utility functions
# =========================================================
def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x1 - x2, y1 - y2)

def load_rsu_config(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    radius = float(data["radius_m"])
    rsus = data["rsus"]

    if not rsus:
        raise ValueError("No RSUs found in rsu_positions.json")

    for rsu in rsus:
        if not all(k in rsu for k in ("id", "x", "y")):
            raise ValueError(f"Invalid RSU entry: {rsu}")

    return radius, rsus

def extract_vehicle_count_from_cfg(cfg_path: str) -> str:
    stem = Path(cfg_path).stem
    parts = stem.split("_")
    for p in reversed(parts):
        if p.isdigit():
            return p
    return "unknown"

# =========================================================
# 3) Metric models
# =========================================================
def latency_ms(alpha_us_per_req: float, n_req: int) -> float:
    # total latency under concurrent load, unit ms
    return alpha_us_per_req * n_req / 1000.0

def throughput_mbps(comm_bytes: float, alpha_us_per_req: float) -> float:
    # Mbps = bits / microsecond
    # 1 bit/us = 1 Mbps
    return 8.0 * comm_bytes / alpha_us_per_req

# =========================================================
# 4) Main simulation logic
# =========================================================
def run_and_collect(
    sumo_cfg: str,
    rsu_json: str,
    output_csv: str,
    use_gui: bool = False,
    step_length: float = 1.0,
):
    radius_m, rsus = load_rsu_config(rsu_json)
    sumo_binary = "sumo-gui" if use_gui else "sumo"

    traci.start([
        sumo_binary,
        "-c", sumo_cfg,
        "--step-length", str(step_length)
    ])

    per_rsu_max = {rsu["id"]: 0 for rsu in rsus}
    per_rsu_peak_time = {rsu["id"]: None for rsu in rsus}

    global_nmax = 0
    global_peak_time = None
    global_peak_rsu = None

    ever_covered_any = False
    printed_debug = False

    coverage_rows = []
    metrics_rows = []

    latency_sum = {name: 0.0 for name in SCHEMES}
    valid_steps = 0

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            sim_time = traci.simulation.getTime()
            vehicle_ids = traci.vehicle.getIDList()

            if (not printed_debug) and vehicle_ids:
                xs, ys = [], []
                for vid in vehicle_ids[:20]:
                    x, y = traci.vehicle.getPosition(vid)
                    xs.append(x)
                    ys.append(y)
                print("Sample vehicle x range:", min(xs), max(xs))
                print("Sample vehicle y range:", min(ys), max(ys))
                print("RSU positions:")
                for rsu in rsus:
                    print(f"  {rsu['id']}: ({rsu['x']}, {rsu['y']}) radius={radius_m}")
                printed_debug = True

            current_counts = {rsu["id"]: 0 for rsu in rsus}

            # nearest-RSU association
            for vid in vehicle_ids:
                x, y = traci.vehicle.getPosition(vid)

                best_rid = None
                best_dist = float("inf")

                for rsu in rsus:
                    d = euclidean_distance(x, y, rsu["x"], rsu["y"])
                    if d <= radius_m and d < best_dist:
                        best_dist = d
                        best_rid = rsu["id"]

                if best_rid is not None:
                    current_counts[best_rid] += 1
                    ever_covered_any = True

            for rsu in rsus:
                rid = rsu["id"]
                c = current_counts[rid]

                if c > per_rsu_max[rid]:
                    per_rsu_max[rid] = c
                    per_rsu_peak_time[rid] = sim_time

                if c > global_nmax:
                    global_nmax = c
                    global_peak_time = sim_time
                    global_peak_rsu = rid

            current_n = max(current_counts.values()) if current_counts else 0

            row = {"time_s": sim_time, "current_n": current_n}
            row.update(current_counts)
            coverage_rows.append(row)

            metric_row = {"time_s": sim_time, "current_n": current_n}
            for name, data in SCHEMES.items():
                alpha = data["alpha_us"]
                comm_bytes = data["comm_bytes"]

                lat = latency_ms(alpha, current_n)
                thr = throughput_mbps(comm_bytes, alpha)

                metric_row[f"{name}_latency_ms"] = lat
                metric_row[f"{name}_throughput_mbps"] = thr

                latency_sum[name] += lat

            metrics_rows.append(metric_row)
            valid_steps += 1

    finally:
        traci.close()

    scenario_vehicle_count = extract_vehicle_count_from_cfg(sumo_cfg)

    result = {
        "scenario": Path(sumo_cfg).name,
        "vehicle_count": scenario_vehicle_count,
        "nmax": global_nmax,
        "peak_rsu": global_peak_rsu,
        "peak_time_s": global_peak_time,
        "radius_m": radius_m,
        "ever_covered_any": ever_covered_any,
        "num_steps": valid_steps,
    }

    for rid in per_rsu_max:
        result[f"{rid}_max"] = per_rsu_max[rid]
        result[f"{rid}_peak_time_s"] = per_rsu_peak_time[rid]

    # summary metrics
    for name, data in SCHEMES.items():
        alpha = data["alpha_us"]
        comm_bytes = data["comm_bytes"]

        result[f"{name}_avg_latency_ms"] = latency_sum[name] / valid_steps if valid_steps else 0.0
        result[f"{name}_throughput_mbps"] = throughput_mbps(comm_bytes, alpha)

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = not output_path.exists()
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(result.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(result)

    scenario_tag = Path(sumo_cfg).stem

    coverage_csv = output_path.with_name(f"{output_path.stem}_{scenario_tag}_coverage_timeseries.csv")
    if coverage_rows:
        with open(coverage_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(coverage_rows[0].keys()))
            writer.writeheader()
            writer.writerows(coverage_rows)

    metrics_csv = output_path.with_name(f"{output_path.stem}_{scenario_tag}_metrics_timeseries.csv")
    if metrics_rows:
        with open(metrics_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(metrics_rows[0].keys()))
            writer.writeheader()
            writer.writerows(metrics_rows)

    return result

# =========================================================
# 5) CLI
# =========================================================
def main():
    parser = argparse.ArgumentParser(
        description="Collect RSU load, average latency, and throughput from a SUMO scenario."
    )
    parser.add_argument("--cfg", required=True, help="Path to the SUMO configuration file (*.sumocfg)")
    parser.add_argument("--rsu", required=True, help="Path to rsu_positions.json")
    parser.add_argument("--out", default="results/latency_throughput_summary.csv", help="Path to output summary CSV")
    parser.add_argument("--gui", action="store_true", help="Run with sumo-gui instead of sumo")
    parser.add_argument("--step-length", type=float, default=1.0, help="SUMO simulation step length in seconds")

    args = parser.parse_args()

    result = run_and_collect(
        sumo_cfg=args.cfg,
        rsu_json=args.rsu,
        output_csv=args.out,
        use_gui=args.gui,
        step_length=args.step_length,
    )

    print("=" * 72)
    print("Simulation finished.")
    print(f"Scenario      : {result['scenario']}")
    print(f"Vehicle count : {result['vehicle_count']}")
    print(f"N_max         : {result['nmax']}")
    print(f"Peak RSU      : {result['peak_rsu']}")
    print(f"Peak time (s) : {result['peak_time_s']}")
    print("-" * 72)
    for name in SCHEMES:
        print(f"{name:24s} avg latency = {result[name + '_avg_latency_ms']:.4f} ms, "
              f"throughput = {result[name + '_throughput_mbps']:.4f} Mbps")
    print("=" * 72)

if __name__ == "__main__":
    main()
