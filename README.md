# jcheng-benchmark

**English** | [简体中文](README.zh-CN.md)

Offline, read-only benchmark harness for the JCHENG Robotics ecosystem. It
declares benchmark suites, consumes recorded JSONL datasets exported by the
capability or system repositories, computes pre-registered metrics and writes a
provenance-labelled report. It does not join DDS, open a device, read a sensor
or command motion.

> Status: **Experimental** as of 2026-11-26. Version 0.1.0. No benchmark
> dataset or result ships with the repository; the harness is exercised only by
> synthetic self-tests, so no accuracy, latency or hardware claim is made.
> English canonical; the Chinese README is a translation.

## Scope and boundary

| Item | This repository |
|---|---|
| Layer | BENCH — outside the runtime dependency graph (see [`.github` `docs/repo-taxonomy.md`](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-taxonomy.md)) |
| Inputs | A suite YAML declaration, a recorded JSONL dataset, CLI provenance fields |
| Outputs | A JSON benchmark report and a Markdown rendering |
| Hardware access | `none` (`capability.yaml`) |
| Owned devices | None |
| Motion authority | `none`; `control_path: none` |
| Forbidden | Joining DDS/ROS, opening devices, sending motion commands, editing measurement data, presenting synthetic results as hardware results |

This repository is **not** a runtime capability. No product repository imports
it, it is not in `ecosystem.lock.yaml`, and it has no path to the robot. It is a
measurement tool: files in, reports out.

## Why this exists

Benchmark numbers were previously produced inside individual repositories with
different sample formats, aggregation rules and provenance notes. That makes
comparisons fragile and lets a synthetic run drift into a hardware claim.

This repository fixes three things:

1. **The suite is declared before the data.** Metrics, minimum sample count and
   thresholds are written down first; the dataset is collected afterwards.
2. **The data is identified, not copied.** Every report records the dataset
   SHA-256, the suite SHA-256, the operator, the host and the time. Large
   recordings stay outside the repository.
3. **The result is labelled by level and source.** A synthetic or mock run is
   never a hardware result, and a benchmark pass is never a safety
   certification.

The rules are in [docs/BENCHMARK_PROTOCOL.md](docs/BENCHMARK_PROTOCOL.md).

## What it measures

| Metric kind | Input on each sample | Output |
|---|---|---|
| `position_error` | `measured_m` and `reference_m`, each `[x, y, z]` in metres | Per-sample Euclidean error in millimetres, then mean/p50/p95/max/min |
| `scalar` | One finite numeric field, for example `latency_ms` | mean/p50/p95/max/min in the declared unit |
| `success_rate` | One boolean field, default `success` | True-count divided by sample count |

Percentiles are nearest-rank, so the definition does not depend on an
interpolation library. One malformed row aborts the run; rows are never
silently dropped.

## Repository layout

```text
jcheng-benchmark/
├── capability.yaml          # admission manifest: bench layer, no hardware
├── benchmarks/
│   ├── README.md            # suite catalogue and authoring notes
│   └── suites/              # pre-registered suite declarations (templates)
├── docs/
│   ├── ARCHITECTURE.md      # trust boundary and components
│   ├── BENCHMARK_PROTOCOL.md# pre-registration, levels, formats, result rules
│   └── EVIDENCE.md          # report storage and immutability
├── evidence/                # reports, once real datasets are processed
├── src/jcheng_benchmark/    # ROS-free runner, model, statistics, CLI
├── scripts/check_repo_gate.sh
└── tests/                   # unit, CLI, report and boundary tests
```

## Requirements

- Python 3.10 or newer (the host runs 3.12; CI covers 3.10 and 3.12).
- `PyYAML` 6.x at runtime; `pytest` 7.4+ for tests.
- No ROS distribution, no DDS middleware, no camera, serial, CAN or GPIO
  device, and no robot access.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[test]'

# Inspect and validate the shipped declarations.
jcheng-benchmark list --dir benchmarks/suites
jcheng-benchmark validate --spec benchmarks/suites/template-position-accuracy.yaml

# Exercise the harness on the committed synthetic fixture.
# This is a self-test, not a benchmark result.
jcheng-benchmark run \
  --spec tests/fixtures/synthetic/suite.yaml \
  --data tests/fixtures/synthetic/samples.jsonl \
  --operator self-test \
  --json /tmp/benchmark-report.json \
  --markdown /tmp/benchmark-report.md

# CI equivalent.
python3 -m pytest -q
bash scripts/check_repo_gate.sh
```

A run exits `0` when every declared threshold passes, `1` when a threshold
fails and `2` when the result is inconclusive or the input is invalid. Exit `0`
means "the declared gate passed for the declared data source"; it does not mean
"hardware validated".

## Validation status

| Claim | Status | Evidence |
|---|---|---|
| Suite, sample and threshold validation rejects malformed input | Partially verified (synthetic) | `tests/test_runner.py`, `tests/test_cli.py` |
| Position, scalar and success metrics compute the declared aggregates | Partially verified (synthetic) | `tests/test_stats.py`, `tests/test_runner.py` |
| A report records level, data source, operator, host and both SHA-256 hashes | Partially verified (synthetic) | `tests/test_reports.py`, synthetic self-test in the gate |
| A recorded-data replay suite has been run | Unverified | No dataset ships; M2 is not started |
| A hardware benchmark has been run | Unverified | No hardware access by design |

Full report: [ACCEPTANCE.md](ACCEPTANCE.md). The status vocabulary follows the
organization [documentation standard](https://github.com/JCHENG-Robotics/.github/blob/main/docs/documentation-standard.md).

## Benchmark levels

| Level | Environment | Allowed data source |
|---|---|---|
| L0 | Contract/static | N/A |
| L1 | Unit | `synthetic` or `mock` |
| L2 | Mock integration | `synthetic` or `mock` |
| L3 | Mock end-to-end | `synthetic` or `mock` |
| L4 | Replay | `recorded` (or `hardware` for a direct hardware recording) |
| L5 | Hardware | `hardware` |

The loader rejects `L4` with synthetic/mock data and `L5` with anything other
than `hardware`.

## Related repositories

- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) — contract source; this repository defines no cross-repo contract.
- [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) — source of fixed-point, cross-view and latency recordings.
- [`jcheng-mobile`](https://github.com/JCHENG-Robotics/jcheng-mobile) — source of laser-odometry, SLAM and Nav2 recordings.
- [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) — source of mock end-to-end and safety-path recordings.
- [`jcheng-ops`](https://github.com/JCHENG-Robotics/jcheng-ops) — operations; not a benchmark consumer.
- [`.github`](https://github.com/JCHENG-Robotics/.github) — ecosystem roadmap, changelog, acceptance and taxonomy.

## License

**Pending.** This repository has no `LICENSE` file; the third-party and
copyright review is open. See [LICENSE-REVIEW.md](LICENSE-REVIEW.md). The
runtime dependency is PyYAML (MIT); tests use pytest (MIT).
