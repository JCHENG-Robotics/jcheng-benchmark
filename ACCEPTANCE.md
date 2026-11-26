# Acceptance report — jcheng-benchmark

> Status: **inconclusive** as of 2026-11-26 for v0.1.0.
> Operator: JerichoCheng. Reviewer: pending.
> Scope: the offline benchmark harness, its protocol and the repository gate.
> The harness passes its unit and synthetic self-tests, but no recorded dataset
> has been processed and no hardware benchmark exists. This report makes no
> accuracy, latency or hardware claim.
> No motion command is sent and no device is opened by this repository.

## 1. Gates

| Gate | Command | Level | Result | Evidence |
|---|---|---|---|---|
| Repository structure and boundary | `bash scripts/check_repo_gate.sh` | L0 | pass (local, 2026-11-26) | `scripts/check_repo_gate.sh` |
| Shipped suite validation | `jcheng-benchmark validate --spec benchmarks/suites/*.yaml` | L0 | pass | `benchmarks/suites/` |
| Unit and CLI tests | `python3 -m pytest -q` | L1 | pass (50 tests) | `tests/` |
| Synthetic self-test | `jcheng-benchmark run --spec tests/fixtures/synthetic/suite.yaml ...` | L2 | pass (synthetic data only) | `tests/fixtures/synthetic/`; gate output |
| Recorded-data replay | `jcheng-benchmark run ...` with a recorded dataset | L4 | not run | No dataset ships |
| Hardware benchmark | — | L5 | not applicable | No hardware access by design |

## 2. Verified claims

| Claim | Level | Evidence |
|---|---|---|
| Malformed JSONL, duplicate sample ids, missing fields and non-finite values abort the run | L1 | `tests/test_runner.py` |
| Position error, scalar aggregates and success rate are computed as declared | L1 | `tests/test_stats.py`, `tests/test_runner.py` |
| L4 requires a recorded/hardware source and L5 requires hardware data | L1 | `tests/test_runner.py` |
| A report records level, data source, operator, host, suite hash and dataset hash | L1–L2 | `tests/test_reports.py`, `tests/test_cli.py` |
| The harness has no ROS, DDS, device, subprocess or network path | L0 | `tests/test_no_hardware.py`; `capability.yaml` |

## 3. Not verified

| Item | Reason | Risk |
|---|---|---|
| Any fixed-point, cross-view, latency or success benchmark | No recorded dataset is committed | No benchmark number exists |
| Threshold provenance for a real suite | Templates have no thresholds; a real threshold needs a cited source | A copied threshold could misrepresent the source gate |
| Replay of a real recording | M2 is not started | Export and schema compatibility are untested |
| Live read-only acquisition | Out of scope for v0.1; M4 | No live data path exists |
| Report-schema compatibility with another repository | Repo-local v1 only | A future consumer may need a promoted contract |
| Long-run or large-dataset behaviour | Only small synthetic fixtures were run | Memory and runtime at production scale are unknown |

## 4. Limitations

- The harness is a file-to-report tool; it does not capture data and cannot
  verify how a recording was produced.
- Synthetic and mock results are labelled and never count as hardware
  validation.
- A benchmark threshold is a project gate, not a safety certification.
- A benchmark report is not an acceptance report and does not replace the
  source repository's `ACCEPTANCE.md`.
- Percentiles are nearest-rank; a report is only comparable with another report
  that uses the same definition and the same declared aggregate.
- The templates ship with zero thresholds deliberately. Running one produces
  an inconclusive, informational result.

## 5. Sign-off

| Role | Name | Date |
|---|---|---|
| Operator | JerichoCheng | 2026-11-26 |
| Reviewer | pending | — |

## 6. Machine-readable report

None. Per-run benchmark reports use the repository-local
`benchmark-report` v1 format described in `docs/BENCHMARK_PROTOCOL.md`; they
are not `acceptance-report.v1` documents. An acceptance report, when produced,
must validate against
`jcheng-interfaces/schemas/acceptance-report.v1.schema.json`.
