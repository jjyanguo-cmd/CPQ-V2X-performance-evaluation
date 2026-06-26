# CPQ-V2X Computation-Overhead Accounting

This directory documents the computation-overhead accounting for the four
evaluated CPQ-V2X modes.

The purpose is to avoid maintaining scattered hardcoded CPQ-V2X computation
totals in the evaluation scripts. The files separate the accounting into:

1. `cpq_operation_counts.csv`, which records the online primitive-operation
   counts for CPQ-V2X Intra-AKA, Inter-AKA, Intra-Re-AKA, and Inter-Re-AKA.
2. `cpq_reported_totals_us.csv`, which records the side-level values reported
   in the revised manuscript tables.
3. `cpq_batch_rsu_expr_us.csv`, which records the RSU-side linear expression
   parameters used for the randomized batch-verification concurrent-load model.
4. `cpq_model.py`, which reads the operation counts and primitive timings and
   exposes reusable functions for the evaluation scripts.

The primitive runtimes are read from
`../baseline_accounting/primitive_costs.csv`, so CPQ-V2X and the baseline
schemes use the same primitive-cost model.

Run `compute_cpq_overhead.py` from this directory to regenerate
`computed_cpq_overhead.csv`. The single-session CPQ-V2X computation overheads
should be fully decomposed by the listed operation counts up to rounding to
three decimal places.

The batch-verification concurrent-load expressions are kept separate from the
single-session operation counts because they represent the amortized
RSU-side randomized batch-verification model used in the manuscript's
concurrent-overhead analysis.
