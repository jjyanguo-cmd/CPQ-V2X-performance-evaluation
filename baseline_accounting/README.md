# Baseline Computation-Overhead Accounting

This directory documents the computation-overhead accounting used for the
baseline schemes in the CPQ-V2X performance evaluation.

The purpose is to make the baseline numbers traceable without claiming that this
package contains full reimplementations of the compared protocols.  The files
separate three layers:

1. `primitive_costs.csv` lists the primitive runtime units used in the adopted
   evaluation model.
2. `baseline_operation_counts.csv` records the online operation counts extracted
   from the protocol-level descriptions used during manuscript preparation.
3. `baseline_reported_totals_us.csv` records the side-level values reported in
   the revised manuscript tables.
4. `baseline_model.py` provides the reusable accounting functions used by the
   evaluation scripts.

Run `compute_baseline_overhead.py` from this directory to regenerate
`computed_baseline_overhead.csv`.  For schemes whose side-level value is fully
decomposed by the listed primitive counts, the residual should be zero up to
rounding.  A nonzero residual indicates an aggregate component that is retained
from the manuscript accounting, such as chain-side or transaction-preparation
overhead, and should be checked before public release.

Current verification status:

- Cui et al. [25], Dabra et al. [17], Cui et al. [33], and Yan et al. [35] are
  decomposed by the listed operation counts and match the revised manuscript
  table after rounding to three decimal places.
- For Yan et al. [35], the mapping follows the original local accounting script:
  blockchain read/write and smart-contract verification are normalized to the
  measured `T_SC_ver` unit, inner-product style vector products are normalized
  to the measured matrix-vector core, and fixed-length XOR operations are mapped
  to the lightweight vector-addition cost. This is an accounting normalization,
  not a full blockchain implementation.

The computation, energy, figure-regeneration, and SUMO/TraCI accounting scripts
read the baseline computation values from `baseline_model.py` instead of
maintaining separate hardcoded baseline totals.

These files are intended as a transparency and verification layer for the
performance-evaluation package.  They are not a substitute for independent
implementation and benchmarking of the complete baseline protocols.
