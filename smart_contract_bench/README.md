# Smart-Contract Microbenchmark

This directory contains the minimal Foundry project used to account for the
smart-contract verification component of the blockchain-assisted baseline.

It is included only as a microbenchmark for the adopted performance model. It
is not a deployment-ready blockchain system and does not implement the complete
baseline protocol stack.

## Files

- `src/YanVerify.sol`: Solidity verification contract used by the benchmark.
- `test/YanVerify.t.sol`: Foundry test/benchmark harness.
- `foundry.toml` and `foundry.lock`: Foundry project configuration files.

## Optional Check

With Foundry installed, run the following command from this directory:

```bash
forge test
```

The resulting gas measurement is used only for normalizing the Chain-side
operation in the evaluation accounting.
