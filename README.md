# CPQ-V2X Performance-Evaluation Package

This staging package contains performance-evaluation artifacts for the CPQ-V2X
revision. It is not a production implementation of the full protocol stack.

## Scope

The package covers:

- primitive-operation benchmark sources;
- computation-overhead accounting for CPQ-V2X and the compared baselines;
- communication-overhead accounting synchronized with the revised manuscript;
- energy-overhead accounting derived from computation and communication costs;
- SUMO/TraCI scripts and extracted latency/throughput result tables;
- plotting scripts for the evaluation figures.

## Quick Check

For the Python plotting and accounting scripts, install the lightweight Python
dependencies if they are not already available:

```bash
python -m pip install -r requirements.txt
```

Run the following command from this directory to verify that the staged
computation, communication, and energy accounting remains closed:

```bash
python verify_accounting.py
```

To verify the staged SUMO/TraCI result tables without re-running SUMO, run:

```bash
python sumo_traci/verify_sumo_results.py
```

If computation or communication accounting values are revised while the SUMO
mobility load is unchanged, first refresh the latency/throughput mapping:

```bash
python sumo_traci/recompute_latency_throughput_from_accounting.py
python sumo_traci/verify_sumo_results.py
```

The verification checks are read-only. They do not run SUMO, regenerate
figures, or compile the manuscript.

## External Tools

The accounting checks use only the staged CSV/JSON/Python files. A full SUMO
re-run additionally requires SUMO/TraCI and a valid `SUMO_HOME` environment
variable. The optional smart-contract microbenchmark requires Foundry. These
external tools are not needed for the read-only verification commands above.

## Figure Display

Plotting scripts save their output files by default. They do not open an
interactive window unless the environment variable `CPQ_SHOW_FIGURES` is set to
`1`.

## Notes

For CPQ-V2X, communication overhead is decomposed into the online message
components used in the four evaluated modes. For baseline schemes, the staged
communication accounting uses protocol-level side payloads adopted in the
revised manuscript, rather than inventing unpublished field-level
decompositions.

The SUMO/TraCI scripts extract mobility-driven concurrent authentication load
and map it to cryptographic authentication-processing latency and throughput.
They do not model PHY/MAC-layer packet loss, retransmission, channel fading,
wireless contention, or intermittent RSU connectivity.
