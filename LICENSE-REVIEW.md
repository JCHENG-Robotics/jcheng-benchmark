# License review — pending

This repository does **not** ship a `LICENSE` file. Copyright is reserved;
the JCHENG-Robotics license review is in progress, consistent with
`jcheng-system`, `jcheng-perception`, `jcheng-ops`, `jcheng-interfaces` and
`.github`.

## What is in this repository

- Original Python source, YAML suite declarations, shell and Markdown written
  for this repository.
- Deterministic synthetic fixture data under `tests/fixtures/synthetic/`; it is
  generated test input, not a recording or a benchmark result.
- No recorded datasets, no model weights, no vendor source and no copied
  third-party code.

## Third-party runtime dependencies

| Dependency | Use | License note |
|---|---|---|
| Python standard library (`argparse`, `json`, `hashlib`, `math`, `statistics`-free aggregates) | harness | PSF-2.0 |
| PyYAML 6.x | suite parsing | MIT |
| pytest 7.4+ | tests only | MIT |

None of these are vendored. The runtime dependency set is one package, PyYAML.

## Data policy

Recorded datasets stay outside the repository. Reports identify a dataset by
its SHA-256 and do not embed the data. If a dataset is ever proposed for
inclusion, its own license and the operator's permission must be reviewed
first; this review does not grant that permission.

## Secrets and weights

The repository contains no credentials. `scripts/check_repo_gate.sh` fails if a
gateway-token-like value, a `*.env` file or a model weight / recorded bag
appears in the tree.
