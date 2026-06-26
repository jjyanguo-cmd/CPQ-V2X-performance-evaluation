# SUMO/TraCI Scenario Evaluation

This directory contains the scripts used to extract mobility-driven concurrent
authentication load from a SUMO road-network scenario and to map that load to
the cryptographic latency and throughput metrics reported in the manuscript.

The scripts evaluate authentication-processing performance under the extracted
mobility load. They do not model PHY/MAC-layer packet loss, retransmission,
channel fading, wireless contention, or intermittent RSU connectivity.

## Files

- `chaoyang.net.xml`: SUMO road network used by the staged scenario.
- `vtype.xml`: vehicle type configuration used for scenario generation.
- `rsu_positions.json`: RSU coordinates and coverage radius.
- `generate_scenarios.ps1`: generates randomized SUMO route/configuration files
  for 100 to 1000 vehicles with 10 runs per vehicle count.
- `collect_latency_throughput.py`: runs one SUMO configuration through TraCI and
  appends authentication-processing metrics to the raw CSV.
- `run_collect_all.ps1`: runs the collector over all generated SUMO
  configuration files and writes the raw CSV to `../results/`.
- `summarize_latency_throughput.py`: aggregates the raw 10-run results into the
  mean/std summary CSV used by the plotting scripts and manuscript.
- `recompute_latency_throughput_from_accounting.py`: reuses the staged
  mobility-derived average concurrent-request load and recomputes all
  authentication latency/throughput columns from the current computation and
  communication accounting model.
- `verify_sumo_results.py`: performs a read-only consistency check over the
  staged raw and summary CSV files.

## Quick Verification Without Re-running SUMO

From the package root, run:

```bash
python sumo_traci/verify_sumo_results.py
```

This check verifies that the staged CSV files contain 10 runs for each vehicle
count from 100 to 1000, that the raw latency/throughput columns are consistent
with the current accounting model, and that the summary CSV is reproduced from
the raw CSV. It does not require SUMO, TraCI, or pandas.

If the computation or communication accounting changes while the SUMO mobility
load remains unchanged, re-map the staged load to the updated accounting model
before re-plotting:

```bash
python sumo_traci/recompute_latency_throughput_from_accounting.py
python sumo_traci/verify_sumo_results.py
```

## Optional Full SUMO Re-run

The full SUMO/TraCI workflow requires SUMO and a valid `SUMO_HOME` environment
variable. From this directory, run:

```powershell
.\generate_scenarios.ps1
.\run_collect_all.ps1
python .\summarize_latency_throughput.py
```

The generated scenario directories may be large and are not included in this
staging package. They can be regenerated from the provided network, vehicle
type, and random-trip settings.

## Interpretation Boundary

The output should be interpreted as cryptographic authentication-processing
latency and throughput under mobility-driven concurrent access load. It should
not be interpreted as an end-to-end wireless reliability or link-layer
performance evaluation.
