# jcheng-benchmark roadmap

> Status: **v0.1.0** as of 2026-11-26. The offline harness and its protocol are
> in place; no recorded or hardware benchmark has been run.

## Current state

| Item | State | Evidence |
|---|---|---|
| Repository admission manifest | Complete (2026-11-26) | `capability.yaml` |
| Offline suite, metric and report runner | Complete (2026-11-26) | `src/jcheng_benchmark/`; `tests/` |
| Benchmark protocol v1 | Complete (2026-11-26) | `docs/BENCHMARK_PROTOCOL.md` |
| Synthetic self-test of the harness | Complete (2026-11-26, synthetic only) | `tests/fixtures/synthetic/`; gate |
| Recorded-data replay benchmark | Not started | No dataset ships |
| Hardware benchmark | Not started | No hardware access by design |
| Cross-repository report contract | Not started | Repo-local v1 only |

## Milestones

| Milestone | Scope | State | Exit criterion | Evidence |
|---|---|---|---|---|
| M0 | Admission and repository skeleton | Complete (2026-11-26) | Four-document set, `capability.yaml`, CI gate, no `LICENSE` before review | `bash scripts/check_repo_gate.sh`; `.github/workflows/ci.yml` |
| M1 | Benchmark protocol v1 | Complete (2026-11-26) | Suite/sample/report formats documented and enforced by the loader and tests | `docs/BENCHMARK_PROTOCOL.md`; `src/jcheng_benchmark/model.py`; `tests/` |
| M2 | First recorded replay suite | Not started | A recorded dataset is exported, the threshold is pre-registered, and a report is stored under `evidence/` | — |
| M3 | Suite catalogue | Planned | Latency, cross-view, mobile and DDS suites each have a dataset source, a pre-registered threshold and a produced report | — |
| M4 | Read-only live acquisition adapter | Planned | A separate capability manifest declares a read-only ROS role; explicit operator authorization is recorded; no motion command | — |
| M5 | Report schema promotion to `jcheng-interfaces` | Planned | A second repository consumes the format and the contract change is accepted | — |

## Next

1. **M2 — first recorded replay suite.** Export one perception fixed-point
   dataset as JSONL with the sample fields defined in the protocol, register
   the threshold and its source before running, then commit the report under
   `evidence/benchmark_<YYYYMMDD>_<slug>/`. Prerequisites: a dataset export and
   the operator's decision on whether the recording may be stored.
2. **M3 — suite catalogue.** Add latency and cross-view suites first, then the
   mobile laser-odometry suite. Each suite needs its own data source and
   threshold; do not reuse a threshold without citing it.

## Out of scope

- Running as a runtime capability or being imported by another repository.
- Joining any DDS domain, subscribing to ROS topics or publishing commands.
- Opening cameras, serial, CAN, GPIO, servo or LiDAR devices.
- Sending motion commands, acquiring a lease or replacing the e-stop.
- Certifying safety, accuracy or reliability; a benchmark report is not an
  acceptance report.
- Generating, editing or back-filling measurement data.
- Storing large recordings or model weights in the repository.

## Dependencies

- `jcheng-interfaces` v0.1.0 is the ecosystem contract source, but this
  repository **consumes no contract** and defines none outside itself. A future
  report contract must be promoted there, not here.
- Python 3.10+ and PyYAML 6.x. No ROS distribution is required.
- Recorded datasets remain outside the repository; the report records their
  SHA-256.
- Any future hardware capture needs separate, explicit operator authorization
  per session. CI and automation never capture hardware data.
