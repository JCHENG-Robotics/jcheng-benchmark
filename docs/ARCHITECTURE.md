# Architecture

> Status: **v0.1.0** as of 2026-11-26. The harness is an offline
> file-in/report-out tool with no runtime dependency and no hardware path.

## 1. Position in the ecosystem

`jcheng-benchmark` is a **BENCH** repository. It is outside the runtime
dependency graph: no product repository imports it, it is not listed in
`jcheng-system/locks/ecosystem.lock.yaml`, and it joins no DDS domain. The
source repositories keep ownership of their data, acceptance thresholds and
`ACCEPTANCE.md`; this repository only applies a declared suite to a declared
dataset.

```text
jcheng-perception ─┐
jcheng-mobile ─────┼─ export ─→ dataset.jsonl (outside the repo)
jcheng-system ─────┘                    │
                                        ▼
suite.yaml ────────────────→ jcheng-benchmark → report.json / report.md
                                                  │
                                                  ▼
                                        evidence/benchmark_<date>_<slug>/
```

The arrow is one-way. There is no path from a report back into a runtime
repository, and no path from this repository to the robot.

## 2. Trust boundary

| Input | Trusted for | Not trusted for |
|---|---|---|
| Suite YAML | The declared metric, aggregate and threshold | That the threshold is appropriate or was registered before the data |
| JSONL dataset | The sample values and their identifiers | How the data was captured, whether it is representative, whether it is licensed |
| Operator / host / time fields | Provenance labels in the report | Identity verification |

The harness identifies both the suite and the dataset by SHA-256 and records
the hashes in the report. It does not copy the dataset into the report, and it
does not verify the capture process. That verification belongs to the source
repository's acceptance record and, for hardware data, to the operator's
session authorization.

## 3. Components

| Module | Responsibility | ROS-free |
|---|---|---|
| `src/jcheng_benchmark/model.py` | Load and validate a suite; enforce level/data-source compatibility | Yes |
| `src/jcheng_benchmark/stats.py` | Mean, nearest-rank percentiles, success rate | Yes |
| `src/jcheng_benchmark/runner.py` | Strict JSONL reader, metric computation, threshold evaluation, report mapping | Yes |
| `src/jcheng_benchmark/report.py` | JSON and Markdown rendering | Yes |
| `src/jcheng_benchmark/cli.py` | `list`, `validate`, `run` subcommands and exit codes | Yes |

The package imports only the Python standard library and PyYAML. It contains no
ROS client library, no serial or device code, no subprocess call and no network
client. `tests/test_no_hardware.py` enforces the boundary over `src/`,
`scripts/` and `benchmarks/`.

## 4. Execution flow

1. **Load the suite.** Unknown fields are rejected; metric ids must be unique;
   each threshold must name a metric and an aggregate that the metric actually
   produces.
2. **Read the dataset.** Blank lines are ignored. Every other line must be a
   JSON object with a unique non-empty `sample_id`. Invalid JSON, a duplicate
   id, a bad `trial` or a malformed value aborts the run.
3. **Compute metrics.** Each declared metric is computed over every sample.
   `position_error` uses `measured_m - reference_m` in metres and reports
   millimetres; `scalar` reads one finite numeric field; `success_rate` reads
   one boolean field.
4. **Evaluate thresholds.** Each threshold compares the declared aggregate with
   its bound. A failed bound is recorded as `pass: false` and is never replaced
   by a more favourable statistic.
5. **Decide the result.** `pass`, `fail` or `inconclusive`, with a reason.
6. **Write the report.** Optional JSON and Markdown outputs; the report records
   the suite hash, dataset hash, operator, host, time, level, data source,
   metrics, thresholds and limitations.

## 5. Failure semantics

| Condition | Result / exit code | Side effect |
|---|---|---|
| Suite cannot be parsed or violates the contract | error, exit 2 | No report |
| Dataset cannot be read, is not UTF-8 or has a malformed row | error, exit 2 | No report |
| Dataset is empty | `inconclusive` | Report with zero metrics |
| Sample count is below `min_samples` | `inconclusive` | Metrics and thresholds are still listed |
| Suite declares no thresholds | `inconclusive` | Metrics are informational |
| Any threshold fails | `fail` | The failed threshold is listed |
| All thresholds pass | `pass` | The report states the sample count |
| Report path cannot be written | error, exit 2 | No partial evidence |

The tool never drops a malformed row to make a run pass, and it never edits a
report in place. A rerun produces a new report.

## 6. Level and data-source enforcement

The loader rejects combinations that would inflate a claim:

- `L4` (replay) requires `data_source: recorded` or `hardware`.
- `L5` (hardware) requires `data_source: hardware`.
- `data_source: hardware` requires `L5`.

Synthetic and mock data are therefore limited to L1–L3. The report also adds a
limitation that says the result is not a hardware or recorded-data result.

## 7. Extension points

- **New metric kind.** Add the kind to the model, the runner, the tests, the
  protocol document and the templates. Bump the protocol document version.
- **New aggregate.** Define it precisely (interpolation matters), implement it,
  and test it against a known vector. Do not add an aggregate only in a report
  script.
- **Live acquisition.** This is deliberately out of scope for v0.1. It would be
  a separate runtime role with a read-only ROS subscription, a new capability
  manifest and its own authorization rules. It must not turn this repository
  into a runtime dependency of a capability.
- **Report contract promotion.** If a second repository consumes the report
  format, propose it to `jcheng-interfaces` under the contract change process.
  Until then the format is repository-local v1.

## 8. Why there is no runtime dependency

A benchmark tool that joins DDS or imports capability packages can accidentally
become part of the control path. Keeping it offline means:

- it cannot publish a motion command, even by mistake;
- it cannot hold a lease or keep a node alive;
- it runs on any workstation with Python, including CI;
- a benchmark result is a file, not a live system state.

The cost is that a human must export the dataset. That export is an explicit,
reviewable step, and its provenance is exactly what the report records.

## Related

- [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) — pre-registration, formats and result rules.
- [EVIDENCE.md](EVIDENCE.md) — report storage and immutability.
- [`capability.yaml`](../capability.yaml) — admission manifest.
- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) — contract source; no contract is consumed here.
- [`.github`](https://github.com/JCHENG-Robotics/.github) — ecosystem taxonomy and documentation standard.
