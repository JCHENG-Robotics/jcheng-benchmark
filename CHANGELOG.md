# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- CI targets Python 3.12 only, matching the Jazzy/Ubuntu 24.04 default
  toolchain.

### Added

- Migrated the read-only host/DDS probe from the frozen `jcheng-manipulation`
  v1.0.0 baseline (`a08b8b6`): `tools/live/host_benchmark.py`,
  `tools/live/run_benchmark.sh` and their tests. The probe is quarantined: not
  packaged, not imported by `jcheng_benchmark`, and statically checked by
  `tests/test_live_probe_boundary.py`.
- Migrated the 2026-11-17 Session 4 host/DDS snapshots to
  `evidence/host_benchmark_20261117_session4/` (byte-for-byte copy) and the
  report to `docs/HOST_BENCHMARK.md`.
- `scripts/check_repo_gate.sh` now checks the probe's shell/Python syntax, its
  confinement and its documentation; `pytest` also collects
  `tools/live/tests`.

## [0.1.0] — 2026-11-26

First version. No tag was created before the first CI run; the release is
pinned to the `jcheng-benchmark` repository only and introduces no cross-repo
contract.

### Added

- `src/jcheng_benchmark/` — an offline, ROS-free harness: suite loader,
  strict JSONL reader, three metric kinds (`position_error`, `scalar`,
  `success_rate`), nearest-rank aggregates, threshold evaluation, and JSON plus
  Markdown reports carrying the operator, host, suite SHA-256 and dataset
  SHA-256.
- `benchmarks/suites/` — three template declarations (position accuracy,
  scalar latency, success rate) with no thresholds; templates produce an
  inconclusive, informational result until a threshold is registered.
- `docs/BENCHMARK_PROTOCOL.md` — pre-registration rules, level and data-source
  mapping, suite/sample/report formats, result semantics and evidence rules.
- `docs/ARCHITECTURE.md` — the file-in/report-out trust boundary and the
  explicit no-DDS/no-device/no-motion design.
- `docs/EVIDENCE.md` — report directory naming, required companion files and
  immutability rules.
- `capability.yaml` — admission manifest: layer `bench`, status `experimental`,
  `hardware_access: none`, `motion_authority: none`, empty topics.
- `tests/` — 50 unit, CLI, report, contract and no-hardware boundary tests; a
  deterministic synthetic fixture exercises pass, fail and inconclusive paths.
- `scripts/check_repo_gate.sh` — required files, no `LICENSE`, shell/Python
  syntax, secret/weight scan, suite validation, tests, synthetic self-test and
  relative-link check.
- `.github/workflows/ci.yml` — `benchmark-gate` on Python 3.10 and 3.12.
