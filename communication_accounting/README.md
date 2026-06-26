# Communication-Overhead Accounting

This directory documents the communication-overhead accounting used by the
performance-evaluation staging package.

The accounting is intentionally split into two levels.

1. For CPQ-V2X, `communication_components.csv` records the online message
   components in the four evaluated modes and their encoded byte lengths under
   the manuscript parameter setting. The main encoded lengths are
   `ring_element_Rq = 384` B, `proof_vector_tau = 768` B,
   `reconciliation_hint = 32` B, `hash_digest = 32` B, `timestamp = 4` B,
   `TID_intra = 48` B, `TID_inter = 64` B, and
   `domain_id = 16` B. The encrypted credential payload `C_i` is represented
   by its adopted manuscript-accounting length.
2. For the compared baseline schemes, `communication_components.csv` records
   protocol-level vehicle-side, RSU-side, and TA/Chain-side online payload
   components used in the revised manuscript accounting. This avoids inventing
   field-level decompositions that are not exposed by the baseline protocol
   descriptions.

`communication_reported_totals_bytes.csv` contains the side-level values
reported in the revised manuscript communication table. Running
`compute_communication_overhead.py` regenerates
`computed_communication_overhead.csv`, which compares component-derived values
against the reported totals. All residuals should be zero if the staged
accounting remains synchronized with the manuscript.

The reusable `communication_model.py` module is imported by the communication
plotting, energy-accounting, and SUMO latency/throughput scripts. This keeps
communication, computation, and energy values from being maintained as
independent hardcoded tables in multiple files.
