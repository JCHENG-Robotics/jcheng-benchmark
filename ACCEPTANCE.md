# Acceptance report — jcheng-benchmark

> Status: **inconclusive** as of 2026-11-26 for v0.1.0.
> Operator: JerichoCheng. Reviewer: pending.
> Scope: the offline benchmark harness, its protocol, the repository gate and
> the quarantined live probe migrated from the baseline.
> The harness passes its unit and synthetic self-tests, but no recorded dataset
> has been processed and no suite has run on hardware. The only hardware record
> is the migrated 2026-11-17 host/DDS snapshot, which is not a suite result.
> This report makes no accuracy, latency or hardware benchmark claim.
> No motion command is sent and no device is opened by this repository.

## 1. Gates

| Gate | Command | Level | Result | Evidence |
|---|---|---|---|---|
| Repository structure and boundary | `bash scripts/check_repo_gate.sh` | L0 | pass (local, 2026-11-26) | `scripts/check_repo_gate.sh` |
| Shipped suite validation | `jcheng-benchmark validate --spec benchmarks/suites/*.yaml` | L0 | pass | `benchmarks/suites/` |
| Unit and CLI tests | `python3 -m pytest -q` | L1 | pass (50 tests) | `tests/` |
| Synthetic self-test | `jcheng-benchmark run --spec tests/fixtures/synthetic/suite.yaml ...` | L2 | pass (synthetic data only) | `tests/fixtures/synthetic/`; gate output |
| Live-probe confinement | `python3 -m pytest -q tests/test_live_probe_boundary.py` | L0 | pass (local, 2026-11-26) | `tests/test_live_probe_boundary.py`; `tools/live/` |
| Recorded-data replay | `jcheng-benchmark run ...` with a recorded dataset | L4 | not run | No dataset ships |
| Hardware suite benchmark | — | L5 | not applicable (no suite) | The migrated probe snapshot is not a suite result; see below |

## 2. Verified claims

| Claim | Level | Evidence |
|---|---|---|
| Malformed JSONL, duplicate sample ids, missing fields and non-finite values abort the run | L1 | `tests/test_runner.py` |
| Position error, scalar aggregates and success rate are computed as declared | L1 | `tests/test_stats.py`, `tests/test_runner.py` |
| L4 requires a recorded/hardware source and L5 requires hardware data | L1 | `tests/test_runner.py` |
| A report records level, data source, operator, host, suite hash and dataset hash | L1–L2 | `tests/test_reports.py`, `tests/test_cli.py` |
| The harness has no ROS, DDS, device, subprocess or network path | L0 | `tests/test_no_hardware.py`; `capability.yaml` |
| The quarantined live probe has no publisher, device, container-restart or motion path, and `src/` never references it | L0 | `tests/test_live_probe_boundary.py` |
| A host/DDS snapshot was measured read-only on 2026-11-17 | L5 (read-only snapshot, not a suite) | `evidence/host_benchmark_20261117_session4/`; migrated, not re-run here |

## 3. Not verified

| Item | Reason | Risk |
|---|---|---|
| Any fixed-point, cross-view, latency or success benchmark | No recorded dataset is committed | No benchmark number exists |
| Threshold provenance for a real suite | Templates have no thresholds; a real threshold needs a cited source | A copied threshold could misrepresent the source gate |
| Replay of a real recording | M2 is not started | Export and schema compatibility are untested |
| Re-run of the live probe in this repository | The tool and its 2026-11-17 snapshot were migrated; no hardware session was held here | The snapshot may drift with RMW, link or image changes |
| Live read-only acquisition | Out of scope for v0.1; M4 | No dataset-producing live data path exists |
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
- The migrated 2026-11-17 snapshot has no suite, threshold or dataset hash; it
  cannot be promoted to a `benchmark-report` v1 claim and is not a suite pass.

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
